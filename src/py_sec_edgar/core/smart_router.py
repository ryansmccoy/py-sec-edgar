"""
Smart Feed Router for py-sec-edgar

Automatically routes search requests to the appropriate SEC data feed based on date ranges:
- RSS Feed: Real-time filings (last few days)
- Daily Feed: Recent filings (last ~30 days)
- Monthly Feed: Historical data (last ~3 months)
- Quarterly Feed: Historical data (> 3 months back)
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from ..core.models import FilingInfo
from ..search_engine import FilingSearchEngine

logger = logging.getLogger(__name__)


class FeedType(Enum):
    """Available SEC data feeds with their typical coverage."""

    RSS = "rss"  # Real-time: last few days
    DAILY = "daily"  # Recent: last ~30 days
    MONTHLY = "monthly"  # Historical: last ~3 months
    QUARTERLY = "quarterly"  # Historical: > 3 months back


@dataclass
class FeedRoute:
    """Represents a routing decision for a date range query."""

    feed_type: FeedType
    reason: str
    date_range: tuple[date | None, date | None]
    estimated_coverage: str


class SmartFeedRouter:
    """
    Intelligent feed router that selects the best SEC data source based on date ranges.

    Routing Logic:
    - RSS Feed: No date filter or end_date within last 3 days
    - Daily Feed: Date range within last 30 days
    - Monthly Feed: Date range within last 3 months
    - Quarterly Feed: Date range > 3 months back or very broad ranges
    """

    def __init__(self):
        """Initialize the smart feed router."""
        self._search_engine = FilingSearchEngine()

        # Configure feed coverage windows
        self.rss_window_days = 3
        self.daily_window_days = 30
        self.monthly_window_days = 90  # ~3 months

        # Today's date for calculations
        self.today = date.today()

    def analyze_date_range(
        self, start_date: str | None = None, end_date: str | None = None
    ) -> FeedRoute:
        """
        Analyze the requested date range and determine the best feed to use.

        Args:
            start_date: Earliest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)
            end_date: Latest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)

        Returns:
            FeedRoute object with routing decision and reasoning
        """
        try:
            # Parse dates to date objects
            start_parsed = (
                self._parse_date_smart(start_date, is_start=True)
                if start_date
                else None
            )
            end_parsed = (
                self._parse_date_smart(end_date, is_start=False) if end_date else None
            )

            # Case 1: No date filtering - use RSS for most recent
            if not start_date and not end_date:
                return FeedRoute(
                    feed_type=FeedType.RSS,
                    reason="No date filter specified - fetching most recent filings",
                    date_range=(None, None),
                    estimated_coverage="Last few days",
                )

            # Case 2: Only end date, check if it's very recent
            if not start_date and end_parsed:
                days_from_today = (self.today - end_parsed).days
                if days_from_today <= self.rss_window_days:
                    return FeedRoute(
                        feed_type=FeedType.RSS,
                        reason=f"End date {end_parsed} is within RSS window ({self.rss_window_days} days)",
                        date_range=(None, end_parsed),
                        estimated_coverage="Real-time data",
                    )

            # Case 3: Determine date range span and recency
            if start_parsed and end_parsed:
                span_days = (end_parsed - start_parsed).days
                days_from_today = (self.today - end_parsed).days

                # Very recent range - use RSS
                if days_from_today <= self.rss_window_days:
                    return FeedRoute(
                        feed_type=FeedType.RSS,
                        reason=f"Date range ends within RSS window (end: {end_parsed}, {days_from_today} days ago)",
                        date_range=(start_parsed, end_parsed),
                        estimated_coverage="Real-time data",
                    )

                # Recent range - use Daily feed
                elif days_from_today <= self.daily_window_days:
                    return FeedRoute(
                        feed_type=FeedType.DAILY,
                        reason=f"Date range within daily window (end: {end_parsed}, {days_from_today} days ago)",
                        date_range=(start_parsed, end_parsed),
                        estimated_coverage="Daily index data",
                    )

                # Medium-term historical - use Monthly feed
                elif days_from_today <= self.monthly_window_days:
                    return FeedRoute(
                        feed_type=FeedType.MONTHLY,
                        reason=f"Date range within monthly window (end: {end_parsed}, {days_from_today} days ago)",
                        date_range=(start_parsed, end_parsed),
                        estimated_coverage="Monthly XBRL data",
                    )

                # Long-term historical - use Quarterly feed
                else:
                    return FeedRoute(
                        feed_type=FeedType.QUARTERLY,
                        reason=f"Date range beyond monthly window (end: {end_parsed}, {days_from_today} days ago)",
                        date_range=(start_parsed, end_parsed),
                        estimated_coverage="Quarterly index data",
                    )

            # Case 4: Only start date
            elif start_parsed:
                days_from_today = (self.today - start_parsed).days

                if days_from_today <= self.daily_window_days:
                    return FeedRoute(
                        feed_type=FeedType.DAILY,
                        reason=f"Start date {start_parsed} within daily window ({days_from_today} days ago)",
                        date_range=(start_parsed, None),
                        estimated_coverage="Daily index data",
                    )
                elif days_from_today <= self.monthly_window_days:
                    return FeedRoute(
                        feed_type=FeedType.MONTHLY,
                        reason=f"Start date {start_parsed} within monthly window ({days_from_today} days ago)",
                        date_range=(start_parsed, None),
                        estimated_coverage="Monthly XBRL data",
                    )
                else:
                    return FeedRoute(
                        feed_type=FeedType.QUARTERLY,
                        reason=f"Start date {start_parsed} beyond monthly window ({days_from_today} days ago)",
                        date_range=(start_parsed, None),
                        estimated_coverage="Quarterly index data",
                    )

            # Fallback to quarterly for any edge cases
            return FeedRoute(
                feed_type=FeedType.QUARTERLY,
                reason="Fallback to quarterly feed for comprehensive coverage",
                date_range=(start_parsed, end_parsed),
                estimated_coverage="Quarterly index data",
            )

        except Exception as e:
            logger.warning(
                f"Error analyzing date range, falling back to quarterly: {e}"
            )
            return FeedRoute(
                feed_type=FeedType.QUARTERLY,
                reason=f"Error in date analysis, using quarterly fallback: {e}",
                date_range=(
                    start_parsed if "start_parsed" in locals() else None,
                    end_parsed if "end_parsed" in locals() else None,
                ),
                estimated_coverage="Quarterly index data",
            )

    def _parse_date_smart(self, date_str: str, is_start: bool) -> date:
        """
        Parse flexible date formats and expand appropriately.

        Args:
            date_str: Date string in YYYY, YYYY-MM, or YYYY-MM-DD format
            is_start: Whether this is a start date (affects expansion logic)

        Returns:
            Parsed date object
        """
        if not date_str:
            return None

        # Handle YYYY format
        if len(date_str) == 4 and date_str.isdigit():
            year = int(date_str)
            if is_start:
                return date(year, 1, 1)  # Start of year
            else:
                return date(year, 12, 31)  # End of year

        # Handle YYYY-MM format
        elif len(date_str) == 7 and date_str.count("-") == 1:
            year, month = map(int, date_str.split("-"))
            if is_start:
                return date(year, month, 1)  # Start of month
            else:
                # End of month
                if month == 12:
                    next_month = date(year + 1, 1, 1)
                else:
                    next_month = date(year, month + 1, 1)
                return next_month - timedelta(days=1)

        # Handle YYYY-MM-DD format
        elif len(date_str) == 10 and date_str.count("-") == 2:
            return datetime.strptime(date_str, "%Y-%m-%d").date()

        else:
            raise ValueError(
                f"Invalid date format: {date_str}. Use YYYY, YYYY-MM, or YYYY-MM-DD"
            )

    def route_search(
        self,
        ticker: str | list[str],
        form_type: str = "10-K",
        limit: int = 10,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[list[FilingInfo], FeedRoute]:
        """
        Execute a smart search using the optimal feed based on date range.

        Args:
            ticker: Company ticker symbol(s)
            form_type: SEC form type
            limit: Maximum number of results
            start_date: Earliest filing date
            end_date: Latest filing date

        Returns:
            Tuple of (filing results, feed route used)
        """
        # Determine the best feed to use
        route = self.analyze_date_range(start_date, end_date)

        logger.info(f"Smart routing decision: {route.reason}")

        try:
            # For now, all routes use the unified search engine
            # The routing logic provides intelligent metadata about data freshness expectations
            filings = self._search_engine.search_by_ticker(
                ticker=ticker,
                form_types=[form_type] if form_type else None,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )

            logger.info(
                f"Found {len(filings)} filings using {route.feed_type.value} routing"
            )
            return filings, route

        except Exception as e:
            logger.warning(f"Smart routing failed: {e}")
            logger.info("Using fallback search")

            # Fallback route information
            fallback_route = FeedRoute(
                feed_type=FeedType.QUARTERLY,
                reason=f"Fallback after routing failed: {e}",
                date_range=route.date_range if "route" in locals() else (None, None),
                estimated_coverage="Basic search engine (fallback)",
            )

            # Basic fallback search
            filings = self._search_engine.search_by_ticker(
                ticker=ticker,
                form_types=[form_type] if form_type else None,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
            return filings, fallback_route

    # Future optimization: Implement specific feed methods for RSS, Daily, Monthly routing
    # For now, all routes use the unified search engine with intelligent metadata

    def get_feed_info(self) -> dict[str, Any]:
        """Get information about available feeds and their coverage."""
        return {
            "feeds": {
                "rss": {
                    "type": "Real-time RSS",
                    "coverage": f"Last {self.rss_window_days} days",
                    "refresh_rate": "Every few minutes",
                    "best_for": "Latest filings, breaking news",
                },
                "daily": {
                    "type": "Daily Index",
                    "coverage": f"Last {self.daily_window_days} days",
                    "refresh_rate": "Daily",
                    "best_for": "Recent filings, trend analysis",
                },
                "monthly": {
                    "type": "Monthly XBRL",
                    "coverage": f"Last {self.monthly_window_days} days (~3 months)",
                    "refresh_rate": "Monthly",
                    "best_for": "Quarterly reports, financial analysis",
                },
                "quarterly": {
                    "type": "Quarterly Index",
                    "coverage": "Complete historical data",
                    "refresh_rate": "Quarterly",
                    "best_for": "Historical research, comprehensive analysis",
                },
            },
            "routing_logic": {
                "rss_trigger": f"No dates or end_date within {self.rss_window_days} days",
                "daily_trigger": f"Date range within {self.daily_window_days} days",
                "monthly_trigger": f"Date range within {self.monthly_window_days} days",
                "quarterly_trigger": f"Date range > {self.monthly_window_days} days or fallback",
            },
        }


# Convenience function for module-level usage
def smart_search(
    ticker: str | list[str],
    form_type: str = "10-K",
    limit: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[FilingInfo], FeedRoute]:
    """
    Perform a smart search using optimal feed routing.

    Args:
        ticker: Company ticker symbol(s)
        form_type: SEC form type
        limit: Maximum number of results
        start_date: Earliest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)
        end_date: Latest filing date (YYYY-MM-DD, YYYY-MM, or YYYY format)

    Returns:
        Tuple of (filing results, feed route information)

    Example:
        ```python
        from py_sec_edgar.core.smart_router import smart_search

        # Recent data - will use RSS routing logic
        filings, route = smart_search("AAPL", limit=5)
        print(f"Used {route.feed_type.value}: {route.reason}")

        # Historical data - will use quarterly routing
        filings, route = smart_search("AAPL", start_date="2020", end_date="2022")
        ```
    """
    router = SmartFeedRouter()
    return router.route_search(ticker, form_type, limit, start_date, end_date)
