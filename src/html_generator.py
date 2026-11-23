"""
HTML 生成模块
根据分析结果生成精美的 HTML 页面
"""
import os
import json
from datetime import datetime
from html import escape
from typing import Dict, Any, List
from pathlib import Path

from src.config import (
    OUTPUT_DIR,
    THEMES,
    SITE_META,
    GITHUB_PAGES_URL
)


class HTMLGenerator:
    """HTML 页面生成器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 复制 CSS 文件到输出目录
        self._setup_css()

    def _setup_css(self):
        """确保 CSS 文件存在"""
        css_dir = self.output_dir / "css"
        css_dir.mkdir(parents=True, exist_ok=True)

        # CSS 文件将在 templates 中处理
        self.css_path = "css/styles.css"

    def generate_daily(self, result: Dict[str, Any]) -> str:
        """
        生成日报 HTML 页面

        Args:
            result: 大模型分析结果

        Returns:
            生成的 HTML 文件路径
        """
        date = result.get("date", datetime.now().strftime("%Y-%m-%d"))
        theme_name = result.get("theme", "blue")
        theme = THEMES.get(theme_name, THEMES["blue"])

        print(f"📄 正在生成 HTML 页面...")
        print(f"   日期: {date}")
        print(f"   主题: {theme['name']}")

        # 构建 HTML
        html_content = self._build_daily_html(result, theme)

        # 写入文件
        filename = f"{date}.html"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML 生成成功: {filepath}")

        # 更新索引页
        self.update_index(date, result)

        return str(filepath)

    def generate_empty(self, date: str, reason: str = "今日暂无资讯"):
        """生成空状态页面"""
        theme = THEMES["gray"]

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Daily · {date} - 暂无资讯</title>
    <meta name="description" content="{SITE_META['description']}">
    <link rel="stylesheet" href="css/styles.css">
</head>
<body data-theme="gray">
    <div class="background-glow"></div>
    <div class="geometric-lines"></div>

    <div class="container">
        <header class="header">
            <div class="logo-icon">🤖</div>
            <h1>AI Daily</h1>
            <div class="date-badge">{self._format_date(date)}</div>
        </header>

        <main class="main-content">
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <h2>今日暂无资讯</h2>
                <p>目标日期: <strong>{date}</strong></p>
                <p>原因: {reason}</p>
                <a href="index.html" class="btn-primary">返回首页</a>
            </div>
        </main>

        <footer class="footer">
            <p>© {datetime.now().year} {SITE_META['title']}</p>
        </footer>
    </div>
</body>
</html>"""

        filename = f"{date}.html"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 空页面生成成功: {filepath}")
        return str(filepath)

    def _build_daily_html(self, result: Dict[str, Any], theme: Dict[str, str]) -> str:
        """构建日报 HTML"""
        date = result.get("date", "")
        summary = result.get("summary", [])
        keywords = result.get("keywords", [])
        categories = result.get("categories", [])

        # 格式化日期
        formatted_date = self._format_date(date)

        # 构建摘要区块
        summary_html = ""
        if summary:
            summary_items = "\n".join([
                f'                <li class="summary-item">{escape(item)}</li>'
                for item in summary
            ])
            summary_html = f"""
            <section class="summary-card">
                <h2 class="section-title">📌 今日核心摘要</h2>
                <ul class="summary-list">
{summary_items}
                </ul>
            </section>
"""

        # 构建分类区块
        categories_html = ""
        for cat in categories:
            if not cat.get("items"):
                continue

            cat_name = cat.get("name", "")
            cat_icon = cat.get("icon", "📄")
            cat_items = cat.get("items", [])

            items_html = ""
            for item in cat_items:
                item_title = escape(item.get("title") or "")
                item_summary = escape(item.get("summary") or "")
                item_url = item.get("url") or ""
                item_tags = item.get("tags", [])
                source_details = " · ".join(filter(None, [
                    item.get("source"), item.get("published_date"),
                ]))
                source_html = ""
                if source_details:
                    source_html = f'<p class="news-summary"><small>{escape(source_details)}</small></p>'

                # 标签
                tags_html = ""
                if item_tags:
                    tags_span = " ".join(f'<span class="tag">#{escape(tag)}</span>' for tag in item_tags[:4])
                    tags_html = f'<div class="item-tags">{tags_span}</div>'

                # 链接处理
                link_html = ""
                if item_url.lower().startswith(("https://", "http://")):
                    link_html = f'<a href="{escape(item_url)}" class="item-link" target="_blank" rel="noopener">详情</a>'

                items_html += f"""
                <article class="news-card">
                    <div class="news-card-header">
                        <h3 class="news-title">{item_title}</h3>
                        {link_html}
                    </div>
                    {source_html}
                    <p class="news-summary">{item_summary}</p>
                    {tags_html}
                </article>
"""

            categories_html += f"""
            <section class="category-section">
                <div class="category-header">
                    <span class="category-icon">{cat_icon}</span>
                    <h2 class="category-title">{cat_name}</h2>
                    <span class="category-count">{len(cat_items)}</span>
                </div>
                <div class="news-grid">
{items_html}
                </div>
            </section>
"""

        # 关键词区块
        keywords_html = ""
        if keywords:
            keywords_str = " | ".join(escape(keyword) for keyword in keywords)
            keywords_html = f"""
        <footer class="keywords-footer">
            <p>#关键词: {keywords_str}</p>
        </footer>
"""

        # 构建完整 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Daily · {formatted_date}</title>
    <meta name="description" content="{SITE_META['description']}">
    <meta name="keywords" content="{escape(', '.join(keywords + SITE_META['keywords']))}">
    <link rel="stylesheet" href="css/styles.css">
