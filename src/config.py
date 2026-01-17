"""
配置模块 - 包含所有配置信息和主题定义
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ============================================================================
# API 配置
# ============================================================================

# Kimi API 配置（适用于 kimi-k2-0905-preview）
K2_BASE_URL = os.getenv(
    "K2_BASE_URL",
    "https://api.moonshot.cn/v1"  # Kimi API 基础 URL
)
K2_API_KEY = os.getenv("K2_API_KEY")
K2_MODEL = os.getenv("K2_MODEL", "kimi-k2-0905-preview")  # Kimi 模型名称
K2_MAX_TOKENS = 8192
K2_API_ENDPOINT = os.getenv("K2_API_ENDPOINT", "/chat/completions")  # API 端点路径

# 兼容旧配置，保持向后兼容
ANTHROPIC_BASE_URL = K2_BASE_URL
ZHIPU_API_KEY = K2_API_KEY
CLAUDE_MODEL = K2_MODEL
CLAUDE_MAX_TOKENS = K2_MAX_TOKENS

# ============================================================================
# RSS 配置
# ============================================================================
RSS_URL = os.getenv("RSS_URL", "https://news.smol.ai/rss.xml")
RSS_TIMEOUT = 30  # 秒

# ============================================================================
# 输出配置
# ============================================================================
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "docs")
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", "")

# ============================================================================
# 邮件通知配置
# ============================================================================
def _get_env_int(key: str, default: int) -> int:
    """获取整数环境变量，处理空字符串情况"""
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return int(value)


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = _get_env_int("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFICATION_TO = os.getenv("NOTIFICATION_TO")
DISABLE_EMAIL_NOTIFICATION = os.getenv("DISABLE_EMAIL_NOTIFICATION") == "true"

# ============================================================================
# 8种主题配色方案
# ============================================================================
THEMES = {
    "blue": {
        "name": "柔和蓝色",
        "description": "适用于科技/商务/数据类内容",
        "glow_start": "#0A1929",
        "glow_end": "#1A3A52",
        "title": "#FFFFFF",
        "text": "#E3F2FD",
        "accent": "#42A5F5",
        "secondary": "#B0BEC5",
        "gradient": "linear-gradient(135deg, #0A1929 0%, #1A3A52 100%)"
    },
    "indigo": {
        "name": "深靛蓝",
        "description": "适用于高端/企业/权威类内容",
        "glow_start": "#0F1C3F",
        "glow_end": "#1A2F5A",
        "title": "#FFFFFF",
        "text": "#E3F2FD",
        "accent": "#5C9FE5",
        "secondary": "#BBDEFB",
        "gradient": "linear-gradient(135deg, #0F1C3F 0%, #1A2F5A 100%)"
    },
    "purple": {
        "name": "优雅紫色",
        "description": "适用于创意/奢华/创新类内容",
        "glow_start": "#1A0A28",
        "glow_end": "#2D1B3D",
        "title": "#FFFFFF",
        "text": "#F3E5F5",
        "accent": "#B39DDB",
        "secondary": "#D1C4E9",
        "gradient": "linear-gradient(135deg, #1A0A28 0%, #2D1B3D 100%)"
    },
    "green": {
        "name": "清新绿色",
        "description": "适用于健康/可持续/成长类内容",
        "glow_start": "#0D1F12",
        "glow_end": "#1B3A26",
        "title": "#FFFFFF",
        "text": "#E8F5E9",
        "accent": "#66BB6A",
        "secondary": "#C8E6C9",
        "gradient": "linear-gradient(135deg, #0D1F12 0%, #1B3A26 100%)"
    },
    "orange": {
        "name": "温暖橙色",
        "description": "适用于活力/热情/社交类内容",
        "glow_start": "#1F1410",
        "glow_end": "#3D2415",
        "title": "#FFFFFF",
        "text": "#FFF3E0",
        "accent": "#FFA726",
        "secondary": "#FFCCBC",
        "gradient": "linear-gradient(135deg, #1F1410 0%, #3D2415 100%)"
    },
    "pink": {
        "name": "玫瑰粉色",
        "description": "适用于生活/美妆/健康类内容",
        "glow_start": "#1F0A14",
        "glow_end": "#3D1528",
        "title": "#FFFFFF",
        "text": "#FCE4EC",
        "accent": "#F06292",
        "secondary": "#F8BBD0",
        "gradient": "linear-gradient(135deg, #1F0A14 0%, #3D1528 100%)"
    },
    "teal": {
        "name": "冷色青绿",
        "description": "适用于金融/信任/稳定类内容",
        "glow_start": "#0A1F1F",
        "glow_end": "#164E4D",
        "title": "#FFFFFF",
        "text": "#E0F2F1",
        "accent": "#26A69A",
        "secondary": "#B2DFDB",
        "gradient": "linear-gradient(135deg, #0A1F1F 0%, #164E4D 100%)"
    },
    "gray": {
        "name": "中性灰色",
        "description": "适用于极简/专业/通用类内容",
        "glow_start": "#1A1A1D",
        "glow_end": "#2D2D30",
        "title": "#FFFFFF",
        "text": "#F5F5F5",
        "accent": "#9E9E9E",
        "secondary": "#E0E0E0",
        "gradient": "linear-gradient(135deg, #1A1A1D 0%, #2D2D30 100%)"
    }
}

# ============================================================================
# 资讯分类定义
# ============================================================================
CATEGORIES = {
    "model": {
        "name": "模型发布",
        "icon": "🤖",
        "description": "新模型/版本更新/架构突破"
    },
    "product": {
        "name": "产品动态",
        "icon": "💼",
        "description": "新产品/功能/企业动态"
    },
    "research": {
        "name": "研究论文",
        "icon": "📚",
        "description": "学术研究/技术突破/论文"
    },
    "tools": {
        "name": "工具框架",
        "icon": "🛠️",
        "description": "开发工具/开源项目/SDK"
    },
    "funding": {
        "name": "融资并购",
        "icon": "💰",
        "description": "投资/收购/IPO"
    },
    "events": {
        "name": "行业事件",
        "icon": "🏆",
        "description": "奖项/争议/政策/监管"
    }
}

# ============================================================================
# 内容类型到主题的映射
# ============================================================================
CATEGORY_THEME_MAP = {
    "model": "blue",      # 模型/框架/开发工具
    "product": "indigo",   # 企业动态/产品发布
    "funding": "teal",     # 融资/并购/金融
    "tools": "blue",       # 开发工具
    "research": "gray",    # 研究/论文/数据
    "events": "orange",    # 热点/争议话题
}

# ============================================================================
# 默认主题（当无法判断内容类型时使用）
# ============================================================================
DEFAULT_THEME = "blue"

# ============================================================================
# 网站元信息
# ============================================================================
SITE_META = {
    "title": "AI Daily",
    "subtitle": "AI 资讯日报",
    "description": "每日 AI 前沿资讯，智能分类，快速掌握核心动态",
    "author": "AI Daily",
    "keywords": ["AI", "人工智能", "机器学习", "深度学习", "资讯", "日报"]
}

# ============================================================================
# HTML 模板配置
# ============================================================================
HTML_TEMPLATE_CONFIG = {
    "lang": "zh-CN",
    "charset": "UTF-8",
    "viewport": "width=device-width, initial-scale=1.0"
}

# ============================================================================
# 图片生成 API 配置 (Firefly Card API)
# ============================================================================
FIREFLY_API_URL = os.getenv("FIREFLY_API_URL", "https://fireflycard-api.302ai.cn/api/saveImg")
FIREFLY_API_KEY = os.getenv("FIREFLY_API_KEY", "")  # 如果需要 API Key

# Firefly Card API 默认配置
FIREFLY_DEFAULT_CONFIG = {
    "font": "SourceHanSerifCN_Bold",
    "align": "left",
    "width": 400,
    "height": 533,
    "fontScale": 1.2,
    "ratio": "3:4",
    "padding": 30,
    "switchConfig": {
        "showIcon": False,
        "showTitle": False,
        "showContent": True,
        "showTranslation": False,
        "showAuthor": False,
        "showQRCode": False,
        "showSignature": False,
        "showQuotes": False,
        "showWatermark": False
    },
    "temp": "tempBlackSun",
    "fonts": {
        "title": 2.1329337874720125,
        "content": 1.9079435748084854,
        "translate": 1.1415042034904328,
        "author": 0.801229782035275
    },
    "textColor": "rgba(0,0,0,0.8)",
    "subTempId": "tempBlackSun",
    "borderRadius": 15,
    "color": "pure-ray-1",
    "useFont": "SourceHanSerifCN_Bold",
    "useLoadingFont": True
}

# 是否启用图片生成功能
ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "false").lower() == "true"


def get_theme(theme_name: str) -> dict:
    """获取指定主题配置"""
    return THEMES.get(theme_name, THEMES[DEFAULT_THEME])


def get_category_info(category_key: str) -> dict:
    """获取分类信息"""
    return CATEGORIES.get(category_key, CATEGORIES["model"])


def guess_theme_from_content(content_analysis: dict) -> str:
    """根据内容分析结果猜测最佳主题"""
    if not content_analysis or "categories" not in content_analysis:
        return DEFAULT_THEME

    categories = content_analysis.get("categories", [])
    if not categories:
        return DEFAULT_THEME

    # 找到包含最多资讯的分类
    max_category = max(categories, key=lambda x: len(x.get("items", [])))
    category_key = max_category.get("key", "")

    return CATEGORY_THEME_MAP.get(category_key, DEFAULT_THEME)
