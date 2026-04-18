import asyncio
from zenml import step
from investment_guru.application.crawlers.dispatcher import CrawlerDispatcher
from investment_guru.infrastructure.mongo_connector import MongoDBConnector


async def _execute_crawler(source_name: str, tickers: list[str]) -> int:
    """Executes a crawler dynamically inside an async context linked to MongoDB."""
    await MongoDBConnector.connect()

    try:
        dispatcher = (
            CrawlerDispatcher.build().register_stock().register_sec().register_rss()
        )
        crawler = dispatcher.get(source_name)

        total_saved = 0
        for ticker in tickers:
            # External fetching is synchronous (Can be parallelized using semaphore)
            docs = crawler.fetch(ticker)

            if docs:
                # Upsterting array of DB documents is async
                saved = await crawler.save(docs)
                total_saved += saved

        return total_saved
    finally:
        await MongoDBConnector.disconnect()


@step
def crawl_stocks_step(tickers: list[str]) -> int:
    """ZenML step: crawl stock pricing and fundamentals."""
    return asyncio.run(_execute_crawler("Stock", tickers))


@step
def crawl_news_step(tickers: list[str]) -> int:
    """ZenML step: crawl news RSS feeds."""
    return asyncio.run(_execute_crawler("RSS", tickers))


@step
def crawl_sec_filings_step(tickers: list[str]) -> int:
    """ZenML step: crawl SEC filings."""
    return asyncio.run(_execute_crawler("SEC", tickers))
