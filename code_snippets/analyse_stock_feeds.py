import yfinance as yf
import feedparser
import json


def explore_yfinance():
    stock = yf.Ticker("AAPL")

    print("=== INFO (fundamentals) ===")
    print(json.dumps(stock.info, indent=2, default=str))

    print("\n=== HISTORY (price data) ===")
    history = stock.history(period="5d")
    print(history)
    print("\nColumns:", history.columns.tolist())
    print("Index type:", type(history.index[0]))


def explore_rss():
    feed = feedparser.parse("https://finance.yahoo.com/news/rssindex")

    print("=== FEED KEYS ===")
    print(feed.keys())

    print("\n=== FIRST ENTRY KEYS ===")
    print(feed.entries[0].keys())

    print("\n=== FIRST ENTRY FULL ===")
    print(json.dumps(dict(feed.entries[0]), indent=2, default=str))


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("YFINANCE")
    print("=" * 50)
    explore_yfinance()

    print("\n" + "=" * 50)
    print("RSS NEWS")
    print("=" * 50)
    explore_rss()
