# Robot Papers - 项目总结

## 项目概述

Robot Papers 是一个自动化的学术论文聚合网站，专注于机器人、计算机视觉、人工智能和图形学领域的最新研究论文。该项目通过 GitHub Actions 自动从 arXiv 获取论文，并生成一个美观的静态网站展示。

**项目地址**: https://liujy25.github.io/robot-papers/

## 核心功能

### 1. 自动化论文聚合
- 使用 ArxivFeed 工具从 arXiv 自动抓取论文
- 支持多个研究领域分类：
  - Robotics (cs.RO)
  - Computer Vision (cs.CV)
  - Artificial Intelligence (cs.AI)
  - Graphics (cs.GR)
- 每个分类限制 300 篇论文
- 默认显示最近 7 天的论文

### 2. 智能高亮系统
项目使用 Rhai 脚本语言实现了智能的关键词和作者高亮功能：

#### 标题关键词高亮 (`scripts/highlight_title.rhai`)
- 自动识别并高亮论文标题中的重要关键词
- 如果作者列表中包含关注的作者，标题前会添加 ★ 标记
- 关键词分为三类：
  - **任务类型**: SLAM, Navigation, Manipulation, Grasping, Planning 等
  - **方法类型**: Diffusion, RL, VLM, NeRF, Gaussian, Transformer 等
  - **论文类型**: Dataset, Survey, Review, Benchmark 等

#### 作者高亮 (`scripts/highlight_author.rhai`)
- 自动高亮关注的作者名字
- 支持不区分大小写的匹配
- 关注的作者包括：Fei Gao, Fu Zhang, Hang Zhao, Cewu Lu, Hao Dong 等

#### 会议高亮 (`scripts/highlight_conference.rhai`)
- 识别并高亮顶级会议和期刊名称
- 包括：CVPR, ICCV, ECCV, NeurIPS, ICRA, IROS, RSS, SIGGRAPH 等

### 3. 用户界面特性
- **HuggingFace 风格设计**: 采用现代化的配色方案（黄色、紫色、蓝色）
- **响应式布局**: 最大宽度 1200px，适配不同屏幕尺寸
- **交互式展开/收起**:
  - 点击论文标题查看详细信息
  - 按 TAB 键可一键展开/收起所有论文
- **日期分组**: 按日期组织论文，每天的论文显示在独立的卡片中
- **标签系统**: 使用 chip 标签显示论文分类

### 4. 自动化部署
通过 GitHub Actions 实现完全自动化的工作流：

#### 触发条件
- 手动触发 (workflow_dispatch)
- 推送到 main 分支
- 定时任务：每天 UTC 时间 2:00 (北京时间 10:00) 自动更新

#### 部署流程
1. 下载最新版本的 ArxivFeed 工具
2. 执行 ArxivFeed 生成 RSS 和 HTML
3. 自动部署到 GitHub Pages

## 技术栈

- **前端**: HTML + CSS + JavaScript (原生)
- **脚本语言**: Rhai (用于高亮逻辑)
- **配置**: TOML
- **构建工具**: ArxivFeed
- **部署**: GitHub Actions + GitHub Pages
- **模板引擎**: Handlebars (index.hbs)

## 项目结构

```
robot-papers/
├── config.toml              # 主配置文件
├── scripts/
│   ├── config.rhai         # 关键词和作者配置
│   ├── highlight_title.rhai    # 标题高亮脚本
│   ├── highlight_author.rhai   # 作者高亮脚本
│   └── highlight_conference.rhai # 会议高亮脚本
├── statics/
│   ├── index.css           # 样式文件
│   └── index.js            # 交互脚本
├── includes/
│   └── index.hbs           # HTML 模板
├── .github/workflows/
│   └── update-feed.yml     # 自动化部署配置
└── imgs/                   # 图片资源
```

## 配置说明

### config.toml
- `site_title`: 网站标题
- `limit_days`: 显示最近几天的论文（默认 7 天）
- `cache_url`: 缓存 JSON 的 URL
- `sources`: 论文来源配置（分类、限制数量）
- `scripts`: 高亮脚本路径配置

### scripts/config.rhai
包含三个主要配置数组：
- `titles`: 需要高亮的标题关键词（100+ 个）
- `authors_array`: 关注的作者列表（20+ 位）
- `conferences`: 顶级会议和期刊列表（20+ 个）

## 特色功能

1. **个性化关注**: 可以通过修改 `scripts/config.rhai` 自定义关注的作者和关键词
2. **零维护成本**: 完全自动化，无需手动更新
3. **快速浏览**: TAB 键快捷操作，快速浏览大量论文
4. **视觉友好**: 清晰的层次结构和配色，易于阅读
5. **缓存机制**: 使用 cache.json 提高加载速度

## 适用场景

- 机器人研究人员跟踪最新论文
- 计算机视觉领域的学术追踪
- 人工智能研究动态监控
- 个人学术论文订阅系统

## 扩展建议

1. 可以添加更多 arXiv 分类
2. 可以自定义关注的作者和关键词
3. 可以调整更新频率（修改 cron 表达式）
4. 可以添加论文摘要的关键词搜索功能
5. 可以集成邮件通知功能
