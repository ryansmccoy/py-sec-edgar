"""
Feed registry for managing feed implementations

This module provides the registry pattern for dynamically managing
different feed implementations while maintaining a clean interface.
"""

import logging

from ..downloader import FilingDownloader
from ..models import FeedType
from .base import AbstractFeed


class FeedRegistry:
    """
    Registry for managing feed implementations

    Provides centralized management of feed implementations with:
    - Dynamic registration of feed types
    - Type-safe feed retrieval
    - Automatic initialization with dependencies
    """

    def __init__(self, downloader: FilingDownloader):
        """
        Initialize registry with downloader dependency

        Args:
            downloader: FilingDownloader instance to inject into feeds
        """
        self.downloader = downloader
        self.logger = logging.getLogger(__name__)
        self._feeds: dict[FeedType, AbstractFeed] = {}
        self._register_default_feeds()

    def _register_default_feeds(self):
        """Register built-in feed implementations using unified wrapper"""
        try:
            # Import unified wrapper factory functions
            from ...feeds.feed_wrapper import (
                create_daily_feed,
                create_full_index_feed,
                create_monthly_feed,
                create_rss_feed,
            )

            # Register each feed using unified wrapper (eliminates ~250 lines of duplicate code)
            self.register(create_rss_feed(self.downloader))
            self.register(create_daily_feed(self.downloader))
            self.register(create_monthly_feed(self.downloader))
            self.register(create_full_index_feed(self.downloader))

            self.logger.info(
                f"Registered {len(self._feeds)} feeds using unified wrapper"
            )

        except ImportError as e:
            # Graceful degradation - fallback to old implementations if needed
            self.logger.warning(f"Could not register unified feeds: {e}")
            self._register_legacy_feeds()

    def _register_legacy_feeds(self):
        """Fallback registration using old abstract implementations"""
        try:
            # Import legacy feed implementations
            from ...feeds.daily_abstract import DailyIndexFeed
            from ...feeds.full_index_abstract import FullIndexFeed
            from ...feeds.monthly_abstract import MonthlyXBRLFeed
            from ...feeds.rss_abstract import RSSFeed

            # Register each feed
            self.register(RSSFeed(self.downloader))
            self.register(DailyIndexFeed(self.downloader))
            self.register(MonthlyXBRLFeed(self.downloader))
            self.register(FullIndexFeed(self.downloader))

            self.logger.info(f"Registered {len(self._feeds)} legacy feeds (fallback)")

        except ImportError as e:
            self.logger.error(f"Could not register any feeds: {e}")

    def register(self, feed: AbstractFeed) -> None:
        """
        Register a feed implementation

        Args:
            feed: Feed implementation to register
        """
        self._feeds[feed.feed_type] = feed
        self.logger.debug(f"Registered feed: {feed.feed_type}")

    def get_feed(self, feed_type: FeedType) -> AbstractFeed:
        """
        Get feed implementation by type

        Args:
            feed_type: Type of feed to retrieve

        Returns:
            Feed implementation

        Raises:
            ValueError: If feed type is not registered
        """
        if feed_type not in self._feeds:
            raise ValueError(f"No feed registered for type: {feed_type}")
        return self._feeds[feed_type]

    def list_feeds(self) -> list[FeedType]:
        """
        List available feed types

        Returns:
            List of registered feed types
        """
        return list(self._feeds.keys())

    def is_registered(self, feed_type: FeedType) -> bool:
        """
        Check if a feed type is registered

        Args:
            feed_type: Feed type to check

        Returns:
            True if registered, False otherwise
        """
        return feed_type in self._feeds

    def unregister(self, feed_type: FeedType) -> None:
        """
        Unregister a feed type

        Args:
            feed_type: Feed type to remove
        """
        if feed_type in self._feeds:
            del self._feeds[feed_type]
            self.logger.debug(f"Unregistered feed: {feed_type}")
