"""
RSS 获取与解析模块
负责下载 RSS XML 并解析出目标日期的内容
"""
import feedparser
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dateutil import parser as date_parser
import re

from src.config import RSS_URL, RSS_TIMEOUT


class RSSFetcher:
    """RSS 获取器"""

    def __init__(self, rss_url: str = None):
        self.rss_url = rss_url or RSS_URL
        self.timeout = RSS_TIMEOUT
        self._feed_data = None

    def fetch(self) -> feedparser.FeedParserDict:
        """下载并解析 RSS"""
        print(f"📥 正在下载 RSS: {self.rss_url}")

        try:
            response = requests.get(
                self.rss_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AI-Daily/1.0)"
                }
            )
            response.raise_for_status()

            # 使用 feedparser 解析
            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(f"⚠️ RSS 解析警告: {feed.bozo_exception}")

            print(f"✅ RSS 下载成功，共 {len(feed.entries)} 条资讯")
            self._feed_data = feed
            return feed

        except requests.RequestException as e:
            raise Exception(f"RSS 下载失败: {e}")
        except Exception as e:
            raise Exception(f"RSS 解析失败: {e}")

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """获取所有条目"""
        if not self._feed_data:
            self.fetch()
        return self._feed_data.entries

    def get_content_by_date(self, target_date: str, feed: feedparser.FeedParserDict = None) -> Optional[Dict[str, Any]]:
        """
        根据日期获取资讯内容

        Args:
            target_date: 目标日期，格式: YYYY-MM-DD
            feed: RSS 数据，如果为空则重新获取

        Returns:
            匹配的条目，如果没有找到则返回 None
        """
        if feed is None:
            feed = self.fetch()

        # 解析目标日期
        try:
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"日期格式错误: {target_date}，期望格式: YYYY-MM-DD")

        print(f"🔍 正在查找日期: {target_date}")

        # 尝试多种方式匹配日期
        for entry in feed.entries:
            # 方法1: 检查 pubDate
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if self._is_same_day(pub_dt, target_dt):
                    return self._extract_entry_content(entry)

            # 方法2: 从 link 中提取日期 (格式: .../issues/YY-MM-DD-slug/)
            if hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link and date_from_link == target_date:
                    return self._extract_entry_content(entry)

        print(f"❌ 未找到日期 {target_date} 的资讯")
        return None

    def _is_same_day(self, dt1: datetime, dt2: datetime) -> bool:
        """判断两个日期是否是同一天"""
        return (dt1.year, dt1.month, dt1.day) == (dt2.year, dt2.month, dt2.day)

    def _extract_date_from_link(self, link: str) -> Optional[str]:
        """从链接中提取日期，格式: YY-MM-DD 或 YYYY-MM-DD"""
        # 匹配 /issues/26-01-13- 或 /issues/2026-01-13- 格式
        patterns = [
            r'/issues/(\d{2})-(\d{2})-(\d{2})-',  # YY-MM-DD
            r'/issues/(\d{4})-(\d{2})-(\d{2})-',  # YYYY-MM-DD
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

    def get_latest_date(self, feed: feedparser.FeedParserDict = None) -> Optional[str]:
        """获取最新的资讯日期"""
        if feed is None:
            feed = self.fetch()

        if not feed.entries:
            return None

        # 获取第一条的日期
        entry = feed.entries[0]

        # 尝试从 link 中提取
        if hasattr(entry, 'link'):
            date_from_link = self._extract_date_from_link(entry.link)
            if date_from_link:
                return date_from_link

        # 尝试从 pubDate 中提取
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%d")

        return None

    def get_date_range(self, feed: feedparser.FeedParserDict = None) -> tuple:
        """获取 RSS 中的日期范围"""
        if feed is None:
            feed = self.fetch()

        if not feed.entries:
            return None, None

        dates = []
        for entry in feed.entries:
            if hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link:
                    dates.append(date_from_link)

        if not dates:
            return None, None

        return min(dates), max(dates)


def fetch_rss_content(target_date: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定日期的 RSS 内容"""
    fetcher = RSSFetcher()
    feed = fetcher.fetch()
    return fetcher.get_content_by_date(target_date, feed)