</head>
<body data-theme="{result.get('theme', 'blue')}">
    <div class="background-glow"></div>
    <div class="geometric-lines"></div>

    <div class="container">
        <header class="header">
            <div class="logo-icon">🤖</div>
            <h1>AI Daily</h1>
            <div class="date-badge">{formatted_date}</div>
        </header>

        <main class="main-content">
{summary_html}
{categories_html}
{keywords_html}
        </main>

        <footer class="footer">
            <p>© {datetime.now().year} {SITE_META['title']} · 大模型聚合与分析</p>
        </footer>
    </div>
</body>
</html>"""

        return html

    def _format_date(self, date_str: str) -> str:
        """格式化日期显示"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # 中文格式: 2026年1月13日 星期一
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = weekdays[dt.weekday()]
            return f"{dt.year}年{dt.month}月{dt.day}日 {weekday}"
        except:
            return date_str

    def update_index(self, date: str, result: Dict[str, Any] = None):
        """更新索引页"""
        index_file = self.output_dir / "index.html"

        # 读取现有索引数据
        index_data_file = self.output_dir / ".index.json"
        existing_entries = []

        if index_data_file.exists():
            with open(index_data_file, 'r', encoding='utf-8') as f:
                try:
                    existing_entries = json.load(f)
                except:
                    existing_entries = []

        # 添加新条目
        summary = result.get("summary", []) if result else []
        summary_text = summary[0] if summary else "暂无摘要"

        new_entry = {
            "date": date,
            "url": f"{date}.html",
            "summary": summary_text[:100],
            "timestamp": datetime.now().isoformat()
        }

        # 检查是否已存在
        existing_entries = [e for e in existing_entries if e["date"] != date]
        existing_entries.insert(0, new_entry)

        # 只保留最近 30 天
        existing_entries = existing_entries[:30]

        # 保存索引数据
        with open(index_data_file, 'w', encoding='utf-8') as f:
            json.dump(existing_entries, f, ensure_ascii=False, indent=2)

        # 生成索引页 HTML
        html_content = self._build_index_html(existing_entries)

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 索引页已更新")

    def _build_index_html(self, entries: List[Dict[str, Any]]) -> str:
        """构建索引页 HTML"""
        # 构建条目列表
        entries_html = ""
        for entry in entries:
            date = entry.get("date", "")
            url = entry.get("url", "")
            summary = entry.get("summary", "")
            formatted_date = self._format_date(date)

            entries_html += f"""
            <article class="index-entry">
                <a href="{url}" class="entry-link">
                    <div class="entry-header">
                        <span class="entry-date">{formatted_date}</span>
                        <span class="entry-arrow">→</span>
                    </div>
                    <p class="entry-summary">{escape(summary)}</p>
                </a>
            </article>
"""

        # 如果没有条目
        if not entries_html:
            entries_html = '<p class="empty-message">暂无资讯记录</p>'

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Daily - AI 资讯日报</title>
    <meta name="description" content="{SITE_META['description']}">
    <link rel="stylesheet" href="css/styles.css">
</head>
<body data-theme="blue">
    <div class="background-glow"></div>
    <div class="geometric-lines"></div>

    <div class="container">
        <header class="header header-center">
            <div class="logo-icon">🤖</div>
            <h1>AI Daily</h1>
            <p class="subtitle">{SITE_META['subtitle']}</p>
        </header>

        <main class="main-content index-page">
            <section class="index-section">
                <h2 class="section-title">📅 资讯归档</h2>
                <div class="index-entries">
{entries_html}
                </div>
            </section>
        </main>

        <footer class="footer">
            <p>© {datetime.now().year} {SITE_META['title']}</p>
        </footer>
    </div>
</body>
</html>"""

        return html

    def generate_css(self):
        """生成 CSS 文件"""
        css_content = self._get_css_content()

        css_dir = self.output_dir / "css"
        css_dir.mkdir(parents=True, exist_ok=True)

        css_file = css_dir / "styles.css"
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)

        print(f"✅ CSS 文件已生成: {css_file}")

    def _get_css_content(self) -> str:
        """获取 CSS 内容"""
        return """/* ========================================
   AI Daily - 样式表
   8种智能主题配色
   ======================================== */

