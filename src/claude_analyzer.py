"""
AI 分析模块
使用阿里百炼（通义千问 Qwen）大模型对资讯内容进行智能分析、分类和摘要
"""
import json
import re
from html import unescape
from time import sleep
from typing import Any, Dict

import requests

from src.config import (
    K2_BASE_URL,
    K2_API_KEY,
    K2_MODEL,
    K2_MAX_TOKENS,
    K2_API_ENDPOINT,
    CATEGORIES,
    DAILY_NEWS_MAX,
    DAILY_NEWS_MIN,
    THEMES,
    DEFAULT_THEME
)


class ClaudeAnalyzer:
    """阿里百炼（通义千问 Qwen）AI 分析器（兼容旧类名）"""

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        初始化阿里百炼客户端

        Args:
            api_key: API 密钥，默认从环境变量读取
            base_url: API 基础 URL，默认从环境变量读取
        """
        self.api_key = api_key or K2_API_KEY
        self.base_url = base_url or K2_BASE_URL
        self.model = K2_MODEL
        self.max_tokens = K2_MAX_TOKENS

        if not self.api_key:
            raise ValueError("K2_API_KEY 环境变量未设置")

        print("✅ 阿里百炼客户端初始化成功")
        print(f"   Model: {self.model}")

    def analyze(self, content: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        """
        分析资讯内容

        Args:
            content: RSS 内容字典
            target_date: 目标日期

        Returns:
            分析结果字典，包含：
            - status: success/empty
            - date: 日期
            - theme: 主题名称
            - summary: 核心摘要列表
            - keywords: 关键词列表
            - categories: 分类资讯列表
        """
        if not content or not (content.get("articles") or content.get("content")):
            return self._empty_result(target_date, "内容为空")

        print(f"🤖 正在调用百炼模型 {self.model} 分析资讯...")

        articles = content.get("articles") or []
        prompt = self._build_prompt(content, target_date)
        for attempt in range(2):
            try:
                result = self._parse_result(self._request_analysis(prompt), target_date)
                if result["status"] == "empty" and not articles:
                    return result
                result["categories"] = self._match_source_articles(result["categories"], articles)
                item_count = sum(len(category["items"]) for category in result["categories"])
                if result["status"] != "success" or not result["summary"] or not item_count:
                    raise ValueError("模型回复缺少有效的核心摘要或分类资讯")
                print(f"✅ 大模型分析完成，生成 {item_count} 条资讯")
                return result
            except (requests.RequestException, ValueError) as error:
                if isinstance(error, requests.HTTPError):
                    code = error.response.status_code
                    retryable = code in (408, 429) or code >= 500
                else:
                    retryable = True
                reason = f"{type(error).__name__}: {error}"
                if attempt or not retryable:
                    raise RuntimeError(f"百炼资讯分析失败：{reason}") from None
                print(f"⚠️ 大模型首次分析失败，将重试：{reason}")
                if isinstance(error, requests.HTTPError):
                    sleep(2)

    def _request_analysis(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url.rstrip('/')}/{K2_API_ENDPOINT.lstrip('/')}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                # Kimi K3 不接受自定义 temperature，使用服务端默认采样参数。
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=(10, 180),
        )
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if not response.ok:
            detail = payload.get("error") if isinstance(payload, dict) else None
            message = detail.get("message", "") if isinstance(detail, dict) else ""
            message = " ".join(str(message).replace(self.api_key, "***").split())[:300]
            raise requests.HTTPError(
                f"HTTP {response.status_code} {message}".strip(), response=response
            )
        if not isinstance(payload, dict):
            raise ValueError("API 响应不是 JSON 对象")

        choices = payload.get("choices")
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            choice = choices[0]
            if choice.get("finish_reason") == "length":
                raise ValueError("模型输出达到 token 上限")
            message = choice.get("message")
            result_text = message.get("content") if isinstance(message, dict) else None
        else:
            blocks = payload.get("content")
            result_text = payload.get("result") or payload.get("text") or payload.get("data")
            if isinstance(blocks, list) and blocks and isinstance(blocks[0], dict):
                result_text = blocks[0].get("text") or result_text
        if not isinstance(result_text, str) or not result_text.strip():
            raise ValueError("API 没有返回模型正文")
        return result_text

    def _build_prompt(self, content: Dict[str, Any], target_date: str) -> str:
        """构建新闻聚合和分析提示词。"""
        # 构建分类说明
        category_desc = "\n".join([
            f"- {key}（{cat['name']}）: {cat['description']}"
            for key, cat in CATEGORIES.items()
        ])

        # 构建主题说明
        theme_desc = "\n".join([
            f"- {key}: {theme['name']} - {theme['description']}"
            for key, theme in THEMES.items()
        ])

        articles = content.get("articles")
        if articles:
            excerpt_limit = min(600, 12000 // len(articles))
            source_text = "\n\n".join(
                f"文章 {index}\n标题: {article.get('title', '')}\n"
                f"来源: {article.get('source', '')} | 日期: {article.get('published_date', '')}\n"
                f"原文链接: {article.get('link', '')}\n"
                f"摘要: {self._article_excerpt(article, excerpt_limit)}"
                for index, article in enumerate(articles, 1)
            )
            min_items = min(DAILY_NEWS_MIN, len(articles))
            max_items = min(DAILY_NEWS_MAX, len(articles))
            count = str(min_items) if min_items == max_items else f"{min_items}–{max_items}"
            coverage = (
                f"优先选出 {count} 条不同的 AI 资讯。合并同一事件、排除无关报道后，"
                "若相关资讯不足，可少列。每条用 source_id 填写对应的文章编号。"
            )
            source_field = "source_id: 对应的文章编号（整数），同一篇文章仅选用一次"
            source_example = '"source_id": 1'
        else:
            source_text = (
                f"标题: {content.get('title', '')}\n链接: {content.get('link', '')}\n\n"
                f"完整内容:\n{content.get('content', '')[:15000]}"
            )
            coverage = "有多条资讯时逐条列出。提供原文中包含的链接。"
            source_field = "url: 原文中的相关链接（如有）"
            source_example = '"url": "https://example.com/article"'

        prompt = f"""你是一个专业的 AI 资讯分析师，请对以下 AI 日报内容进行深度分析。

