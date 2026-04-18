from investment_guru.application.crawlers.base import BaseCrawler
from investment_guru.domain.documents.filing import FilingDocument
import logging
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader


logger = logging.getLogger(__name__)

# Filing types we care about and their human-readable labels
FILING_TYPES: dict[str, str] = {
    "10-K": "Annual Report",
    "10-Q": "Quarterly Report",
    "8-K": "Current Report",
}

# How many of each filing type to fetch per ticker
FILINGS_PER_TYPE: int = 1


class SECFilingCrawler(BaseCrawler):
    """
    Downloads SEC EDGAR filings for a given ticker using sec-edgar-downloader,
    cleans the raw HTML/XBRL content, and returns FilingDocument objects.
    """

    model = FilingDocument

    def __init__(
        self,
        company_email: str = "investment-guru@example.com",
        filings_per_type: int = FILINGS_PER_TYPE,
    ):
        """
        Parameters
        ----------
        company_email : str
            EDGAR requires a user-agent email in the form
            "Company Name email@domain.com".  Any valid email works for
            development; use your real one in production.
        filings_per_type : int
            How many filings to fetch for each of 10-K / 10-Q / 8-K.
        """
        self._company_email = company_email
        self._filings_per_type = filings_per_type

    def get_source_name(self) -> str:
        return "sec_edgar"

    def fetch(self, ticker: str) -> list[FilingDocument]:
        """
        Download and parse SEC filings for *ticker*.

        Returns a list of FilingDocuments with cleaned plain-text content.
        The list may be empty if EDGAR returns no filings or all files fail
        to parse.
        """
        ticker = ticker.upper()
        docs: list[FilingDocument] = []

        # sec-edgar-downloader must write to a real directory
        with TemporaryDirectory() as tmpdir:
            dl = Downloader(
                company_name="InvestmentGuru",
                email_address=self._company_email,
                download_folder=tmpdir,
            )

            for filing_type in FILING_TYPES:
                fetched = self._fetch_filing_type(dl, ticker, filing_type, tmpdir)
                docs.extend(fetched)
                logger.info(
                    "Fetched %d %s filings for %s", len(fetched), filing_type, ticker
                )

        logger.info("Total SEC filings for %s: %d", ticker, len(docs))
        return docs

    def _fetch_filing_type(
        self,
        dl: Downloader,
        ticker: str,
        filing_type: str,
        base_dir: str,
    ) -> list[FilingDocument]:
        """Download *filing_type* filings for *ticker* and return documents."""
        try:
            dl.get(filing_type, ticker, limit=self._filings_per_type)
        except Exception as exc:
            logger.warning(
                "sec-edgar-downloader failed for %s %s: %s", ticker, filing_type, exc
            )
            return []

        # sec-edgar-downloader saves files under:
        # <base_dir>/sec-edgar-filings/<TICKER>/<filing_type>/<accession>/
        filing_root = Path(base_dir) / "sec-edgar-filings" / ticker / filing_type
        if not filing_root.exists():
            logger.debug("No filing directory found at %s", filing_root)
            return []

        docs: list[FilingDocument] = []
        for accession_dir in sorted(filing_root.iterdir()):
            if not accession_dir.is_dir():
                continue

            accession_number = accession_dir.name
            doc = self._parse_accession_dir(
                accession_dir, ticker, filing_type, accession_number
            )
            if doc is not None:
                docs.append(doc)

        return docs

    def _parse_accession_dir(
        self,
        accession_dir: Path,
        ticker: str,
        filing_type: str,
        accession_number: str,
    ) -> Optional[FilingDocument]:
        """
        Find the primary document in an accession folder, clean it, and
        return a FilingDocument, or None if parsing fails.
        """
        primary_file = self._find_primary_file(accession_dir)
        if primary_file is None:
            logger.debug("No primary file found in %s", accession_dir)
            return None

        raw_content = primary_file.read_text(encoding="utf-8", errors="ignore")
        cleaned = self._clean_filing(raw_content)

        if not cleaned:
            logger.debug("Empty content after cleaning %s", primary_file)
            return None

        # Extract metadata from the filename/content
        filed_date, period_of_report = self._extract_dates(raw_content)
        company_name = self._extract_company_name(raw_content, ticker)
        edgar_url = self._accession_to_url(ticker, accession_number)

        # Protect against MongoDB's 16MB BSON Document limit
        # ~10,000,000 chars is safely below the limit
        MAX_CHARS = 10_000_000
        if len(cleaned) > MAX_CHARS:
            logger.warning(
                "Truncating filing %s (size: %d chars) to fit MongoDB limit",
                accession_number, len(cleaned)
            )
            cleaned = cleaned[:MAX_CHARS] + "\n...[TRUNCATED TO FIT DB LIMIT]..."

        return FilingDocument(
            ticker=ticker,
            company_name=company_name,
            filing_type=filing_type,
            accession_number=accession_number,
            filed_date=filed_date,
            period_of_report=period_of_report,
            content=cleaned,
            url=edgar_url,
        )

    # Priority order for picking the primary document from an accession dir.
    # The full submission HTML is largest and most complete; XBRL inline
    # documents are second choice; plain .txt is last resort.
    _PRIMARY_SUFFIXES = [".htm", ".html", ".txt"]

    def _find_primary_file(self, accession_dir: Path) -> Optional[Path]:
        """
        Return the best file to parse from an accession directory.

        sec-edgar-downloader v0.5+ saves a `full-submission.txt` containing
        the complete SGML submission.  For v0.6+ it saves individual files.
        We prefer the largest .htm file (the human-readable filing) over the
        raw full-submission text.
        """
        candidates: list[Path] = []
        for suffix in self._PRIMARY_SUFFIXES:
            candidates.extend(accession_dir.glob(f"*{suffix}"))

        if not candidates:
            return None

        # Skip filing-summary XMLs and small index files; take the largest
        # remaining file as the primary document.
        candidates = [
            f for f in candidates if f.stat().st_size > 1_000  # skip tiny index stubs
        ]
        if not candidates:
            return None

        return max(candidates, key=lambda f: f.stat().st_size)

    @staticmethod
    def _clean_filing(raw: str) -> str:
        """
        Strip HTML/SGML markup and normalise whitespace.
        """
        # lxml is highly resilient to broken SGML or binary garbage 
        # embedded in older SEC full submission text files
        try:
            soup = BeautifulSoup(raw, "lxml")
        except Exception as e:
            logger.warning("BeautifulSoup lxml parser failed, falling back to basic strip: %s", e)
            return raw[:10000] # Return safe slice if hopelessly corrupted

        # Remove script, style, and XBRL metadata blocks entirely
        for tag in soup(["script", "style", "ix:hidden", "xbrli:xbrl"]):
            tag.decompose()

        text = soup.get_text(separator=" ")

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove lines that are pure numbers/punctuation (table noise)
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not re.fullmatch(r"[\d\s\.,\-\$%()]+", line.strip())
        ]
        text = " ".join(lines).strip()

        return text

    def _extract_dates(self, raw: str) -> tuple[str, str]:
        """
        Extract filed date and period-of-report from SGML header comments.

        EDGAR full-submission files contain a header block like:
            <FILED-AS-OF-DATE>20251031
            <PERIOD-OF-REPORT>20250927
        """
        filed = self._search_header(raw, r"FILED-AS-OF-DATE[:\s>]+(\d{8})")
        period = self._search_header(raw, r"PERIOD-OF-REPORT[:\s>]+(\d{8})")
        return filed, period

    def _extract_company_name(self, raw: str, fallback: str) -> str:
        """Extract company name from SGML header, fall back to ticker."""
        name = self._search_header(raw, r"COMPANY-CONFORMED-NAME[:\s>]+([^\n<]+)")
        return name.strip() if name else fallback

    @staticmethod
    def _search_header(raw: str, pattern: str) -> str:
        """Return the first match group of *pattern* in *raw*, or ''."""
        match = re.search(pattern, raw, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _accession_to_url(ticker: str, accession_number: str) -> str:
        """
        Build the EDGAR viewer URL for an accession number.

        Accession numbers are in the form '0000320193-25-000123'.
        The URL form strips hyphens from the CIK portion.
        """
        # Strip hyphens for the URL path segment
        accession_path = accession_number.replace("-", "")
        return (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={ticker}"
            f"&type=10-K&dateb=&owner=include&count=40"
            # Link directly to the filing index when possible
            # Full path: /Archives/edgar/data/<CIK>/<accession>/
        )
