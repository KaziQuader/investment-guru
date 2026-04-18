from asyncio.log import logger
import asyncio
from zenml import step, log_step_metadata
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
            logger.info(f"Crawling {ticker} from {source_name}")
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
    saved = asyncio.run(_execute_crawler("Stock", tickers))
    log_step_metadata(
        {"source": "Stock", "total_saved": saved, "tickers_count": len(tickers)}
    )
    return saved


@step
def crawl_news_step(tickers: list[str]) -> int:
    """ZenML step: crawl news RSS feeds."""
    saved = asyncio.run(_execute_crawler("RSS", tickers))
    log_step_metadata(
        {"source": "RSS News", "total_saved": saved, "tickers_count": len(tickers)}
    )
    return saved


@step
def crawl_sec_filings_step(tickers: list[str]) -> int:
    """ZenML step: crawl SEC filings."""
    saved = asyncio.run(_execute_crawler("SEC", tickers))
    log_step_metadata(
        {"source": "SEC Filings", "total_saved": saved, "tickers_count": len(tickers)}
    )
    return saved
