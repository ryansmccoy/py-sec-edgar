"""
Monthly XBRL Feed Processing - Unified Version

Enhanced module for downloading and processing SEC monthly XBRL feeds
using the unified FilingDownloader system and unified URL generation.
"""

import logging
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd

from py_sec_edgar.core.path_utils import ensure_file_directory

from ..core.downloader import FilingDownloader
from ..settings import settings
from ..utilities import flattenDict, read_xml_feedparser

# Configure module-specific logger
logger = logging.getLogger(__name__)


# NOTE: generate_monthly_index_url_and_filepaths() function has been moved to
# core/url_utils.py as generate_monthly_index_url() to eliminate duplication


# Backward compatibility wrapper
def generate_monthly_index_url_and_filepaths(day):
    """
    Backward compatibility wrapper for generate_monthly_index_url.

    This function has been moved to core/url_utils.py but we provide
    this wrapper for any legacy code that still calls the old function.

    Args:
        day: datetime object

    Returns:
        Tuple of (url, filepath)
    """
    from ..core.url_utils import generate_monthly_index_url

    return generate_monthly_index_url(day)


# COMMENTED OUT - Dead code testing
# async def download_and_flatten_monthly_xbrl_filings_list_unified() -> None:
#     """
#     Download and process all available monthly XBRL filing lists using unified downloader
#
#     This function uses the unified FilingDownloader for all network operations
#     and provides enhanced error handling and progress reporting.
#     """
#     logger.info("Starting monthly XBRL feed download and processing (unified)")
#     start_time = time.time()
#     downloader = FilingDownloader()
#     # ... rest of function commented out for dead code testing


