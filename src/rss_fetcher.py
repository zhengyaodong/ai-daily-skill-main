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

from src.config import RSS_URL, RSS_URLS, RSS_TIMEOUT


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

        # 按发布时间排序（最新的在前）
        merged_feed.entries.sort(
            key=lambda entry: getattr(entry, 'published_parsed', (0, 0, 0)),
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
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            target_dt = target_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"日期格式错误: {target_date}，期望格式: YYYY-MM-DD")

        print(f"🔍 正在查找日期: {target_date}")

        # 收集目标日期的所有文章
        matched_entries = []
        for entry in feed.entries:
            matched = False
            # 方法1: 检查 pubDate
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if self._is_same_day(pub_dt, target_dt):
                    matched = True

            # 方法2: 从 link 中提取日期
            if not matched and hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link and date_from_link == target_date:
                    matched = True

            if matched:
                matched_entries.append(entry)

        if not matched_entries:
            print(f"❌ 未找到日期 {target_date} 的资讯")
            return None

        print(f"   找到 {len(matched_entries)} 篇相关文章")

        # 合并所有匹配的文章内容
        return self._merge_entries_content(matched_entries, target_date)

    def _is_same_day(self, dt1: datetime, dt2: datetime) -> bool:
        """判断两个日期是否是同一天"""
        return (dt1.year, dt1.month, dt1.day) == (dt2.year, dt2.month, dt2.day)

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
        if len(entries) == 1:
            return self._extract_entry_content(entries[0])

        titles = []
        links = []
        contents = []
        pub_date = ""

        for entry in entries:
            entry_content = self._extract_entry_content(entry)
            titles.append(entry_content["title"])
            if entry_content["link"]:
                links.append(entry_content["link"])
            if entry_content["content"]:
                # 添加文章标题作为分隔标记
                contents.append(f"--- 文章: {entry_content['title']} ---\n{entry_content['content']}")
            if not pub_date and entry_content["pubDate"]:
                pub_date = entry_content["pubDate"]

        return {
            "title": f"AI Daily 资讯聚合 - {target_date}（共{len(entries)}篇）",
            "link": links[0] if links else "",
            "guid": links[0] if links else "",
            "description": f"包含 {len(entries)} 篇AI相关文章: {', '.join(titles[:5])}",
            "content": "\n\n".join(contents),
            "pubDate": pub_date
        }

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
        """
        获取 RSS 中的日期范围
        
        Args:
            feed: RSS 数据，如果为空则重新获取
            
        Returns:
            (最小日期, 最大日期)，如果没有找到日期则返回 (None, None)
        """
        if feed is None:
            feed = self.fetch()

        if not feed.entries:
            return None, None

        dates = []
        for entry in feed.entries:
            # 方法1: 从 pubDate 中提取
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                dates.append(dt.strftime("%Y-%m-%d"))
                continue

            # 方法2: 从 link 中提取
            if hasattr(entry, 'link'):
                date_from_link = self._extract_date_from_link(entry.link)
                if date_from_link:
                    dates.append(date_from_link)

        if not dates:
            return None, None

        # 去重并排序
        unique_dates = sorted(list(set(dates)))
        return unique_dates[0], unique_dates[-1]


def fetch_rss_content(target_date: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取指定日期的 RSS 内容"""
    fetcher = RSSFetcher()
    feed = fetcher.fetch()
    return fetcher.get_content_by_date(target_date, feed)