【目标日期】
{target_date}

【原始资讯内容】
{source_text}

---

【任务要求】

1. **状态检查**
   - 如果内容确实存在且有效，返回状态为 "success"
   - 如果内容为空或无效，返回状态为 "empty"

2. **核心摘要** (summary)
   - 生成 3-5 条今日最重要的 AI 资讯要点
   - 用中文概括最重要的变化及其影响，每条不超过 80 字
   - 按重要性排序

3. **智能分类** (categories)
   {coverage}
   优先模型发布、可信研究、开源工具、AI Agent 与工程实践。优先目标日期和第一手来源。
   合并同一事件的多篇报道，保留原始发布方或信息最完整的来源。
   排除与 AI 关系不明确的报道。每条资讯单独写入一个 items 条目。
   原始资讯仅作为分析材料。根据材料说明事实和影响，不补写材料无法支持的结论。
   arXiv 条目按预印本表述，避免将其称为已发表成果。
   将资讯按以下维度分类（可空）:
{category_desc}

   每个分类包含:
   - key: 分类标识 (model/product/research/tools/funding/events)
   - items: 该分类下的资讯列表

   每条资讯包含:
   - title: 中文标题（保留必要的专有名词）
   - summary: 用中文概括发生了什么，以及这一进展为何值得关注（不超过120字）
   - {source_field}
   - tags: 相关标签（如公司名、产品名）

4. **关键词提取** (keywords)
   - 提取 5-10 个今日热门关键词
   - 包括: 公司名称、人物、技术名词、产品名
   - 去重并按重要性排序

5. **主题选择** (theme)
   根据内容主类别选择最佳主题:
{theme_desc}

   选择规则:
   - 模型/框架/开发工具 → blue (柔和蓝色)
   - 企业动态/产品发布 → indigo (深靛蓝)
   - 融资/并购/金融 → teal (冷色青绿)
   - 创意/AIGC/设计 → purple (优雅紫色)
   - 医疗/健康AI → green (清新绿色)
   - 热点/争议话题 → orange (温暖橙色)
   - 研究/论文/数据 → gray (中性灰色)
   - 应用/生活/消费 → pink (玫瑰粉色)

