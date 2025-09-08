"""
SEC Filing Search Engine

Core search functionality for py-sec-edgar with modern async patterns and
comprehensive error handling. Built on proven ticker → CIK → filings workflow.
"""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from py_sec_edgar.settings import settings

from .core.downloader import FilingDownloader
from .core.models import FilingInfo
from .core.url_utils import (
    generate_filing_document_url,
    generate_sec_website_url,
    generate_submission_filing_url,
)


class FilingSearchError(Exception):
    """Custom exception for filing search operations"""

    pass


class FilingSearchEngine:
    """Professional SEC Filing Search Engine for Real-Time and Historical Data.

    Provides a comprehensive, modern interface for SEC filing discovery and retrieval
    using the proven ticker → CIK → filings workflow. Combines real-time SEC EDGAR
    APIs with historical quarterly index data for complete filing coverage.

    Features:
        🔍 Smart Search: Ticker symbol to CIK resolution with fuzzy matching
        📊 Dual Data Sources: Real-time API + historical quarterly indexes
        🚀 Modern Interface: Async-ready with comprehensive error handling
        📋 Rich Results: Structured FilingInfo objects with metadata
        🛡️ Production Ready: Rate limiting, caching, and robust error handling

    Data Sources:
        - **Real-time**: SEC EDGAR APIs for current filings (updated nightly)
        - **Historical**: Quarterly IDX files for comprehensive historical data
        - **Note**: IDX files are updated quarterly; use API for most recent filings

    Example:
        Basic search workflow:

        ```python
        from py_sec_edgar.search_engine import FilingSearchEngine

        engine = FilingSearchEngine()

        # Search for Apple's 10-K filings
        results = engine.search_by_ticker(
            ticker="AAPL",
            form_type="10-K",
            limit=5
        )

        # Access structured results
        for filing in results:
            print(f"{filing.company_name}: {filing.form_type} ({filing.filing_date})")
        ```

    Dependencies:
        Requires company_tickers.json and merged filing index data.
        Run `py-sec-edgar feeds update-full-index` to download required data.

    See Also:
        core.models.FilingInfo: Structured filing data containers
        core.downloader.FilingDownloader: Download filing documents
        client: High-level programmatic interface
    """

    def __init__(self) -> None:
        """Initialize the SEC Filing Search Engine.

        Sets up data source paths, initializes caches, and verifies that
        required reference data files are available. Will raise FilingSearchError
        if critical data files are missing.

        Raises:
            FilingSearchError: If company_tickers.json or filing index data is missing.

        Note:
            Uses lazy loading for data files - actual loading occurs on first use
            to optimize performance for applications that may not need all data.
        """
        self.ticker_map_path = settings.ref_dir / "company_tickers.json"
        self.filing_index_path = settings.merged_idx_filepath
        self.edgar_base_url = settings.edgar_archives_url

        # Cache for loaded data
        self._company_tickers: dict | None = None
        self._filing_index: pd.DataFrame | None = None

        # Verify data sources exist
        self._check_data_sources()

    def _check_data_sources(self) -> None:
        """Verify required data files exist"""
        missing_files = []

        if not self.ticker_map_path.exists():
            missing_files.append(str(self.ticker_map_path))

        if not self.filing_index_path.exists():
            missing_files.append(str(self.filing_index_path))

        if missing_files:
            raise FilingSearchError(
                f"Missing required data files: {', '.join(missing_files)}\n"
                "To download required data, run: uv run py-sec-edgar feeds update-full-index"
            )

    def _load_company_tickers(self) -> dict[str, Any]:
        """Load SEC company ticker mapping data"""
        if self._company_tickers is not None:
            return self._company_tickers

        try:
            with open(self.ticker_map_path) as f:
                self._company_tickers = json.load(f)
            return self._company_tickers
        except Exception as e:
            raise FilingSearchError(f"Failed to load company tickers: {e}") from e

    def _load_filing_index(self) -> pd.DataFrame:
        """Load SEC filing index data"""
        if self._filing_index is not None:
            return self._filing_index

        try:
            self._filing_index = pd.read_parquet(self.filing_index_path)
            return self._filing_index
        except Exception as e:
            raise FilingSearchError(f"Failed to load filing index: {e}") from e

    def get_cik_for_ticker(self, ticker: str) -> tuple[str, str]:
        """
        Get CIK and company name for a ticker symbol

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')

        Returns:
            tuple: (cik, company_name)

        Raises:
            FilingSearchError: If ticker not found
        """
        ticker = ticker.upper().strip()
        company_data = self._load_company_tickers()

        for entry in company_data.values():
            if entry["ticker"].upper() == ticker:
                cik = str(entry["cik_str"]).lstrip("0")
                company_name = entry.get("title", "Unknown Company")
                return cik, company_name

        raise FilingSearchError(
            f"Ticker '{ticker}' not found in SEC company mapping. "
            "Verify the ticker symbol is correct and the company files with the SEC."
        )

    def search_by_cik(
        self,
        cik: str,
        form_types: list[str] | None = None,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        limit: int = 50,
    ) -> list[FilingInfo]:
        """
        Search filings by CIK with filtering options

        Args:
            cik: Central Index Key (company identifier)
            form_types: List of SEC form types to include (e.g., ['10-K', '10-Q'])
            start_date: Earliest filing date to include
            end_date: Latest filing date to include
            limit: Maximum number of results to return

        Returns:
            List of FilingInfo objects sorted by filing date (newest first)
        """
        df = self._load_filing_index()

        # Filter by CIK
        cik_int = int(cik)
        df_filtered = df[df["CIK"] == cik_int].copy()

        if len(df_filtered) == 0:
            return []

        # Filter by form types if specified
        if form_types:
            form_types_upper = [ft.upper() for ft in form_types]
            df_filtered = df_filtered[df_filtered["Form Type"].isin(form_types_upper)]

        # Filter by date range if specified
        if start_date or end_date:
            df_filtered["Date Filed"] = pd.to_datetime(df_filtered["Date Filed"])

            if start_date:
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                df_filtered = df_filtered[df_filtered["Date Filed"] >= start_date]

            if end_date:
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                df_filtered = df_filtered[df_filtered["Date Filed"] <= end_date]

        # Sort by date (newest first) and apply limit
        df_filtered = df_filtered.sort_values("Date Filed", ascending=False)
        df_filtered = df_filtered.head(limit)

        # Get company name for the CIK
        company_name = "Unknown Company"
        ticker = "UNKNOWN"
        try:
            company_data = self._load_company_tickers()
            for entry in company_data.values():
                if str(entry["cik_str"]).lstrip("0") == cik:
                    company_name = entry.get("title", "Unknown Company")
                    ticker = entry.get("ticker", "UNKNOWN")
                    break
        except Exception:
            pass  # Use defaults if lookup fails

        # Convert to FilingInfo objects
        results = []
        for _, row in df_filtered.iterrows():
            filing_info = FilingInfo.from_search_result(
                ticker=ticker,
                company_name=company_name,
                cik=cik,
                form_type=row["Form Type"],
                filing_date=str(row["Date Filed"]).split()[0],  # Date only, no time
                document_url=generate_filing_document_url(
                    row["Filename"], row["Form Type"]
                ),
                filename=row["Filename"],
                # Enhanced URL fields
                submission_url=generate_submission_filing_url(row["Filename"]),
                sec_website_url=generate_sec_website_url(row["Filename"]),
            )
            results.append(filing_info)

        return results

    def search_by_ticker(
        self,
        ticker: str | list[str],
        form_types: list[str] | None = None,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        limit: int = 50,
    ) -> list[FilingInfo]:
        """
        Search filings by ticker symbol(s) with filtering options

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL') or list of tickers, or comma-separated string
            form_types: List of SEC form types to include (e.g., ['10-K', '10-Q'])
            start_date: Earliest filing date to include
            end_date: Latest filing date to include
            limit: Maximum number of results to return per ticker

        Returns:
            List of FilingInfo objects sorted by filing date (newest first)

        Raises:
            FilingSearchError: If ticker not found or search fails
        """
        # Handle different input formats
        if isinstance(ticker, str):
            # Check if comma-separated
            if "," in ticker:
                tickers = [t.strip().upper() for t in ticker.split(",") if t.strip()]
            else:
                tickers = [ticker.upper().strip()]
        elif isinstance(ticker, list):
            tickers = [t.upper().strip() for t in ticker]
        else:
            raise FilingSearchError(f"Invalid ticker format: {ticker}")

        if not tickers:
            raise FilingSearchError("No valid tickers provided")

        # For single ticker, use original logic
        if len(tickers) == 1:
            return self._search_single_ticker(
                tickers[0], form_types, start_date, end_date, limit
            )

        # For multiple tickers, search each and combine results
        all_results = []
        failed_tickers = []

        for single_ticker in tickers:
            try:
                results = self._search_single_ticker(
                    single_ticker, form_types, start_date, end_date, limit
                )
                all_results.extend(results)
            except FilingSearchError:
                # Continue with other tickers if one fails
                failed_tickers.append(single_ticker)
                continue

        if not all_results:
            if failed_tickers:
                raise FilingSearchError(
                    f"No filings found for any of the provided tickers: {', '.join(tickers)}"
                )
            else:
                raise FilingSearchError(
                    f"No filings found for any of the provided tickers: {', '.join(tickers)}"
                )

        # Sort combined results by filing date (newest first)
        all_results.sort(key=lambda x: x.filing_date, reverse=True)

        return all_results

    def _search_single_ticker(
        self,
        ticker: str,
        form_types: list[str] | None = None,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        limit: int = 50,
    ) -> list[FilingInfo]:
        """
        Search filings for a single ticker (internal method)

        Args:
            ticker: Single stock ticker symbol (e.g., 'AAPL')
            form_types: List of SEC form types to include
            start_date: Earliest filing date to include
            end_date: Latest filing date to include
            limit: Maximum number of results to return

        Returns:
            List of FilingInfo objects for the ticker
        """
        try:
            # Get CIK for ticker
            cik, company_name = self.get_cik_for_ticker(ticker)

            # Search by CIK
            results = self.search_by_cik(
                cik=cik,
                form_types=form_types,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            # Update company info in results
            for result in results:
                result.ticker = ticker.upper()
                result.company_name = company_name

            return results

        except Exception as e:
            if isinstance(e, FilingSearchError):
                raise
            raise FilingSearchError(f"Failed to search for {ticker}: {e}") from e

    # UNUSED: get_latest_filing method - not currently called but useful utility for getting most recent filing
    # def get_latest_filing(
    #     self,
    #     ticker: str,
    #     form_type: str = "10-K"
    # ) -> FilingInfo | None:
    #     """
    #     Get the most recent filing of a specific type
    #
    #     Args:
    #         ticker: Stock ticker symbol
    #         form_type: SEC form type (default: 10-K)
    #
    #     Returns:
    #         FilingInfo object or None if no filing found
    #     """
    #     results = self.search_by_ticker(
    #         ticker=ticker,
    #         form_types=[form_type],
    #         limit=1
    #     )
    #
    #     return results[0] if results else None

    def get_filing_types_for_ticker(self, ticker: str) -> dict[str, int]:
        """
        Get summary of all filing types available for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary mapping form type to count of filings
        """
        try:
            cik, _ = self.get_cik_for_ticker(ticker)
            df = self._load_filing_index()

            cik_int = int(cik)
            company_filings = df[df["CIK"] == cik_int]

            if len(company_filings) == 0:
                return {}

            return company_filings["Form Type"].value_counts().to_dict()

        except Exception as e:
            raise FilingSearchError(
                f"Failed to get filing types for {ticker}: {e}"
            ) from e

    async def download_filing_content(
        self,
        filing_info: FilingInfo,
        save_to_disk: bool = True,
        force_redownload: bool = False,
    ) -> str:
        """
        Download the actual filing content from SEC EDGAR

        Args:
            filing_info: FilingInfo object with document URL
            save_to_disk: Whether to save the file to local storage (default: True)
            force_redownload: Whether to redownload even if file exists locally

        Returns:
            Raw filing content as string

        Raises:
            FilingSearchError: If download fails
        """
        try:
            downloader = FilingDownloader()

            # Check if we should skip cache
            if force_redownload and save_to_disk:
                # Remove local file to force redownload
                local_path = downloader._get_local_path(filing_info)
                if local_path.exists():
                    local_path.unlink()

            content = await downloader.download_filing(
                filing_info, save_to_disk=save_to_disk, show_progress=True
            )

            return content

        except Exception as e:
            raise FilingSearchError(
                f"Failed to download filing for {filing_info.ticker}: {e}"
            ) from e

    # NOTE: Local filing methods moved to unified FilingDownloader in core/downloader.py
    # These methods are kept for backward compatibility but delegate to the unified downloader

    def get_local_filing_status(
        self, filing_info: FilingInfo
    ) -> tuple[str, str, Path | None]:
        """
        Check local filing status and get file information

        Args:
            filing_info: FilingInfo object

        Returns:
            Tuple of (status, size_str, file_path)
            - status: "local", "remote", or "partial"
            - size_str: Human-readable file size or "-"
            - file_path: Path to local file if it exists, None otherwise
        """
        try:
            downloader = FilingDownloader()
            status_info = downloader.get_local_status(filing_info)

            if status_info["is_local"]:
                file_path = Path(status_info["path"])
                size = status_info["size"]

                if size < 1024:
                    size_str = f"{size}B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f}KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f}MB"

                # Basic validation - check if file seems complete
                if size > 100:  # Minimum reasonable size for a filing
                    return "local", size_str, file_path
                else:
                    return "partial", size_str, file_path
            else:
                return "remote", "-", None

        except Exception:
            return "remote", "-", None


# Convenience functions for common use cases
# COMMENTED OUT - Dead code testing
# def search_company_filings(ticker: str, form_type: str = "10-K", limit: int = 10) -> list[FilingInfo]:
#     """Simple interface for searching company filings"""
#     engine = FilingSearchEngine()
#     return engine.search_by_ticker(ticker=ticker, form_types=[form_type] if form_type else None, limit=limit)
#
# def get_latest_10k(ticker: str) -> FilingInfo | None:
#     """Get the most recent 10-K filing for a company"""
#     engine = FilingSearchEngine()
#     return engine.get_latest_filing(ticker, "10-K")
#
# def get_latest_10q(ticker: str) -> FilingInfo | None:
#     """Get the most recent 10-Q filing for a company"""
#     engine = FilingSearchEngine()
#     return engine.get_latest_filing(ticker, "10-Q")
#
# async def download_latest_10k_content(ticker: str) -> str | None:
#     """Download content of the most recent 10-K filing"""
#     engine = FilingSearchEngine()
#     filing = engine.get_latest_filing(ticker, "10-K")
#     if filing:
#         return await engine.download_filing_content(filing)
#     return None
