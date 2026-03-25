"""Monthly SEC EDGAR workflow script

This is the primary execution point for running the Monthly XBRL filing updates.
It downloads monthly XBRL RSS feeds and processes filings.
"""

from py_sec_edgar.core.path_utils import ensure_file_directory

# Use centralized logging configuration (DRY solution)
from ..logging_utils import setup_workflow_logging

# Set up logging using centralized utility
logger = setup_workflow_logging(
    log_filename="monthly_workflow.log", log_level="INFO", force_reconfigure=False
)

import os
import time
from datetime import datetime, timedelta
from pprint import pprint

import click
import feedparser
import pandas as pd

import py_sec_edgar.feeds.monthly

from ..core.download_service import UnifiedDownloadService
from ..core.url_utils import generate_filing_url, generate_monthly_index_url
from ..process import FilingProcessor
from ..settings import settings
from ..utilities import cik_column_to_list


@click.command()
@click.option("--ticker-list", default=str(settings.ticker_list_filepath))
@click.option("--form-list", default=True)
@click.option(
    "--months-back", default=1, help="Number of months back to process (default: 1)"
)
def main(ticker_list, form_list, months_back):
    logger.info("Starting SEC EDGAR monthly XBRL data processing...")
    logger.info(
        f"Parameters: ticker_list={ticker_list}, form_list={form_list}, months_back={months_back}"
    )

    # Download only the specific monthly XBRL RSS feeds needed based on months_back
    logger.info(
        f"Starting selective monthly XBRL feed download for last {months_back} months..."
    )

    # Download only the monthly files we need based on months_back parameter
    for months_ago in range(months_back):
        target_date = datetime.now() - timedelta(
            days=months_ago * 30
        )  # Approximate months
        url, filepath = (
            py_sec_edgar.feeds.monthly.generate_monthly_index_url_and_filepaths(
                target_date
            )
        )

        # Ensure the directory exists using unified path manager
        ensure_file_directory(filepath)

        if not os.path.exists(filepath):
            logger.info(f"Downloading monthly XBRL file: {url}")

            # Rate limiting: respect SEC's request delay
            time.sleep(settings.request_delay)

            try:
                # Use unified download service for consistency
                download_service = UnifiedDownloadService()
                content = download_service.download_binary(url)

                with open(filepath, "wb") as f:
                    f.write(content)

                logger.info(f"Successfully downloaded: {filepath}")
            except Exception as e:
                logger.warning(f"Failed to download {url}: {e}")
        else:
            logger.info(f"Monthly XBRL file already exists: {filepath}")

    logger.info("Selective monthly XBRL feed download completed")

    # Used to convert CIK to Tickers
    logger.info("Loading CIK to ticker mapping...")
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))
    logger.info(f"Loaded {len(df_cik_tickers)} CIK-ticker mappings")

    # Load monthly XBRL RSS files for the specified date range
    logger.info("Loading monthly XBRL RSS files...")
    monthly_filings = []

    for months_ago in range(months_back):
        target_date = datetime.now() - timedelta(
            days=months_ago * 30
        )  # Approximate months
        url, filepath = generate_monthly_index_url(target_date)

        if os.path.exists(filepath):
            logger.info(f"Processing monthly file: {filepath}")
            try:
                # Parse the XBRL RSS feed
                feed = feedparser.parse(filepath)

                filing_records = []
                for entry in feed.entries:
                    # Extract filing information from RSS entry
                    filing_record = {
                        "CIK": entry.get("edgar_cik", ""),
                        "Company Name": entry.get("edgar_companyname", ""),
                        "Form Type": entry.get("edgar_formtype", ""),
                        "Date Filed": entry.get("edgar_fileddate", ""),
                        "Filename": entry.get("edgar_xbrlfile", ""),
                        "Title": entry.get("title", ""),
                        "Link": entry.get("link", ""),
                    }
                    filing_records.append(filing_record)

                df_monthly = pd.DataFrame(filing_records)
                if not df_monthly.empty:
                    df_monthly["Date Filed"] = pd.to_datetime(
                        df_monthly["Date Filed"], errors="coerce"
                    )
                    df_monthly = df_monthly.dropna(subset=["Date Filed"])
                    monthly_filings.append(df_monthly)
                    logger.info(
                        f"Loaded {len(df_monthly)} XBRL filings from {filepath}"
                    )

            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")

    if not monthly_filings:
        logger.error("No monthly XBRL filing data found")
        return 1

    # Combine all monthly filings
    df_merged_monthly = pd.concat(monthly_filings, ignore_index=True).sort_values(
        "Date Filed", ascending=False
    )
    logger.info(f"Combined monthly XBRL data: {len(df_merged_monthly)} filing records")

    # If you specified tickers in settings
    # Then load the file and filter out only the companies specified
    if ticker_list:
        logger.info(f"Filtering by ticker list: {ticker_list}")
        df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers["SYMBOL"].isin(df_ticker_list)]
        logger.info(f"Filtered to {len(df_cik_tickers)} companies")

    # If you specified forms in settings
    # Then Filter the URL list to only the forms specified
    if form_list:
        logger.info("Loading Forms Filter...")
        logger.info(f"Filtering by forms: {settings.forms_list}")
        df_merged_monthly = df_merged_monthly[
            df_merged_monthly["Form Type"].isin(settings.forms_list)
        ]
        logger.info(f"Filtered to {len(df_merged_monthly)} filings")

    # return only list of CIK tickers for companies and forms specified
    cik_list = cik_column_to_list(df_cik_tickers)
    logger.info(f"Generated CIK list with {len(cik_list)} companies")

    if ticker_list:
        # Convert CIK column to numeric for comparison
        df_merged_monthly["CIK"] = pd.to_numeric(
            df_merged_monthly["CIK"], errors="coerce"
        )
        df_merged_monthly = df_merged_monthly[df_merged_monthly["CIK"].isin(cik_list)]
        logger.info(f"Final filtered dataset: {len(df_merged_monthly)} filings")

    # Create a new column in the dataframe of filings with the Output Filepaths
    # For XBRL files, use the Link field or construct from Filename
    df_filings = df_merged_monthly.copy()
    if "Link" in df_filings.columns and not df_filings["Link"].isna().all():
        df_filings["url"] = df_filings["Link"]
    else:
        # Use unified URL generator instead of inline urljoin
        df_filings["url"] = df_filings["Filename"].apply(
            lambda x: generate_filing_url(x) if pd.notna(x) else ""
        )

    logger.info(f"Generated URLs for {len(df_filings)} XBRL filings")

    # Initialize the FilingProcessor which will oversee the Extraction process
    # Use a project-relative path instead of hardcoded system path
    filing_data_dir = str(
        settings.base_dir / "data" / "Archives" / "edgar" / "data" / "CIK" / "FOLDER"
    )
    logger.info(f"Filing data directory: {filing_data_dir}")
    filing_broker = FilingProcessor(
        filing_data_dir=filing_data_dir, edgar_Archives_url=settings.edgar_archives_url
    )

    logger.info(f"Starting to process {len(df_filings)} monthly XBRL filings...")
    for i, sec_filing in df_filings.iterrows():
        logger.info(
            f"Processing filing {i + 1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}"
        )
        pprint(str(sec_filing))

        filing_broker.process(sec_filing)

    logger.info("All monthly XBRL filings processed successfully!")
    return 0


if __name__ == "__main__":
    main()
