# Robot Papers

机器人研究日报：<https://liujy25.github.io/robot-papers/>

从 arXiv 聚合 Robotics、Computer Vision、Artificial Intelligence 和 Graphics。支持标题、作者、摘要搜索，分类和日期筛选、关注作者筛选、摘要展开。跨分类论文合并展示，关键词与关注作者高亮。Tab 保持正常键盘导航，`/` 聚焦搜索框。

## 本地构建

仅需要 Python 3.11+，无需第三方 Python 包：

```sh
python scripts/build.py
python -m http.server 8000 --directory target
```

使用现有缓存生成设计预览（页面会明确标记为缓存预览）：

```sh
python scripts/build.py --offline-cache path/to/cache.json
```

测试：

```sh
python -m unittest discover -s tests -v
node --check statics/index.js
```

## 配置

- `config.toml`：站点名、保留天数、缓存地址与 arXiv 分类。`sources.limit` 是每页请求大小，不是整个分类的论文总数限制；最多 500。默认保留最近 14 个 UTC 日期。
- `preferences.json`：`keywords`、`authors`、`conferences`。原有 Rhai 配置中的关键词、作者和会议列表已迁移到这里；作者匹配忽略大小写，按完整名字匹配。
- `includes/index.html`：页面模板。构建脚本替换其中的大写注释占位符。
- `statics/index.css` / `statics/index.js`：响应式布局与浏览器交互。

## 更新机制与故障处理

GitHub Actions 每天北京时间 04:17、10:17、16:17、22:17 尝试更新，也可手动触发。GitHub 的定时任务可能延迟，arXiv 本身也不是实时发布；页面论文日期代表论文在 arXiv 上的最后修订日期，不代表网站同步时间。

1. 读取已发布缓存，通过 HTTPS 请求 arXiv Atom API。
2. 串行请求，相邻 arXiv 请求间隔至少 3.2 秒；超时、HTTP 错误、非 XML 响应重试。
3. 每个分类按最后修订时间倒序分页，直到覆盖保留窗口。设有 20,000 条的保护上限；到达上限会作为该分类失败处理，不伪装完整更新。
4. 合并旧缓存和新数据，同一分类同一论文只保留最新版本。跨分类在页面合并为一张卡片。
5. 一个分类失败时保留该分类缓存，`status.json` 记录失败及最近成功时间，页面明确提示。所有分类失败或没有论文时，构建失败，不发布空页面。
6. 检查生成的 HTML、缓存、状态文件后才发布到现有 `gh-pages` 分支；保持当前 GitHub Pages 设置。

排错时查看 Actions 中的 **Build feed** 和上传的 `feed-build-log`。现在构建错误会直接使构建步骤失败，不会再被管道日志掩盖。首页区分论文更新日期、页面生成时间与各分类成功同步状态；页面超过 48 小时未生成时显示提示。

PR 运行测试但不抓取、发布。推送到 `main` 后运行完整更新与发布。

## 2026-09 修复背景

9 月 15 日的运行记录显示，旧抓取器在 cs.RO 收到非 XML 内容，出现 `Unexpected characters outside the root element: R`。旧脚本的管道没有启用 `pipefail`，随后仍输出构建成功，最终发布步骤因缺少 `target` 失败。此次替换不检查 HTTP 状态、无重试的外部二进制抓取器，改用仓库内可测试的 Python 构建脚本；保留旧 `cache.json` 格式以恢复已有数据。
