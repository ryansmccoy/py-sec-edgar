"""
Unified Filing Feed Manager

Modern interface for all SEC EDGAR feed operations using AbstractFeed interface
and registry pattern. Provides comprehensive error handling,
progress reporting, and status monitoring.
"""

import logging
from typing import Any

from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from py_sec_edgar import settings
from py_sec_edgar.core.downloader import FilingDownloader
from py_sec_edgar.core.feeds.registry import FeedRegistry
from py_sec_edgar.core.models import FeedConfig, FeedResult, FeedType


class FilingFeedError(Exception):
    """Custom exception for feed operations"""

    pass


class FilingFeedManager:
    """
    Unified interface for all SEC EDGAR feed operations

    Modern interface with:
    - Clean abstraction through AbstractFeed
    - Registry pattern for extensibility
    - Comprehensive status monitoring
    - Standardized error handling

    Example:
        # Initialize manager
        manager = FilingFeedManager()

        # Fetch RSS data
        result = manager.fetch_rss(count=100, form_type="8-K")

        # Update all feeds
        results = manager.update_all()

        # Get system status
        status = manager.get_system_status()
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize feed manager

        Args:
            console: Rich console for output (optional)
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        self.downloader = FilingDownloader()
        self.registry = FeedRegistry(self.downloader)

        # Store last operation results
        self._results: dict[FeedType, FeedResult] = {}

        # Verify data directories exist
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required data directories exist"""
        directories = [
            settings.data_dir,
            settings.ref_dir,
            settings.full_index_data_dir,
            settings.daily_index_data_dir,
            settings.monthly_data_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    # ===== RSS OPERATIONS =====

    def fetch_rss(
        self,
        count: int = 40,
        form_type: str | None = None,
        cik: str | None = None,
        company: str | None = None,
        show_progress: bool = True,
    ) -> FeedResult:
        """
        Fetch recent filings from SEC RSS feed

        Args:
            count: Number of filings to fetch (max 400)
            form_type: Filter by form type (e.g., "10-K", "8-K")
            cik: Filter by Central Index Key
            company: Filter by company name
            show_progress: Show progress indicators

        Returns:
            FeedResult with filings data
        """
        if show_progress:
            with Progress() as progress:
                task = progress.add_task(
                    f"Fetching {count} recent filings...", total=100
                )

                config = FeedConfig(
                    feed_type=FeedType.RSS,
                    params={
                        "count": count,
                        "form_type": form_type,
                        "cik": cik,
                        "company": company,
                    },
                )

                progress.update(task, advance=30)

                feed = self.registry.get_feed(FeedType.RSS)
                result = feed.fetch(config)

                progress.update(task, advance=70)
                progress.update(task, completed=100)
        else:
            config = FeedConfig(
                feed_type=FeedType.RSS,
                params={
                    "count": count,
                    "form_type": form_type,
                    "cik": cik,
                    "company": company,
                },
            )

            feed = self.registry.get_feed(FeedType.RSS)
            result = feed.fetch(config)

        # Store result
        self._results[FeedType.RSS] = result

        if show_progress:
            if result.success:
                self.console.print(
                    f"✅ Fetched {result.items_processed} recent filings ({result.duration:.2f}s)"
                )
            else:
                self.console.print(
                    f"❌ RSS fetch failed: {result.errors[0] if result.errors else 'Unknown error'}"
                )

        return result

    # ===== INDEX OPERATIONS =====

    def update_daily(
        self, days_back: int = 1, skip_existing: bool = True, show_progress: bool = True
    ) -> FeedResult:
        """
        Update daily index files

        Args:
            days_back: Number of days to look back
            skip_existing: Skip files that already exist
            show_progress: Show progress indicators

        Returns:
            FeedResult with update results
        """
        config = FeedConfig(
            feed_type=FeedType.DAILY_INDEX,
            params={"days_back": days_back, "skip_if_exists": skip_existing},
            show_progress=show_progress,
        )

        if show_progress:
            self.console.print(f"🔄 Updating daily index (last {days_back} days)...")

        feed = self.registry.get_feed(FeedType.DAILY_INDEX)
        result = feed.update(config)

        # Store result
        self._results[FeedType.DAILY_INDEX] = result

        if show_progress:
            if result.success:
                self.console.print(
                    f"✅ Daily index update complete: {result.items_processed} days processed ({result.duration:.1f}s)"
                )
            else:
                self.console.print(
                    f"❌ Daily index update failed: {result.errors[0] if result.errors else 'Unknown error'}"
                )

        return result

    def update_monthly(
        self, months_back: int = 1, show_progress: bool = True
    ) -> FeedResult:
        """
        Update monthly XBRL files

        Args:
            months_back: Number of months to look back
            show_progress: Show progress indicators

        Returns:
            FeedResult with update results
        """
        config = FeedConfig(
            feed_type=FeedType.MONTHLY_XBRL,
            params={"months_back": months_back},
            show_progress=show_progress,
        )

        if show_progress:
            self.console.print(
                f"🔄 Updating monthly XBRL data (last {months_back} months)..."
            )

        feed = self.registry.get_feed(FeedType.MONTHLY_XBRL)
        result = feed.update(config)

        # Store result
        self._results[FeedType.MONTHLY_XBRL] = result

        if show_progress:
            if result.success:
                self.console.print(
                    f"✅ Monthly XBRL update complete: {result.items_processed} months processed ({result.duration:.1f}s)"
                )
            else:
                self.console.print(
                    f"❌ Monthly XBRL update failed: {result.errors[0] if result.errors else 'Unknown error'}"
                )

        return result

    def update_full_index(
        self,
        save_csv: bool = True,
        skip_existing: bool = True,
        merge_after_update: bool = True,
        show_progress: bool = True,
        custom_start_date: str | None = None,
        custom_end_date: str | None = None,
    ) -> FeedResult:
        """
        Update full index files

        Args:
            save_csv: Save IDX files as CSV format
            skip_existing: Skip files that already exist
            merge_after_update: Merge index files after update
            show_progress: Show progress indicators
            custom_start_date: Custom start date (MM/DD/YYYY format)
            custom_end_date: Custom end date (MM/DD/YYYY format)

        Returns:
            FeedResult with update results
        """
        config = FeedConfig(
            feed_type=FeedType.FULL_INDEX,
            params={
                "save_csv": save_csv,
                "skip_existing": skip_existing,
                "merge_after_update": merge_after_update,
                "custom_start_date": custom_start_date,
                "custom_end_date": custom_end_date,
            },
            show_progress=show_progress,
        )

        if show_progress:
            self.console.print("🔄 Starting full index update...")

        feed = self.registry.get_feed(FeedType.FULL_INDEX)
        result = feed.update(config)

        # Store result
        self._results[FeedType.FULL_INDEX] = result

        if show_progress:
            if result.success:
                self.console.print(
                    f"✅ Full index update complete: {result.items_processed} files processed ({result.duration:.1f}s)"
                )
            else:
                self.console.print(
                    f"❌ Full index update failed: {result.errors[0] if result.errors else 'Unknown error'}"
                )

        return result

    # ===== BATCH OPERATIONS =====

    def update_all(
        self,
        daily_days: int = 1,
        monthly_months: int = 1,
        rss_count: int = 100,
        skip_existing: bool = True,
        show_progress: bool = True,
    ) -> dict[FeedType, FeedResult]:
        """
        Update all feeds sequentially

        Args:
            daily_days: Days back for daily index
            monthly_months: Months back for monthly XBRL
            rss_count: Number of RSS filings to fetch
            skip_existing: Skip existing files
            show_progress: Show progress indicators

        Returns:
            Dictionary mapping feed type to FeedResult
        """
        if show_progress:
            self.console.print("🚀 Starting feed updates...")

        import time

        start_time = time.time()
        result_dict = {}

        try:
            # Update feeds sequentially
            # feed_types = [FeedType.FULL_INDEX, FeedType.DAILY_INDEX, FeedType.MONTHLY_XBRL, FeedType.RSS]  # Commented: unused variable

            # Full index (run first as other feeds may depend on it)
            try:
                result_dict[FeedType.FULL_INDEX] = self.update_full_index(
                    skip_existing=skip_existing,
                    show_progress=False,  # Disable individual progress for batch
                )
            except Exception as e:
                result_dict[FeedType.FULL_INDEX] = FeedResult(
                    feed_type=FeedType.FULL_INDEX,
                    success=False,
                    items_processed=0,
                    duration=0.0,
                    errors=[str(e)],
                )

            # Daily index
            try:
                result_dict[FeedType.DAILY_INDEX] = self.update_daily(
                    days_back=daily_days,
                    skip_existing=skip_existing,
                    show_progress=False,
                )
            except Exception as e:
                result_dict[FeedType.DAILY_INDEX] = FeedResult(
                    feed_type=FeedType.DAILY_INDEX,
                    success=False,
                    items_processed=0,
                    duration=0.0,
                    errors=[str(e)],
                )

            # Monthly XBRL
            try:
                result_dict[FeedType.MONTHLY_XBRL] = self.update_monthly(
                    months_back=monthly_months, show_progress=False
                )
            except Exception as e:
                result_dict[FeedType.MONTHLY_XBRL] = FeedResult(
                    feed_type=FeedType.MONTHLY_XBRL,
                    success=False,
                    items_processed=0,
                    duration=0.0,
                    errors=[str(e)],
                )

            # RSS feed
            try:
                result_dict[FeedType.RSS] = self.fetch_rss(
                    count=rss_count, show_progress=False
                )
            except Exception as e:
                result_dict[FeedType.RSS] = FeedResult(
                    feed_type=FeedType.RSS,
                    success=False,
                    items_processed=0,
                    duration=0.0,
                    errors=[str(e)],
                )

            total_duration = time.time() - start_time

            if show_progress:
                self._display_batch_results(result_dict, total_duration)

            return result_dict

        except Exception as e:
            self.logger.error(f"Batch update failed: {e}")
            raise FilingFeedError(f"Batch update failed: {e}")

    # ===== STATUS AND MONITORING =====

    def get_system_status(self) -> dict[FeedType, dict[str, Any]]:
        """
        Get comprehensive status of all feed types

        Returns:
            Dictionary mapping feed type to status information
        """
        status_map = {}

        for feed_type in self.registry.list_feeds():
            try:
                feed = self.registry.get_feed(feed_type)
                status_map[feed_type] = feed.get_status()
            except Exception as e:
                status_map[feed_type] = {
                    "type": feed_type.value,
                    "status": "error",
                    "error": str(e),
                }

        return status_map

    def display_status(
        self, status: dict[FeedType, dict[str, Any]] | None = None
    ) -> None:
        """
        Display system status in a formatted table

        Args:
            status: Status dictionary (will fetch if not provided)
        """
        if status is None:
            status = self.get_system_status()

        table = Table(title="SEC Filing Feed Status")
        table.add_column("Feed Type", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Description", style="blue")
        table.add_column("Files", justify="right")
        table.add_column("Size", justify="right")

        for feed_type, feed_status in status.items():
            # Format status with emoji
            status_display = {
                "available": "✅ Available",
                "missing": "❌ Missing",
                "outdated": "⚠️ Outdated",
                "error": "🚫 Error",
                "unknown": "❓ Unknown",
            }.get(
                feed_status.get("status", "unknown"),
                feed_status.get("status", "unknown"),
            )

            description = feed_status.get("description", feed_type.value)
            file_count = (
                str(feed_status.get("file_count", 0))
                if feed_status.get("file_count", 0) > 0
                else "-"
            )

            # Format size
            total_size = feed_status.get("total_size", 0)
            if total_size > 0:
                if total_size < 1024:
                    size_str = f"{total_size}B"
                elif total_size < 1024 * 1024:
                    size_str = f"{total_size / 1024:.1f}KB"
                elif total_size < 1024 * 1024 * 1024:
                    size_str = f"{total_size / (1024 * 1024):.1f}MB"
                else:
                    size_str = f"{total_size / (1024 * 1024 * 1024):.1f}GB"
            else:
                size_str = "-"

            table.add_row(
                feed_type.value.replace("_", " ").title(),
                status_display,
                description[:50] + "..." if len(description) > 50 else description,
                file_count,
                size_str,
            )

        self.console.print(table)

    # ===== HELPER METHODS =====

    def _display_batch_results(
        self, results: dict[FeedType, FeedResult], total_duration: float
    ) -> None:
        """Display results of batch update operation"""
        table = Table(
            title=f"Parallel Feed Update Results ({total_duration:.1f}s total)"
        )
        table.add_column("Feed Type", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Items", justify="right")
        table.add_column("Duration", justify="right")
        table.add_column("Notes")

        for feed_type, result in results.items():
            status_display = "✅ Success" if result.success else "❌ Failed"
            items_str = (
                str(result.items_processed) if result.items_processed > 0 else "-"
            )
            duration_str = f"{result.duration:.1f}s" if result.duration > 0 else "-"

            notes = ""
            if result.errors:
                notes = (
                    result.errors[0][:50] + "..."
                    if len(result.errors[0]) > 50
                    else result.errors[0]
                )
            elif result.data:
                notes = (
                    f"{len(result.data)} items"
                    if isinstance(result.data, list)
                    else "Data updated"
                )

            table.add_row(
                feed_type.value.replace("_", " ").title(),
                status_display,
                items_str,
                duration_str,
                notes,
            )

        self.console.print(table)

        # Summary
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)

        if successful == total:
            self.console.print(
                f"🎉 All {total} feed operations completed successfully!"
            )
        else:
            self.console.print(
                f"⚠️ {successful}/{total} feed operations completed successfully"
            )


# Convenience functions for backward compatibility
def update_all_feeds(
    daily_days: int = 1, monthly_months: int = 1, show_progress: bool = True
) -> dict[FeedType, FeedResult]:
    """
    Simple interface for updating all feeds with parallel execution

    Args:
        daily_days: Days back for daily index
        monthly_months: Months back for monthly XBRL
        show_progress: Show progress indicators

    Returns:
        Dictionary mapping feed type to FeedResult
    """
    manager = FilingFeedManager()
    return manager.update_all(
        daily_days=daily_days,
        monthly_months=monthly_months,
        show_progress=show_progress,
    )


def fetch_recent_filings(count: int = 40, form_type: str | None = None) -> FeedResult:
    """
    Simple interface for fetching recent filings

    Args:
        count: Number of filings to fetch
        form_type: Filter by form type

    Returns:
        FeedResult with filing data
    """
    manager = FilingFeedManager()
    return manager.fetch_rss(count=count, form_type=form_type)


def display_feed_status() -> None:
    """Display current feed system status"""
    manager = FilingFeedManager()
    manager.display_status()
