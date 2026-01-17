原github链接：https://github.com/geekjourneyx/ai-daily-skill/blob/main/.env.example

本例修改为K2模型，用qq邮箱

# AI Daily Skill

> AI 资讯日报 Claude Code Skill - 每天自动获取、分析、归类 AI 前沿资讯

> [!CAUTION]
$\color{#FF0000}{想每天咖啡时间就帮你找到好的选题，自动发给你吗？ 有需要定制的朋友拉到底部通过公众号联系到我。}$

---

## 简介

AI Daily 是一个 Claude Code Skill，帮助你在 Claude Code 中快速获取 AI 行业资讯。它从 [smol.ai](https://news.smol.ai/) 获取资讯，使用内置的 Claude AI 能力进行智能分析和分类，生成结构化的 Markdown 文档，并可按需生成精美的网页。

### 核心功能

- 每天自动获取 AI 行业资讯
- Claude AI 智能摘要和分类
- 支持相对日期查询（昨天、前天等）
- 可选生成精美网页（苹果风/深海蓝/秋日暖阳主题）
- 可选生成分享卡片图片（智能尺寸，适合社交媒体分享）
- 可选生成小红书风格封面（3:4 比例，极简格栅设计）
- 友好的用户体验，无数据时提供建议

---

## 安装

### 方式一：Plugin Marketplace（推荐）

在 Claude Code 中运行：

```bash
/plugin marketplace add geekjourneyx/ai-daily-skill
/plugin install ai-daily@geekjourneyx-ai-daily-skill
```

### 方式二：项目内使用

克隆项目后，Skill 自动可用：

```bash
git clone https://github.com/geekjourneyx/ai-daily-skill.git
cd ai-daily-skill
```

在 Claude Code 中直接使用即可。

### 方式三：全局安装

```bash
cp -r plugins/ai-daily ~/.claude/skills/
```

---

## 使用方法

### 基础查询

```bash
# 昨天的 AI 资讯
昨天AI资讯

# 前天的 AI 新闻
前天AI资讯

# 具体日期
2026-01-13的AI新闻

# 按分类筛选
昨天的模型发布相关资讯
```

### 生成网页

```bash
# 查询并询问是否生成网页
昨天AI资讯，生成网页

# 直接选择主题
昨天AI资讯，生成苹果风网页
```

### 生成分享图片

```bash
# 生成社交媒体分享卡片
昨天AI资讯，生成分享图片
生成日报卡片图片
```

### 生成小红书封面

自动生成小红书风格封面，包含：
- 3:4 比例（750x1000px）
- 极简格栅主义设计
- 黑白主色调 + 绿色点缀
- 一键保存为 PNG 图片

封面保存在 `docs/xiaohongshu/` 目录，在浏览器中打开 HTML 文件后点击"保存封面"按钮即可下载。

### 完整对话示例

```
用户: 昨天AI资讯

Claude: [展示 Markdown 格式的资讯摘要，包含核心摘要和分类资讯]

用户: 生成网页

Claude: 可选主题:
- 苹果风 - 简洁专业，适合技术内容
- 深海蓝 - 商务风格，适合产品发布
- 秋日暖阳 - 温暖活力，适合社区动态

用户: 苹果风

Claude: [生成 HTML 网页并保存到 docs/ 目录]
```

---

## 项目结构

```
ai-daily-skill/
├── .claude-plugin/
│   └── plugin.json                 # 插件清单
├── plugins/ai-daily/skills/ai-daily/
│   ├── SKILL.md                     # 主技能定义
│   ├── scripts/
│   │   └── fetch_news.py            # RSS 获取脚本
│   └── references/
│       ├── output-format.md         # Markdown 输出格式
│       └── html-themes.md            # 网页主题提示词
├── docs/                            # 生成的网页和文档
│   ├── images/                      # 分享卡片图片
│   ├── xiaohongshu/                 # 小红书封面
│   ├── css/                         # 样式文件
│   └── *.html                       # 生成的 HTML 页面
├── src/                             # GitHub Actions 自动化脚本
│   ├── main.py                      # 主入口
│   ├── config.py                    # 配置管理
│   ├── rss_fetcher.py               # RSS 获取
│   ├── claude_analyzer.py           # AI 分析
│   ├── html_generator.py            # HTML 生成
│   ├── image_generator.py           # 图片生成
│   ├── xiaohongshu_generator.py     # 小红书封面生成
│   └── notifier.py                  # 邮件通知
└── README.md
```

---

## 输出格式

### Markdown 格式

```markdown
# AI Daily · 2026年1月13日

## 核心摘要

- Anthropic 发布 Cowork 统一 Agent 平台
- Google 开源 MedGemma 1.5 医疗多模态模型
- LangChain Agent Builder 正式发布

## 模型发布

### MedGemma 1.5
Google 发布 4B 参数医疗多模态模型...
[原文链接](https://news.smol.ai/issues/26-01-13-not-much/)

## 关键词

#Anthropic #Google #MedGemma #LangChain
```

### 网页格式

- 纯黑背景 + 渐变光晕
- 响应式设计，支持移动端
- 平滑动画和悬停效果
- 单文件 HTML，无外部依赖

---

## 网页主题

| 主题 | 风格 | 适用场景 |
|------|------|----------|
| 苹果风 | 简洁专业 | 技术内容、产品评测 |
| 深海蓝 | 商务风格 | 产品发布、企业动态 |
| 秋日暖阳 | 温暖活力 | 社区新闻、讨论 |

---

## 常见问题

### Q: 支持哪些日期查询方式？

A: 支持相对日期（昨天、前天、今天）和绝对日期（YYYY-MM-DD 格式）。

### Q: 如果某天没有资讯会怎样？

A: 系统会友好提示，并列出可用的日期范围供选择。

### Q: 网页保存在哪里？

A: 网页保存在 `docs/` 目录，文件名为 `{日期}.html` 格式。

### Q: 图片保存在哪里？

A: 分享卡片图片保存在 `docs/images/` 目录，文件名为 `{日期}.png` 格式。

### Q: 需要配置 API Key 吗？

A: 不需要。Skill 使用 Claude Code 内置的 AI 能力，无需额外配置。

### Q: 如何启用图片生成功能？

A: 需要设置环境变量 `ENABLE_IMAGE_GENERATION=true`，并配置 Firefly API。

### Q: 可以自定义主题吗？

A: 可以。主题提示词在 `references/html-themes.md` 中，可以修改或添加新主题。

---

## 开发

### 环境要求

- Python 3.11+
- feedparser
- requests

### 环境变量

```bash
# Claude API 配置（必需）
ZHIPU_API_KEY=your_api_key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic

# 图片生成配置（可选）
ENABLE_IMAGE_GENERATION=true
FIREFLY_API_URL=https://fireflycard-api.302ai.cn/api/saveImg
FIREFLY_API_KEY=your_firefly_key

# 邮件通知配置（可选）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_password
NOTIFICATION_TO=recipient@example.com
```

### 安装依赖

```bash
pip install feedparser requests
```

### 测试脚本

```bash
# 获取可用日期范围
python plugins/ai-daily/skills/ai-daily/scripts/fetch_news.py --date-range

# 获取特定日期内容
python plugins/ai-daily/skills/ai-daily/scripts/fetch_news.py --date 2026-01-13

# 获取昨天的内容
python plugins/ai-daily/skills/ai-daily/scripts/fetch_news.py --relative yesterday
```
