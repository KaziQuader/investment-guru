from investement_guru.domain.types import DataCategory
from pydantic import Field
from datetime import datetime
from beanie import Document


class FilingDocument(Document):
    ticker: str
    company_name: str
    filing_type: str  # "10-K", "10-Q", "8-K"
    accession_number: str  # unique filing ID — use as dedup key
    filed_date: str  # "20251031"
    period_of_report: str  # "20250927"
    content: str  # cleaned plain text only — no HTML
    url: str  # link back to EDGAR for citations
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = DataCategory.FILINGS
