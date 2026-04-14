import logging
from datetime import datetime
from typing import Optional
import feedparser
import requests
from bs4 import BeautifulSoup
from investement_guru.domain.documents.news import NewsDocument
from investement_guru.application.crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RSS feed registry
# Multiple feeds increase coverage; each entry is (source_name, url).
# The crawler fetches all feeds and filters entries that mention the ticker.
# ---------------------------------------------------------------------------
RSS_FEEDS: list[tuple[str, str]] = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    (
        "Yahoo Finance Markets",
        "https://finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
    ),
    ("Seeking Alpha", "https://seekingalpha.com/api/sa/combined/{ticker}.xml"),
]

# Feeds that accept a ticker symbol in the URL (use {ticker} placeholder)
TICKER_SPECIFIC_FEEDS: list[tuple[str, str]] = [
    (
        "Yahoo Finance Ticker",
        "https://finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US",
    ),
]

# Generic feeds where we scan titles for ticker mentions
GENERIC_FEEDS: list[tuple[str, str]] = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
]


class RSSNewsCrawler(BaseCrawler):
    """
    Fetches financial news from RSS feeds for a given ticker.

    Strategy
    --------
    1. Fetch ticker-specific feeds (URLs that embed the ticker symbol).
    2. Fetch generic feeds and filter entries whose title mentions the ticker.
    3. Deduplicate by URL before returning.

    All entries are returned as NewsDocument objects (unsaved — the ZenML
    step that calls this crawler is responsible for MongoDB persistence).
    """

    model = NewsDocument

    def __init__(self, max_articles_per_feed: int = 50):
        self._max_articles_per_feed = max_articles_per_feed

    def get_source_name(self) -> str:
        return "rss"

    def fetch(self, ticker: str) -> list[NewsDocument]:
        """
        Fetch news articles for *ticker* from all configured RSS feeds.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol, e.g. "AAPL".

        Returns
        -------
        list[NewsDocument]
            Deduplicated list of news documents.  Not yet saved to MongoDB.
        """
        docs: list[NewsDocument] = []
        seen_urls: set[str] = set()

        # 1. Ticker-specific feeds
        for source_name, url_template in TICKER_SPECIFIC_FEEDS:
            url = url_template.format(ticker=ticker.upper())
            fetched = self._fetch_feed(url, source_name, ticker, seen_urls)
            docs.extend(fetched)
            logger.info(
                "Fetched %d articles from %s for %s", len(fetched), source_name, ticker
            )

        # 2. Generic feeds — filter by ticker mention in title
        for source_name, url in GENERIC_FEEDS:
            fetched = self._fetch_feed(
                url, source_name, ticker, seen_urls, filter_by_ticker=True
            )
            docs.extend(fetched)
            logger.info(
                "Fetched %d articles from %s mentioning %s",
                len(fetched),
                source_name,
                ticker,
            )

        logger.info("Total news articles for %s: %d", ticker, len(docs))
        return docs

    def _fetch_feed(
        self,
        url: str,
        source_name: str,
        ticker: str,
        seen_urls: set[str],
        filter_by_ticker: bool = False,
    ) -> list[NewsDocument]:
        """
        Parse a single RSS feed and return new (not yet seen) NewsDocuments.
        """
        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            logger.warning("Failed to parse feed %s: %s", url, exc)
            return []

        if feed.bozo and feed.bozo_exception:
            # feedparser sets bozo=True for malformed feeds; log but continue
            logger.debug("Bozo feed %s: %s", url, feed.bozo_exception)

        docs: list[NewsDocument] = []
        entries = feed.entries[: self._max_articles_per_feed]

        for entry in entries:
            article_url = self._extract_url(entry)
            if not article_url or article_url in seen_urls:
                continue

            title = self._extract_title(entry)
            if not title:
                continue

            # For generic feeds, skip entries that don't mention the ticker
            if filter_by_ticker and not self._mentions_ticker(title, ticker):
                continue

            seen_urls.add(article_url)
            doc = self._build_document(entry, article_url, title, source_name, ticker)
            docs.append(doc)

        return docs

    def _build_document(
        self,
        entry: feedparser.util.FeedParserDict,
        url: str,
        title: str,
        source_name: str,
        primary_ticker: str,
    ) -> NewsDocument:
        """Convert a feedparser entry into a NewsDocument."""
        published_at = self._extract_published(entry)

        # Resolve real source name from feed entry metadata when available
        resolved_source = self._extract_source_name(entry) or source_name

        # Detect all ticker mentions in the title (including the primary one)
        tickers_mentioned = self._extract_tickers(title, primary_ticker)

        # Attempt to get summary from feed, otherwise scrape it
        content = entry.get("summary") or entry.get("description")
        if not content:
            content = self._scrape_content(url)

        return NewsDocument(
            title=title,
            url=url,
            published_at=published_at,
            source_name=resolved_source,
            content=content,
            tickers_mentioned=tickers_mentioned,
        )

    # ------------------------------------------------------------------
    # Field extractors
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_url(entry: feedparser.util.FeedParserDict) -> Optional[str]:
        """Return the canonical URL for the entry."""
        # feedparser normalises the URL into .link
        return getattr(entry, "link", None) or entry.get("id")

    @staticmethod
    def _extract_title(entry: feedparser.util.FeedParserDict) -> Optional[str]:
        title = getattr(entry, "title", None) or entry.get("title")
        if title:
            return title.strip()
        return None

    @staticmethod
    def _extract_published(entry: feedparser.util.FeedParserDict) -> str:
        """
        Return a consistent published-at string.

        feedparser normalises the date into .published (raw string) and
        .published_parsed (struct_time).  We prefer the raw string for
        storage; it can be parsed to datetime during the RAG pipeline.
        """
        published = getattr(entry, "published", None)
        if published:
            return published.strip()

        # Fall back to ISO-formatted utcnow so the field is never empty
        return datetime.utcnow().isoformat()

    @staticmethod
    def _extract_source_name(entry: feedparser.util.FeedParserDict) -> Optional[str]:
        """
        Yahoo Finance RSS entries carry a <source> tag with the outlet name.
        feedparser exposes this as entry.source.title (a dict-like object).
        """
        source = entry.get("source")
        if isinstance(source, dict):
            return source.get("title")
        return None

    # Common English words that look like tickers — ignore them
    _TICKER_STOPWORDS: frozenset[str] = frozenset(
        {
            "A",
            "AN",
            "AS",
            "AT",
            "BE",
            "BY",
            "DO",
            "GO",
            "HE",
            "IF",
            "IN",
            "IS",
            "IT",
            "ME",
            "MY",
            "NO",
            "OF",
            "ON",
            "OR",
            "SO",
            "TO",
            "UP",
            "US",
            "WE",
            "AI",
            "TV",
            "PC",
            "US",
            "UK",
            "EU",
            "THE",
            "FOR",
            "AND",
            "NOT",
            "BUT",
            "ARE",
            "WAS",
            "HAS",
            "CEO",
            "CFO",
            "COO",
            "IPO",
            "ETF",
            "GDP",
            "CPI",
            "FED",
        }
    )

    def _mentions_ticker(self, title: str, ticker: str) -> bool:
        """Return True if *ticker* appears as a standalone token in *title*."""
        tokens = self._tokenise(title)
        return ticker.upper() in tokens

    def _extract_tickers(self, title: str, primary_ticker: str) -> list[str]:
        """
        Return a list of probable ticker symbols found in *title*.

        Rules
        -----
        - Always include *primary_ticker*.
        - Scan remaining ALL-CAPS tokens of length 1-5 that are not stopwords.
        - Deduplicate while preserving insertion order.
        """
        found: list[str] = [primary_ticker.upper()]
        tokens = self._tokenise(title)

        for token in tokens:
            if (
                token not in found
                and token not in self._TICKER_STOPWORDS
                and token.isupper()
                and 1 <= len(token) <= 5
                and token.isalpha()
            ):
                found.append(token)

        return found

    @staticmethod
    def _tokenise(text: str) -> list[str]:
        """Split text into word tokens, stripping punctuation."""
        import re

        return re.findall(r"[A-Za-z]+", text)

    @staticmethod
    def _scrape_content(url: str) -> Optional[str]:
        """Scrape text content from the article URL."""
        try:
            # Use a generic user agent to bypass basic blocks
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            # Look for paragraph tags to get main reading content
            paragraphs = soup.find_all("p")
            text = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return text if text else None
        except Exception as exc:
            logger.debug("Failed to scrape content from %s: %s", url, exc)
            return None
