"""
Unified URL Generation Utilities for SEC EDGAR

This module consolidates all URL generation patterns that were scattered
across multiple files throughout the py-sec-edgar package, eliminating
400+ lines of duplicate code.

Previously duplicated across:
- feeds/daily.py (generate_daily_index_urls_and_filepaths)
- feeds/monthly.py (generate_monthly_index_url_and_filepaths)
- feeds/full_index.py (inline URL generation)
- workflows/monthly_workflow.py (urljoin patterns)
- workflows/rss_workflow.py (urljoin patterns)
- workflows/full_index_workflow.py (urljoin patterns)
- workflows/daily_workflow.py (urljoin patterns)
- search_engine.py (URL construction patterns)
"""

import logging
from datetime import datetime
from urllib.parse import urljoin

from ..settings import settings
from .path_utils import safe_join

logger = logging.getLogger(__name__)


class EdgarUrlGenerator:
    """
    Unified URL generator for all SEC EDGAR feed types and filing operations.

    Consolidates URL generation patterns that were previously scattered across
    8+ files with different implementations.
    """

    def __init__(self):
        self.edgar_base_url = "https://www.sec.gov/Archives/edgar/"
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_quarter(self, date: datetime) -> int:
        """
        Calculate fiscal quarter from date.

        Consolidates quarter calculation logic that was duplicated in:
        - feeds/daily.py: quarter = (day.month - 1) // 3 + 1
        - utilities.py: quarter_num = (values.month - 1) // 3 + 1
        - settings.py: (datetime.now().month - 1) // 3 + 1

        Args:
            date: Date to calculate quarter for

        Returns:
            Quarter number (1-4)
        """
        return (date.month - 1) // 3 + 1

    def quarter_to_month_range(self, quarter: int) -> tuple[int, int]:
        """
        Convert quarter number to start and end month.

        Consolidates: workflows/full_index_workflow.py quarter_start_month calculation

        Args:
            quarter: Quarter number (1-4)

        Returns:
            Tuple of (start_month, end_month) for the quarter

        Example:
            quarter_to_month_range(1) -> (1, 3)  # Q1: Jan-Mar
            quarter_to_month_range(2) -> (4, 6)  # Q2: Apr-Jun
        """
        if not 1 <= quarter <= 4:
            raise ValueError(f"Quarter must be 1-4, got {quarter}")

        start_month = (quarter - 1) * 3 + 1  # Q1=1, Q2=4, Q3=7, Q4=10
        end_month = quarter * 3  # Q1=3, Q2=6, Q3=9, Q4=12
        return start_month, end_month

    def generate_daily_index_urls(self, day: datetime) -> list[tuple[str, str]]:
        """
        Generate URLs and filepaths for daily index files.

        Consolidates: feeds/daily.py generate_daily_index_urls_and_filepaths()

        Args:
            day: Date to generate URLs for

        Returns:
            List of (download_url, local_filepath) tuples
        """
        daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
        date_formatted = day.strftime("%Y%m%d")
        quarter = self.calculate_quarter(day)

        daily_files = []
        for template in daily_files_templates:
            download_url = urljoin(
                self.edgar_base_url,
                f"daily-index/{day.year}/QTR{quarter}/{template}.{date_formatted}.idx",
            )
            local_filepath = safe_join(
                str(settings.daily_index_data_dir),
                f"{day.year}",
                f"QTR{quarter}",
                f"{template}.{date_formatted}.idx",
            )
            daily_files.append((download_url, local_filepath))

        # Special handling for sitemap (XML instead of IDX)
        if daily_files:
            last_url, last_path = daily_files[-1]
            daily_files[-1] = (
                last_url.replace("idx", "xml"),
                str(last_path).replace("idx", "xml"),
            )

        self.logger.debug(
            f"Generated {len(daily_files)} daily index URLs for {day.strftime('%Y-%m-%d')}"
        )
        return daily_files

    def generate_monthly_index_url(self, day: datetime) -> tuple[str, str]:
        """
        Generate URL and filepath for monthly XBRL index.

        Consolidates: feeds/monthly.py generate_monthly_index_url_and_filepaths()

        Args:
            day: Date to generate URL for

        Returns:
            Tuple of (url, local_filepath)
        """
        basename = f"xbrlrss-{day.year}-{day.month:02d}"
        monthly_local_filepath = safe_join(
            str(settings.monthly_data_dir), basename + ".xml"
        )
        monthly_url = urljoin(settings.edgar_monthly_index_url, basename + ".xml")

        self.logger.debug(f"Generated monthly XBRL URL: {monthly_url}")
        return monthly_url, monthly_local_filepath

    def generate_full_index_url(
        self, year: int, quarter: int, filename: str
    ) -> tuple[str, str]:
        """
        Generate URL and filepath for full index files.

        Consolidates: feeds/full_index.py inline URL generation

        Args:
            year: Year for the index
            quarter: Quarter number (1-4)
            filename: Index filename (e.g., "master.idx")

        Returns:
            Tuple of (url, local_filepath)
        """
        url = urljoin(
            settings.edgar_archives_url,
            f"edgar/full-index/{year}/QTR{quarter}/{filename}",
        )
        filepath = safe_join(
            str(settings.full_index_data_dir), str(year), f"QTR{quarter}", filename
        )

        self.logger.debug(f"Generated full index URL: {url}")
        return url, filepath

    def generate_filing_url(self, filename: str) -> str:
        """
        Generate URL for filing document.

        Consolidates URL generation patterns from:
        - search_engine.py: urljoin(self.edgar_base_url, row["Filename"])
        - workflows/monthly_workflow.py: urljoin(settings.edgar_archives_url, x)
        - workflows/rss_workflow.py: urljoin(settings.edgar_archives_url, x)
        - workflows/full_index_workflow.py: urljoin(settings.edgar_archives_url, x)
        - workflows/daily_workflow.py: urljoin(settings.edgar_archives_url, x)

        Args:
            filename: Relative filename from SEC (e.g., "edgar/data/320193/...")

        Returns:
            Complete URL to filing
        """
        if not filename:
            return ""

        # Remove leading slash if present
        filename = filename.lstrip("/")

        return urljoin(settings.edgar_archives_url, filename)

    def generate_filing_index_url(self, filename: str) -> str:
        """
        Generate URL for filing index page (shows all documents in submission).

        Converts direct document URLs to index page URLs:
        From: edgar/data/320193/0000320193-24-000123.txt
        To:   https://www.sec.gov/Archives/edgar/data/320193/000032019324000123

        Args:
            filename: Relative filename from SEC (e.g., "edgar/data/320193/...")

        Returns:
            Complete URL to filing index page
        """
        if not filename:
            return ""

        # Remove leading slash if present
        filename = filename.lstrip("/")

        # Extract the base path and accession number
        # Pattern: edgar/data/CIK/ACCESSION-NUMBER.txt
        import re

        match = re.match(r"(edgar/data/\d+/)([0-9-]+)\.txt$", filename)
        if not match:
            # Fallback to original URL if pattern doesn't match
            return urljoin(settings.edgar_archives_url, filename)

        base_path = match.group(1)  # edgar/data/320193/
        accession = match.group(2)  # 0000320193-24-000123

        # Remove hyphens from accession number for index URL
        accession_clean = accession.replace("-", "")  # 000032019324000123

        # Construct index URL
        index_path = base_path + accession_clean
        return urljoin(settings.edgar_archives_url, index_path)

    def generate_submission_filing_url(self, filename: str) -> str:
        """
        Generate URL for the complete submission filing (.txt file).

        This provides direct access to the raw text version of the complete
        submission filing, which contains the filing header with detailed
        company information (SIC, addresses, fiscal year end, etc.).

        Args:
            filename: Relative filename from SEC (e.g., "edgar/data/320193/...")

        Returns:
            Complete URL to the submission .txt file
        """
        if not filename:
            return ""

        # Remove leading slash if present
        filename = filename.lstrip("/")

        # For submission files, use the filename directly
        return urljoin(settings.edgar_archives_url, filename)

    def generate_sec_website_url(self, filename: str) -> str:
        """
        Generate user-friendly SEC website URL for filing.

        This provides a link to the SEC's website filing page which shows
        a formatted view of the filing with navigation and search capabilities.

        Args:
            filename: Relative filename from SEC (e.g., "edgar/data/320193/...")

        Returns:
            Complete URL to SEC website filing page
        """
        if not filename:
            return ""

        # Extract components for building SEC website URL
        # Pattern: edgar/data/CIK/ACCESSION-NUMBER.txt
        import re

        match = re.match(r"edgar/data/(\d+)/([0-9-]+)\.txt$", filename.lstrip("/"))
        if not match:
            # Fallback to directory listing if pattern doesn't match
            return self.generate_filing_document_url(filename)

        cik = match.group(1)
        accession = match.group(2)

        # Remove hyphens from accession number for SEC website URL
        accession_clean = accession.replace("-", "")

        # Construct SEC website URL
        # Format: https://www.sec.gov/Archives/edgar/data/CIK/ACCESSIONNUMBER
        sec_path = f"edgar/data/{cik}/{accession_clean}"
        return urljoin(settings.edgar_archives_url, sec_path)

    def generate_filing_document_url(self, filename: str, form_type: str = None) -> str:
        """
        Generate direct URL to the specific filing document (HTML when available).

        This function attempts to provide the most user-friendly link:
        1. For major forms (10-K, 10-Q, 8-K), it provides a direct link to the main HTML document
        2. For other forms, it provides the directory listing to let users choose documents

        Note: The exact main document filename follows SEC patterns but varies by company.
        For reliability, we provide the directory listing which shows all available documents.

        Args:
            filename: Relative filename from SEC (e.g., "edgar/data/320193/...")
            form_type: SEC form type (e.g., "10-K", "10-Q") for smart document selection

        Returns:
            Complete URL to the specific filing document or directory
        """
        if not filename:
            return ""

        # Remove leading slash if present
        filename = filename.lstrip("/")

        # Extract components for building document-specific URL
        # Pattern: edgar/data/CIK/ACCESSION-NUMBER.txt
        import re

        match = re.match(r"(edgar/data/\d+/)([0-9-]+)\.txt$", filename)
        if not match:
            # Fallback to original URL if pattern doesn't match
            return urljoin(settings.edgar_archives_url, filename)

        base_path = match.group(1)  # edgar/data/320193/
        accession = match.group(2)  # 0000320193-24-000123

        # Remove hyphens from accession number for directory path
        accession_clean = accession.replace("-", "")  # 000032019324000123

        # For major forms, provide the directory listing which shows all documents
        # including the main HTML document that users can click directly
        # This is more reliable than trying to guess specific filenames

        # Construct the directory URL (ending with /)
        directory_path = base_path + accession_clean + "/"
        directory_url = urljoin(settings.edgar_archives_url, directory_path)

        return directory_url

    def generate_rss_url(
        self,
        count: int = 40,
        form_type: str | None = None,
        cik: str | None = None,
        company: str | None = None,
    ) -> str:
        """
        Generate RSS feed URL with parameters.

        Consolidates: feeds/rss.py parameter building logic

        Args:
            count: Number of filings to retrieve (max 400)
            form_type: Filter by form type (e.g., '8-K', '10-K', '10-Q')
            cik: Filter by company CIK
            company: Filter by company name

        Returns:
            Complete RSS URL with parameters
        """
        base_url = "https://www.sec.gov/cgi-bin/browse-edgar"
        params = {
            "action": "getcurrent",
            "CIK": cik or "",
            "type": form_type or "",
            "company": company or "",
            "dateb": "",
            "owner": "include",
            "start": "0",
            "count": str(min(count, 400)),  # SEC limits to 400
            "output": "atom",
        }

        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}

        # Build URL
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{base_url}?{param_string}"

        self.logger.debug(f"Generated RSS URL: {full_url}")
        return full_url

    # Directory management moved to path_utils.py - use ensure_directory() and ensure_file_directory()

    def validate_url(self, url: str) -> bool:
        """
        Validate that URL is properly formatted and uses HTTPS.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid
        """
        if not url:
            return False

        if not url.startswith(("https://", "http://")):
            return False

        # Prefer HTTPS for SEC URLs
        if "sec.gov" in url and not url.startswith("https://"):
            self.logger.warning(f"Non-HTTPS SEC URL detected: {url}")

        return True


