from investment_guru.domain.types import DataCategory
from typing import Annotated
from pydantic import Field
from datetime import datetime
from beanie import Document, Indexed


class FilingDocument(Document):
    ticker: str
    company_name: str
    filing_type: str  # "10-K", "10-Q", "8-K"
    accession_number: Annotated[str, Indexed(unique=True)]  # SEC's unique filing ID
    filed_date: str  # "20251031"
    period_of_report: str  # "20250927"
    content: str  # cleaned plain text only — no HTML
    url: str  # link back to EDGAR for citations
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = DataCategory.FILINGS
        use_revision = True

        upsert_fields: list[str] = ["accession_number"]
        upsert_mode: str = "skip"
