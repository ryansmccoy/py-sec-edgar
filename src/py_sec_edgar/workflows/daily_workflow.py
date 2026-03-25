"""Daily SEC EDGAR workflow script

This is the primary execution point for running the Daily filing updates.
It downloads daily index files and processes filings.
"""

import logging
import os
from datetime import datetime, timedelta

import click
import pandas as pd

import py_sec_edgar.feeds.daily

from ..core.url_utils import generate_filing_url

# Use centralized logging configuration (DRY solution)
from ..logging_utils import setup_workflow_logging
from ..process import FilingProcessor
from ..settings import settings
from ..utilities import cik_column_to_list

# Set up logging using centralized utility
logger = setup_workflow_logging(
    log_filename="daily_workflow.log", log_level="INFO", force_reconfigure=False
)


def run_daily_workflow_with_dates(
    ticker_list: str | None = None,
    form_list: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    download: bool = True,
    extract: bool = False,
) -> dict:
    """Enhanced daily workflow that supports start/end date ranges.

    Args:
        ticker_list: Path to ticker CSV file or None
        form_list: List of form types to filter
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        download: Whether to download files
        extract: Whether to extract file contents

    Returns:
        Summary dictionary with processing results
    """
    logger.info("Starting enhanced SEC EDGAR daily data processing with date range...")
    logger.info(
        f"Parameters: ticker_list={ticker_list}, form_list={form_list}, start_date={start_date}, end_date={end_date}, download={download}, extract={extract}"
    )

    if not download:
        logger.info("⚠️  Download is disabled - skipping daily index feed download")
    else:
        # Downloads the daily index files from SEC Edgar website for the date range
        logger.info("Starting daily index feed download for date range...")
        try:
            py_sec_edgar.feeds.daily.update_daily_files(
                start_date=start_date, end_date=end_date
            )
            logger.info("Daily index feed download completed")
        except Exception as e:
            logger.warning(f"Failed to download daily index files: {e}")
            logger.info("Continuing with existing data if available...")

    # Used to convert CIK to Tickers
    logger.info("Loading CIK to ticker mapping...")
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))
    logger.info(f"Loaded {len(df_cik_tickers)} CIK-ticker mappings")

    # Convert date strings to datetime objects for processing
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # Generate date range for processing
    date_range = pd.date_range(start_dt, end_dt, freq="D")
    business_days = [d for d in date_range if d.weekday() < 5]  # Monday=0, Friday=4

    logger.info(
        f"Processing {len(business_days)} business days from {start_date} to {end_date}"
    )

    # Load daily IDX files for the specified date range
    logger.info("Loading daily IDX files for date range...")
    daily_filings = []
    files_processed = 0
    files_found = 0

    for target_date in business_days:
        daily_files = py_sec_edgar.core.url_utils.generate_daily_index_urls(target_date)

        for url, filepath in daily_files:
            if os.path.exists(filepath) and "master" in filepath:
                logger.info(f"Processing daily file: {filepath}")
                files_found += 1
                try:
                    # Read the daily master file
                    df_daily = pd.read_csv(
                        filepath,
                        sep="|",
                        names=[
                            "CIK",
                            "Company Name",
                            "Form Type",
                            "Date Filed",
                            "Filename",
                        ],
                        skiprows=11,
                    )  # Skip header lines in SEC daily files
                    df_daily["Date Filed"] = pd.to_datetime(df_daily["Date Filed"])
                    daily_filings.append(df_daily)
                    files_processed += 1
                    logger.info(f"Loaded {len(df_daily)} filings from {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    if not daily_filings:
        logger.error(
            f"No daily filing data found for date range {start_date} to {end_date}"
        )
        logger.error("This may indicate:")
        logger.error("1. No index files downloaded for this date range")
        logger.error("2. Date range includes only weekends/holidays")
        logger.error("3. Network issues during download")
        logger.error("Try running with --download to fetch the required index files")
        return {
            "status": "error",
            "message": "No daily filing data found",
            "files_found": files_found,
            "files_processed": files_processed,
            "date_range": f"{start_date} to {end_date}",
            "business_days": len(business_days),
        }

    # Combine all daily filings
    df_merged_daily = pd.concat(daily_filings, ignore_index=True).sort_values(
        "Date Filed", ascending=False
    )
    logger.info(f"Combined daily data: {len(df_merged_daily)} filing records")

    # Filter by ticker list if specified
    if ticker_list:
        logger.info(f"Filtering by ticker list: {ticker_list}")
        try:
            df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
            df_cik_tickers_filtered = df_cik_tickers[
                df_cik_tickers["SYMBOL"].isin(df_ticker_list)
            ]
            logger.info(f"Filtered to {len(df_cik_tickers_filtered)} companies")

            # Filter filings by CIK
            cik_list = cik_column_to_list(df_cik_tickers_filtered)
            df_merged_daily = df_merged_daily[df_merged_daily["CIK"].isin(cik_list)]
            logger.info(f"Filtered filings to {len(df_merged_daily)} records")
        except Exception as e:
            logger.warning(f"Failed to apply ticker filter: {e}")

    # Filter by form types if specified
    if form_list:
        logger.info(f"Filtering by forms: {form_list}")
        df_merged_daily = df_merged_daily[df_merged_daily["Form Type"].isin(form_list)]
        logger.info(f"Filtered to {len(df_merged_daily)} filings")

    # Create URLs for filings using unified URL generator
    df_filings = df_merged_daily.assign(
        url=df_merged_daily["Filename"].apply(lambda x: generate_filing_url(x))
    )
    logger.info(f"Generated URLs for {len(df_filings)} filings")

    if len(df_filings) == 0:
        logger.warning("No filings match the specified criteria")
        return {
            "status": "completed",
            "message": "No filings match the specified criteria",
            "total_filings": 0,
            "processed_filings": 0,
            "date_range": f"{start_date} to {end_date}",
            "files_found": files_found,
            "files_processed": files_processed,
        }

    # Initialize the FilingProcessor with template patterns
    filing_data_dir = str(
        settings.base_dir / "data" / "Archives" / "edgar" / "data" / "CIK" / "FOLDER"
    )
    logger.info(f"Filing data directory template: {filing_data_dir}")
    filing_broker = FilingProcessor(
        filing_data_dir=filing_data_dir,
        edgar_Archives_url=settings.edgar_archives_url,
        download=download,
        extract=extract,
    )

    logger.info(f"Starting to process {len(df_filings)} daily filings...")
    processed_count = 0

    for i, sec_filing in df_filings.iterrows():
        logger.info(
            f"Processing filing {i + 1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}"
        )
        # Log filing details in a clean format
        logger.info(
            f"📄 {sec_filing['Company Name']} | {sec_filing['Form Type']} | "
            f"Filed: {sec_filing['Date Filed'].strftime('%Y-%m-%d')} | File: {sec_filing['Filename'].split('/')[-1]}"
        )

        try:
            filing_broker.process(sec_filing)
            processed_count += 1
        except Exception as e:
            logger.warning(f"Failed to process filing {sec_filing['Filename']}: {e}")

    logger.info("Daily filings processing completed!")

    return {
        "status": "completed",
        "total_filings": len(df_filings),
        "processed_filings": processed_count,
        "date_range": f"{start_date} to {end_date}",
        "business_days": len(business_days),
        "files_found": files_found,
        "files_processed": files_processed,
    }


@click.command()
@click.option("--ticker-list", default=str(settings.ticker_list_filepath))
@click.option("--form-list", default=True)
@click.option(
    "--custom-forms",
    default=None,
    help="Custom forms list (comma-separated) to override settings",
)
@click.option(
    "--days-back", default=1, help="Number of days back to process (default: 1)"
)
@click.option(
    "--download/--no-download",
    default=False,
    help="Download filing files (default: False)",
)
@click.option(
    "--extract/--no-extract",
    default=False,
    help="Extract filing contents (default: False)",
)
def main(ticker_list, form_list, custom_forms, days_back, download, extract):
    logger.info("Starting SEC EDGAR daily data processing...")
    logger.info(
        f"Parameters: ticker_list={ticker_list}, form_list={form_list}, custom_forms={custom_forms}, days_back={days_back}, download={download}, extract={extract}"
    )

    if not download:
        logger.info("⚠️  Download is disabled - skipping daily index feed download")
    else:
        # Downloads the daily index files from SEC Edgar website
        logger.info("Starting daily index feed download...")
        py_sec_edgar.feeds.daily.update_daily_files()
        logger.info("Daily index feed download completed")

    # Used to convert CIK to Tickers
    logger.info("Loading CIK to ticker mapping...")
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))
    logger.info(f"Loaded {len(df_cik_tickers)} CIK-ticker mappings")

    # Load daily IDX files for the specified date range
    logger.info("Loading daily IDX files...")
    daily_filings = []

    for days_ago in range(days_back):
        target_date = datetime.now() - timedelta(days=days_ago)
        daily_files = py_sec_edgar.core.url_utils.generate_daily_index_urls(target_date)

        for url, filepath in daily_files:
            if os.path.exists(filepath) and "master" in filepath:
                logger.info(f"Processing daily file: {filepath}")
                try:
                    # Read the daily master file
                    df_daily = pd.read_csv(
                        filepath,
                        sep="|",
                        names=[
                            "CIK",
                            "Company Name",
                            "Form Type",
                            "Date Filed",
                            "Filename",
                        ],
                        skiprows=11,
                    )  # Skip header lines in SEC daily files
                    df_daily["Date Filed"] = pd.to_datetime(df_daily["Date Filed"])
                    daily_filings.append(df_daily)
                    logger.info(f"Loaded {len(df_daily)} filings from {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    if not daily_filings:
        logger.error("No daily filing data found")
        return 1

    # Combine all daily filings
    df_merged_daily = pd.concat(daily_filings, ignore_index=True).sort_values(
        "Date Filed", ascending=False
    )
    logger.info(f"Combined daily data: {len(df_merged_daily)} filing records")

    # If you specified tickers in settings
    # Then load the file and filter out only the companies specified
    if ticker_list:
        logger.info(f"Filtering by ticker list: {ticker_list}")
        df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers["SYMBOL"].isin(df_ticker_list)]
        logger.info(f"Filtered to {len(df_cik_tickers)} companies")

    # If you specified forms in settings or custom forms
    # Then Filter the URL list to only the forms specified
    if form_list:
        logger.info("Loading Forms Filter...")
        # Use custom forms if provided, otherwise fall back to settings
        forms_to_use = custom_forms.split(",") if custom_forms else settings.forms_list
        forms_to_use = (
            [form.strip() for form in forms_to_use]
            if isinstance(forms_to_use, list)
            else forms_to_use
        )
        logger.info(f"Filtering by forms: {forms_to_use}")
        df_merged_daily = df_merged_daily[
            df_merged_daily["Form Type"].isin(forms_to_use)
        ]
        logger.info(f"Filtered to {len(df_merged_daily)} filings")

    # return only list of CIK tickers for companies and forms specified
    cik_list = cik_column_to_list(df_cik_tickers)
    logger.info(f"Generated CIK list with {len(cik_list)} companies")

    if ticker_list:
        df_merged_daily = df_merged_daily[df_merged_daily["CIK"].isin(cik_list)]
        logger.info(f"Final filtered dataset: {len(df_merged_daily)} filings")

    # Create a new column in the dataframe of filings with the Output Filepaths using unified URL generator
    df_filings = df_merged_daily.assign(
        url=df_merged_daily["Filename"].apply(lambda x: generate_filing_url(x))
    )
    logger.info(f"Generated URLs for {len(df_filings)} filings")

    # Initialize the FilingProcessor which will oversee the Extraction process
    # Use a project-relative path for filing data with template patterns
    filing_data_dir = str(
        settings.base_dir / "data" / "Archives" / "edgar" / "data" / "CIK" / "FOLDER"
    )
    logger.info(f"Filing data directory template: {filing_data_dir}")
    filing_broker = FilingProcessor(
        filing_data_dir=filing_data_dir,
        edgar_Archives_url=settings.edgar_archives_url,
        download=download,
        extract=extract,
    )

    logger.info(f"Starting to process {len(df_filings)} daily filings...")
    for i, sec_filing in df_filings.iterrows():
        logger.info(
            f"Processing filing {i + 1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}"
        )
        # Log filing details in a clean format
        logger.info(
            f"📄 {sec_filing['Company Name']} | {sec_filing['Form Type']} | "
            f"Filed: {sec_filing['Date Filed'].strftime('%Y-%m-%d')} | File: {sec_filing['Filename'].split('/')[-1]}"
        )

        filing_broker.process(sec_filing)

    logger.info("All daily filings processed successfully!")
    return 0


# ---------------------------
# Configuration-based API
# ---------------------------

from dataclasses import dataclass
from typing import Any


@dataclass
class DailyConfig:
    """Configuration for Daily workflow execution."""

    ticker_list: str | None = None
    form_list: list[str] | None = None
    start_date: str | None = None
    end_date: str | None = None
    download: bool = True
    extract: bool = False
    log_level: str = "INFO"


def set_log_level(level: str):
    """Set the logging level for the daily workflow."""
    logging.getLogger().setLevel(getattr(logging, level.upper()))


def run_daily_workflow(config: DailyConfig) -> dict[str, Any]:
    """Run the Daily workflow with the provided configuration.

    Returns a summary dictionary with counts and basic metadata for easy
    consumption by an API or UI layer.
    """
    set_log_level(config.log_level)

    logger.info("Starting SEC EDGAR Daily workflow...")
    logger.info(f"Config: {config}")

    # Use the existing enhanced function with the config parameters
    result = run_daily_workflow_with_dates(
        ticker_list=config.ticker_list,
        form_list=config.form_list,
        start_date=config.start_date,
        end_date=config.end_date,
        download=config.download,
        extract=config.extract,
    )

    return result


if __name__ == "__main__":
    main()
