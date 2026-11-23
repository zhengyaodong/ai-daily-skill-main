"""Regression tests for the RSS, analysis, HTML, and email pipeline."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
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
        expected = [{"title": entry.title, "url": entry.link} for entry in self.entries]
        response = {"categories": [{"name": "AI", "items": expected}]}
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": json.dumps(response)}}],
        }

        content = self.fetcher.get_content_by_date(self.date, self.feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(len(content["articles"]), 3)
        prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
        for entry in self.entries:
            self.assertIn(entry.title, prompt)
            self.assertIn(entry.link, prompt)
        self.assertLess(len(prompt), 15000)
        items = result["categories"][0]["items"]
        self.assertEqual([{key: item[key] for key in ("title", "url")} for item in items], expected)
        self.assertEqual([item["published_date"] for item in items], [self.date] * 3)

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
    def test_three_model_items_trigger_fallback_when_sources_have_more(self, post):
        self.feed.entries.extend(self._additional_entries(14, 22, "github.blog"))
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "categories": [{"items": [
                    {"title": "Model summary", "url": entry.link} for entry in self.entries
                ]}],
            })}}],
        }
        content = self.fetcher.get_digest_content(self.date, self.feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(len(result["categories"][0]["items"]), 15)
        self.assertEqual(result["categories"][0]["name"], "RSS 原始资讯")

    @patch("src.claude_analyzer.requests.post")
    def test_malformed_or_sparse_analysis_keeps_individual_articles(self, post):
        content = self.fetcher.get_content_by_date(self.date, self.feed)
        for response_text in (
            "```json\n{",
            '{"categories": []}',
            '{"status": "empty"}',
            '{"categories": [{"items": [{"title": "Only one"}]}]}',
        ):
            with self.subTest(response=response_text):
                post.return_value.json.return_value = {
                    "choices": [{"message": {"content": response_text}}],
                }
                result = self.analyzer.analyze(content, self.date)
                items = result["categories"][0]["items"]
                self.assertEqual([item["url"] for item in items], [e.link for e in self.entries])
                self.assertEqual(items[1]["summary"], "Second summary.")

    @patch("src.claude_analyzer.requests.post", side_effect=requests.Timeout)
    @patch("src.notifier.smtplib.SMTP")
    def test_api_failure_sends_full_digest_in_email(self, smtp, post):
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
            main.main()

        send_message = smtp.return_value.__enter__.return_value.send_message
        send_message.assert_called_once()
        message = send_message.call_args.args[0]
        body = next(part for part in message.walk() if part.get_content_type() == "text/html")
        html = body.get_payload(decode=True).decode("utf-8")
        self.assertIn("资讯条数: 12 条", html)
        self.assertEqual(html.count('<article class="news-card">'), 12)
        self.assertIn("github.blog · 2026-11-21", html)
        self.assertIn("First news", html)
        self.assertIn("Second &amp; third-party news", html)
        self.assertIn("https://example.test/second?a=1&amp;b=2", html)
        self.assertIn("Third news", html)

    @patch("src.claude_analyzer.requests.post", side_effect=requests.Timeout)
    def test_single_article_stays_single(self, post):
        feed = feedparser.FeedParserDict(entries=[self.entries[-1]])
        content = self.fetcher.get_content_by_date(self.date, feed)
        result = self.analyzer.analyze(content, self.date)

        self.assertEqual(result["categories"][0]["items"][0]["title"], "Third news")
        self.assertEqual(len(result["categories"][0]["items"]), 1)


if __name__ == "__main__":
    unittest.main()