/* CSS 变量 - 8种主题 */
:root {
    --bg-color: #000000;
    --title-color: #FFFFFF;
}

/* 1. 柔和蓝色主题 */
body[data-theme="blue"] {
    --glow-start: #0A1929;
    --glow-end: #1A3A52;
    --text-color: #E3F2FD;
    --accent-color: #42A5F5;
    --secondary-color: #B0BEC5;
}

/* 2. 深靛蓝主题 */
body[data-theme="indigo"] {
    --glow-start: #0F1C3F;
    --glow-end: #1A2F5A;
    --text-color: #E3F2FD;
    --accent-color: #5C9FE5;
    --secondary-color: #BBDEFB;
}

/* 3. 优雅紫色主题 */
body[data-theme="purple"] {
    --glow-start: #1A0A28;
    --glow-end: #2D1B3D;
    --text-color: #F3E5F5;
    --accent-color: #B39DDB;
    --secondary-color: #D1C4E9;
}

/* 4. 清新绿色主题 */
body[data-theme="green"] {
    --glow-start: #0D1F12;
    --glow-end: #1B3A26;
    --text-color: #E8F5E9;
    --accent-color: #66BB6A;
    --secondary-color: #C8E6C9;
}

/* 5. 温暖橙色主题 */
body[data-theme="orange"] {
    --glow-start: #1F1410;
    --glow-end: #3D2415;
    --text-color: #FFF3E0;
    --accent-color: #FFA726;
    --secondary-color: #FFCCBC;
}

/* 6. 玫瑰粉色主题 */
body[data-theme="pink"] {
    --glow-start: #1F0A14;
    --glow-end: #3D1528;
    --text-color: #FCE4EC;
    --accent-color: #F06292;
    --secondary-color: #F8BBD0;
}

/* 7. 冷色青绿主题 */
body[data-theme="teal"] {
    --glow-start: #0A1F1F;
    --glow-end: #164E4D;
    --text-color: #E0F2F1;
    --accent-color: #26A69A;
    --secondary-color: #B2DFDB;
}

/* 8. 中性灰色主题 */
body[data-theme="gray"] {
    --glow-start: #1A1A1D;
    --glow-end: #2D2D30;
    --text-color: #F5F5F5;
    --accent-color: #9E9E9E;
    --secondary-color: #E0E0E0;
}

/* ========================================
   基础样式
   ======================================== */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-color);
    line-height: 1.6;
    min-height: 100vh;
    overflow-x: hidden;
}

/* 背景光晕 */
.background-glow {
    position: fixed;
    bottom: -20%;
    right: -20%;
    width: 70%;
    height: 70%;
    background: radial-gradient(
        circle at center,
        var(--glow-end) 0%,
        var(--glow-start) 40%,
        transparent 80%
    );
    opacity: 0.6;
    filter: blur(80px);
    z-index: -2;
    pointer-events: none;
}

/* 几何线条 */
.geometric-lines {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image:
        linear-gradient(90deg, transparent 49%, var(--accent-color) 50%, transparent 51%),
        linear-gradient(0deg, transparent 49%, var(--accent-color) 50%, transparent 51%);
    background-size: 200px 200px;
    opacity: 0.08;
    z-index: -1;
    pointer-events: none;
}

/* ========================================
   布局容器
   ======================================== */
.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 20px;
    min-height: 100vh;
}

/* ========================================
   页头
   ======================================== */
.header {
    text-align: center;
    margin-bottom: 60px;
}

.header-center {
    margin-bottom: 80px;
}

.logo-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: var(--accent-color);
    border-radius: 16px;
    font-size: 32px;
    margin-bottom: 20px;
    box-shadow: 0 0 40px var(--accent-color), 0 0 80px var(--accent-color);
    animation: glow-pulse 3s ease-in-out infinite;
}

@keyframes glow-pulse {
    0%, 100% {
        opacity: 1;
        box-shadow: 0 0 40px var(--accent-color), 0 0 80px var(--accent-color);
    }
    50% {
        opacity: 0.9;
        box-shadow: 0 0 50px var(--accent-color), 0 0 100px var(--accent-color);
    }
}

.header h1 {
    font-size: 48px;
    font-weight: 700;
    color: var(--title-color);
    margin-bottom: 12px;
    letter-spacing: -0.02em;
}

.subtitle {
    font-size: 18px;
    color: var(--secondary-color);
    opacity: 0.8;
}

.date-badge {
    display: inline-block;
    padding: 8px 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    font-size: 14px;
    color: var(--secondary-color);
    backdrop-filter: blur(10px);
}

