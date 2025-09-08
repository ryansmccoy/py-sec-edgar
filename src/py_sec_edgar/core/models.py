"""
Core data models for py-sec-edgar

This module provides unified data models used throughout the codebase,
replacing the fragmented model definitions that were previously scattered
across multiple modules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

__all__ = [
    "FilingInfo",
    "CompanyInfo",
    "FilingHeader",
    "SearchResult",
    "FilingType",
    "DocumentInfo",
    "FeedStatus",
    "FeedUpdate",
    "FeedType",
    "FeedConfig",
    "FeedResult",
]


class FeedType(str, Enum):
    """Enumeration of SEC feed types."""

    RSS = "rss"
    DAILY_INDEX = "daily_index"
    MONTHLY_XBRL = "monthly_xbrl"
    FULL_INDEX = "full_index"
    MERGED_INDEX = "merged_index"


class FilingType(str, Enum):
    """Enumeration of common SEC filing types."""

    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_20F = "20-F"
    FORM_DEF14A = "DEF 14A"
    FORM_S1 = "S-1"
    FORM_S3 = "S-3"
    FORM_S4 = "S-4"
    FORM_13F = "13F-HR"
    FORM_4 = "4"
    FORM_3 = "3"
    FORM_5 = "5"


@dataclass
class CompanyInfo:
    """Company identification and basic information."""

    cik: str
    ticker: str = ""
    company_name: str = ""
    sic: str | None = None
    state_of_incorporation: str | None = None
    fiscal_year_end: str | None = None
    business_address: dict[str, str] | None = None
    mailing_address: dict[str, str] | None = None

    def __post_init__(self):
        """Ensure proper data formatting."""
        self.ticker = self.ticker.upper() if self.ticker else ""
        self.cik = str(self.cik).lstrip("0") if self.cik else ""


@dataclass
class FilingInfo:
    """
    Unified SEC filing information model.

    This replaces the three different FilingInfo classes that were previously
    defined in search_engine.py, models.py, and parse/base.py.

    Combines all necessary fields for:
    - Search results (ticker, company_name, cik, form_type, filing_date, document_url, filename)
    - API validation (accession_number, date_filed, url, size)
    - Parsing operations (report_date, file_number, fiscal_year_end, addresses)
    """

    # Core identification fields (required)
    cik: str
    form_type: str
    filing_date: str  # Keep as string for consistency with SEC data
    accession_number: str

    # Company information (usually available)
    company_name: str = ""
    ticker: str = ""

    # Document access fields
    document_url: str = ""  # Direct link to filing document (directory listing)
    submission_url: str = ""  # Complete submission filing URL (.txt file)
    sec_website_url: str = ""  # Human-readable SEC website link
    filename: str = ""
    size: int | None = None

    # Additional filing metadata (optional)
    report_date: str | None = None  # Period of report
    file_number: str | None = None  # SEC file number

    # Company details (parsed from filing headers)
    fiscal_year_end: str | None = None
    state_of_incorporation: str | None = None
    sic: str | None = None
    business_address: dict[str, str] | None = None
    mailing_address: dict[str, str] | None = None

    # Processing metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure proper data types and formatting."""
        self.ticker = self.ticker.upper() if self.ticker else ""
        self.cik = str(self.cik).lstrip("0") if self.cik else ""
        self.form_type = self.form_type.upper() if self.form_type else ""

    @property
    def filing_date_parsed(self) -> datetime | None:
        """Parse filing_date string to datetime object."""
        if not self.filing_date:
            return None
        try:
            return datetime.strptime(self.filing_date, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(self.filing_date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

    @property
    def report_date_parsed(self) -> datetime | None:
        """Parse report_date string to datetime object."""
        if not self.report_date:
            return None
        try:
            return datetime.strptime(self.report_date, "%Y-%m-%d")
        except ValueError:
            return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "cik": self.cik,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "form_type": self.form_type,
            "filing_date": self.filing_date,
            "accession_number": self.accession_number,
            "document_url": self.document_url,
            "submission_url": self.submission_url,
            "sec_website_url": self.sec_website_url,
            "filename": self.filename,
            "size": self.size,
            "report_date": self.report_date,
            "file_number": self.file_number,
            "fiscal_year_end": self.fiscal_year_end,
            "state_of_incorporation": self.state_of_incorporation,
            "sic": self.sic,
            "business_address": self.business_address,
            "mailing_address": self.mailing_address,
            "metadata": self.metadata,
        }

    @classmethod
    def from_search_result(
        cls,
        ticker: str,
        company_name: str,
        cik: str,
        form_type: str,
        filing_date: str,
        document_url: str,
        filename: str,
        accession_number: str = "",
        submission_url: str = "",
        sec_website_url: str = "",
        **kwargs,
    ) -> "FilingInfo":
        """Create FilingInfo from search engine results (legacy compatibility)."""
        return cls(
            ticker=ticker,
            company_name=company_name,
            cik=cik,
            form_type=form_type,
            filing_date=filing_date,
            document_url=document_url,
            submission_url=submission_url,
            sec_website_url=sec_website_url,
            filename=filename,
            accession_number=accession_number
            or cls._extract_accession_from_url(document_url),
            **kwargs,
        )

    @classmethod
    def from_api_data(
        cls,
        accession_number: str,
        cik: str,
        company_name: str,
        form_type: str,
        date_filed: datetime,
        filename: str,
        url: str,
        size: int | None = None,
        **kwargs,
    ) -> "FilingInfo":
        """Create FilingInfo from API data (models.py compatibility)."""
        return cls(
            accession_number=accession_number,
            cik=cik,
            company_name=company_name,
            form_type=form_type,
            filing_date=date_filed.strftime("%Y-%m-%d")
            if isinstance(date_filed, datetime)
            else str(date_filed),
            filename=filename,
            document_url=url,
            size=size,
            **kwargs,
        )

    @classmethod
    def from_parsed_header(
        cls,
        company_name: str | None = None,
        cik: str | None = None,
        form_type: str | None = None,
        filing_date: str | None = None,
        report_date: str | None = None,
        accession_number: str | None = None,
        file_number: str | None = None,
        fiscal_year_end: str | None = None,
        state_of_incorporation: str | None = None,
        business_address: dict[str, str] | None = None,
        mailing_address: dict[str, str] | None = None,
        **kwargs,
    ) -> "FilingInfo":
        """Create FilingInfo from parsed header data (parse/base.py compatibility)."""
        return cls(
            company_name=company_name or "",
            cik=cik or "",
            form_type=form_type or "",
            filing_date=filing_date or "",
            accession_number=accession_number or "",
            report_date=report_date,
            file_number=file_number,
            fiscal_year_end=fiscal_year_end,
            state_of_incorporation=state_of_incorporation,
            business_address=business_address,
            mailing_address=mailing_address,
            **kwargs,
        )

    @staticmethod
    def _extract_accession_from_url(url: str) -> str:
        """Extract accession number from SEC document URL."""
        if not url:
            return ""
        # URL format: https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240930.htm
        try:
            parts = url.split("/")
            if len(parts) >= 2:
                accession_part = parts[-2]  # e.g., "000032019324000123"
                # Format as standard accession number: 0000320193-24-000123
                if len(accession_part) >= 18:
                    return f"{accession_part[:10]}-{accession_part[10:12]}-{accession_part[12:]}"
        except (IndexError, ValueError):
            pass
        return ""


@dataclass
class FeedStatus:
    """Feed status information for monitoring and health checks."""

    feed_type: str
    last_updated: datetime | None = None
    file_count: int = 0
    data_size: int = 0
    status: str = "unknown"  # "available", "missing", "outdated", "unknown"
    error_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        """Check if feed is in a healthy state."""
        return self.status == "available" and self.error_count == 0

    @property
    def age_days(self) -> int | None:
        """Get age of data in days."""
        if not self.last_updated:
            return None
        return (datetime.now() - self.last_updated).days

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "feed_type": self.feed_type,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
            "file_count": self.file_count,
            "data_size": self.data_size,
            "status": self.status,
            "error_count": self.error_count,
            "errors": self.errors,
            "is_healthy": self.is_healthy,
            "age_days": self.age_days,
        }


