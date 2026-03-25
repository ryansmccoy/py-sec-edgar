import asyncio
import logging
import os
import sys

from py_sec_edgar.core.path_utils import ensure_file_directory, safe_join

from ..core.downloader import FilingDownloader
from ..core.url_utils import generate_full_index_url

# Now you can import
from ..logging_utils import (
    cleanup_logging,
    configure_module_logger,
    log_exception,
    setup_logging,
)
from ..settings import settings
from ..utilities import generate_folder_names_years_quarters
from .idx import convert_idx_to_csv, merge_idx_files  # Re-enabled merge functionality

#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"


def update_full_index_feed(
    save_idx_as_csv=True,
    skip_if_exists=False,
    custom_start_date=None,
    custom_end_date=None,
    merge_index=True,
):
    """
    Update SEC EDGAR full index files.

    Args:
        save_idx_as_csv: Whether to save index as CSV format
        skip_if_exists: Whether to skip if files already exist
        custom_start_date: Custom start date (MM/DD/YYYY format), overrides settings
        custom_end_date: Custom end date (MM/DD/YYYY format), overrides settings
        merge_index: Whether to merge all CSV files into unified search index
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting full index feed update...")
    logger.info(
        f"Parameters: save_idx_as_csv={save_idx_as_csv}, skip_if_exists={skip_if_exists}"
    )

    # Use custom dates if provided, otherwise use settings
    start_date = custom_start_date or settings.index_start_date
    end_date = custom_end_date or settings.index_end_date

    if custom_start_date or custom_end_date:
        logger.info(f"Using custom date range: {start_date} to {end_date}")

    try:
        # Direct implementation to avoid recursion
        downloader = FilingDownloader()

        # Get date ranges for processing
        dates_quarters = generate_folder_names_years_quarters(start_date, end_date)

        files_updated = 0

        # Process each quarter with progress tracking
        total_quarters = len(dates_quarters)
        logger.info(
            f"📊 Processing {total_quarters} quarters from {start_date} to {end_date}..."
        )

        quarters_processed = 0
        files_skipped = 0
        files_failed = 0

        for year, qtr in dates_quarters:
            # Extract quarter number from QTR format (e.g., "QTR2" -> 2)
            qtr_num = int(qtr.replace("QTR", ""))
            quarters_processed += 1

            # Log progress every 5 quarters or at start/end
            if (
                quarters_processed == 1
                or quarters_processed % 5 == 0
                or quarters_processed == total_quarters
            ):
                logger.info(
                    f"📈 Progress: {quarters_processed}/{total_quarters} quarters ({quarters_processed / total_quarters * 100:.1f}%) - Current: {year} Q{qtr_num}"
                )

            for file in settings.index_files:
                url, filepath = generate_full_index_url(int(year), qtr_num, file)

                # Skip if file exists and skip_if_exists is True
                if skip_if_exists and os.path.exists(filepath):
                    files_skipped += 1
                    logger.debug(f"Skipping existing file: {filepath}")
                    continue

                # Ensure directory exists
                ensure_file_directory(filepath)

                # Download the file using modern FilingDownloader
                logger.debug(f"⬇️ Downloading {year} Q{qtr_num} {file}: {url}")
                success = _download_file_sync(downloader, url, filepath)
                if success:
                    files_updated += 1
                    # Log file size for significant downloads
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
                        if file_size > 1:  # Only log if > 1MB
                            logger.debug(
                                f"✅ Downloaded {year} Q{qtr_num} {file} ({file_size:.1f}MB)"
                            )
                else:
                    files_failed += 1
                    logger.warning(
                        f"❌ Failed to download {year} Q{qtr_num} {file} from {url}"
                    )

        # Log comprehensive completion statistics
        logger.info("✅ Full index feed update completed successfully!")
        logger.info(
            f"📊 Summary: {files_updated} files updated, {files_skipped} skipped, {files_failed} failed"
        )
        logger.info(
            f"📅 Processed {quarters_processed} quarters from {start_date} to {end_date}"
        )
        if files_failed > 0:
            logger.warning(
                f"⚠️ {files_failed} files failed to download - some data may be incomplete"
            )

        # Handle CSV conversion if requested
        if save_idx_as_csv:
            logger.info("🔄 Converting index files to CSV format...")
            logger.info(
                "ℹ️ Note: CSV conversion enables fast local searching and merging"
            )
            _convert_legacy_full_index_to_csv(
                skip_if_exists=skip_if_exists, start_date=start_date, end_date=end_date
            )

        # Handle index merging if requested
        if merge_index and save_idx_as_csv:
            logger.info("🔗 Merging CSV files into unified search index...")
            logger.info("ℹ️ Note: Merged index enables fast search across all quarters")
            merge_success = merge_idx_files(force_rebuild=True)
            if merge_success:
                logger.info(
                    "✅ Index merge completed successfully - search index is now current"
                )
            else:
                logger.warning("⚠️ Index merge failed - search may use outdated data")

    except Exception as e:
        logger.error(f"Failed to update full index feed: {e}")
        raise


async def _download_file_async(
    downloader: FilingDownloader, url: str, filepath: str
) -> bool:
    """
    Download a file using the modern FilingDownloader.

    Args:
        downloader: FilingDownloader instance
        url: URL to download from
        filepath: Local path to save the file

    Returns:
        True if download successful, False otherwise
    """
    try:
        # Use fetch_content to get the data
        content = await downloader.fetch_content(url)

        # Write content to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return True
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to download {url} to {filepath}: {e}")
        return False


def _download_file_sync(downloader: FilingDownloader, url: str, filepath: str) -> bool:
    """
    Synchronous wrapper for downloading files using FilingDownloader.

    Args:
        downloader: FilingDownloader instance
        url: URL to download from
        filepath: Local path to save the file

    Returns:
        True if download successful, False otherwise
    """
    return asyncio.run(_download_file_async(downloader, url, filepath))


def _convert_legacy_full_index_to_csv(
    skip_if_exists=True, start_date=None, end_date=None
):
    """Legacy CSV conversion for backward compatibility.

    Args:
        skip_if_exists: If True, skip conversion if CSV already exists
        start_date: Custom start date, if None uses settings default
        end_date: Custom end date, if None uses settings default
    """
    logger = logging.getLogger(__name__)

    # Use custom dates if provided, otherwise fall back to settings
    conversion_start_date = start_date or settings.index_start_date
    conversion_end_date = end_date or settings.index_end_date

    dates_quarters = generate_folder_names_years_quarters(
        conversion_start_date, conversion_end_date
    )
    latest_full_index_master = safe_join(
        str(settings.full_index_data_dir), "master.idx"
    )

    files_converted = 0
    files_skipped = 0
    total_files_to_check = (
        len(dates_quarters) * len(settings.index_files) + 1
    )  # +1 for master

    logger.info(f"📋 Checking {total_files_to_check} index files for CSV conversion...")

    if os.path.exists(latest_full_index_master):
        csv_path = str(latest_full_index_master).replace(".idx", ".csv")
        if (
            not skip_if_exists
            or not os.path.exists(csv_path)
            or os.path.getmtime(csv_path) < os.path.getmtime(latest_full_index_master)
        ):
            logger.debug("🔄 Converting master index to CSV...")
            convert_idx_to_csv(latest_full_index_master, skip_if_exists=False)
            files_converted += 1
        else:
            files_skipped += 1
            logger.debug("⏭️ Skipping master index - CSV already exists and is current")

    files_processed = 0
    for year, qtr in dates_quarters:
        for file in settings.index_files:
            files_processed += 1
            # Extract quarter number from QTR format (e.g., "QTR2" -> 2)
            qtr_num = int(qtr.replace("QTR", ""))
            url, filepath = generate_full_index_url(int(year), qtr_num, file)
            if os.path.exists(filepath):
                csv_path = str(filepath).replace(".idx", ".csv")
                if (
                    not skip_if_exists
                    or not os.path.exists(csv_path)
                    or os.path.getmtime(csv_path) < os.path.getmtime(filepath)
                ):
                    logger.debug(f"🔄 Converting {year} Q{qtr_num} {file} to CSV...")
                    convert_idx_to_csv(filepath, skip_if_exists=False)
                    files_converted += 1

                    # Log progress every 10 conversions
                    if files_converted % 10 == 0:
                        logger.info(
                            f"📈 CSV conversion progress: {files_converted} files converted"
                        )
                else:
                    files_skipped += 1
                    logger.debug(
                        f"⏭️ Skipping {year} Q{qtr_num} {file} - CSV already current"
                    )
            else:
                logger.debug(f"⚠️ IDX file not found: {filepath}")

    # Log comprehensive CSV conversion summary
    total_processed = files_converted + files_skipped
    if files_converted == 0:
        logger.info(
            f"✅ All {total_processed} CSV files are already up to date - no conversion needed"
        )
    else:
        logger.info(
            f"✅ CSV conversion completed: {files_converted} files converted, {files_skipped} skipped"
        )
        logger.info(
            f"📊 Total processed: {total_processed} files checked for conversion"
        )


def display_configuration():
    """Display current configuration settings."""
    logger = logging.getLogger(__name__)

    print("🚀 SEC EDGAR Full Index Feed Update")
    print("=" * 60)
    print(f"📅 Date Range: {settings.index_start_date} to {settings.index_end_date}")
    print(f"📁 Output Directory: {settings.full_index_data_dir}")
    print(f"📋 Index Files: {settings.index_files}")
    print(f"🌐 Edgar Archives URL: {settings.edgar_archives_url}")
    print(f"🔄 Request Delay: {settings.request_delay}s")
    print("=" * 60)

    # Also log the configuration
    logger.info("Configuration Settings:")
    logger.info(
        f"   Date Range: {settings.index_start_date} to {settings.index_end_date}"
    )
    logger.info(f"   Output Directory: {settings.full_index_data_dir}")
    logger.info(f"   Index Files: {settings.index_files}")
    logger.info(f"   Edgar Archives URL: {settings.edgar_archives_url}")
    logger.info(f"   Request Delay: {settings.request_delay}s")


def run_full_index_update(save_as_csv=True, skip_existing=False, dry_run=False):
    """
    Run the full index update with proper error handling.

    Args:
        save_as_csv: Whether to convert .idx files to .csv
        skip_existing: Whether to skip existing files
        dry_run: If True, only show what would be done without executing

    Returns:
        bool: True if successful, False otherwise

    Raises:
        Exception: Re-raises any unexpected exceptions after logging
    """
    logger = logging.getLogger(__name__)

    try:
        logger.info("🎯 Starting full index feed update...")

        print("⚙️  Parameters:")
        print(f"   - Save as CSV: {save_as_csv}")
        print(f"   - Skip existing: {skip_existing}")
        print(f"   - Dry run: {dry_run}")
        print()

        if dry_run:
            logger.info("🔍 DRY RUN MODE - No actual downloads will occur")
            print("🔍 DRY RUN MODE - Showing what would be done...")

            # Show what quarters would be processed
            dates_quarters = generate_folder_names_years_quarters(
                settings.index_start_date, settings.index_end_date
            )
            print(f"📊 Would process {len(dates_quarters)} quarters:")
            for year, qtr in dates_quarters:
                print(f"   - {year}/{qtr}")

            logger.info("✅ Dry run completed successfully")
            return True

        # Actual execution
        update_full_index_feed(
            save_idx_as_csv=save_as_csv, skip_if_exists=skip_existing
        )

        logger.info("✅ Full index feed update completed successfully!")
        print("\n🎉 SUCCESS: Full index feed update completed!")
        print(f"📁 Check the output directory: {settings.full_index_data_dir}")
        return True

    except KeyboardInterrupt:
        logger.warning("🛑 Update interrupted by user (Ctrl+C)")
        print("\n⚠️  Update interrupted by user")
        return False

    except FileNotFoundError as e:
        log_exception(logger, "📁 File/directory not found", e)
        print(f"\n💥 FILE ERROR: {e}")
        return False

    except PermissionError as e:
        log_exception(logger, "🔒 Permission denied", e)
        print(f"\n💥 PERMISSION ERROR: {e}")
        print("   Try running as administrator or check file permissions")
        return False

    except ConnectionError as e:
        log_exception(logger, "🌐 Network connection error", e)
        print(f"\n💥 CONNECTION ERROR: {e}")
        print("   Check your internet connection and try again")
        return False

    except Exception as e:
        log_exception(logger, "❌ Unexpected error during full index update", e)
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        print("   Check the log file for detailed stack trace")
        raise  # Re-raise for debugging if needed


def main():
    """
    Main function with comprehensive error handling and logging setup.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    # Configuration
    LOG_FILE = "full_index_update.log"

    try:
        # Set up logging using the utility function
        setup_logging(log_level=logging.INFO, log_file=LOG_FILE)
        logger = configure_module_logger(__name__)

        # Display configuration
        display_configuration()

        # Run the update
        success = run_full_index_update(
            save_as_csv=True,
            skip_existing=False,
            dry_run=False,  # Change to True for testing
        )

        if success:
            logger.info("🏁 Program completed successfully")
            return 0
        else:
            logger.error("🚫 Program completed with errors")
            return 1

    except Exception as e:
        # Final catch-all for any setup errors
        print(f"\n💥 FATAL ERROR: {e}")
        try:
            logger = logging.getLogger(__name__)
            log_exception(logger, "Fatal error in main function", e, logging.CRITICAL)
        except:
            pass  # Logging might not be set up yet
        return 1

    finally:
        # Cleanup logging handlers using utility function
        cleanup_logging()


if __name__ == "__main__":
    """
    Test runner for update_full_index_feed function.

    Run this script directly to test the full index update:
    python full_index.py
    """
    import sys

    exit_code = main()
    sys.exit(exit_code)
