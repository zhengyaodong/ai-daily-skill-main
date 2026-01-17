# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **图片生成功能**
  - 集成 Firefly Card API，支持生成分享卡片图片
  - 高度自适应：根据内容长度动态计算图片高度（600-3000px）
  - 比例自动选择：根据宽高比自动匹配最佳比例（1:1/3:4/2:3/9:16/9:19）
  - 智能排版配置：根据内容复杂度自动调整宽度、padding、字体缩放
  - 纯黑太阳主题 (tempBlackSun)，思源宋体字体
  - 自动保存到 `docs/images/{日期}.png`
  - 支持通过环境变量 `ENABLE_IMAGE_GENERATION` 开关控制
- **小红书封面生成**
  - 3:4 比例封面（750x1000px）
  - 极简格栅主义设计风格
  - 黑白主色调 + 绿色点缀
  - 自动提取关键词作为主标题
  - 一键保存为 PNG 图片
  - 保存在 `docs/xiaohongshu/` 目录

### Changed
- GitHub Actions 工作流新增 Firefly API 环境变量配置
- Skill 定义新增 Step 7 图片生成流程
- README 新增图片生成功能说明和配置文档

### Fixed
- 修复 SKILL.md 中 API 返回格式描述不准确的问题
- 修复 image_generator.py 中未定义变量的 bug
- 修复图片高度计算不足导致内容显示不全的问题
  - 增加高度计算余量（20% 安全缓冲）
  - 增加字符宽度估算（16px）
  - 降低 padding 比例到 8%
  - 空行也计入高度计算

[Unreleased]: https://github.com/geekjourneyx/ai-daily-skill/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/geekjourneyx/ai-daily-skill/releases/tag/v1.0.0

---

## [1.0.0] - 2026-01-15

### Added
- 自动从 smol.ai 获取 AI 资讯
- Claude AI 智能分析分类和摘要提取
- 8 种智能主题配色，根据内容类型自动选择
- 精美 HTML 页面生成，支持响应式设计
- 邮件通知功能（可选配置）
  - 成功通知：包含资讯数量和页面链接
  - 空数据通知：当日无资讯时提醒
  - 错误通知：失败时附带 GitHub Actions 日志链接
- GitHub Actions 定时任务
  - 每天 UTC 02:00（北京时间 10:00）自动运行
  - 支持手动触发
  - 自动部署到 GitHub Pages
- 资讯智能分类（模型发布、产品动态、研究论文、工具框架、融资并购、行业事件）
- 索引页面，按日期倒序展示所有日报
- 关键词提取和标签展示
- Claude Code Skill 插件支持
  - 在 Claude Code 中直接查询 AI 资讯
  - 支持相对日期查询（昨天、前天、今天）
  - 支持绝对日期查询（YYYY-MM-DD）
  - 内置 Claude AI 智能摘要和分类
  - 可选生成精美网页（苹果风/深海蓝/秋日暖阳主题）
  - 友好的用户无数据提示

### Configuration
- 支持 8 种主题配色：柔和蓝色、深靛蓝、优雅紫色、清新绿色、温暖橙色、玫瑰粉色、冷色青绿、中性灰色
- 支持通过环境变量自定义 RSS 源
- 支持通过环境变量配置 SMTP 邮件通知

### Documentation
- 完整的 README.md 使用文档
- 常见问题（FAQ）章节
- 本地开发指南