@dataclass
class FeedUpdate:
    """Result of a feed update operation."""

    feed_type: str
    operation: str
    files_processed: int = 0
    duration: float = 0.0
    success: bool = False
    errors: list[str] = field(default_factory=list)
    data_updated: bool = False
    start_time: datetime | None = None
    end_time: datetime | None = None

    def __post_init__(self):
        """Set timing information if not provided."""
        if self.start_time is None:
            self.start_time = datetime.now()
        if self.end_time is None and self.duration > 0:
            self.end_time = self.start_time + timedelta(seconds=self.duration)

    @property
    def files_per_second(self) -> float:
        """Calculate processing rate."""
        if self.duration > 0 and self.files_processed > 0:
            return self.files_processed / self.duration
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "feed_type": self.feed_type,
            "operation": self.operation,
            "files_processed": self.files_processed,
            "duration": self.duration,
            "success": self.success,
            "errors": self.errors,
            "data_updated": self.data_updated,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "files_per_second": self.files_per_second,
        }


@dataclass
class DocumentInfo:
    """Information about a document within a SEC filing."""

    type: str
    filename: str
    sequence: str | None = None
    size: int = 0
    encoding: str = "utf-8"
    url: str = ""


@dataclass
class SearchResult:
    """Container for search operation results."""

    query: str
    total_results: int
    filings: list[FilingInfo] = field(default_factory=list)
    companies: list[CompanyInfo] = field(default_factory=list)
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "query": self.query,
            "total_results": self.total_results,
            "filings": [f.to_dict() for f in self.filings],
            "companies": [
                {
                    "cik": c.cik,
                    "ticker": c.ticker,
                    "company_name": c.company_name,
                    "sic": c.sic,
                    "state_of_incorporation": c.state_of_incorporation,
                    "fiscal_year_end": c.fiscal_year_end,
                }
                for c in self.companies
            ],
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


@dataclass
class FeedConfig:
    """Configuration for feed operations"""

    feed_type: FeedType
    params: dict[str, Any] = field(default_factory=dict)
    show_progress: bool = True
    save_to_disk: bool = True


@dataclass
class FeedResult:
    """Standardized result from feed operations"""

    feed_type: FeedType
    success: bool
    items_processed: int
    duration: float
    data: list[dict[str, Any]] | None = None
    errors: list[str] | None = None
    metadata: dict[str, Any] | None = None