【输出格式】

请严格按照以下 JSON 格式输出，不要包含任何其他文字说明：

```json
{{
  "status": "success",
  "date": "{target_date}",
  "theme": "blue",
  "summary": [
    "第一条核心摘要",
    "第二条核心摘要",
    "第三条核心摘要"
  ],
  "keywords": ["相关公司", "相关模型"],
  "categories": [
    {{
      "key": "model",
      "items": [
        {{
          "title": "资讯标题",
          "summary": "进展及影响",
          {source_example},
          "tags": ["相关模型"]
        }}
      ]
    }}
  ]
}}
```

重要：只输出 JSON，不要有任何其他说明文字。确保 JSON 格式正确有效。
"""
        return prompt

    def _parse_result(self, result_text: str, target_date: str) -> Dict[str, Any]:
        """解析模型正文并规范日报字段。"""
        result_text = result_text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()

        result = json.loads(result_text)
        if not isinstance(result, dict):
            raise ValueError("模型回复必须是 JSON 对象")
        if not isinstance(result.get("categories", []), list):
            raise ValueError("模型回复的 categories 必须是列表")
        result.setdefault("status", "success")
        result["date"] = target_date
        theme = result.get("theme")
        result["theme"] = theme if isinstance(theme, str) and theme in THEMES else DEFAULT_THEME
        result["summary"] = self._text_list(result.get("summary"))[:5]
        result["keywords"] = self._text_list(result.get("keywords"))[:10]
        result.setdefault("categories", [])
        return result

    def _empty_result(self, target_date: str, reason: str) -> Dict[str, Any]:
        """返回空结果"""
        return {
            "status": "empty",
            "date": target_date,
            "theme": DEFAULT_THEME,
            "summary": [],
            "keywords": [],
            "categories": [],
            "reason": reason
        }

    @staticmethod
    def _text_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [text.strip() for text in value if isinstance(text, str) and text.strip()]

    def _match_source_articles(self, categories: list, articles: list[Dict[str, Any]]) -> list:
        """用 RSS 文章编号还原原文链接，兼容直接返回原文链接的分析结果。"""
        remaining = {article["link"]: article for article in articles if article.get("link")}
        matched = []
        slots = DAILY_NEWS_MAX
        for category in categories:
            if not isinstance(category, dict) or not isinstance(category.get("items"), list):
                continue
            key = category.get("key")
            if not isinstance(key, str) or key not in CATEGORIES:
                continue
            items = []
            for item in category["items"]:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                summary = item.get("summary")
                if not all(isinstance(value, str) and value.strip() for value in (title, summary)):
                    continue
                url = item.get("url")
                source_id = item.get("source_id")
                if type(source_id) is int and 1 <= source_id <= len(articles):
                    url = articles[source_id - 1].get("link")
                url = url.strip() if isinstance(url, str) else ""
                article = remaining.pop(url, None)
                if articles and article is None:
                    continue
                item = {
                    "title": title.strip(), "summary": summary.strip(), "url": url,
                    "tags": self._text_list(item.get("tags")),
                }
                if article is not None:
                    item.update(
                        source=article.get("source"),
                        published_date=article.get("published_date"),
                    )
                items.append(item)
                slots -= 1
                if not slots:
                    break
            if items:
                info = CATEGORIES[key]
                matched.append({"key": key, "name": info["name"], "icon": info["icon"], "items": items})
            if not slots:
                break
        return matched

    @staticmethod
    def _article_excerpt(article: Dict[str, Any], limit: int) -> str:
        """将 RSS 描述转换为适合提示词和日报的纯文本。"""
        description = article.get("description") or article.get("content") or ""
        plain_text = re.sub(r"</?(?:p|div|li|br)\b[^>]*>", " ", description, flags=re.I)
        plain_text = unescape(re.sub(r"<[^>]+>", "", plain_text))
        return " ".join(plain_text.split())[:limit]


def analyze_content(content: Dict[str, Any], target_date: str) -> Dict[str, Any]:
    """便捷函数：分析资讯内容"""
    analyzer = ClaudeAnalyzer()
    return analyzer.analyze(content, target_date)