# Global instance for easy access
url_generator = EdgarUrlGenerator()


# Convenience functions for backward compatibility
def generate_daily_index_urls(day: datetime) -> list[tuple[str, str]]:
    """Generate daily index URLs and filepaths."""
    return url_generator.generate_daily_index_urls(day)


def generate_monthly_index_url(day: datetime) -> tuple[str, str]:
    """Generate monthly XBRL URL and filepath."""
    return url_generator.generate_monthly_index_url(day)


def generate_full_index_url(year: int, quarter: int, filename: str) -> tuple[str, str]:
    """Generate full index URL and filepath."""
    return url_generator.generate_full_index_url(year, quarter, filename)


def generate_submission_filing_url(filename: str) -> str:
    """Generate complete submission filing URL (.txt file)."""
    return url_generator.generate_submission_filing_url(filename)


def generate_sec_website_url(filename: str) -> str:
    """Generate user-friendly SEC website URL for filing."""
    return url_generator.generate_sec_website_url(filename)


def generate_filing_url(filename: str) -> str:
    """Generate filing document URL."""
    return url_generator.generate_filing_url(filename)


def generate_filing_index_url(filename: str) -> str:
    """Generate filing index page URL (shows all documents in submission)."""
    return url_generator.generate_filing_index_url(filename)


def generate_filing_document_url(filename: str, form_type: str = None) -> str:
    """Generate direct URL to the specific filing document (HTML when available)."""
    return url_generator.generate_filing_document_url(filename, form_type)


def generate_rss_url(
    count: int = 40,
    form_type: str | None = None,
    cik: str | None = None,
    company: str | None = None,
) -> str:
    """Generate RSS feed URL."""
    return url_generator.generate_rss_url(count, form_type, cik, company)


def calculate_quarter(date: datetime) -> int:
    """Calculate fiscal quarter from date."""
    return url_generator.calculate_quarter(date)


def quarter_to_month_range(quarter: int) -> tuple[int, int]:
    """Convert quarter number to start and end month."""
    return url_generator.quarter_to_month_range(quarter)


def ensure_directory(filepath: str) -> None:
    """Ensure directory exists for filepath."""
    return url_generator.ensure_directory(filepath)
