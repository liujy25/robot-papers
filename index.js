'use strict';
const papers = [...document.querySelectorAll('.paper')].map(element => ({
  element, categories: JSON.parse(element.dataset.categories),
  followed: element.dataset.followed === 'true', text: element.textContent.toLocaleLowerCase(),
  date: element.closest('.day').querySelector('time').dateTime
}));
const search = document.querySelector('#search');
const followed = document.querySelector('#followed');
const dateFilter = document.querySelector('#date-filter');
const categories = [...document.querySelectorAll('[data-category]')];
let selected = 'all';
let expanded = false;
for (const day of [...new Set(papers.map(p => p.date))]) {
  const option = document.createElement('option');
  option.value = day; option.textContent = day; dateFilter.append(option);
}
function filter() {
  const terms = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  const matches = papers.filter(p => (!followed.checked || p.followed)
    && (dateFilter.value === 'all' || p.date === dateFilter.value) && terms.every(term => p.text.includes(term)));
  const matching = new Set(matches);
  let count = 0;
  for (const paper of papers) {
    const visible = matching.has(paper) && (selected === 'all' || paper.categories.includes(selected));
    paper.element.hidden = !visible;
    if (visible) count++;
  }
  for (const button of categories) {
    button.querySelector('.category-count').textContent = matches.filter(p => button.dataset.category === 'all' || p.categories.includes(button.dataset.category)).length;
    button.setAttribute('aria-pressed', String(button.dataset.category === selected));
  }
  for (const day of document.querySelectorAll('.day')) {
    const visible = day.querySelectorAll('.paper:not([hidden])').length;
    day.hidden = visible === 0;
    day.querySelector('h2>span').textContent = `${visible} 篇`;
  }
  document.querySelector('#result-count').textContent = `${count} 篇论文`;
  document.querySelector('#empty').hidden = count !== 0;
  document.querySelector('#list-title').textContent = selected === 'all' ? '全部论文' : categories.find(b => b.dataset.category === selected).querySelector('span').childNodes[0].textContent;
}
search.addEventListener('input', filter);
followed.addEventListener('change', filter);
dateFilter.addEventListener('change', filter);
categories.forEach(button => button.addEventListener('click', () => { selected = button.dataset.category; filter(); }));
document.querySelector('#reset').addEventListener('click', () => {
  search.value = ''; followed.checked = false; dateFilter.value = 'all'; selected = 'all'; filter();
});
document.querySelector('#expand-all').addEventListener('click', event => {
  expanded = !expanded;
  papers.filter(p => !p.element.hidden).forEach(p => { p.element.querySelector('details').open = expanded; });
  event.currentTarget.textContent = expanded ? '收起摘要' : '展开摘要';
});
document.addEventListener('keydown', event => {
  if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !event.target.closest('input,textarea,select,[contenteditable="true"]')) {
    event.preventDefault(); search.focus();
  }
});
const buildTime = document.querySelector('#build-time');
const built = new Date(buildTime.dateTime);
if (!Number.isNaN(built.getTime())) buildTime.textContent = built.toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
const freshness = document.querySelector('#freshness');
const warnings = [];
if (Date.now() - built.getTime() > 48 * 3600000) warnings.push('页面已超过 48 小时未生成，请检查自动更新任务。');
function showWarnings() { freshness.hidden = warnings.length === 0; freshness.textContent = warnings.join(' '); }
showWarnings();
fetch('status.json', {cache:'no-cache'}).then(response => {
  if (!response.ok) throw new Error('Missing sync metadata');
  return response.json();
}).then(status => {
  const panel = document.querySelector('#source-status'); panel.replaceChildren();
  if (status.preview) warnings.push('当前为缓存预览，尚未执行实时同步。');
  let hasStaleSource = false;
  for (const [name, source] of Object.entries(status.sources)) {
    const row = document.createElement('div'); row.className = 'source-row';
    const label = document.createElement('span'); label.textContent = source.category;
    const value = document.createElement('span');
    const old = !source.last_success || Date.now() - new Date(source.last_success).getTime() > 48 * 3600000;
    const fallback = source.state === 'rss';
    const stale = !['ok', 'rss'].includes(source.state) || old;
    value.textContent = stale ? '缓存 · 待同步' : fallback ? '公告已同步' : '已同步';
    if (stale) value.className = 'stale';
    row.title = source.last_success ? `${name} 最近成功同步：${new Date(source.last_success).toLocaleString('zh-CN')}` : `${name} 暂无成功同步记录`;
    row.append(label, value); panel.append(row);
    if (fallback) row.title += '；使用官方每日公告，历史缺口将在 API 恢复后补齐。';
    if (stale && !status.preview) hasStaleSource = true;
  }
  if (hasStaleSource) warnings.push('部分来源暂未同步，详情见数据同步状态。');
  showWarnings();
}).catch(() => {
  document.querySelector('#source-status').textContent = '同步记录暂不可用';
  warnings.push('暂时无法读取同步状态。'); showWarnings();
});
filter();

// Render formulae only when an abstract is opened. Search keeps its original text.
for (const detail of document.querySelectorAll('.abstract')) {
  detail.addEventListener('toggle', () => {
    if (!detail.open || detail.dataset.mathRendered || typeof renderMathInElement !== 'function') return;
    renderMathInElement(detail, {delimiters:[
      {left:'$$',right:'$$',display:true}, {left:'$',right:'$',display:false},
      {left:'\\(',right:'\\)',display:false}, {left:'\\[',right:'\\]',display:true}
    ], throwOnError:false, trust:false});
    detail.dataset.mathRendered = 'true';
  });
}
