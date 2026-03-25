"""SEC Daily Filing Feed Processor

Processes recent SEC EDGAR daily filing indexes for up-to-date filing discovery.
Daily feeds contain filings from the last several business days and are ideal
for monitoring recent corporate activity and real-time filing analysis.

Key Features:
    📅 **Recent Coverage**: Last 3-5 business days of SEC filings
    🔄 **Real-time Updates**: Updated throughout business days as filings are processed
    🎯 **Focused Data**: Smaller datasets ideal for near real-time monitoring
    📊 **Full Metadata**: Complete filing information including CIK, ticker, form types
    🚀 **Fast Processing**: Optimized for quick data retrieval and processing

Data Coverage:
    - Daily index files from SEC EDGAR database
    - All form types: 10-K, 10-Q, 8-K, proxy statements, etc.
    - Recent filings only (typically last 3-5 business days)
    - Full filing metadata with direct download URLs

Usage Patterns:
    - Real-time filing monitoring
    - Recent activity analysis
    - Alert systems for new filings
    - Supplementing quarterly data with recent updates

Example:
    ```python
    from py_sec_edgar.feeds.daily import process_daily_feeds

    # Process recent daily filings
    recent_filings = process_daily_feeds(
        tickers=['AAPL', 'MSFT'],
        form_types=['10-K', '10-Q', '8-K'],
        days_back=3
    )
    ```

See Also:
    feeds.full_index: Comprehensive quarterly filing indexes
    feeds.rss: Real-time RSS feed processing
    core.url_utils: URL generation for daily index files
    workflows.daily_workflow: Complete daily processing workflow
"""

import logging
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

# Handle both relative imports (when run as module) and direct imports (when run directly)
try:
    from ..core.downloader import FilingDownloader
    from ..core.url_utils import generate_daily_index_urls
    from ..settings import settings

    # from ..core.url_utils import calculate_quarter  # Commented: unused import
    from ..utilities import edgar_and_local_differ
except ImportError:
    # Add parent directories to path for direct execution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    grandparent_dir = os.path.dirname(parent_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, grandparent_dir)

    import logging

    from py_sec_edgar.core.downloader import FilingDownloader
    from py_sec_edgar.settings import settings
import os
import sys

from py_sec_edgar.core.path_utils import create_temp_file, ensure_file_directory
from py_sec_edgar.core.url_utils import generate_daily_index_urls
from py_sec_edgar.utilities import edgar_and_local_differ

# Create module logger
logger = logging.getLogger(__name__)


#######################
# DAILY FILINGS FEEDS
# https://www.sec.gov/Archives/edgar/daily-index/
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=400&output=atom
# https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=8-K&type=8-K&owner=exclude&count=400&action=getcurrent

# NOTE: generate_daily_index_urls_and_filepaths() function has been moved to
# core/url_utils.py as generate_daily_index_urls() to eliminate duplication


def _parse_date(d: str | None) -> datetime | None:
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except Exception:
        logger.warning(f"Invalid date format '{d}'. Expected YYYY-MM-DD.")
        return None


def _get_last_business_day(from_date: datetime | None = None) -> datetime:
    """Get the last business day (Monday-Friday) with available SEC data.

    SEC typically publishes daily index files with a 1-2 day delay,
    so we need to go back further than just weekends.
    """
    if from_date is None:
        from_date = datetime.today()

    # Start by going back at least 1 day to account for publishing delay
    check_date = from_date - timedelta(days=1)

    # Keep going back until we find a business day that's at least 2 days ago
    # This accounts for both weekends and SEC publishing delays
    while check_date.weekday() >= 5 or (from_date - check_date).days < 2:
        check_date = check_date - timedelta(days=1)
        # Safety check to avoid infinite loop
        if (from_date - check_date).days > 10:
            break

    return check_date


def _compute_date_window(
    start_date: str | None,
    end_date: str | None,
    days_back: int | None,
    default_years: int = 2,
    max_weekdays: int | None = 100,
) -> tuple[datetime, datetime, int]:
    """Compute an effective date window and a cap on weekdays to process."""
    today = datetime.today()
    last_business_day = _get_last_business_day(today)
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    if start_dt and not end_dt:
        end_dt = last_business_day
    if end_dt and not start_dt:
        start_dt = end_dt - timedelta(days=7)
    if start_dt and end_dt and start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    if not start_dt and not end_dt:
        if days_back is not None:
            # When using days_back, start from last business day and go back
            end_dt = last_business_day
            start_dt = last_business_day - timedelta(days=days_back - 1)
        else:
            start_dt = last_business_day - timedelta(days=365 * default_years)
            end_dt = last_business_day

    cap = max_weekdays if (isinstance(max_weekdays, int) and max_weekdays > 0) else 100
    # Defensive: ensure non-None for typing
    assert start_dt is not None and end_dt is not None
    return start_dt, end_dt, cap


