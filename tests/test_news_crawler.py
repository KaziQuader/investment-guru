"""
Standalone smoke test for RSSNewsCrawler.

Run from the inner project folder:
    poetry run python tests/test_news_crawler.py

No MongoDB connection needed — just validates RSS parsing and document shape.
"""

from investement_guru.application.crawlers.news_crawler import RSSNewsCrawler
from investement_guru.domain.documents.news import NewsDocument
from unittest.mock import Mock
import sys
import os

# Allow running from the inner project root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Beanie initialization requirement for standalone testing
NewsDocument.get_pymongo_collection = Mock()


def test_news_crawler(ticker: str = "AAPL") -> None:
    crawler = RSSNewsCrawler(max_articles_per_feed=10)

    print(f"\n{'='*60}")
    print(f"Testing RSSNewsCrawler for ticker: {ticker}")
    print(f"{'='*60}")

    # fetch is synchronous
    docs = crawler.fetch(ticker)

    if not docs:
        print("WARNING: No articles returned. Check network access or feed URLs.")
        return

    print(f"\nFetched {len(docs)} articles\n")

    for i, doc in enumerate(docs[:5], 1):
        print(f"[{i}] {doc.title}")
        print(f"    Source : {doc.source_name}")
        print(f"    URL    : {doc.url}")
        print(f"    Date   : {doc.published_at}")
        print(f"    Tickers: {doc.tickers_mentioned}")
        print(
            f"    Content snippet: {doc.content[:150] + '...' if doc.content else 'None'}"
        )
        print()

    # Assertions
    assert all(doc.title for doc in docs), "All docs must have a title"
    assert all(doc.url for doc in docs), "All docs must have a URL"
    assert all(doc.published_at for doc in docs), "All docs must have a date"
    assert all(
        ticker.upper() in doc.tickers_mentioned for doc in docs
    ), f"All docs must mention {ticker}"
    assert len(docs) == len(
        {doc.url for doc in docs}
    ), "Duplicate URLs found — dedup logic failed"

    print("All assertions passed.")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_news_crawler(ticker)
