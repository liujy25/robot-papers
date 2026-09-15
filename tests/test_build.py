import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('build', Path(__file__).resolve().parents[1] / 'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

FEED = '''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/">
<opensearch:totalResults>1</opensearch:totalResults><entry>
<id>http://arxiv.org/abs/2609.12345v2</id><title>A &amp; B &lt;script&gt;</title>
<published>2026-09-10T12:00:00Z</published><updated>2026-09-15T12:00:00Z</updated>
<summary>Robot control.</summary><author><name>Fei Gao</name></author>
<link href="http://arxiv.org/pdf/2609.12345v2" title="pdf"/></entry></feed>'''


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.paper = build.parse_feed(FEED)[0][0]
        self.cutoff = datetime(2026, 9, 2, tzinfo=timezone.utc)

    def test_atom_normalizes_links_without_attribute_order_dependency(self):
        self.assertEqual(self.paper['pdf_url'], 'https://arxiv.org/pdf/2609.12345v2')
        self.assertEqual(self.paper['title'], 'A & B <script>')
        self.assertEqual(self.paper['authors'], ['Fei Gao'])

    def test_rejects_non_feed_and_api_errors(self):
        for body in ['Rate exceeded', '<html/>', FEED.replace('http://arxiv.org/abs/2609.12345v2', 'http://arxiv.org/api/errors#bad')]:
            with self.assertRaises((ValueError, build.ET.ParseError)):
                build.parse_feed(body)

    def test_revision_replaces_previous_day_and_preserves_failed_category(self):
        old = dict(self.paper, id='http://arxiv.org/abs/2609.12345v1', updated='2026-09-10T12:00:00Z')
        cache = {'2026-09-10T00:00:00Z': {'Robotics': [old], 'Computer Vision': [old]}}
        merged = build.merge(cache, {'Robotics': [self.paper]}, self.cutoff)
        self.assertNotIn('Robotics', merged.get('2026-09-10T00:00:00Z', {}))
        self.assertEqual(len(merged['2026-09-15T00:00:00Z']['Robotics']), 1)
        self.assertIn('Computer Vision', merged['2026-09-10T00:00:00Z'])

    def test_paginates_until_date_window_covered(self):
        older = FEED.replace('2026-09-15', '2026-08-01')
        with patch.object(build, 'request', side_effect=[FEED.replace('totalResults>1', 'totalResults>2'), older]) as request:
            papers = build.fetch_source({'category': 'cs.RO', 'limit': 1}, self.cutoff)
        self.assertEqual(len(papers), 1)
        self.assertEqual(request.call_count, 2)
        self.assertIn('start=1', request.call_args[0][0])

    def test_retries_malformed_xml(self):
        with patch.object(build, 'request', side_effect=['Rate exceeded', FEED]), patch.object(build.time, 'sleep'):
            self.assertEqual(len(build.fetch_source({'category':'cs.RO','limit':200}, self.cutoff)), 1)

    def test_empty_page_is_not_success(self):
        with patch.object(build, 'request', return_value=FEED[:FEED.index('<entry>')] + '</feed>'):
            with self.assertRaises(ValueError):
                build.fetch_source({'category':'cs.RO','limit':200}, self.cutoff)

    def test_render_escapes_metadata_and_deduplicates_cross_lists(self):
        cache = build.merge({}, {'Robotics':[self.paper], 'Computer Vision':[self.paper]}, self.cutoff)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            build.render(cache, {'built_at':'2026-09-16T00:00:00Z'}, {'site_title':'Robot Papers','limit_days':14}, target)
            page = (target / 'index.html').read_text()
            self.assertEqual(page.count('class="paper"'), 1)
            self.assertIn('&lt;script&gt;', page)
            self.assertIn('data-followed="true"', page)
            self.assertIn('/pdf/2609.12345', page)
            self.assertNotIn('<!--PAPERS-->', page)

    def test_cross_date_revision_keeps_all_category_filters(self):
        old = dict(self.paper, id='http://arxiv.org/abs/2609.12345v1', updated='2026-09-10T12:00:00Z')
        cache = build.merge({}, {'Robotics':[self.paper], 'Computer Vision':[old]}, self.cutoff)
        with tempfile.TemporaryDirectory() as directory:
            build.render(cache, {'built_at':'2026-09-16T00:00:00Z'}, {'site_title':'Robot Papers','limit_days':14}, Path(directory))
            page = (Path(directory) / 'index.html').read_text()
            self.assertEqual(page.count('class="paper"'), 1)
            self.assertIn('&quot;Computer Vision&quot;, &quot;Robotics&quot;', page)

    def test_all_failed_does_not_write_deployment(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(build.sys, 'argv', ['build.py','--output',directory]), patch.object(build, 'request', side_effect=OSError('offline')), patch.object(build, 'fetch_source', side_effect=OSError('offline')):
            with self.assertRaisesRegex(RuntimeError, 'All sources failed'):
                build.main()
            self.assertFalse((Path(directory) / 'index.html').exists())

    def test_highlight_escapes_and_avoids_substring_matches(self):
        output = build.highlighter(['RL', 'robot'])('URL robot <img>')
        self.assertEqual(output, 'URL <mark>robot</mark> &lt;img&gt;')


if __name__ == '__main__':
    unittest.main()