/* ========================================
   主内容区
   ======================================== */
.main-content {
    max-width: 700px;
    margin: 0 auto;
}

.index-page {
    max-width: 800px;
}

/* ========================================
   章节标题
   ======================================== */
.section-title {
    font-size: 24px;
    font-weight: 600;
    color: var(--title-color);
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
}

/* ========================================
   核心摘要卡片
   ======================================== */
.summary-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 28px;
    margin-bottom: 48px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-list {
    list-style: none;
}

.summary-item {
    font-size: 16px;
    line-height: 1.8;
    padding: 12px 0;
    padding-left: 24px;
    position: relative;
}

.summary-item::before {
    content: "•";
    position: absolute;
    left: 0;
    color: var(--accent-color);
    font-size: 20px;
}

.summary-item:not(:last-child) {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

/* ========================================
   分类区块
   ======================================== */
.category-section {
    margin-bottom: 56px;
}

.category-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}

.category-icon {
    font-size: 32px;
}

.category-title {
    font-size: 28px;
    font-weight: 600;
    color: var(--title-color);
    flex: 1;
}

.category-count {
    padding: 4px 12px;
    background: var(--accent-color);
    color: #000;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
}

/* ========================================
   资讯卡片网格
   ======================================== */
.news-grid {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.news-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.3s ease;
}

.news-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--accent-color);
    transform: translateY(-2px);
}

.news-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 12px;
}

.news-title {
    font-size: 18px;
    font-weight: 600;
    color: var(--title-color);
    flex: 1;
}

.item-link {
    padding: 6px 16px;
    background: var(--accent-color);
    color: #000;
    text-decoration: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    transition: opacity 0.2s;
}

.item-link:hover {
    opacity: 0.8;
}

.news-summary {
    color: var(--text-color);
    font-size: 15px;
    line-height: 1.7;
    margin-bottom: 16px;
}

.item-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.tag {
    padding: 4px 10px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    font-size: 12px;
    color: var(--secondary-color);
}

/* ========================================
   关键词页脚
   ======================================== */
.keywords-footer {
    text-align: center;
    padding: 32px 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    margin-top: 40px;
}

.keywords-footer p {
    color: var(--secondary-color);
    font-size: 14px;
}

/* ========================================
   空状态
   ======================================== */
.empty-state {
    text-align: center;
    padding: 80px 20px;
}

.empty-icon {
    font-size: 64px;
    margin-bottom: 20px;
}

.empty-state h2 {
    font-size: 24px;
    color: var(--title-color);
    margin-bottom: 16px;
}

.empty-state p {
    color: var(--secondary-color);
    margin-bottom: 8px;
}

.btn-primary {
    display: inline-block;
    margin-top: 24px;
    padding: 12px 32px;
    background: var(--accent-color);
    color: #000;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 500;
}

/* ========================================
   索引页
   ======================================== */
.index-section {
    margin-bottom: 40px;
}

.index-entries {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.index-entry {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    transition: all 0.3s ease;
}

.index-entry:hover {
    border-color: var(--accent-color);
    transform: translateX(4px);
}

.entry-link {
    display: block;
    padding: 20px 24px;
    text-decoration: none;
}

.entry-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.entry-date {
    font-size: 16px;
    font-weight: 600;
    color: var(--title-color);
}

.entry-arrow {
    font-size: 20px;
    color: var(--accent-color);
}

.entry-summary {
    color: var(--secondary-color);
    font-size: 14px;
}

.empty-message {
    text-align: center;
    padding: 60px 20px;
    color: var(--secondary-color);
}

/* ========================================
   页脚
   ======================================== */
.footer {
    text-align: center;
    padding: 40px 20px;
    margin-top: 60px;
}

.footer p {
    color: var(--secondary-color);
    font-size: 14px;
}

/* ========================================
   响应式设计
   ======================================== */
@media (max-width: 768px) {
    .container {
        padding: 24px 16px;
    }

    .header h1 {
        font-size: 32px;
    }

    .logo-icon {
        width: 48px;
        height: 48px;
        font-size: 24px;
    }

    .section-title {
        font-size: 20px;
    }

    .category-title {
        font-size: 22px;
    }

    .news-card-header {
        flex-direction: column;
    }

    .item-link {
        align-self: flex-start;
    }

    .background-glow {
        width: 100%;
        height: 50%;
        bottom: -10%;
        right: -10%;
    }
}

@media (max-width: 480px) {
    .summary-card {
        padding: 20px;
    }

    .news-card {
        padding: 16px;
    }

    .date-badge {
        font-size: 12px;
        padding: 6px 14px;
    }
}
"""
        return css_content


def generate_daily_html(result: Dict[str, Any]) -> str:
    """便捷函数：生成日报 HTML"""
    generator = HTMLGenerator()
    generator.generate_css()
    return generator.generate_daily(result)
