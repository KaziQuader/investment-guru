from typing import Optional
from pydantic import Field
from datetime import datetime
from beanie import Document
from investment_guru.domain.types import DataCategory


class NewsDocument(Document):
    title: str
    url: str
    published_at: str  # TODO: parse to datetime for recency filtering in RAG pipeline
    source_name: str
    content: Optional[str] = None
    tickers_mentioned: list[str] = Field(default_factory=list)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = DataCategory.NEWS
