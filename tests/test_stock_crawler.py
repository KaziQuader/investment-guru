"""
Standalone smoke test for StockCrawler.

Run from the inner project folder:
    poetry run python tests/test_stock_crawler.py

No MongoDB connection needed — just validates yfinance fetching and document shape.
"""

from investement_guru.application.crawlers.stock_crawler import StockCrawler
from investement_guru.domain.documents.stocks import StockDocument
from unittest.mock import Mock
import sys
import os

# Allow running from the inner project root without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Beanie initialization requirement for standalone testing
StockDocument.get_pymongo_collection = Mock()


def test_stock_crawler(ticker: str = "AAPL") -> None:
    crawler = StockCrawler()

    print(f"\n{'='*60}")
    print(f"Testing StockCrawler for ticker: {ticker}")
    print(f"{'='*60}")

    docs = crawler.fetch(ticker)

    if not docs:
        print("WARNING: No stock document returned. Check network access or ticker validity.")
        return

    print(f"\nFetched {len(docs)} stock document(s)\n")

    for i, doc in enumerate(docs[:5], 1):
        print(f"[{i}] {doc.company_name} ({doc.ticker})")
        print(f"    Sector       : {doc.sector}")
        print(f"    Industry     : {doc.industry}")
        print(f"    Current Price: {doc.current_price}")
        print(f"    Market Cap   : {doc.market_cap}")
        print(f"    Price History: {len(doc.price_history)} days fetched")
        print()

    # Assertions
    assert all(doc.ticker == ticker.upper() for doc in docs), "All docs must match the ticker"
    assert all(doc.company_name for doc in docs), "All docs must have a company name"
    assert all(doc.current_price for doc in docs), "All docs must have a current price"
    assert all(len(doc.price_history) > 0 for doc in docs), "All docs must have price history"

    print("All assertions passed.")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_stock_crawler(ticker)
