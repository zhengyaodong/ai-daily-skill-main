"""
RSS 获取与解析模块
负责下载 RSS XML 并解析出目标日期的内容
"""
import re
from datetime import datetime, timedelta, timezone
from itertools import chain, zip_longest
from typing import Optional, Dict, List, Any
from urllib.parse import urlsplit

import feedparser
import requests

from src.config import (
    DAILY_NEWS_LOOKBACK_DAYS,
    DAILY_NEWS_MAX,
    DAILY_NEWS_MAX_CANDIDATES,
    DAILY_NEWS_MAX_PREPRINTS,
    RSS_TIMEOUT,
    RSS_URL,
    RSS_URLS,
)


class RSSFetcher:
    """RSS 获取器"""

    def __init__(self, rss_url: str = None, rss_urls: List[str] = None):
        # 支持单源配置（向后兼容）
        self.rss_url = rss_url or RSS_URL
        # 支持多源配置
        self.rss_urls = rss_urls or RSS_URLS
        self.timeout = RSS_TIMEOUT
        self._feed_data = None

    def fetch(self) -> feedparser.FeedParserDict:
        """
        下载并解析多个 RSS 源，合并结果
        """
        print(f"📥 正在下载多个 RSS 源，共 {len(self.rss_urls)} 个源")

        # 创建合并后的 feed 对象
        merged_feed = feedparser.FeedParserDict()
        merged_feed.entries = []
        merged_feed.feed = {"title": "合并的 AI 资讯 RSS", "link": ""}
        merged_feed.bozo = False
        merged_feed.version = "2.0"

        total_entries = 0
        failed_sources = 0

        for i, rss_url in enumerate(self.rss_urls, 1):
            try:
                print(f"   [{i}/{len(self.rss_urls)}] 正在下载: {rss_url}")
                
                response = requests.get(
                    rss_url,
                    timeout=self.timeout,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; AI-Daily/1.0)"
                    }
                )
                response.raise_for_status()

                # 使用 feedparser 解析单个源
                feed = feedparser.parse(response.content)

                if feed.bozo:
                    print(f"     ⚠️ 解析警告: {feed.bozo_exception}")

                if hasattr(feed, 'entries') and feed.entries:
                    entries_count = len(feed.entries)
                    merged_feed.entries.extend(feed.entries)
                    total_entries += entries_count
                    print(f"     ✅ 成功，获取 {entries_count} 条资讯")
                else:
                    print(f"     ⚠️ 该源无内容")

            except requests.RequestException as e:
                print(f"     ❌ 下载失败: {e}")
                failed_sources += 1
            except Exception as e:
                print(f"     ❌ 解析失败: {e}")
                failed_sources += 1

        # 按文章日期排序（最新的在前）
        merged_feed.entries.sort(
            key=lambda entry: (
                self._get_entry_date(entry) or "",
                entry.get("published_parsed") or entry.get("updated_parsed") or (),
            ),
            reverse=True
        )

        print(f"\n📊 RSS 下载完成")
        print(f"   总源数: {len(self.rss_urls)}")
        print(f"   成功源数: {len(self.rss_urls) - failed_sources}")
        print(f"   失败源数: {failed_sources}")
        print(f"   总资讯数: {total_entries}")
        
        if total_entries == 0:
            raise Exception("所有 RSS 源均未获取到内容")

        self._feed_data = merged_feed
        return merged_feed

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """获取所有条目"""
        if not self._feed_data:
            self.fetch()
        return self._feed_data.entries

    def get_content_by_date(self, target_date: str, feed: feedparser.FeedParserDict = None) -> Optional[Dict[str, Any]]:
        """
        根据日期获取资讯内容，聚合多个RSS源中同一天的所有文章

        Args:
            target_date: 目标日期，格式: YYYY-MM-DD
            feed: RSS 数据，如果为空则重新获取

        Returns:
            合并后的资讯内容字典，如果没有找到则返回 None
        """
        if feed is None:
            feed = self.fetch()

        # 解析目标日期
        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date().isoformat()
        except ValueError:
            raise ValueError(f"日期格式错误: {target_date}，期望格式: YYYY-MM-DD")

        print(f"🔍 正在查找日期: {target_date}")

        matched_entries = [
            entry for entry in feed.entries
            if self._get_entry_date(entry) == target_date
        ]

        if not matched_entries:
            print(f"❌ 未找到日期 {target_date} 的资讯")
            return None

        print(f"   找到 {len(matched_entries)} 篇相关文章")

        # 合并所有匹配的文章内容
        return self._merge_entries_content(matched_entries, target_date)

    def get_digest_content(
        self, target_date: str, feed: feedparser.FeedParserDict
    ) -> Optional[Dict[str, Any]]:
        """优先选目标日期的资讯，候选不足时按日期向前补充。"""
        target_day = datetime.strptime(target_date, "%Y-%m-%d").date()
        by_day = {
            (target_day - timedelta(days=offset)).isoformat(): {}
            for offset in range(DAILY_NEWS_LOOKBACK_DAYS)
        }

        for entry in feed.entries:
            day = self._get_entry_date(entry)
            if day not in by_day or not (entry.get("title") or "").strip():
                continue
            link = entry.get("link") or ""
            if not link.startswith(("https://", "http://")):
                continue
            source = self._get_source(link)
            if source:
                by_day[day].setdefault(source, []).append(entry)

        selected = []
        seen_links = set()
        seen_titles = set()
        preprint_count = 0
        for sources in by_day.values():
            # 同一天的来源轮流提供一条，避免高频来源占满邮件。
            entries = chain.from_iterable(zip_longest(*sources.values()))
            for entry in filter(None, entries):
                link = entry.link.split("#", 1)[0]
                title = " ".join(entry.title.casefold().split())
                if link in seen_links or title in seen_titles:
                    continue
                if self._get_source(link) == "arXiv 预印本":
                    if preprint_count >= DAILY_NEWS_MAX_PREPRINTS:
                        continue
                    preprint_count += 1
                selected.append(entry)
                seen_links.add(link)
                seen_titles.add(title)
                if len(selected) == DAILY_NEWS_MAX_CANDIDATES:
                    return self._merge_entries_content(selected, target_date)
            if len(selected) >= DAILY_NEWS_MAX:
                break

        return self._merge_entries_content(selected, target_date) if selected else None

    @staticmethod
    def _get_source(link: str) -> str:
        try:
            host = (urlsplit(link).hostname or "").removeprefix("www.")
        except ValueError:
            return ""
        if host == "arxiv.org" or host.endswith(".arxiv.org"):
            return "arXiv 预印本"
        return host

    def _get_entry_date(self, entry: feedparser.FeedParserDict) -> Optional[str]:
        """优先使用发布日期，兼容只提供链接日期或更新时间的源。"""
        published = entry.get("published_parsed")
        if published:
            return datetime(*published[:6], tzinfo=timezone.utc).date().isoformat()

        link_date = self._extract_date_from_link(entry.get("link") or "")
        if link_date:
            return link_date

        updated = entry.get("updated_parsed")
        if updated:
            return datetime(*updated[:6], tzinfo=timezone.utc).date().isoformat()

        return None

    def _extract_date_from_link(self, link: str) -> Optional[str]:
        """从链接中提取日期，支持多种URL格式"""
        # 匹配各种URL中的日期格式
        patterns = [
            r'/issues/(\d{2})-(\d{2})-(\d{2})-',  # smol.ai: /issues/26-01-13-slug
            r'/issues/(\d{4})-(\d{2})-(\d{2})-',  # smol.ai: /issues/2026-01-13-slug
            r'/(\d{4})/(\d{2})/(\d{2})/',          # 通用: /2026/01/13/
            r'/(\d{4})-(\d{2})-(\d{2})/',           # 通用: /2026-01-13/
            r'\?p=(\d{4})(\d{2})(\d{2})',           # WordPress: ?p=20260113
        ]

        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                year, month, day = match.groups()
                # 如果是两位年份，转换为四位
                if len(year) == 2:
                    year = "20" + year
                return f"{year}-{month}-{day}"

        return None

    def _extract_entry_content(self, entry) -> Dict[str, Any]:
        """提取条目内容"""
        content = {
            "title": "",
            "link": "",
            "guid": "",
            "description": "",
            "content": "",
            "pubDate": ""
        }

        # 提取标题
        content["title"] = entry.get("title", "")

        # 提取链接
        content["link"] = entry.get("link", "")
        content["source"] = self._get_source(content["link"])
        content["published_date"] = self._get_entry_date(entry)

        # 提取 GUID
        content["guid"] = entry.get("id", entry.get("guid", content["link"]))

        # 提取描述
        content["description"] = entry.get("description", "")

        # 提取完整内容
        if hasattr(entry, 'content') and entry.content:
            content["content"] = entry.content[0].get('value', '')
        elif hasattr(entry, 'summary'):
            content["content"] = entry.summary
        else:
            content["content"] = content["description"]

        # 提取发布日期
        if hasattr(entry, 'published'):
            content["pubDate"] = entry.published
        elif hasattr(entry, 'updated'):
            content["pubDate"] = entry.updated

        # 清理 HTML 实体
        content["content"] = content["content"].replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        return content

    def _merge_entries_content(self, entries: list, target_date: str) -> Dict[str, Any]:
        """
        合并多个RSS条目为一个统一的内容字典

        Args:
            entries: 匹配的RSS条目列表
            target_date: 目标日期

        Returns:
            合并后的内容字典
        """
        articles = []
        seen_links = set()
        for entry in entries:
            article = self._extract_entry_content(entry)
            link = article["link"]
            if link and link in seen_links:
                continue
            if link:
                seen_links.add(link)
            articles.append(article)

        if len(articles) == 1:
            return {**articles[0], "articles": articles}

        titles = []
        links = []
        contents = []
        pub_date = ""

        for entry_content in articles:
            titles.append(entry_content["title"])
            if entry_content["link"]:
                links.append(entry_content["link"])
            if entry_content["content"]:
                # 添加文章标题作为分隔标记
                contents.append(f"--- 文章: {entry_content['title']} ---\n{entry_content['content']}")
            if not pub_date and entry_content["pubDate"]:
                pub_date = entry_content["pubDate"]

        return {
            "title": f"AI Daily 资讯聚合 - {target_date}（共{len(articles)}篇）",
            "link": links[0] if links else "",
            "guid": links[0] if links else "",
            "description": f"包含 {len(articles)} 篇AI相关文章: {', '.join(titles[:5])}",
            "content": "\n\n".join(contents),
            "pubDate": pub_date,
            "articles": articles,
        }

    def get_latest_date(self, feed: feedparser.FeedParserDict = None) -> Optional[str]:
        """获取最新的资讯日期"""
        return self.get_date_range(feed)[1]

    def get_date_range(self, feed: feedparser.FeedParserDict = None) -> tuple:
        """
        获取 RSS 中的日期范围
        
        Args:
            feed: RSS 数据，如果为空则重新获取
            
        Returns:
            (最小日期, 最大日期)，如果没有找到日期则返回 (None, None)
        """
        if feed is None:
            feed = self.fetch()

        dates = [self._get_entry_date(entry) for entry in feed.entries]
        dates = [date for date in dates if date]
        return (min(dates), max(dates)) if dates else (None, None)


def fetch_rss_content(target_date: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定日期的 RSS 内容"""
    fetcher = RSSFetcher()
    feed = fetcher.fetch()
    return fetcher.get_content_by_date(target_date, feed)
