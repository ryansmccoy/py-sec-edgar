import logging
import os
import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin

import pandas as pd

# Handle both relative imports (when run as module) and direct imports (when run directly)
try:
    from ..settings import settings
    from ..utilities import RetryRequest, edgar_and_local_differ
except ImportError:
    # Add parent directories to path for direct execution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    grandparent_dir = os.path.dirname(parent_dir)
    sys.path.insert(0, parent_dir)
    sys.path.insert(0, grandparent_dir)

    from py_sec_edgar.settings import settings
    from py_sec_edgar.utilities import RetryRequest, edgar_and_local_differ

# Create module logger
logger = logging.getLogger(__name__)


#######################
# DAILY FILINGS FEEDS
# https://www.sec.gov/Archives/edgar/daily-index/
# https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=400&output=atom
# https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK=&type=8-K&type=8-K&owner=exclude&count=400&action=getcurrent


def generate_daily_index_urls_and_filepaths(day):
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    daily_files_templates = ["master", "form", "company", "crawler", "sitemap"]
    date_formated = datetime.strftime(day, "%Y%m%d")
    # Calculate quarter correctly: (month - 1) // 3 + 1
    quarter = (day.month - 1) // 3 + 1
    daily_files = []
    for template in daily_files_templates:
        download_url = urljoin(edgar_url, f"daily-index/{day.year}/QTR{quarter}/{template}.{date_formated}.idx")
        local_filepath = os.path.join(str(settings.daily_index_data_dir), f"{day.year}", f"QTR{quarter}", f"{template}.{date_formated}.idx")
        daily_files.append((download_url, local_filepath))
    daily_files[-1] = (daily_files[-1][0].replace("idx", "xml"),
                       daily_files[-1][1].replace("idx", "xml"))
    return daily_files


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
    if auto_triggered and getattr(settings, 'disable_auto_daily_updates', True):
        message = "Auto daily updates are disabled. Skipping automatic update."
        log.info(message)
        print(message)  # Keep print for direct execution
        return

    log.info("Starting daily index files update")

    start_dt, end_dt, cap = _compute_date_window(start_date, end_date, days_back, default_years=2, max_weekdays=max_weekdays)
    sec_dates = pd.date_range(start_dt.date(), end_dt.date())
    sec_dates_weekdays = sec_dates[sec_dates.weekday < 5]
    sec_dates_weekdays = sec_dates_weekdays.sort_values(ascending=False)

    log.info(f"Processing up to {min(cap, len(sec_dates_weekdays))} weekdays from {start_dt.date()} to {end_dt.date()}")

    consecutive_days_same = 0
    files_processed = 0
    files_downloaded = 0
    files_updated = 0
    files_unchanged = 0

    for i, day in enumerate(sec_dates_weekdays):
        # Limit to cap for safety
        if i >= cap:
            break

        daily_files = generate_daily_index_urls_and_filepaths(day)
        log.info(f"Processing {len(daily_files)} files for date {day.strftime('%Y-%m-%d')}")

        for daily_url, daily_local_filepath in daily_files:
            try:
                files_processed += 1
                filename = os.path.basename(daily_local_filepath)

                # Ensure directory exists
                os.makedirs(os.path.dirname(daily_local_filepath), exist_ok=True)

                # Create temp filepath for download
                temp_filepath = os.path.join(os.path.dirname(daily_local_filepath),
                                           f"temp_{os.path.basename(daily_local_filepath)}")

                if os.path.exists(daily_local_filepath):
                    log.info(f"Checking for updates: {filename}")
                    # Try to download to temp file first to compare
                    g = RetryRequest()
                    success = g.download_file(daily_url, temp_filepath)

                    if success:
                        # Now compare files using the edgar_and_local_differ function
                        status = edgar_and_local_differ(daily_url, daily_local_filepath)
                        if not status:  # Files are the same
                            consecutive_days_same += 1
                            files_unchanged += 1
                            log.info(f"File unchanged: {filename}")
                        else:
                            consecutive_days_same = 0
                            files_updated += 1
                            log.info(f"File updated: {filename}")
                    else:
                        log.error(f"Failed to download {filename} from {daily_url}")
                        continue
                else:
                    log.info(f"Downloading new file: {filename}")
                    # File doesn't exist, download directly
                    g = RetryRequest()
                    success = g.download_file(daily_url, daily_local_filepath)
                    if success:
                        consecutive_days_same = 0
                        files_downloaded += 1
                        log.info(f"Successfully downloaded new file: {filename}")
                    else:
                        log.error(f"Failed to download {filename} from {daily_url}")

            except Exception as e:
                log.error(f"Error processing {os.path.basename(daily_local_filepath)}: {str(e)}")
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
        "files_unchanged": files_unchanged
    }

if __name__ == "__main__":
    """
    Test runner for update_full_index_feed function.
    
    Run this script directly to test the full index update:
    python full_index.py
    """
    import sys

    update_daily_files()
