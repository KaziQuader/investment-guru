from investment_guru.domain.types import DataCategory
from datetime import datetime
from typing import Optional, Annotated
from beanie import Document, Indexed
from pydantic import Field


class StockDocument(Document):
    ticker: Annotated[str, Indexed(unique=True)]
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    business_summary: Optional[str] = None

    # pricing
    current_price: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None

    # valuation
    market_cap: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None

    # growth and quality
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    profit_margins: Optional[float] = None
    return_on_equity: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cashflow: Optional[float] = None
    total_revenue: Optional[float] = None

    # risk and dividends
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None

    # analyst consensus
    recommendation: Optional[str] = None
    target_mean_price: Optional[float] = None
    analyst_count: Optional[int] = None

    # price history
    price_history: list = Field(default_factory=list)

    # metadata
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = "yfinance"

    class Settings:
        name = DataCategory.STOCKS
        use_revision = True

    # Used by BaseCrawler.save() to determine upsert behaviour:
    #   'replace' → update the existing document in-place (daily refresh)
    #   'skip'    → do not overwrite if a match already exists
    upsert_fields: list[str] = ["ticker"]
    upsert_mode: str = "replace"