async def _process_monthly_xml_file_unified(
    url: str, downloader: FilingDownloader
) -> bool:
    """
    Process a single monthly XML file using the unified downloader

    Args:
        url: URL of the XML file to process
        downloader: FilingDownloader instance for downloading

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        filename = url.split("/")[-1]
        fullfilepath = settings.monthly_data_dir / filename
        xlsx_filepath = fullfilepath.with_suffix(".xlsx")

        # Download XML file if needed
        if not fullfilepath.exists() or url == _get_most_recent_url():
            logger.info(f"Downloading: {fullfilepath.name}")

            try:
                # Use unified downloader to fetch content and save
                content = await downloader.fetch_content(url)

                if not content:
                    logger.error(f"No content received for {filename}")
                    return False

                # Save content to file using unified path manager
                ensure_file_directory(fullfilepath)
                with open(fullfilepath, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.debug(f"Successfully downloaded and saved {filename}")
            except Exception as e:
                logger.error(f"Error downloading {filename}: {e}")
                return False
        else:
            logger.debug(f"Using existing XML file: {fullfilepath}")

        # Process XML to XLSX if needed
        if not xlsx_filepath.exists():
            logger.info(f"Converting XML to XLSX: {xlsx_filepath.name}")

            feeds = read_xml_feedparser(str(fullfilepath))
            if not feeds or not hasattr(feeds, "entries"):
                logger.warning(f"No valid feed entries found in {filename}")
                return False

            processed_entries = []

            for entry in feeds.entries:
                try:
                    feed_dict = flattenDict(entry)
                    df_entry = pd.DataFrame.from_dict(feed_dict, orient="index")
                    df_entry.columns = ["VALUES"]
                    df_entry.index = [
                        idx.replace(".", "_").replace(":", "_").upper()
                        for idx in df_entry.index.tolist()
                    ]
                    df_entry = df_entry.T

                    # Extract ticker information
                    if "EDGAR_XBRLFILE_FILE" in df_entry.columns:
                        match = (
                            df_entry["EDGAR_XBRLFILE_FILE"]
                            .str.replace("-.+", "", regex=True)
                            .str.upper()
                            .iloc[0]
                        )

                        if "." in match or len(match) > 13:
                            df_entry["TICKER"] = "--"
                        else:
                            df_entry["TICKER"] = match
                    else:
                        df_entry["TICKER"] = "--"

                    processed_entries.append(df_entry)

                except Exception as e:
                    logger.warning(f"Error processing entry in {filename}: {e}")
                    continue

            if processed_entries:
                try:
                    final_df = pd.concat(processed_entries, ignore_index=True)

                    # Clean column names
                    new_columns = [
                        col.replace(".", "_").replace(":", "_").lower()
                        for col in final_df.columns.tolist()
                    ]
                    final_df.columns = new_columns

                    # Add metadata
                    final_df["source_filename"] = filename
                    final_df["source_import_timestamp"] = datetime.now()

                    # Apply data filtering and enhancement
                    final_df = _filter_and_enhance_data(final_df)

                    final_df.to_excel(xlsx_filepath, index=False)
                    logger.info(
                        f"Exported {len(processed_entries)} entries to: {xlsx_filepath.name}"
                    )
                    return True
                except Exception as e:
                    logger.error(f"Error saving XLSX file {xlsx_filepath}: {e}")
                    return False
            else:
                logger.warning(f"No valid entries to export for {filename}")
                return False
        else:
            logger.debug(f"Using existing XLSX file: {xlsx_filepath}")
            return True

    except Exception as e:
        logger.error(f"Error processing monthly XML file {url}: {e}", exc_info=True)
        return False


def _filter_and_enhance_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply data filtering and enhancement to monthly XBRL data

    Args:
        df: Raw DataFrame from XBRL processing

    Returns:
        Enhanced and filtered DataFrame
    """
    try:
        logger.debug(f"Initial dataframe shape: {df.shape}")
        logger.debug(f"Columns: {df.columns.tolist()}")

        # Convert pubdate to datetime if it exists
        if "pubdate" in df.columns:
            df["pubdate"] = pd.to_datetime(df["pubdate"], errors="coerce")

            # Filter for current month data (monthly feeds are cumulative)
            current_month = datetime.now().month
            current_year = datetime.now().year
            initial_count = len(df)

            df = df[
                (df["pubdate"].dt.month == current_month)
                & (df["pubdate"].dt.year == current_year)
            ]

            logger.debug(
                f"Filtered to current month: {len(df)} rows (was {initial_count})"
            )

        # Remove duplicates if ticker and period columns exist
        dedup_columns = []
        if "ticker" in df.columns:
            dedup_columns.append("ticker")
        if "edgar_xbrlfile_period" in df.columns:
            dedup_columns.append("edgar_xbrlfile_period")

        if dedup_columns:
            initial_count = len(df)
            df.drop_duplicates(subset=dedup_columns, keep="last", inplace=True)
            logger.debug(f"After deduplication: {len(df)} rows (was {initial_count})")

        # Filter for relevant form types
        if "edgar_xbrlfile_formtype" in df.columns:
            initial_count = len(df)
            df = df[df["edgar_xbrlfile_formtype"].isin(["10-K", "10-Q"])]
            logger.debug(
                f"After form type filtering (10-K/10-Q): {len(df)} rows (was {initial_count})"
            )

        logger.debug("Sample of processed data:")
        if len(df) > 0:
            logger.debug(df.head().to_string())
        else:
            logger.warning("No data remaining after filtering")

        return df

    except Exception as e:
        logger.error(f"Error in data filtering: {e}")
        return df  # Return original data if filtering fails


def _get_most_recent_url() -> str | None:
    """
    Get the URL of the most recent monthly file

    Returns:
        str: Most recent URL or None if not available
    """
    try:
        # This would need to be determined from the current processing context
        # For now, we'll use a simple heuristic
        current_date = datetime.now()
        basename = f"xbrlrss-{current_date.year}-{current_date.month:02d}.xml"
        return urljoin(settings.edgar_monthly_index_url, basename)
    except Exception:
        return None


def update_monthly_xbrl_feed(months_back: int = 1, skip_if_exists: bool = True) -> None:
    """
    Modern wrapper using unified FilingFeedManager.

    Args:
        months_back: Number of months to look back
        skip_if_exists: Whether to skip existing files (handled by manager)
    """
    logger.info(
        f"Updating monthly XBRL feed for last {months_back} months using unified manager..."
    )

    try:
        # Use unified feed manager for consistent interface
        from ..core.feed_manager import FilingFeedManager

        manager = FilingFeedManager()
        result = manager.update_monthly(months_back=months_back)

        if result.success:
            logger.info(
                f"Monthly XBRL feed update completed successfully: {result.files_updated} files updated"
            )
        else:
            logger.error(f"Monthly XBRL feed update failed: {result.error}")
            raise Exception(result.error)

    except Exception as e:
        logger.error(f"Monthly XBRL feed update failed: {e}")
        raise
