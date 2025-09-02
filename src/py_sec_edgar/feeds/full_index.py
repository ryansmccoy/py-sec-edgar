import logging
import os
import sys
from urllib.parse import urljoin

sys.path.append(r'b:\github\sec-edgar-app\packages')

# Now you can import
from ..logging_utils import (
    cleanup_logging,
    configure_module_logger,
    log_exception,
    setup_logging,
)
from ..settings import settings
from ..utilities import RetryRequest, generate_folder_names_years_quarters
from .idx import convert_idx_to_csv, merge_idx_files

#######################
# FULL-INDEX FILINGS FEEDS (TXT)
# https://www.sec.gov/Archives/edgar/full-index/
# "./{YEAR}/QTR{NUMBER}/"


def update_full_index_feed(save_idx_as_csv=True, skip_if_exists=False):
    logger = logging.getLogger(__name__)

    logger.info("Starting full index feed update...")
    logger.info(f"Parameters: save_idx_as_csv={save_idx_as_csv}, skip_if_exists={skip_if_exists}")

    dates_quarters = generate_folder_names_years_quarters(settings.index_start_date, settings.index_end_date)
    logger.info(f"Processing {len(dates_quarters)} quarters: {dates_quarters}")

    latest_full_index_master = os.path.join(str(settings.full_index_data_dir), "master.idx")
    logger.info(f"Master index file path: {latest_full_index_master}")

    if os.path.exists(latest_full_index_master):
        logger.info(f"Removing existing master index file: {latest_full_index_master}")
        os.remove(latest_full_index_master)

    g = RetryRequest()
    logger.info(f"Downloading master index from: {settings.edgar_full_master_url}")

    g.download_file(settings.edgar_full_master_url, latest_full_index_master)
    logger.info(f"Master index downloaded successfully to: {latest_full_index_master}")

    logger.info("Converting master index to CSV...")
    convert_idx_to_csv(latest_full_index_master)
    logger.info("Master index CSV conversion completed")

    for year, qtr in dates_quarters:
        logger.info(f"Processing quarter: {year}/{qtr}")

        # settings.index_files = ['master.idx']
        for i, file in enumerate(settings.index_files):
            logger.info(f"Processing file {i+1}/{len(settings.index_files)}: {file}")

            filepath = os.path.join(str(settings.full_index_data_dir), year, qtr, file)
            csv_filepath = filepath.replace('.idx', '.csv')

            logger.info(f"Target file path: {filepath}")
            logger.info(f"Target CSV path: {csv_filepath}")

            if os.path.exists(filepath) and skip_if_exists == False:
                logger.info(f"Removing existing idx file: {filepath}")
                os.remove(filepath)

            if os.path.exists(csv_filepath) and skip_if_exists == False:
                logger.info(f"Removing existing CSV file: {csv_filepath}")
                os.remove(csv_filepath)

            if not os.path.exists(filepath):
                logger.info("File doesn't exist, proceeding with download...")

                if not os.path.exists(os.path.dirname(filepath)):
                    logger.info(f"Creating directory: {os.path.dirname(filepath)}")
                    os.makedirs(os.path.dirname(filepath))

                url = urljoin(settings.edgar_archives_url, f'edgar/full-index/{year}/{qtr}/{file}')
                logger.info(f"Downloading from URL: {url}")

                g.download_file(url, filepath)
                logger.info(f"Downloaded successfully to: {filepath}")

                if save_idx_as_csv == True:
                    logger.info(f'Converting idx to csv: {filepath} -> {csv_filepath}')
                    convert_idx_to_csv(filepath)
                    logger.info(f'CSV conversion completed: {csv_filepath}')
            else:
                logger.info(f"Skipping existing file: {filepath}")

    logger.info('Starting to merge IDX files...')
    merge_idx_files()
    logger.info('IDX files merge completed successfully')
    logger.info('Full index download process completed!')
    logger.info(f'All files saved to: {settings.full_index_data_dir}')


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
    logger.info(f"   Date Range: {settings.index_start_date} to {settings.index_end_date}")
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
                settings.index_start_date,
                settings.index_end_date
            )
            print(f"📊 Would process {len(dates_quarters)} quarters:")
            for year, qtr in dates_quarters:
                print(f"   - {year}/{qtr}")

            logger.info("✅ Dry run completed successfully")
            return True

        # Actual execution
        update_full_index_feed(
            save_idx_as_csv=save_as_csv,
            skip_if_exists=skip_existing
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
    LOG_FILE = 'full_index_update.log'

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
            dry_run=False  # Change to True for testing
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
