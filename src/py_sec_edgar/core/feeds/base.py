"""
Abstract base interface for SEC EDGAR feeds

This module defines the common interface that all feed implementations
must follow, ensuring consistency and interchangeability.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from ..downloader import FilingDownloader
from ..models import FeedConfig, FeedResult, FeedType


class AbstractFeed(ABC):
    """
    Base interface for all SEC feed types

    This abstract class defines the common interface that all feed
    implementations must follow. It provides:

    - Standardized interface for all feed operations
    - Consistent configuration and result handling
    - Built-in error handling patterns
    - Integration with FilingDownloader
    """

    def __init__(self, downloader: FilingDownloader):
        """
        Initialize feed with downloader dependency

        Args:
            downloader: FilingDownloader instance for network operations
        """
        self.downloader = downloader
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def feed_type(self) -> FeedType:
        """Return the feed type identifier"""
        pass

    @abstractmethod
    def fetch(self, config: FeedConfig) -> FeedResult:
        """
        Fetch data from SEC for this feed type

        Args:
            config: Configuration for the fetch operation

        Returns:
            FeedResult with operation results and data
        """
        pass

    @abstractmethod
    def update(self, config: FeedConfig) -> FeedResult:
        """
        Update local data for this feed type

        Args:
            config: Configuration for the update operation

        Returns:
            FeedResult with operation results
        """
        pass

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Get current status of this feed

        Returns:
            Dictionary with status information
        """
        pass

    def _create_success_result(
        self,
        operation: str,
        items_processed: int,
        start_time: float,
        data: Any = None,
        metadata: dict[str, Any] = None,
    ) -> FeedResult:
        """Helper to create successful FeedResult"""
        return FeedResult(
            feed_type=self.feed_type,
            success=True,
            items_processed=items_processed,
            duration=time.time() - start_time,
            data=data,
            metadata=metadata or {},
        )

    def _create_error_result(
        self, operation: str, start_time: float, error: Exception
    ) -> FeedResult:
        """Helper to create error FeedResult"""
        return FeedResult(
            feed_type=self.feed_type,
            success=False,
            items_processed=0,
            duration=time.time() - start_time,
            errors=[str(error)],
        )
