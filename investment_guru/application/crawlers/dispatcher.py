from investment_guru.application.crawlers.base import BaseCrawler
from investment_guru.application.crawlers.news_crawler import RSSNewsCrawler
from investment_guru.application.crawlers.sec_filing_crawler import SECFilingCrawler
from investment_guru.application.crawlers.stock_crawler import StockCrawler


class CrawlerDispatcher:
    def __init__(self):
        self._crawlers = {}

    @classmethod
    def build(cls) -> "CrawlerDispatcher":
        dispatcher = cls()
        return dispatcher

    def register_stock(self) -> "CrawlerDispatcher":
        self.register("Stock", StockCrawler)
        return self

    def register_sec(self) -> "CrawlerDispatcher":
        self.register("SEC", SECFilingCrawler)
        return self

    def register_rss(self) -> "CrawlerDispatcher":
        self.register("RSS", RSSNewsCrawler)
        return self

    def register(self, source_name: str, crawler: type[BaseCrawler]) -> None:
        self._crawlers[source_name] = crawler

    def get(self, source_name: str) -> BaseCrawler:
        crawler_cls = self._crawlers.get(source_name)
        if crawler_cls is None:
            raise ValueError(f"Crawler {source_name} not registered")
        return crawler_cls()
