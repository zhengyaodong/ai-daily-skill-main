"""Regression tests for the RSS, analysis, HTML, and email pipeline."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import feedparser
import requests

from src import main
from src.claude_analyzer import ClaudeAnalyzer
from src.html_generator import HTMLGenerator
from src.notifier import EmailNotifier
from src.rss_fetcher import RSSFetcher


class DailyNewsTest(unittest.TestCase):
    date = "2026-11-22"

    def setUp(self):
        output = redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)
        date_tuple = datetime(2026, 11, 22, tzinfo=timezone.utc).utctimetuple()
        self.entries = [
            feedparser.FeedParserDict(
                title="First news",
                link="https://example.test/first",
                published_parsed=date_tuple,
                summary="<p>" + "long report " * 2000 + "</p>",
            ),
            feedparser.FeedParserDict(
                title="Second & third-party news",
                link="https://example.test/second?a=1&b=2",
                updated_parsed=date_tuple,
                summary="<p>Second <strong>summary</strong>.</p>",
            ),
            feedparser.FeedParserDict(
                title="Third news",
                link="https://example.test/2026/11/22/third",
            ),
        ]
        self.feed = feedparser.FeedParserDict(entries=self.entries + [self.entries[0]])
        self.fetcher = RSSFetcher()
        self.analyzer = ClaudeAnalyzer(api_key="test-only")

    @patch("src.claude_analyzer.requests.post")
    def test_all_article_links_reach_model_and_valid_analysis_is_kept(self, post):
        self.analyzer.model = "kimi-k3.1-pro"
        expected = [
            {"title": f"中文资讯 {index}", "summary": "模型分析的影响", "url": entry.link}
            for index, entry in enumerate(self.entries, 1)
        ]
        model_items = [
            {"title": item["title"], "summary": item["summary"], "source_id": index}
            for index, item in enumerate(expected, 1)
        ]
        model_items.extend([
            {"title": "重复文章", "summary": "已有文章", "source_id": 1},
            {"title": "无对应来源", "summary": "跳过", "source_id": 99},
        ])
        response = {"summary": ["大模型生成的中文核心摘要"], "categories": [
            {"key": "model", "items": model_items}
        ]}
        post.return_value = self._completion(json.dumps(response))

        content = self.fetcher.get_content_by_date(self.date, self.feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(len(content["articles"]), 3)
        request_data = post.call_args.kwargs["json"]
        self.assertEqual(request_data["model"], "kimi-k3.1-pro")
        self.assertNotIn("temperature", request_data)
        prompt = request_data["messages"][0]["content"]
        for entry in self.entries:
            self.assertIn(entry.title, prompt)
            self.assertIn(entry.link, prompt)
        self.assertLess(len(prompt), 15000)
        items = result["categories"][0]["items"]
        self.assertEqual([{key: item[key] for key in expected[0]} for item in items], expected)
        self.assertEqual([item["published_date"] for item in items], [self.date] * 3)

        with tempfile.TemporaryDirectory() as output_dir:
            html_path = HTMLGenerator(output_dir).generate_daily(result)
            html = Path(html_path).read_text(encoding="utf-8")
            self.assertIn("大模型生成的中文核心摘要", html)
            self.assertIn("模型分析的影响", html)
            self.assertIn("https://example.test/second?a=1&amp;b=2", html)
            self.assertNotIn("RSS 原始资讯", html)

    @staticmethod
    def _api_response(status_code, payload):
        response = requests.Response()
        response.status_code = status_code
        response._content = json.dumps(payload).encode("utf-8")
        return response

    @classmethod
    def _completion(cls, text):
        return cls._api_response(200, {
            "choices": [{"finish_reason": "stop", "message": {"content": text}}],
        })

    @staticmethod
    def _additional_entries(count, day, host):
        date_tuple = datetime(2026, 11, day, tzinfo=timezone.utc).utctimetuple()
        return [
            feedparser.FeedParserDict(
                title=f"Article {host} {day}-{index}",
                link=f"https://{host}/{day}/{index}",
                published_parsed=date_tuple,
            )
            for index in range(count)
        ]

    def test_digest_backfills_recent_news_and_limits_preprints(self):
        papers = self._additional_entries(20, 22, "arxiv.org")
        tools = self._additional_entries(9, 21, "github.blog")
        older = self._additional_entries(3, 20, "deepmind.google")
        stale = self._additional_entries(20, 19, "old.example.test")
        future = self._additional_entries(2, 23, "future.example.test")
        duplicate = feedparser.FeedParserDict(
            title="  FIRST news  ", link="https://another.example.test/first",
            published_parsed=self.entries[0].published_parsed,
        )
        self.feed.entries.extend(papers + tools + older + stale + future + [duplicate])

        content = self.fetcher.get_digest_content(self.date, self.feed)
        articles = content["articles"]

        self.assertEqual(len(articles), 16)
        self.assertEqual(articles[1]["source"], "arXiv 预印本")
        self.assertEqual(sum(article["source"] == "arXiv 预印本" for article in articles), 4)
        self.assertEqual({article["published_date"] for article in articles}, {self.date, "2026-11-21"})

    @patch("src.claude_analyzer.requests.post")
    def test_keeps_a_shorter_deduplicated_digest(self, post):
        self.feed.entries.extend(self._additional_entries(14, 22, "github.blog"))
        post.return_value = self._completion(json.dumps({
            "summary": ["合并重复报道后的重点"],
            "categories": [{"key": "tools", "items": [
                {"title": "工具动态", "summary": "发布新的开发工具", "url": entry.link}
                for entry in self.entries
            ]}],
        }))
        content = self.fetcher.get_digest_content(self.date, self.feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(len(result["categories"][0]["items"]), 3)
        self.assertEqual(result["categories"][0]["name"], "工具框架")
        post.assert_called_once()

    @patch("src.claude_analyzer.requests.post")
    def test_invalid_analysis_fails_after_retry(self, post):
        content = self.fetcher.get_content_by_date(self.date, self.feed)
        for response_text in (
            "```json\n{",
            '{"categories": []}',
            '{"status": "empty"}',
            '{"summary": ["概要"], "categories": [{"key": "model", "items": [{"title": "仅有标题"}]}]}',
        ):
            with self.subTest(response=response_text):
                post.reset_mock()
                post.return_value = self._completion(response_text)
                with self.assertRaisesRegex(RuntimeError, "百炼资讯分析失败"):
                    self.analyzer.analyze(content, self.date)
                self.assertEqual(post.call_count, 2)

    @patch("src.claude_analyzer.requests.post")
    def test_http_400_reports_api_error_without_retry(self, post):
        post.return_value = self._api_response(400, {
            "error": {"message": "Parameter 'temperature'=0.3 is not supported for kimi-k3 model."}
        })
        content = self.fetcher.get_content_by_date(self.date, self.feed)
        with self.assertRaisesRegex(RuntimeError, "HTTP 400.*temperature.*kimi-k3"):
            self.analyzer.analyze(content, self.date)
        post.assert_called_once()

    @patch("src.claude_analyzer.requests.post", side_effect=requests.Timeout)
    @patch("src.notifier.smtplib.SMTP")
    def test_api_failure_preserves_existing_report_and_sends_error_email(self, smtp, post):
        self.feed.entries.extend(self._additional_entries(9, 21, "github.blog"))
        notifier = EmailNotifier(
            host="smtp.example.test", user="sender@example.test",
            password="test-only", to_email="recipient@example.test",
        )
        with (
            tempfile.TemporaryDirectory() as output_dir,
            patch.object(main, "get_target_date", return_value=self.date),
            patch.object(main, "ZHIPU_API_KEY", "test-only"),
            patch.object(main, "ENABLE_IMAGE_GENERATION", False),
            patch.object(main, "RSSFetcher", return_value=self.fetcher),
            patch.object(self.fetcher, "fetch", return_value=self.feed),
            patch.object(main, "ClaudeAnalyzer", return_value=self.analyzer),
            patch.object(main, "HTMLGenerator", return_value=HTMLGenerator(output_dir)),
            patch.object(main, "EmailNotifier", return_value=notifier),
            patch("src.notifier.DISABLE_EMAIL_NOTIFICATION", False),
            patch("src.notifier.OUTPUT_DIR", output_dir),
        ):
            daily_path = Path(output_dir) / f"{self.date}.html"
            index_path = Path(output_dir) / "index.html"
            daily_path.write_text("Existing report", encoding="utf-8")
            index_path.write_text("Existing index", encoding="utf-8")
            with self.assertRaises(SystemExit) as error, patch("traceback.print_exc"):
                main.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(daily_path.read_text(encoding="utf-8"), "Existing report")
            self.assertEqual(index_path.read_text(encoding="utf-8"), "Existing index")

        send_message = smtp.return_value.__enter__.return_value.send_message
        send_message.assert_called_once()
        message = send_message.call_args.args[0]
        self.assertIn("生成失败", str(message["Subject"]))
        self.assertEqual(post.call_count, 2)

    @patch("src.claude_analyzer.requests.post")
    def test_single_article_is_analyzed_after_transient_timeout(self, post):
        post.side_effect = [requests.Timeout(), self._completion(json.dumps({
            "summary": ["单篇资讯的核心变化"],
            "categories": [{"key": "research", "items": [
                {"title": "研究进展", "summary": "介绍研究方法与用途", "source_id": 1}
            ]}],
        }))]
        feed = feedparser.FeedParserDict(entries=[self.entries[-1]])
        content = self.fetcher.get_content_by_date(self.date, feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(result["categories"][0]["items"][0]["title"], "研究进展")
        self.assertEqual(len(result["categories"][0]["items"]), 1)
        self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
