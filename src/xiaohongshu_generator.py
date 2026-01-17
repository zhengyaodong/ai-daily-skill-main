"""
小红书风格封面生成模块
生成适合小红书分享的 3:4 比例封面
"""
import os
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.config import OUTPUT_DIR


class XiaohongshuGenerator:
    """小红书封面生成器"""

    # 账号信息
    ACCOUNT_NAME = "极客杰尼"
    ACCOUNT_SLOGAN = "AI实战派"

    # 尺寸配置
    COVER_WIDTH = 750
    COVER_HEIGHT = 1000  # 3:4 比例

    def __init__(self, output_dir: str = None):
        """
        初始化生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir or OUTPUT_DIR) / "xiaohongshu"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成小红书风格封面 HTML

        Args:
            analysis_result: Claude 分析结果

        Returns:
            生成的 HTML 文件路径
        """
        date = analysis_result.get("date", "")
        summary = analysis_result.get("summary", [])
        keywords = analysis_result.get("keywords", [])

        # 格式化日期
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = f"{dt.month}.{dt.day}"
        except:
            formatted_date = date

        # 提取关键信息
        main_title = self._extract_main_title(summary)
        subtitle = self._extract_subtitle(summary)
        highlights = summary[:3] if summary else []

        # 生成 HTML
        html_content = self._build_html(
            date=formatted_date,
            main_title=main_title,
            subtitle=subtitle,
            highlights=highlights,
            keywords=keywords
        )

        # 保存文件
        filename = f"xhs-{date}.html"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(filepath)

    def _extract_main_title(self, summary: list) -> str:
        """
        从摘要中提取主标题（2-3个关键词）

        Args:
            summary: 摘要列表

        Returns:
            主标题
        """
        if not summary:
            return "AI日报"

        # 取前两条摘要，提取关键词
        text = " ".join(summary[:2])

        # 常见的高价值关键词
        priority_keywords = [
            "Claude", "GPT", "OpenAI", "Anthropic", "Google",
            "发布", "开源", "更新", "突破", "首个", "首次",
            "Agent", "模型", "AI", "大模型", "多模态"
        ]

        # 提取优先关键词
        found_keywords = []
        for keyword in priority_keywords:
            if keyword in text:
                found_keywords.append(keyword)
                if len(found_keywords) >= 3:
                    break

        if found_keywords:
            return " · ".join(found_keywords[:2])

        # 如果没有找到关键词，使用第一条摘要的前两个字
        first = summary[0]
        if len(first) >= 4:
            return first[:4]

        return "AI日报"

    def _extract_subtitle(self, summary: list) -> str:
        """
        提取副标题

        Args:
            summary: 摘要列表

        Returns:
            副标题
        """
        if not summary:
            return f"{self.ACCOUNT_SLOGAN}每日更新"

        # 使用第一条摘要作为副标题，截取合适长度
        first = summary[0]
        if len(first) > 25:
            return first[:25] + "..."
        return first

    def _build_html(
        self,
        date: str,
        main_title: str,
        subtitle: str,
        highlights: list,
        keywords: list
    ) -> str:
        """
        构建 HTML 内容

        Args:
            date: 日期
            main_title: 主标题
            subtitle: 副标题
            highlights: 亮点列表
            keywords: 关键词列表

        Returns:
            HTML 字符串
        """
        # 高亮关键词
        highlight_spans = ""
        for i, item in enumerate(highlights[:3]):
            # 提取关键词（取前6个字）
            key_text = item[:6] if len(item) > 6 else item
            highlight_spans += f'<span class="highlight-item">{key_text}</span>'

        # 关键词标签
        keyword_tags = ""
        for kw in keywords[:5]:
            keyword_tags += f'<span class="keyword-tag">#{kw}</span>'

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Daily - 小红书封面</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Noto Sans SC', sans-serif;
            background: #1a1a1a;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }}

        .container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
        }}

        /* 封面画布 - 3:4 比例 */
        .cover-canvas {{
            width: {self.COVER_WIDTH}px;
            height: {self.COVER_HEIGHT}px;
            background: #000000;
            position: relative;
            overflow: hidden;
        }}

        /* 网格背景线 */
        .grid-lines {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image:
                linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
        }}

        /* 装饰性几何元素 */
        .geo-circle {{
            position: absolute;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 50%;
        }}

        .geo-circle-1 {{
            width: 300px;
            height: 300px;
            top: -100px;
            right: -100px;
        }}

        .geo-circle-2 {{
            width: 200px;
            height: 200px;
            bottom: 100px;
            left: -50px;
            border-color: rgba(0, 255, 136, 0.1);
        }}

        .geo-square {{
            position: absolute;
            border: 1px solid rgba(255,255,255,0.05);
        }}

        .geo-square-1 {{
            width: 80px;
            height: 80px;
            top: 150px;
            left: 30px;
        }}

        /* 内容区域 */
        .content {{
            position: relative;
            z-index: 10;
            height: 100%;
            display: flex;
            flex-direction: column;
            padding: 50px 40px;
        }}

        /* 顶部信息 */
        .top-info {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 60px;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .brand-dot {{
            width: 8px;
            height: 8px;
            background: #00ff88;
        }}

        .brand-name {{
            font-size: 14px;
            font-weight: 300;
            color: rgba(255,255,255,0.6);
            letter-spacing: 2px;
        }}

        .date-badge {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: rgba(255,255,255,0.4);
            font-weight: 400;
        }}

        /* 主标题区域 */
        .title-section {{
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}

        .main-title {{
            font-size: 72px;
            font-weight: 900;
            color: #ffffff;
            line-height: 1.1;
            letter-spacing: -2px;
            margin-bottom: 30px;
            word-break: keep-all;
        }}

        .main-title .highlight {{
            color: #00ff88;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
        }}

        /* 分割线 */
        .divider {{
            width: 60px;
            height: 3px;
            background: #00ff88;
            margin: 30px 0;
        }}

        /* 副标题 */
        .subtitle {{
            font-size: 24px;
            font-weight: 300;
            color: rgba(255,255,255,0.7);
            line-height: 1.5;
            margin-bottom: 40px;
            max-width: 80%;
        }}

        /* 亮点标签区域 */
        .highlights {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 40px;
        }}

        .highlight-item {{
            font-size: 16px;
            color: rgba(255,255,255,0.5);
            padding: 8px 16px;
            border: 1px solid rgba(255,255,255,0.1);
            font-weight: 300;
        }}

        /* 底部区域 */
        .bottom-section {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}

        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            max-width: 70%;
        }}

        .keyword-tag {{
            font-size: 13px;
            color: #00ff88;
            font-weight: 400;
        }}

        .account-info {{
            text-align: right;
        }}

        .account-name {{
            font-size: 14px;
            color: rgba(255,255,255,0.4);
            font-weight: 300;
            letter-spacing: 1px;
        }}

        .account-slogan {{
            font-size: 12px;
            color: #00ff88;
            margin-top: 4px;
            font-weight: 400;
        }}

        /* 装饰性指示线 */
        .indicator-line {{
            position: absolute;
            bottom: 50px;
            left: 40px;
            width: 100px;
            height: 1px;
            background: linear-gradient(90deg, rgba(255,255,255,0.3), transparent);
        }}

        .indicator-line::after {{
            content: '';
            position: absolute;
            right: 0;
            top: -3px;
            width: 7px;
            height: 7px;
            background: #00ff88;
            border-radius: 50%;
        }}

        /* 控制面板 */
        .controls {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}

        .btn {{
            padding: 12px 30px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Noto Sans SC', sans-serif;
            border-radius: 4px;
        }}

        .btn:hover {{
            background: rgba(255,255,255,0.15);
            border-color: rgba(255,255,255,0.3);
        }}

        .btn-primary {{
            background: #00ff88;
            color: #000;
            border: none;
            font-weight: 500;
        }}

        .btn-primary:hover {{
            background: #00cc6a;
        }}

        .status {{
            color: rgba(255,255,255,0.5);
            font-size: 13px;
            min-width: 150px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="cover-canvas" id="cover">
            <!-- 网格背景 -->
            <div class="grid-lines"></div>

            <!-- 几何装饰 -->
            <div class="geo-circle geo-circle-1"></div>
            <div class="geo-circle geo-circle-2"></div>
            <div class="geo-square geo-square-1"></div>

            <!-- 内容 -->
            <div class="content">
                <!-- 顶部信息 -->
                <div class="top-info">
                    <div class="brand">
                        <span class="brand-dot"></span>
                        <span class="brand-name">{self.ACCOUNT_NAME.upper()}</span>
                    </div>
                    <div class="date-badge">{date}</div>
                </div>

                <!-- 主标题区域 -->
                <div class="title-section">
                    <div class="main-title">{main_title}</div>
                    <div class="divider"></div>
                    <div class="subtitle">{subtitle}</div>

                    <!-- 亮点 -->
                    <div class="highlights">
                        {highlight_spans}
                    </div>
                </div>

                <!-- 底部区域 -->
                <div class="bottom-section">
                    <div class="keywords">
                        {keyword_tags}
                    </div>
                    <div class="account-info">
                        <div class="account-name">{self.ACCOUNT_NAME}</div>
                        <div class="account-slogan">{self.ACCOUNT_SLOGAN}</div>
                    </div>
                </div>

                <!-- 指示线 -->
                <div class="indicator-line"></div>
            </div>
        </div>

        <!-- 控制面板 -->
        <div class="controls">
            <button class="btn btn-primary" onclick="saveImage()">保存封面</button>
            <div class="status" id="status">点击保存按钮下载封面</div>
        </div>
    </div>

    <script>
        async function saveImage() {{
            const cover = document.getElementById('cover');
            const status = document.getElementById('status');

            status.textContent = '生成中...';

            try {{
                const canvas = await html2canvas(cover, {{
                    scale: 2,
                    useCORS: true,
                    backgroundColor: '#000000',
                    logging: false
                }});

                const link = document.createElement('a');
                link.download = 'ai-daily-xhs-{date}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();

                status.textContent = '✓ 封面已保存';
            }} catch (error) {{
                console.error(error);
                status.textContent = '保存失败，请重试';
            }}
        }}
    </script>
</body>
</html>'''
        return html


def generate_xiaohongshu_cover(analysis_result: Dict[str, Any], output_dir: str = None) -> str:
    """
    便捷函数：生成小红书封面

    Args:
        analysis_result: 分析结果
        output_dir: 输出目录

    Returns:
        生成的 HTML 文件路径
    """
    generator = XiaohongshuGenerator(output_dir)
    return generator.generate(analysis_result)
