"""Build the feed with Python 3.11+, using only the standard library."""
import argparse
import html
import json
import re
import shutil
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {'a': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom',
      'op': 'http://a9.com/-/spec/opensearch/1.1/',
      'dc': 'http://purl.org/dc/elements/1.1/'}
LAST_REQUEST = 0.0


def now():
    return datetime.now(timezone.utc)


def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def date(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def request(url, attempts=3):
    global LAST_REQUEST
    for attempt in range(attempts):
        try:
            # arXiv requests are sequential and at least 3 seconds apart.
            if urllib.parse.urlparse(url).hostname in {'export.arxiv.org', 'rss.arxiv.org'}:
                time.sleep(max(0, 3.2 - (time.monotonic() - LAST_REQUEST)))
                LAST_REQUEST = time.monotonic()
            req = urllib.request.Request(url, headers={'User-Agent': 'RobotPapers/2.1 (https://github.com/liujy25/robot-papers)',
                                                       'Accept': 'application/atom+xml, application/json, application/xml;q=0.9, */*;q=0.1'})
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            # Retrying an identical refused request does not resolve HTTP 406.
            if isinstance(exc, urllib.error.HTTPError) and exc.code in {400, 401, 403, 404, 406}:
                raise
            if attempt == attempts - 1:
                raise
            delay = 8 * (attempt + 1)
            if isinstance(exc, urllib.error.HTTPError):
                retry_after = exc.headers.get('Retry-After', '')
                if retry_after.isdigit():
                    delay = min(120, max(delay, int(retry_after)))
            print(f'Retrying request in {delay}s: {exc}', flush=True)
            time.sleep(delay)


def parse_feed(body):
    root = ET.fromstring(body)
    if root.tag != '{' + NS['a'] + '}feed':
        raise ValueError('arXiv did not return an Atom feed')
    papers = []
    for entry in root.findall('a:entry', NS):
        text = lambda key: ' '.join(entry.findtext(key, '', NS).split())
        identifier = text('a:id').replace('http://', 'https://')
        if not re.fullmatch(r'https://arxiv.org/abs/[\w./-]+v\d+', identifier):
            raise ValueError(f'arXiv returned an invalid paper entry: {identifier}')
        published, updated = text('a:published'), text('a:updated')
        date(published)
        date(updated)
        papers.append(dict(id=identifier, title=text('a:title'), summary=text('a:summary'),
                           published=published, updated=updated,
                           authors=[' '.join(a.findtext('a:name', '', NS).split()) for a in entry.findall('a:author', NS)],
                           pdf_url=identifier.replace('/abs/', '/pdf/'), comment=text('arxiv:comment') or None))
    total = root.findtext('op:totalResults', None, NS)
    if total is None:
        raise ValueError('Missing arXiv result count')
    return papers, int(total)


def fetch_source(source, cutoff):
    papers = []
    size = min(source.get('limit', 200), 500)
    if size < 1:
        raise ValueError('Source limit must be positive')
    start = 0
    while start < 20000:
        query = urllib.parse.urlencode(dict(search_query=f"cat:{source['category']}", start=start,
                                           max_results=size, sortBy='lastUpdatedDate', sortOrder='descending'))
        # Retry malformed/non-XML responses as well as transport errors.
        for attempt in range(3):
            try:
                batch, total = parse_feed(request('https://export.arxiv.org/api/query?' + query))
                break
            except (ET.ParseError, ValueError):
                if attempt == 2:
                    raise
                time.sleep(8 * (attempt + 1))
        if not batch and start < total:
            raise ValueError('Unexpected empty arXiv page')
        papers.extend(p for p in batch if date(p['updated']) >= cutoff)
        if not batch or min(date(p['updated']) for p in batch) < cutoff or start + len(batch) >= total:
            return papers
        start += len(batch)
    raise ValueError('Backfill limit reached before the date window was covered')


def fetch_daily(source, cutoff):
    """Official announcements are a fallback, not a complete historical query."""
    root = ET.fromstring(request('https://rss.arxiv.org/atom/' + source['category']))
    if root.tag != '{' + NS['a'] + '}feed':
        raise ValueError('Daily source did not return an Atom feed')
    feed_date = date(root.findtext('a:updated', '', NS))
    if now() - feed_date > timedelta(days=7):
        raise ValueError('Daily feed is older than seven days')
    papers = []
    for entry in root.findall('a:entry', NS):
        text = lambda key: ' '.join(entry.findtext(key, '', NS).split())
        identifier = text('a:id').removeprefix('oai:arXiv.org:')
        if not re.fullmatch(r'[\w./-]+v\d+', identifier):
            raise ValueError('Invalid daily paper identifier')
        announcement = date(text('a:published'))
        if announcement < cutoff:
            continue
        url = 'https://arxiv.org/abs/' + identifier
        summary = text('a:summary').split('Abstract:', 1)[-1].strip()
        papers.append(dict(id=url, title=text('a:title'), summary=summary,
                           authors=[a.strip() for a in text('dc:creator').split(',') if a.strip()],
                           updated=stamp(announcement), published=stamp(announcement),
                           pdf_url=url.replace('/abs/', '/pdf/'), comment=None,
                           metadata_source='rss', announce_type=text('arxiv:announce_type')))
    return papers


def paper_rank(paper):
    # Prefer the newest version; API dates are authoritative for the same version.
    version = re.search(r'v(\d+)$', paper['id'])
    return (int(version[1]) if version else 0, paper.get('metadata_source') != 'rss', date(paper['updated']))


def source_cutoff(source, previous, cache, cutoff):
    last_api = previous.get('last_api_success')
    if not last_api and previous.get('state') == 'ok':
        last_api = previous.get('last_success')
    if last_api and any(source['title'] in subjects for subjects in cache.values()):
        try:
            return max(cutoff, date(last_api) - timedelta(days=2))
        except ValueError:
            pass
    return cutoff


def paper_key(paper):
    return re.sub(r'v\d+$', '', paper['id'].replace('http://', 'https://'))


def merge(cache, fetched, cutoff):
    by_source = {}
    for subjects in cache.values():
        for subject, papers in subjects.items():
            by_source.setdefault(subject, []).extend(papers)
    for subject, papers in fetched.items():
        by_source.setdefault(subject, []).extend(papers)
    result = {}
    for subject, papers in by_source.items():
        unique = {}
        for p in papers:
            if date(p['updated']) < cutoff:
                continue
            key = paper_key(p)
            if key not in unique or paper_rank(p) >= paper_rank(unique[key]):
                unique[key] = p
        for p in unique.values():
            day = p['updated'][:10] + 'T00:00:00Z'
            result.setdefault(day, {}).setdefault(subject, []).append(p)
    return result


def highlighter(words):
    pattern = re.compile(r'(?<!\w)(' + '|'.join(re.escape(w) for w in sorted(set(words), key=len, reverse=True)) + r')(?!\w)', re.I) if words else None
    def highlight(text):
        if not pattern:
            return html.escape(text)
        parts, end = [], 0
        for match in pattern.finditer(text):
            parts.extend((html.escape(text[end:match.start()]), '<mark>' + html.escape(match.group()) + '</mark>'))
            end = match.end()
        return ''.join(parts) + html.escape(text[end:])
    return highlight


def render(cache, status, config, target):
    preferences = json.loads((ROOT / 'preferences.json').read_text())
    highlight = highlighter(preferences['keywords'])
    authors = {a.casefold() for a in preferences['authors']}
    conference = re.compile(r'(?<!\w)(' + '|'.join(re.escape(c) for c in preferences['conferences']) + r')(?!\w)', re.I)
    sections, count, unique = [], 0, set()
    # Keep all category memberships even when a failed source has an older version.
    all_entries = {}
    for subjects in cache.values():
        for subject, papers in subjects.items():
            for p in papers:
                key = paper_key(p)
                if key not in all_entries:
                    all_entries[key] = (p, set())
                previous, categories = all_entries[key]
                categories.add(subject)
                if paper_rank(p) >= paper_rank(previous):
                    all_entries[key] = (p, categories)
    days = {}
    for key, (p, categories) in all_entries.items():
        days.setdefault(p['updated'][:10], {})[key] = (p, sorted(categories))
    for day, entries in sorted(days.items(), reverse=True):
        cards = []
        for key, (p, categories) in sorted(entries.items(), key=lambda item: item[1][0]['updated'], reverse=True):
            if key in unique:
                continue
            unique.add(key)
            count += 1
            followed = any(a.casefold() in authors for a in p['authors'])
            tags = ''.join(f'<span class="tag">{html.escape(c)}</span>' for c in categories)
            match = conference.search(p.get('comment') or '')
            if match:
                tags += f'<span class="tag conference">{html.escape(match.group())}</span>'
            if p.get('metadata_source') == 'rss':
                tags += '<span class="tag">官方公告</span>'
            if (p.get('metadata_source') == 'rss' and p.get('announce_type') in {'replace', 'replace-cross'}) or (p.get('metadata_source') != 'rss' and p['updated'] != p['published']):
                tags += '<span class="tag revision">修订</span>'
            if followed:
                tags += '<span class="tag followed">★ 关注作者</span>'
            author_html = ', '.join(f'<strong>{html.escape(a)}</strong>' if a.casefold() in authors else html.escape(a) for a in p['authors'])
            url = paper_key(p)
            if not re.fullmatch(r'https://arxiv.org/abs/[\w./-]+', url):
                raise ValueError('Unsafe paper URL')
            dates = (f"公告 {p['updated'][:10]} · 投稿日期见 arXiv" if p.get('metadata_source') == 'rss'
                     else f"更新 {p['updated'][:10]} · 首发 {p['published'][:10]}")
            cards.append(f'''<article class="paper" data-categories="{html.escape(json.dumps(categories), quote=True)}" data-followed="{str(followed).lower()}">
              <div class="paper-meta">{tags}</div>
              <h3><a href="{url}" target="_blank" rel="noopener">{highlight(p['title'])}</a></h3>
              <p class="authors">{author_html}</p>
              <details class="abstract"><summary>摘要 <span aria-hidden="true">＋</span></summary><p>{html.escape(p['summary'])}</p>
              <p class="comment">{html.escape(p.get('comment') or '')}</p></details>
              <div class="paper-links"><a href="{url}" target="_blank" rel="noopener">arXiv ↗</a><a href="{url.replace('/abs/', '/pdf/')}" target="_blank" rel="noopener">PDF ↗</a><span>{dates}</span></div>
            </article>''')
        if cards:
            sections.append(f'<section class="day"><h2><time datetime="{day[:10]}">{day[:10]}</time><span>{len(cards)} 篇</span></h2><div class="paper-list">' + ''.join(cards) + '</div></section>')
    newest = max((d[:10] for d in cache), default='暂无数据')
    template = (ROOT / 'includes/index.html').read_text()
    replacements = {'TITLE': html.escape(config['site_title']), 'PAPERS': ''.join(sections), 'COUNT': str(count),
                    'LATEST': newest, 'BUILD_TIME': status['built_at'], 'DAYS': str(config['limit_days'])}
    for key, value in replacements.items():
        template = template.replace('<!--' + key + '-->', value)
    target.mkdir(parents=True, exist_ok=True)
    for file in (ROOT / 'statics').iterdir():
        if file.is_file():
            shutil.copy2(file, target / file.name)
    (target / 'index.html').write_text(template)
    (target / 'cache.json').write_text(json.dumps(cache, ensure_ascii=False))
    (target / 'status.json').write_text(json.dumps(status, ensure_ascii=False))
    (target / '.nojekyll').touch()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline-cache', type=Path, help='Preview only; does not claim a successful sync')
    parser.add_argument('--output', type=Path, default=ROOT / 'target')
    args = parser.parse_args()
    config = tomllib.loads((ROOT / 'config.toml').read_text())
    cutoff = now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=config['limit_days'] - 1)
    cache, previous = {}, {}
    if args.offline_cache:
        cache = json.loads(args.offline_cache.read_text())
    else:
        try:
            cache = json.loads(request(config['cache_url']))
        except Exception as exc:
            print(f'Cache unavailable: {exc}', flush=True)
        try:
            previous = json.loads(request(urllib.parse.urljoin(config['cache_url'], 'status.json'), attempts=1))
        except Exception:
            pass
    status = dict(built_at=stamp(now()), preview=bool(args.offline_cache), sources={})
    fetched = {}
    for source in config['sources']:
        title = source['title']
        old = previous.get('sources', {}).get(title, {})
        item = dict(category=source['category'], last_success=old.get('last_success'),
                    last_api_success=old.get('last_api_success') or (old.get('last_success') if old.get('state') == 'ok' else None), state='cached')
        if not args.offline_cache:
            try:
                fetch_cutoff = source_cutoff(source, old, cache, cutoff)
                print(f'{title}: querying updates since {stamp(fetch_cutoff)}', flush=True)
                fetched[title] = fetch_source(source, fetch_cutoff)
                item.update(state='ok', last_success=stamp(now()), last_api_success=stamp(now()), count=len(fetched[title]))
                print(f'{title}: {item["count"]} papers fetched', flush=True)
            except Exception as exc:
                item['error'] = str(exc)
                print(f'::warning::{title}: API unavailable ({exc}); trying official daily feed', flush=True)
                try:
                    fetched[title] = fetch_daily(source, cutoff)
                    item.update(state='rss', last_success=stamp(now()), count=len(fetched[title]))
                    print(f'{title}: {len(fetched[title])} daily announcements fetched; historical backfill pending', flush=True)
                except Exception as daily_exc:
                    item['daily_error'] = str(daily_exc)
                    print(f'::warning::{title}: daily feed unavailable ({daily_exc}); keeping cached papers', flush=True)
        status['sources'][title] = item
    if not fetched and not args.offline_cache:
        raise RuntimeError('All sources failed; the existing published site is retained')
    merged = merge(cache, fetched, cutoff)
    if not merged:
        raise RuntimeError('No papers available; refusing an empty deployment')
    render(merged, status, config, args.output)
    print(f'Built {args.output}/index.html', flush=True)


if __name__ == '__main__':
    main()
