"""
Enhanced SearchResults collection for py-sec-edgar programmatic interface

Provides rich operations, filtering, and export capabilities for filing search results.
"""

import asyncio
import json
from collections.abc import Callable, Iterator
from datetime import date, datetime
from pathlib import Path
from typing import Any, Union

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .downloader import FilingDownloader
from .models import FilingInfo


class SearchResults:
    """
    Collection of filing search results with rich operations and export capabilities.

    Provides filtering, sorting, export, and batch operations on filing search results.
    Designed to be intuitive and pythonic for data analysis workflows.
    """

    def __init__(
        self, filings: list[FilingInfo], metadata: dict[str, Any] | None = None
    ):
        """
        Initialize SearchResults collection.

        Args:
            filings: List of FilingInfo objects
            metadata: Optional metadata about the search operation
        """
        self._filings = filings
        self._metadata = metadata or {}
        self._downloader = FilingDownloader()

    # Collection interface
    def __len__(self) -> int:
        """Return number of filings in results."""
        return len(self._filings)

    def __iter__(self) -> Iterator[FilingInfo]:
        """Iterate over filings."""
        return iter(self._filings)

    def __getitem__(self, index: int | slice) -> Union[FilingInfo, "SearchResults"]:
        """Get filing by index or slice."""
        if isinstance(index, int):
            return self._filings[index]
        elif isinstance(index, slice):
            return SearchResults(self._filings[index], self._metadata.copy())
        else:
            raise TypeError("Index must be int or slice")

    def __bool__(self) -> bool:
        """Return True if results contain any filings."""
        return len(self._filings) > 0

    # Properties
    @property
    def filings(self) -> list[FilingInfo]:
        """Get list of filings."""
        return self._filings

    @property
    def metadata(self) -> dict[str, Any]:
        """Get search metadata."""
        return self._metadata

    @property
    def tickers(self) -> list[str]:
        """Get unique ticker symbols in results."""
        return list(set(f.ticker for f in self._filings if f.ticker))

    @property
    def companies(self) -> list[str]:
        """Get unique company names in results."""
        return list(set(f.company_name for f in self._filings if f.company_name))

    @property
    def form_types(self) -> list[str]:
        """Get unique form types in results."""
        return list(set(f.form_type for f in self._filings if f.form_type))

    # Filtering methods
    def filter_by_ticker(self, tickers: str | list[str]) -> "SearchResults":
        """
        Filter results by ticker symbol(s).

        Args:
            tickers: Single ticker or list of tickers

        Returns:
            New SearchResults with filtered filings
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        tickers = [t.upper() for t in tickers]

        filtered = [f for f in self._filings if f.ticker.upper() in tickers]
        return SearchResults(filtered, self._metadata.copy())

    def filter_by_form_type(self, form_types: str | list[str]) -> "SearchResults":
        """
        Filter results by SEC form type(s).

        Args:
            form_types: Single form type or list of form types

        Returns:
            New SearchResults with filtered filings
        """
        if isinstance(form_types, str):
            form_types = [form_types]
        form_types = [ft.upper() for ft in form_types]

        filtered = [f for f in self._filings if f.form_type.upper() in form_types]
        return SearchResults(filtered, self._metadata.copy())

    def filter_by_date_range(
        self, start_date: str | date | None = None, end_date: str | date | None = None
    ) -> "SearchResults":
        """
        Filter results by filing date range.

        Args:
            start_date: Earliest filing date (inclusive)
            end_date: Latest filing date (inclusive)

        Returns:
            New SearchResults with filtered filings
        """
        filtered = []

        for filing in self._filings:
            filing_date = filing.filing_date_parsed
            if not filing_date:
                continue

            # Convert to date objects for comparison
            filing_date_only = filing_date.date()

            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                if filing_date_only < start_date:
                    continue

            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                if filing_date_only > end_date:
                    continue

            filtered.append(filing)

        return SearchResults(filtered, self._metadata.copy())

    def filter_local_only(self) -> "SearchResults":
        """
        Filter to only filings that are available locally.

        Returns:
            New SearchResults with only locally available filings
        """
        # This would need to check if files exist locally
        # For now, return all filings (assuming downloader handles local checking)
        return SearchResults(self._filings.copy(), self._metadata.copy())

    # Sorting methods
    def sort_by_date(self, descending: bool = True) -> "SearchResults":
        """
        Sort results by filing date.

        Args:
            descending: If True, sort newest first

        Returns:
            New SearchResults with sorted filings
        """
        sorted_filings = sorted(
            self._filings,
            key=lambda f: f.filing_date_parsed or datetime.min,
            reverse=descending,
        )
        return SearchResults(sorted_filings, self._metadata.copy())

    def sort_by_ticker(self, descending: bool = False) -> "SearchResults":
        """
        Sort results by ticker symbol.

        Args:
            descending: If True, sort Z to A

        Returns:
            New SearchResults with sorted filings
        """
        sorted_filings = sorted(
            self._filings, key=lambda f: f.ticker or "", reverse=descending
        )
        return SearchResults(sorted_filings, self._metadata.copy())

    # Export methods
    def to_dict(self) -> dict[str, Any]:
        """
        Convert results to dictionary format.

        Returns:
            Dictionary with metadata and filings
        """
        return {
            "metadata": {
                **self._metadata,
                "total_results": len(self._filings),
                "companies_found": len(self.tickers),
                "form_types": self.form_types,
                "export_timestamp": datetime.now().isoformat(),
            },
            "filings": [f.to_dict() for f in self._filings],
        }

    def to_json(self, indent: int | None = 2) -> str:
        """
        Convert results to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_dataframe(self) -> "pd.DataFrame":
        """
        Convert results to pandas DataFrame.

        Returns:
            DataFrame with filing information

        Raises:
            ImportError: If pandas is not available
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for DataFrame export. "
                "Install with: pip install pandas"
            )

        if not self._filings:
            return pd.DataFrame()

        # Convert filings to list of dictionaries
        data = []
        for filing in self._filings:
            filing_dict = filing.to_dict()
            # Flatten nested dictionaries for DataFrame compatibility
            if "metadata" in filing_dict and isinstance(filing_dict["metadata"], dict):
                filing_dict.update(filing_dict.pop("metadata"))
            data.append(filing_dict)

        df = pd.DataFrame(data)

        # Convert date strings to datetime
        if "filing_date" in df.columns:
            df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
        if "report_date" in df.columns:
            df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")

        return df

    def to_csv(self, filepath: str | Path, **kwargs) -> None:
        """
        Export results to CSV file.

        Args:
            filepath: Output file path
            **kwargs: Additional arguments passed to pandas.to_csv()
        """
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, **kwargs)

    def to_excel(
        self, filepath: str | Path, include_metadata: bool = True, **kwargs
    ) -> None:
        """
        Export results to Excel file.

        Args:
            filepath: Output file path
            include_metadata: Whether to include metadata sheet
            **kwargs: Additional arguments passed to pandas.to_excel()
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for Excel export. "
                "Install with: pip install pandas openpyxl"
            )

        df = self.to_dataframe()

        if include_metadata and self._metadata:
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Filings", index=False, **kwargs)

                # Create metadata sheet
                metadata_df = pd.DataFrame(
                    [{"Key": k, "Value": str(v)} for k, v in self.get_summary().items()]
                )
                metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
        else:
            df.to_excel(filepath, index=False, **kwargs)

    # Batch operations
    async def download_all(
        self,
        progress_callback: Callable[[int, int, FilingInfo], None] | None = None,
        max_concurrent: int = 5,
    ) -> list[str]:
        """
        Download all filings in results.

        Args:
            progress_callback: Optional callback function for progress updates
            max_concurrent: Maximum number of concurrent downloads

        Returns:
            List of downloaded content strings
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def download_single(index: int, filing: FilingInfo) -> str:
            async with semaphore:
                if progress_callback:
                    progress_callback(index + 1, len(self._filings), filing)
                content = await self._downloader.download_filing_async(filing)
                return content

        tasks = [download_single(i, filing) for i, filing in enumerate(self._filings)]

        results = await asyncio.gather(*tasks)
        return results

    def download_all_sync(
        self, progress_callback: Callable[[int, int, FilingInfo], None] | None = None
    ) -> list[str]:
        """
        Synchronous version of download_all.

        Args:
            progress_callback: Optional callback function for progress updates

        Returns:
            List of downloaded content strings
        """
        results = []
        for i, filing in enumerate(self._filings):
            if progress_callback:
                progress_callback(i + 1, len(self._filings), filing)
            content = self._downloader.download_filing(filing)
            results.append(content)
        return results

    # Summary and statistics
    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics for the search results.

        Returns:
            Dictionary with summary information
        """
        if not self._filings:
            return {
                "total_filings": 0,
                "companies": 0,
                "form_types": [],
                "date_range": None,
            }

        # Get date range
        dates = [f.filing_date_parsed for f in self._filings if f.filing_date_parsed]
        date_range = None
        if dates:
            min_date = min(dates).date()
            max_date = max(dates).date()
            date_range = {"start": min_date.isoformat(), "end": max_date.isoformat()}

        return {
            "total_filings": len(self._filings),
            "companies": len(self.tickers),
            "unique_tickers": self.tickers,
            "form_types": self.form_types,
            "date_range": date_range,
            "filings_by_ticker": {
                ticker: len([f for f in self._filings if f.ticker == ticker])
                for ticker in self.tickers
            },
            "filings_by_form_type": {
                form_type: len([f for f in self._filings if f.form_type == form_type])
                for form_type in self.form_types
            },
        }

    # Utility methods
    def extend(self, other: "SearchResults") -> None:
        """
        Extend this SearchResults with filings from another.

        Args:
            other: Another SearchResults object to merge
        """
        self._filings.extend(other._filings)
        # Merge metadata
        if other._metadata:
            self._metadata.update(other._metadata)

    def __repr__(self) -> str:
        """String representation of SearchResults."""
        return f"SearchResults({len(self._filings)} filings, {len(self.tickers)} companies)"

    def __str__(self) -> str:
        """Human-readable string representation."""
        summary = self.get_summary()
        return (
            f"SearchResults: {summary['total_filings']} filings from "
            f"{summary['companies']} companies\n"
            f"Form types: {', '.join(summary['form_types'])}\n"
            f"Date range: {summary['date_range']}"
        )
