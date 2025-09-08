"""
Simple, intuitive Python interface for SEC filing search and download

This module provides a clean, easy-to-use interface that wraps the more complex
FilingSearchEngine functionality for common use cases.

Example Usage:
    ```python
    import py_sec_edgar as sec

    # Simple search
    filings = sec.search("AAPL")
    filings = sec.search("AAPL", form_type="10-Q", limit=5)

    # Multiple companies
    filings = sec.search(["AAPL", "MSFT"], form_type="10-K")

    # Download filings
    content = sec.download(filings[0])
    sec.download_all(filings)

    # Get company info
    company = sec.company("AAPL")
    ```
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .core.downloader import FilingDownloader
from .core.models import FilingInfo
from .core.search_results import SearchResults
from .core.smart_router import SmartFeedRouter
from .search_engine import FilingSearchEngine

logger = logging.getLogger(__name__)


class SecEdgarClient:
    """
    Enhanced client interface for SEC EDGAR operations with rich result handling.

    Provides modern, pythonic interface for SEC filing search, download, and analysis.
    Returns SearchResults objects with advanced filtering, export, and batch operations.
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        rate_limit_delay: float = 0.1,
        enable_local_storage: bool = True,
    ):
        """
        Initialize SEC EDGAR client.

        Args:
            cache_dir: Optional custom cache directory
            rate_limit_delay: Delay between API requests (seconds)
            enable_local_storage: Whether to use local file caching
        """
        self._engine = FilingSearchEngine()
        self._downloader = FilingDownloader()
        self._router = SmartFeedRouter()
        self._config = {
            "cache_dir": cache_dir,
            "rate_limit_delay": rate_limit_delay,
            "enable_local_storage": enable_local_storage,
        }

    def search(
        self,
        ticker: str | list[str],
        form_type: str = "10-K",
        limit: int = 10,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> SearchResults:
        """
        Search SEC filings for one or more companies with enhanced result handling.

        Args:
            ticker: Company ticker symbol(s) (e.g., "AAPL" or ["AAPL", "MSFT"])
            form_type: SEC form type (default: "10-K")
            limit: Maximum number of results to return (default: 10)
            start_date: Earliest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)
            end_date: Latest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)

        Returns:
            SearchResults object with advanced filtering and export capabilities

        Example:
            ```python
            # Get latest 10-K for Apple with advanced result handling
            results = client.search("AAPL", form_type="10-K", limit=1)

            # Filter and export
            recent = results.filter_by_date_range(start_date="2023-01-01")
            recent.to_excel("apple_filings.xlsx")

            # Get quarterly reports for multiple companies
            results = client.search(["AAPL", "MSFT"], form_type="10-Q", limit=5)

            # Search with date range (flexible formats)
            results = client.search("AAPL", start_date="2023-01-01", end_date="2023-12-31")
            results = client.search("AAPL", start_date="2023-03", end_date="2023-04")
            results = client.search("AAPL", start_date="2023", end_date="2024")
            ```
        """
        # Analyze date range and route to optimal feed
        # route = self._router.analyze_date_range(start_date, end_date)  # Commented: unused variable

        # Use smart routing for optimal data source
        try:
            filings, actual_route = self._router.route_search(
                ticker=ticker,
                form_type=form_type,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )

            # Create metadata including routing information
            metadata = {
                "search_timestamp": datetime.now().isoformat(),
                "query_ticker": ticker,
                "query_form_type": form_type,
                "query_limit": limit,
                "query_start_date": start_date,
                "query_end_date": end_date,
                "feed_route": {
                    "feed_type": actual_route.feed_type.value,
                    "reason": actual_route.reason,
                    "estimated_coverage": actual_route.estimated_coverage,
                },
            }

        except Exception as e:
            # Fallback to traditional search engine if smart routing fails
            logger.warning(f"Smart routing failed, using traditional search: {e}")
            filings = self._engine.search_by_ticker(
                ticker=ticker,
                form_types=[form_type] if form_type else None,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            # Create metadata for fallback
            metadata = {
                "search_timestamp": datetime.now().isoformat(),
                "query_ticker": ticker,
                "query_form_type": form_type,
                "query_limit": limit,
                "query_start_date": start_date,
                "query_end_date": end_date,
                "feed_route": {
                    "feed_type": "quarterly",
                    "reason": f"Fallback after smart routing failed: {e}",
                    "estimated_coverage": "Quarterly index data (fallback)",
                },
            }

        return SearchResults(filings, metadata)

    def search_multiple_forms(
        self,
        ticker: str | list[str],
        form_types: list[str],
        limit: int = 20,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> SearchResults:
        """
        Search for multiple form types for given companies.

        Args:
            ticker: Company ticker symbol(s)
            form_types: List of SEC form types (e.g., ["10-K", "10-Q", "8-K"])
            limit: Maximum total results across all form types
            start_date: Earliest filing date
            end_date: Latest filing date

        Returns:
            SearchResults with filings from all requested form types
        """
        all_filings = []

        for form_type in form_types:
            filings = self._engine.search_by_ticker(
                ticker=ticker,
                form_types=[form_type],
                start_date=start_date,
                end_date=end_date,
                limit=limit // len(form_types),  # Distribute limit across form types
            )
            all_filings.extend(filings)

        # Sort by date and apply overall limit
        all_filings.sort(
            key=lambda f: f.filing_date_parsed or datetime.min, reverse=True
        )
        all_filings = all_filings[:limit]

        metadata = {
            "search_timestamp": datetime.now().isoformat(),
            "query_ticker": ticker,
            "query_form_types": form_types,
            "query_limit": limit,
            "query_start_date": start_date,
            "query_end_date": end_date,
        }

        return SearchResults(all_filings, metadata)

    def search_portfolio(
        self,
        tickers: list[str],
        form_types: str | list[str] = "10-K",
        per_ticker_limit: int = 5,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> SearchResults:
        """
        Search filings for a portfolio of companies.

        Args:
            tickers: List of ticker symbols
            form_types: Form type(s) to search for
            per_ticker_limit: Maximum filings per company
            start_date: Earliest filing date
            end_date: Latest filing date

        Returns:
            SearchResults with portfolio-wide filing results
        """
        if isinstance(form_types, str):
            form_types = [form_types]

        all_filings = []
        successful_tickers = []
        failed_tickers = []

        for ticker in tickers:
            try:
                for form_type in form_types:
                    filings = self._engine.search_by_ticker(
                        ticker=ticker,
                        form_types=[form_type],
                        start_date=start_date,
                        end_date=end_date,
                        limit=per_ticker_limit,
                    )
                    all_filings.extend(filings)

                if ticker not in successful_tickers:
                    successful_tickers.append(ticker)

            except Exception as e:
                failed_tickers.append({"ticker": ticker, "error": str(e)})

        metadata = {
            "search_timestamp": datetime.now().isoformat(),
            "query_tickers": tickers,
            "query_form_types": form_types,
            "per_ticker_limit": per_ticker_limit,
            "query_start_date": start_date,
            "query_end_date": end_date,
            "successful_tickers": successful_tickers,
            "failed_tickers": failed_tickers,
            "success_rate": len(successful_tickers) / len(tickers) if tickers else 0,
        }

        return SearchResults(all_filings, metadata)

    async def _search_async(
        self,
        ticker: str | list[str],
        form_type: str,
        limit: int,
        per_ticker_limit: int | None,
    ) -> list[FilingInfo]:
        """Async implementation of search"""
        return await self._engine.search_by_ticker(
            ticker=ticker,
            form_type=form_type,
            limit=limit,
            per_ticker_limit=per_ticker_limit,
        )

    def download(self, filing: FilingInfo) -> str:
        """
        Download filing content

        Args:
            filing: FilingInfo object from search results

        Returns:
            Filing content as string

        Example:
            ```python
            filings = client.search("AAPL")
            content = client.download(filings[0])
            print(f"Downloaded {len(content):,} characters")
            ```
        """
        return asyncio.run(self._download_async(filing))

    async def _download_async(self, filing: FilingInfo) -> str:
        """Async implementation of download"""
        return await self._downloader.download_filing(filing, save_to_disk=True)

    def download_all(
        self, filings: list[FilingInfo], save_to_disk: bool = True
    ) -> list[str]:
        """
        Download multiple filings

        Args:
            filings: List of FilingInfo objects
            save_to_disk: Whether to save files locally (default: True)

        Returns:
            List of filing contents as strings

        Example:
            ```python
            filings = client.search(["AAPL", "MSFT"], limit=5)
            contents = client.download_all(filings)
            print(f"Downloaded {len(contents)} filings")
            ```
        """
        return asyncio.run(self._download_all_async(filings, save_to_disk))

    async def _download_all_async(
        self, filings: list[FilingInfo], save_to_disk: bool
    ) -> list[str]:
        """Async implementation of download_all"""
        return await self._downloader.download_filings(
            filings, save_to_disk=save_to_disk
        )

    def company(self, ticker: str) -> dict:
        """
        Get company information

        Args:
            ticker: Company ticker symbol

        Returns:
            Dictionary with company details

        Example:
            ```python
            company = client.company("AAPL")
            print(f"{company['name']} (CIK: {company['cik']})")
            ```
        """
        cik, company_name = self._engine.get_cik_for_ticker(ticker)
        return {"ticker": ticker.upper(), "name": company_name, "cik": cik}

    async def _company_async(self, ticker: str) -> dict:
        """Async implementation of company info"""
        cik, company_name = await self._engine.get_cik_for_ticker(ticker)
        return {"ticker": ticker.upper(), "name": company_name, "cik": cik}

    def filings_summary(self, ticker: str) -> dict:
        """
        Get summary of available filing types for a company

        Args:
            ticker: Company ticker symbol

        Returns:
            Dictionary mapping form types to counts

        Example:
            ```python
            summary = client.filings_summary("AAPL")
            for form_type, count in summary.items():
                print(f"{form_type}: {count} filings")
            ```
        """
        return self._engine.get_filing_types_for_ticker(ticker)

    async def _filings_summary_async(self, ticker: str) -> dict:
        """Async implementation of filings summary"""
        return await self._engine.get_filing_types_for_ticker(ticker)


# Global client instance for simple module-level functions
_client = None


def _get_client() -> SecEdgarClient:
    """Get or create global client instance"""
    global _client
    if _client is None:
        _client = SecEdgarClient()
    return _client


# Module-level convenience functions
def search(
    ticker: str | list[str],
    form_type: str = "10-K",
    limit: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
) -> SearchResults:
    """
    Search SEC filings for one or more companies

    Args:
        ticker: Company ticker symbol(s) (e.g., "AAPL" or ["AAPL", "MSFT"])
        form_type: SEC form type (default: "10-K")
        limit: Maximum number of results to return (default: 10)
        start_date: Earliest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)
        end_date: Latest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)

    Returns:
        SearchResults object with advanced filtering and export capabilities

    Example:
        ```python
        import py_sec_edgar as sec

        # Get latest 10-K for Apple with enhanced results
        results = sec.search("AAPL", form_type="10-K", limit=1)

        # Use advanced filtering and export
        results.to_excel("apple_filings.xlsx")
        summary = results.get_summary()

        # Get quarterly reports for multiple companies
        results = sec.search(["AAPL", "MSFT"], form_type="10-Q", limit=5)

        # Search with date range (flexible formats)
        results = sec.search("AAPL", start_date="2023-01-01", end_date="2023-12-31")
        results = sec.search("AAPL", start_date="2023-03", end_date="2023-04")
        results = sec.search("AAPL", start_date="2023", end_date="2024")
        ```
    """
    return _get_client().search(ticker, form_type, limit, start_date, end_date)


def download(filing: FilingInfo) -> str:
    """
    Download filing content

    Args:
        filing: FilingInfo object from search results

    Returns:
        Filing content as string

    Example:
        ```python
        import py_sec_edgar as sec

        filings = sec.search("AAPL")
        content = sec.download(filings[0])
        print(f"Downloaded {len(content):,} characters")
        ```
    """
    return _get_client().download(filing)


def download_all(filings: list[FilingInfo], save_to_disk: bool = True) -> list[str]:
    """
    Download multiple filings

    Args:
        filings: List of FilingInfo objects
        save_to_disk: Whether to save files locally (default: True)

    Returns:
        List of filing contents as strings

    Example:
        ```python
        import py_sec_edgar as sec

        filings = sec.search(["AAPL", "MSFT"], limit=5)
        contents = sec.download_all(filings)
        print(f"Downloaded {len(contents)} filings")
        ```
    """
    return _get_client().download_all(filings, save_to_disk)


def company(ticker: str) -> dict:
    """
    Get company information

    Args:
        ticker: Company ticker symbol

    Returns:
        Dictionary with company details

    Example:
        ```python
        import py_sec_edgar as sec

        company = sec.company("AAPL")
        print(f"{company['name']} (CIK: {company['cik']})")
        ```
    """
    return _get_client().company(ticker)


def filings_summary(ticker: str) -> dict:
    """
    Get summary of available filing types for a company

    Args:
        ticker: Company ticker symbol

    Returns:
        Dictionary mapping form types to counts

    Example:
        ```python
        import py_sec_edgar as sec

        summary = sec.filings_summary("AAPL")
        for form_type, count in summary.items():
            print(f"{form_type}: {count} filings")
        ```
    """
    return _get_client().filings_summary(ticker)


def search_portfolio(
    tickers: list[str],
    form_types: str | list[str] = "10-K",
    per_ticker_limit: int = 5,
    start_date: str | None = None,
    end_date: str | None = None,
) -> SearchResults:
    """
    Search filings for a portfolio of companies.

    Args:
        tickers: List of ticker symbols
        form_types: Form type(s) to search for
        per_ticker_limit: Maximum filings per company
        start_date: Earliest filing date
        end_date: Latest filing date

    Returns:
        SearchResults with portfolio-wide filing results

    Example:
        ```python
        import py_sec_edgar as sec

        # Search recent 8-K filings for tech giants
        results = sec.search_portfolio(
            ["AAPL", "MSFT", "GOOGL", "AMZN"],
            form_types="8-K",
            per_ticker_limit=3,
            start_date="2024-01-01"
        )

        # Export to Excel with summary
        results.to_excel("tech_portfolio_8k.xlsx")
        print(results.get_summary())
        ```
    """
    return _get_client().search_portfolio(
        tickers, form_types, per_ticker_limit, start_date, end_date
    )


def search_multiple_forms(
    ticker: str | list[str],
    form_types: list[str],
    limit: int = 20,
    start_date: str | None = None,
    end_date: str | None = None,
) -> SearchResults:
    """
    Search for multiple form types for given companies.

    Args:
        ticker: Company ticker symbol(s)
        form_types: List of SEC form types (e.g., ["10-K", "10-Q", "8-K"])
        limit: Maximum total results across all form types
        start_date: Earliest filing date
        end_date: Latest filing date

    Returns:
        SearchResults with filings from all requested form types

    Example:
        ```python
        import py_sec_edgar as sec

        # Get various filing types for Apple
        results = sec.search_multiple_forms(
            "AAPL",
            ["10-K", "10-Q", "8-K"],
            limit=15,
            start_date="2023"
        )

        # Filter by form type
        annual_reports = results.filter_by_form_type("10-K")
        quarterly_reports = results.filter_by_form_type("10-Q")
        ```
    """
    return _get_client().search_multiple_forms(
        ticker, form_types, limit, start_date, end_date
    )