def update_daily_files(
    auto_triggered: bool = False,
    task_logger=None,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    days_back: int | None = None,
    max_weekdays: int | None = 100,
):
    """Update daily index files from SEC EDGAR archive.

    Args:
        auto_triggered: If True, respects settings.disable_auto_daily_updates.
        task_logger: Optional external logger to integrate with task systems.
        start_date: YYYY-MM-DD inclusive; overrides days_back if paired with end_date.
        end_date: YYYY-MM-DD inclusive; overrides days_back if paired with start_date.
        days_back: Rolling window from today when explicit dates are not provided.
        max_weekdays: Safety cap on number of weekdays to process.
    """

    # Use task logger if provided, otherwise use module logger
    log = task_logger if task_logger else logger

    # Skip if this is an auto-triggered update and auto-updates are disabled
    if auto_triggered and getattr(settings, "disable_auto_daily_updates", True):
        message = "Auto daily updates are disabled. Skipping automatic update."
        log.info(message)
        print(message)  # Keep print for direct execution
        return

    log.info("Starting daily index files update")

    start_dt, end_dt, cap = _compute_date_window(
        start_date, end_date, days_back, default_years=2, max_weekdays=max_weekdays
    )
    sec_dates = pd.date_range(start_dt.date(), end_dt.date())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)

    log.info(
        f"Processing up to {min(cap, len(sec_dates_weekdays))} weekdays from {start_dt.date()} to {end_dt.date()}"
    )

    # consecutive_days_same = 0  # Commented: unused variable
    files_processed = 0
    files_downloaded = 0
    files_updated = 0
    files_unchanged = 0

    for i, day in enumerate(sec_dates_weekdays):
        # Limit to cap for safety
        if i >= cap:
            break

        daily_files = generate_daily_index_urls(day)
        log.info(
            f"Processing {len(daily_files)} files for date {day.strftime('%Y-%m-%d')}"
        )

        for daily_url, daily_local_filepath in daily_files:
            try:
                files_processed += 1
                filename = os.path.basename(daily_local_filepath)

                # Ensure directory exists using unified path manager
                ensure_file_directory(daily_local_filepath)

                # Create temp filepath for download using unified temp file creator
                temp_filepath = create_temp_file(
                    suffix=f"_{os.path.basename(daily_local_filepath)}",
                    prefix="temp_daily_",
                    directory=os.path.dirname(daily_local_filepath),
                )

                if os.path.exists(daily_local_filepath):
                    log.info(f"Checking for updates: {filename}")
                    # Try to download to temp file first to compare
                    downloader = FilingDownloader()
                    import asyncio

                    try:
                        content = asyncio.run(downloader.fetch_content(daily_url))
                        with open(temp_filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        success = True
                    except Exception as e:
                        log.error(f"Failed to download {filename}: {e}")
                        success = False

                    if success:
                        # Now compare files using the edgar_and_local_differ function
                        status = edgar_and_local_differ(daily_url, daily_local_filepath)
                        if not status:  # Files are the same
                            # consecutive_days_same += 1  # Commented: unused variable
                            files_unchanged += 1
                            log.info(f"File unchanged: {filename}")
                        else:
                            # consecutive_days_same = 0  # Commented: unused variable
                            files_updated += 1
                            log.info(f"File updated: {filename}")
                    else:
                        log.error(f"Failed to download {filename} from {daily_url}")
                        continue
                else:
                    log.info(f"Downloading new file: {filename}")
                    # File doesn't exist, download directly
                    downloader = FilingDownloader()
                    import asyncio

                    try:
                        content = asyncio.run(downloader.fetch_content(daily_url))
                        ensure_file_directory(daily_local_filepath)
                        with open(daily_local_filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        success = True
                    except Exception as e:
                        log.error(f"Failed to download {filename}: {e}")
                        success = False
                    if success:
                        # consecutive_days_same = 0  # Commented: unused variable
                        files_downloaded += 1
                        log.info(f"Successfully downloaded new file: {filename}")
                    else:
                        log.error(f"Failed to download {filename} from {daily_url}")

            except Exception as e:
                log.error(
                    f"Error processing {os.path.basename(daily_local_filepath)}: {str(e)}"
                )
                continue

    # Log summary
    log.info("Daily index update completed:")
    log.info(f"  - Files processed: {files_processed}")
    log.info(f"  - New files downloaded: {files_downloaded}")
    log.info(f"  - Files updated: {files_updated}")
    log.info(f"  - Files unchanged: {files_unchanged}")

    return {
        "files_processed": files_processed,
        "files_downloaded": files_downloaded,
        "files_updated": files_updated,
        "files_unchanged": files_unchanged,
    }


def update_daily_index_feed(days_back: int = 1, skip_if_exists: bool = True):
    """
    Modern wrapper using unified FilingFeedManager.

    Args:
        days_back: Number of days back to process
        skip_if_exists: Skip download if files already exist (handled by manager)
    """
    logger.info(
        f"Updating daily index feed for last {days_back} days using unified manager..."
    )

    try:
        # Use unified feed manager for consistent interface
        from ..core.feed_manager import FilingFeedManager

        manager = FilingFeedManager()
        result = manager.update_daily(days_back=days_back)

        if result.success:
            logger.info(
                f"Daily index feed update completed successfully: {result.files_updated} files updated"
            )
        else:
            logger.error(f"Daily index feed update failed: {result.error}")
            raise Exception(result.error)

    except Exception as e:
        logger.error(f"Failed to update daily index feed: {e}")
        raise


if __name__ == "__main__":
    """
    Test runner for update_daily_files function.

    Run this script directly to test the daily update:
    python daily.py
    """
    import sys

    update_daily_files()
