"""Daily SEC EDGAR workflow script

This is the primary execution point for running the Daily filing updates.
It downloads daily index files and processes filings.
"""
import logging

# Set up logging at the module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('logs/sec_edgar_daily.log')  # File output
    ]
)

logger = logging.getLogger(__name__)

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from pprint import pprint
from urllib.parse import urljoin

import click
import pandas as pd

import py_sec_edgar.feeds.daily

from ..process import FilingProcessor
from ..settings import settings
from ..utilities import cik_column_to_list


@click.command()
@click.option('--ticker-list', default=str(settings.ticker_list_filepath))
@click.option('--form-list', default=True)
@click.option('--custom-forms', default=None, help='Custom forms list (comma-separated) to override settings')
@click.option('--days-back', default=1, help='Number of days back to process (default: 1)')
@click.option('--download/--no-download', default=False, help='Download filing files (default: False)')
@click.option('--extract/--no-extract', default=False, help='Extract filing contents (default: False)')
def main(ticker_list, form_list, custom_forms, days_back, download, extract):
    logger.info("Starting SEC EDGAR daily data processing...")
    logger.info(f"Parameters: ticker_list={ticker_list}, form_list={form_list}, custom_forms={custom_forms}, days_back={days_back}, download={download}, extract={extract}")

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
        daily_files = py_sec_edgar.feeds.daily.generate_daily_index_urls_and_filepaths(target_date)

        for url, filepath in daily_files:
            if os.path.exists(filepath) and 'master' in filepath:
                logger.info(f"Processing daily file: {filepath}")
                try:
                    # Read the daily master file
                    df_daily = pd.read_csv(filepath, sep='|',
                                         names=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'],
                                         skiprows=11)  # Skip header lines in SEC daily files
                    df_daily['Date Filed'] = pd.to_datetime(df_daily['Date Filed'])
                    daily_filings.append(df_daily)
                    logger.info(f"Loaded {len(df_daily)} filings from {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to load {filepath}: {e}")

    if not daily_filings:
        logger.error("No daily filing data found")
        return 1

    # Combine all daily filings
    df_merged_daily = pd.concat(daily_filings, ignore_index=True).sort_values("Date Filed", ascending=False)
    logger.info(f"Combined daily data: {len(df_merged_daily)} filing records")

    # If you specified tickers in settings
    # Then load the file and filter out only the companies specified
    if ticker_list:
        logger.info(f"Filtering by ticker list: {ticker_list}")
        df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers['SYMBOL'].isin(df_ticker_list)]
        logger.info(f"Filtered to {len(df_cik_tickers)} companies")

    # If you specified forms in settings or custom forms
    # Then Filter the URL list to only the forms specified
    if form_list:
        logger.info('Loading Forms Filter...')
        # Use custom forms if provided, otherwise fall back to settings
        forms_to_use = custom_forms.split(',') if custom_forms else settings.forms_list
        forms_to_use = [form.strip() for form in forms_to_use] if isinstance(forms_to_use, list) else forms_to_use
        logger.info(f'Filtering by forms: {forms_to_use}')
        df_merged_daily = df_merged_daily[df_merged_daily['Form Type'].isin(forms_to_use)]
        logger.info(f'Filtered to {len(df_merged_daily)} filings')

    # return only list of CIK tickers for companies and forms specified
    cik_list = cik_column_to_list(df_cik_tickers)
    logger.info(f"Generated CIK list with {len(cik_list)} companies")

    if ticker_list:
        df_merged_daily = df_merged_daily[df_merged_daily['CIK'].isin(cik_list)]
        logger.info(f"Final filtered dataset: {len(df_merged_daily)} filings")

    # Create a new column in the dataframe of filings with the Output Filepaths
    df_filings = df_merged_daily.assign(url=df_merged_daily['Filename'].apply(lambda x: urljoin(settings.edgar_archives_url, x)))
    logger.info(f"Generated URLs for {len(df_filings)} filings")

    # Initialize the FilingProcessor which will oversee the Extraction process
    # Use a project-relative path for filing data
    filing_data_dir = str(settings.base_dir / "data" / "Archives" / "edgar" / "data")
    logger.info(f"Filing data directory: {filing_data_dir}")
    filing_broker = FilingProcessor(
        filing_data_dir=filing_data_dir, 
        edgar_Archives_url=settings.edgar_archives_url,
        download=download,
        extract=extract
    )

    logger.info(f"Starting to process {len(df_filings)} daily filings...")
    for i, sec_filing in df_filings.iterrows():
        logger.info(f"Processing filing {i+1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}")
        # Log filing details in a clean format
        logger.info(
            f"📄 {sec_filing['Company Name']} | {sec_filing['Form Type']} | "
            f"Filed: {sec_filing['Date Filed'].strftime('%Y-%m-%d')} | File: {sec_filing['Filename'].split('/')[-1]}"
        )

        filing_broker.process(sec_filing)

    logger.info("All daily filings processed successfully!")
    return 0

if __name__ == "__main__":
    main()
