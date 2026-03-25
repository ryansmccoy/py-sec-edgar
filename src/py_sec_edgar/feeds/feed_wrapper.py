"""
Unified Feed Wrapper - Simple Solution for Abstract Feed Duplication

This module provides a single, flexible wrapper that eliminates the need for
4 separate abstract feed files with 95% duplicate code.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..core.downloader import FilingDownloader
from ..core.feeds.base import AbstractFeed
from ..core.models import FeedConfig, FeedResult, FeedType


class UnifiedFeedWrapper(AbstractFeed):
    """
    Universal feed wrapper that can wrap any legacy feed function

    This single class replaces 4 nearly identical abstract wrapper classes,
    eliminating ~250 lines of duplicate code.
    """

    def __init__(
        self,
        downloader: FilingDownloader,
        feed_type: FeedType,
        legacy_function: Callable,
        description: str,
        source_url: str,
        data_dir_setting: str,
        **kwargs,
    ):
        """
        Initialize unified wrapper

        Args:
            downloader: Filing downloader instance
            feed_type: Type of feed (DAILY_INDEX, MONTHLY_XBRL, etc.)
            legacy_function: The legacy function to wrap
            description: Human-readable description
            source_url: Source URL for this feed type
            data_dir_setting: Settings attribute name for data directory
            **kwargs: Additional feed-specific configuration
        """
        super().__init__(downloader)
        self._feed_type = feed_type
        self._legacy_function = legacy_function
        self._description = description
        self._source_url = source_url
        self._data_dir_setting = data_dir_setting
        self._config = kwargs

    @property
    def feed_type(self) -> FeedType:
        """Return feed type"""
        return self._feed_type

    def fetch(self, config: FeedConfig) -> FeedResult:
        """Fetch data (same as update for most feeds)"""
        return self.update(config)

    def update(self, config: FeedConfig) -> FeedResult:
        """
        Update feed using legacy function

        Args:
            config: Configuration with parameters

        Returns:
            FeedResult with operation results
        """
        start_time = time.time()

        try:
            # Merge config params with wrapper config
            params = {**self._config, **config.params}

            # Call legacy function with appropriate parameters
            if self._feed_type == FeedType.RSS:
                # RSS feed is special - it returns data
                result_data = self._legacy_function(**params)
                items_count = len(result_data) if result_data else 0

                return self._create_success_result(
                    operation="fetch",
                    items_processed=items_count,
                    start_time=start_time,
                    data=result_data,
                    metadata=params,
                )
            else:
                # Other feeds are update operations - filter parameters for each feed type
                if self._feed_type == FeedType.DAILY_INDEX:
                    # Daily feed expects: days_back, skip_if_exists
                    filtered_params = {
                        k: v
                        for k, v in params.items()
                        if k in ["days_back", "skip_if_exists"]
                    }
                elif self._feed_type == FeedType.MONTHLY_XBRL:
                    # Monthly feed expects: months_back
                    filtered_params = {
                        k: v for k, v in params.items() if k in ["months_back"]
                    }
                elif self._feed_type == FeedType.FULL_INDEX:
                    # Full index feed expects: save_idx_as_csv, skip_if_exists, custom_start_date, custom_end_date, merge_index
                    filtered_params = {}
                    if "save_csv" in params:
                        filtered_params["save_idx_as_csv"] = params["save_csv"]
                    if "skip_existing" in params:
                        filtered_params["skip_if_exists"] = params["skip_existing"]
                    if "custom_start_date" in params:
                        filtered_params["custom_start_date"] = params[
                            "custom_start_date"
                        ]
                    if "custom_end_date" in params:
                        filtered_params["custom_end_date"] = params["custom_end_date"]
                    if "merge_after_update" in params:
                        filtered_params["merge_index"] = params["merge_after_update"]
                else:
                    filtered_params = params

                self._legacy_function(**filtered_params)
                items_count = self._estimate_items_processed(params)

                return self._create_success_result(
                    operation="update",
                    items_processed=items_count,
                    start_time=start_time,
                    metadata=params,
                )

        except Exception as e:
            self.logger.error(f"{self._feed_type.value} operation failed: {e}")
            return self._create_error_result("update", start_time, e)

    def get_status(self) -> dict[str, Any]:
        """
        Get feed status

        Returns:
            Status dictionary with feed information
        """
        try:
            from .. import settings

            base_status = {
                "type": self._feed_type.value.lower(),
                "description": self._description,
                "source_url": self._source_url,
            }

            # RSS is always available
            if self._feed_type == FeedType.RSS:
                return {
                    **base_status,
                    "status": "available",
                    "real_time": True,
                    "max_count": 400,
                    "supports_filtering": True,
                    "filters": ["form_type", "cik", "company"],
                }

            # For other feeds, check data directory
            data_dir = getattr(settings, self._data_dir_setting, None)
            if not data_dir:
                return {
                    **base_status,
                    "status": "error",
                    "error": f"No {self._data_dir_setting} setting",
                }

            data_dir = Path(data_dir)
            base_status["data_directory"] = str(data_dir)

            if data_dir.exists():
                files = list(data_dir.glob("**/*"))
                data_files = [f for f in files if f.is_file()]
                total_size = sum(f.stat().st_size for f in data_files)

                return {
                    **base_status,
                    "status": "available" if data_files else "missing",
                    "file_count": len(data_files),
                    "total_size": total_size,
                }
            else:
                return {**base_status, "status": "missing"}

        except Exception as e:
            return {
                "type": self._feed_type.value.lower(),
                "status": "error",
                "error": str(e),
            }

    def _estimate_items_processed(self, params: dict[str, Any]) -> int:
        """Estimate number of items processed based on parameters"""
        if self._feed_type == FeedType.DAILY_INDEX:
            return params.get("days_back", 1)
        elif self._feed_type == FeedType.MONTHLY_XBRL:
            return params.get("months_back", 1)
        elif self._feed_type == FeedType.FULL_INDEX:
            # Try to count actual files
            try:
                from .. import settings

                data_dir = getattr(settings, self._data_dir_setting)
                return (
                    len(list(Path(data_dir).glob("**/*")))
                    if Path(data_dir).exists()
                    else 0
                )
            except Exception:
                return 1
        else:
            return 1


# Factory functions for easy creation
def create_daily_feed(downloader: FilingDownloader) -> UnifiedFeedWrapper:
    """Create daily index feed wrapper"""
    from .daily import update_daily_index_feed

    return UnifiedFeedWrapper(
        downloader=downloader,
        feed_type=FeedType.DAILY_INDEX,
        legacy_function=update_daily_index_feed,
        description="SEC EDGAR daily index files",
        source_url="https://www.sec.gov/Archives/edgar/daily-index/",
        data_dir_setting="daily_index_data_dir",
    )


def create_monthly_feed(downloader: FilingDownloader) -> UnifiedFeedWrapper:
    """Create monthly XBRL feed wrapper"""
    from .monthly import update_monthly_xbrl_feed

    return UnifiedFeedWrapper(
        downloader=downloader,
        feed_type=FeedType.MONTHLY_XBRL,
        legacy_function=update_monthly_xbrl_feed,
        description="SEC EDGAR monthly XBRL structured data",
        source_url="https://www.sec.gov/Archives/edgar/monthly-index/",
        data_dir_setting="monthly_data_dir",
    )


def create_full_index_feed(downloader: FilingDownloader) -> UnifiedFeedWrapper:
    """Create full index feed wrapper"""
    from .full_index import update_full_index_feed

    return UnifiedFeedWrapper(
        downloader=downloader,
        feed_type=FeedType.FULL_INDEX,
        legacy_function=update_full_index_feed,
        description="SEC EDGAR full quarterly index files",
        source_url="https://www.sec.gov/Archives/edgar/full-index/",
        data_dir_setting="full_index_data_dir",
    )


def create_rss_feed(downloader: FilingDownloader) -> UnifiedFeedWrapper:
    """Create RSS feed wrapper"""
    from .rss import RecentFilingsFeed

    # RSS is special - create instance and use its method
    rss_instance = RecentFilingsFeed()

    return UnifiedFeedWrapper(
        downloader=downloader,
        feed_type=FeedType.RSS,
        legacy_function=rss_instance.fetch_recent_filings,
        description="SEC EDGAR RSS feed for recent filings",
        source_url="https://www.sec.gov/cgi-bin/browse-edgar",
        data_dir_setting="rss_data_dir",  # Not used for RSS
    )
