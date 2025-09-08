"""RSS SEC EDGAR workflow script

This is the primary execution point for running the RSS (Recent) filing updates.
It fetches the most recent filings from the SEC EDGAR RSS feeds.
"""

# Use centralized logging configuration (DRY solution)
from ..logging_utils import setup_workflow_logging

# Set up logging using centralized utility
logger = setup_workflow_logging(
    log_filename="rss_workflow.log", log_level="INFO", force_reconfigure=False
)


from datetime import datetime

import click
import pandas as pd

import py_sec_edgar.feeds.rss
from py_sec_edgar.core.url_utils import generate_filing_url

from ..process import FilingProcessor
from ..settings import settings
from ..utilities import cik_column_to_list


@click.command()
@click.option("--ticker-list", default=str(settings.ticker_list_filepath))
@click.option("--form-list", default=True)
@click.option(
    "--count", default=100, help="Number of recent filings to fetch (default: 100)"
)
@click.option(
    "--form-type", default=None, help="Specific form type to filter (e.g., 8-K, 10-K)"
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
@click.option(
    "--list-only",
    is_flag=True,
    help="Just list the RSS filings without processing them",
)
@click.option(
    "--save-to-file", default=None, help="Save RSS data to file (e.g., rss_data.json)"
)
@click.option(
    "--load-from-file", default=None, help="Load RSS data from file instead of fetching"
)
@click.option(
    "--query-cik", default=None, help="Filter by specific CIK when loading from file"
)
@click.option(
    "--query-ticker",
    default=None,
    help="Filter by specific ticker when loading from file",
)
@click.option(
    "--query-form", default=None, help="Filter by specific form when loading from file"
)
@click.option(
    "--show-entries", is_flag=True, help="Show detailed RSS entries with all fields"
)
@click.option(
    "--search-text",
    default=None,
    help="Search for text in company names or descriptions",
)
def main(
    ticker_list,
    form_list,
    count,
    form_type,
    download,
    extract,
    list_only,
    save_to_file,
    load_from_file,
    query_cik,
    query_ticker,
    query_form,
    show_entries,
    search_text,
):
    logger.info("Starting SEC EDGAR RSS (recent) data processing...")
    logger.info(
        f"Parameters: ticker_list={ticker_list}, form_list={form_list}, count={count}, form_type={form_type}"
    )
    logger.info(
        f"Options: download={download}, extract={extract}, list_only={list_only}"
    )
    logger.info(
        f"File operations: save_to_file={save_to_file}, load_from_file={load_from_file}"
    )
    logger.info(
        f"Query filters: query_cik={query_cik}, query_ticker={query_ticker}, query_form={query_form}"
    )
    logger.info(
        f"Display options: show_entries={show_entries}, search_text={search_text}"
    )

    # Load from file or fetch from RSS feed
    if load_from_file:
        logger.info(f"Loading RSS data from file: {load_from_file}")
        try:
            import json

            with open(load_from_file) as f:
                recent_filings_data = json.load(f)
            logger.info(
                f"Loaded {len(recent_filings_data)} filings from {load_from_file}"
            )
        except Exception as e:
            logger.error(f"Failed to load RSS data from file: {e}")
            return 1
    else:
        # Initialize the recent filings feed
        logger.info("Initializing recent filings RSS feed...")
        recent_feed = py_sec_edgar.feeds.rss.RecentFilingsFeed()

        # Fetch recent filings from RSS feed
        logger.info(f"Fetching {count} recent filings from RSS feed...")
        try:
            # Call the sync function directly (no async needed)
            recent_filings_data = recent_feed.fetch_recent_filings(
                count=count, form_type=form_type
            )

            if not recent_filings_data:
                logger.error("No recent filing data retrieved")
                return 1

        except Exception as e:
            logger.error(f"Failed to fetch recent filings: {e}")
            return 1

    # Convert to DataFrame
    df_recent_filings = pd.DataFrame(recent_filings_data)
    logger.info(f"Retrieved {len(df_recent_filings)} recent filings")

    # Apply query filters if loading from file
    if load_from_file and (query_cik or query_ticker or query_form or search_text):
        original_count = len(df_recent_filings)

        if query_cik:
            logger.info(f"Filtering by CIK: {query_cik}")
            df_recent_filings = df_recent_filings[
                df_recent_filings["cik"]
                .astype(str)
                .str.contains(query_cik, case=False, na=False)
            ]

        if query_ticker:
            logger.info(f"Filtering by ticker: {query_ticker}")
            df_recent_filings = df_recent_filings[
                df_recent_filings["ticker"]
                .astype(str)
                .str.contains(query_ticker, case=False, na=False)
            ]

        if query_form:
            logger.info(f"Filtering by form type: {query_form}")
            df_recent_filings = df_recent_filings[
                df_recent_filings["form_type"]
                .astype(str)
                .str.contains(query_form, case=False, na=False)
            ]

        if search_text:
            logger.info(f"Searching for text: {search_text}")
            # Search in company_name and title fields
            company_matches = (
                df_recent_filings["company_name"]
                .astype(str)
                .str.contains(search_text, case=False, na=False)
            )
            title_matches = (
                df_recent_filings.get("title", pd.Series(dtype=str))
                .astype(str)
                .str.contains(search_text, case=False, na=False)
            )
            description_matches = (
                df_recent_filings.get("description", pd.Series(dtype=str))
                .astype(str)
                .str.contains(search_text, case=False, na=False)
            )
            df_recent_filings = df_recent_filings[
                company_matches | title_matches | description_matches
            ]

        logger.info(
            f"Query filtering: {original_count} -> {len(df_recent_filings)} filings"
        )

    # Save to file if requested
    if save_to_file:
        logger.info(f"Saving RSS data to file: {save_to_file}")
        try:
            import json

            with open(save_to_file, "w") as f:
                json.dump(recent_filings_data, f, indent=2, default=str)
            logger.info(
                f"✅ Saved {len(recent_filings_data)} filings to {save_to_file}"
            )

            if not load_from_file:  # If we just fetched and saved, show summary
                click.echo(f"\n📁 RSS data saved to: {save_to_file}")
                click.echo(f"📊 Total filings: {len(recent_filings_data)}")
                click.echo("💡 Use --load-from-file to query this data later")
                return 0

        except Exception as e:
            logger.error(f"Failed to save RSS data to file: {e}")
            return 1

    # If list-only mode, just display the filings and exit
    if list_only:
        click.echo("\n" + "=" * 80)
        click.echo(f"📋 RSS FEED FILINGS ({len(df_recent_filings)} total)")
        click.echo("=" * 80)

        if show_entries:
            # Show detailed entries with all fields
            for i, filing in enumerate(df_recent_filings.itertuples(), 1):
                click.echo(f"\n📄 Filing {i}:")
                click.echo(f"   Form Type: {getattr(filing, 'form_type', 'N/A')}")
                click.echo(f"   Company: {getattr(filing, 'company_name', 'N/A')}")
                click.echo(f"   CIK: {getattr(filing, 'cik', 'N/A')}")
                click.echo(f"   Filed Date: {getattr(filing, 'filed_date', 'N/A')}")
                click.echo(f"   Filing URL: {getattr(filing, 'filing_url', 'N/A')}")
                if hasattr(filing, "ticker") and filing.ticker:
                    click.echo(f"   Ticker: {filing.ticker}")
                if hasattr(filing, "title") and filing.title:
                    click.echo(f"   Title: {filing.title}")
                if hasattr(filing, "description") and filing.description:
                    click.echo(f"   Description: {filing.description}")
                if hasattr(filing, "summary") and filing.summary:
                    click.echo(f"   Summary: {filing.summary}")
                click.echo("-" * 40)
        else:
            # Show compact entries
            for i, filing in enumerate(df_recent_filings.itertuples(), 1):
                company = getattr(filing, "company_name", "N/A")
                form_type = getattr(filing, "form_type", "N/A")
                filed_date = getattr(filing, "filed_date", "N/A")
                cik = getattr(filing, "cik", "N/A")
                ticker = getattr(filing, "ticker", "")
                ticker_str = f" ({ticker})" if ticker else ""

                click.echo(
                    f"{i:3d}. {form_type:8s} | {company[:50]:50s}{ticker_str} | CIK: {cik} | {filed_date}"
                )

        click.echo(f"\n✅ Listed {len(df_recent_filings)} RSS filings")
        if not show_entries:
            click.echo("💡 Use --show-entries for detailed view")
        click.echo("💡 Use without --list-only to process/download these filings")
        return 0

    # Used to convert CIK to Tickers
    logger.info("Loading CIK to ticker mapping...")
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))
    logger.info(f"Loaded {len(df_cik_tickers)} CIK-ticker mappings")

    # Ensure proper data types and column names
    if "date_filed" in df_recent_filings.columns:
        df_recent_filings["Date Filed"] = pd.to_datetime(
            df_recent_filings["date_filed"], errors="coerce"
        )
    elif "Date Filed" not in df_recent_filings.columns:
        df_recent_filings["Date Filed"] = datetime.now()  # Default to current time

    # Standardize column names
    column_mapping = {
        "cik": "CIK",
        "company_name": "Company Name",
        "form_type": "Form Type",
        "filing_url": "url",  # Map filing_url to url
    }

    for old_col, new_col in column_mapping.items():
        if (
            old_col in df_recent_filings.columns
            and new_col not in df_recent_filings.columns
        ):
            df_recent_filings[new_col] = df_recent_filings[old_col]

    # Create Filename column from filing_url for compatibility with FilingProcessor
    if (
        "filing_url" in df_recent_filings.columns
        and "Filename" not in df_recent_filings.columns
    ):

        def extract_filename_from_url(url):
            """Extract the path part from SEC filing URL for Filename column."""
            if pd.isna(url) or not url:
                return ""
            # Remove the base URL to get the relative path
            # e.g., "https://www.sec.gov/Archives/edgar/data/123/file.txt" -> "edgar/data/123/file.txt"
            import re

            if "Archives/" in url:
                # Extract everything after 'Archives/'
                match = re.search(r"Archives/(.+)", url)
                if match:
                    return match.group(1)
            # Fallback: extract path from URL
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.path.lstrip("/")

        df_recent_filings["Filename"] = df_recent_filings["filing_url"].apply(
            extract_filename_from_url
        )
        logger.info(
            "Created Filename column from filing_url for FilingProcessor compatibility"
        )

    # Sort by date filed
    df_recent_filings = df_recent_filings.sort_values("Date Filed", ascending=False)
    logger.info(f"Processed RSS data: {len(df_recent_filings)} filing records")

    # If you specified tickers in settings - BUT ONLY if NOT loading from file
    # When loading from file, we want to see all data unless specifically filtered
    if not load_from_file and ticker_list and ticker_list.strip():
        logger.info(f"Filtering by ticker list: {ticker_list}")
        df_ticker_list = pd.read_csv(ticker_list, header=None).iloc[:, 0].tolist()
        df_cik_tickers = df_cik_tickers[df_cik_tickers["SYMBOL"].isin(df_ticker_list)]
        logger.info(f"Filtered to {len(df_cik_tickers)} companies")

        # Generate CIK list for filtering
        cik_list = cik_column_to_list(df_cik_tickers)
        logger.info(f"Generated CIK list with {len(cik_list)} companies")
    else:
        if load_from_file:
            logger.info("Loading from file - skipping default ticker filtering")
        else:
            logger.info("No ticker filtering - processing all companies")
        cik_list = None

    # If you specified forms in settings - BUT ONLY if NOT loading from file
    # When loading from file, we want to see all data unless specifically filtered
    if not load_from_file and form_list and hasattr(settings, "forms_list"):
        logger.info("Loading Forms Filter...")
        logger.info(f"Filtering by forms: {settings.forms_list}")
        df_recent_filings = df_recent_filings[
            df_recent_filings["Form Type"].isin(settings.forms_list)
        ]
        logger.info(f"Filtered to {len(df_recent_filings)} filings")
    elif load_from_file:
        logger.info("Loading from file - skipping default form filtering")

    # Apply CIK filtering only if ticker filtering was requested AND not loading from file
    if not load_from_file and ticker_list and ticker_list.strip() and cik_list:
        # Convert CIK column to numeric for comparison
        df_recent_filings["CIK"] = pd.to_numeric(
            df_recent_filings["CIK"], errors="coerce"
        )
        df_recent_filings = df_recent_filings[df_recent_filings["CIK"].isin(cik_list)]
        logger.info(f"Final filtered dataset: {len(df_recent_filings)} filings")
    else:
        if load_from_file:
            logger.info(
                f"Loading from file - processing all {len(df_recent_filings)} filings without CIK filtering"
            )
        else:
            logger.info(
                f"No CIK filtering applied - processing all {len(df_recent_filings)} filings"
            )

    # Ensure URL column exists
    if "url" not in df_recent_filings.columns:
        if "Filename" in df_recent_filings.columns:
            df_recent_filings["url"] = df_recent_filings["Filename"].apply(
                lambda x: generate_filing_url(x) if pd.notna(x) else ""
            )
        else:
            logger.warning(
                "No URL or Filename column found - filings may not be processable"
            )
            df_recent_filings["url"] = ""

    df_filings = df_recent_filings
    logger.info(f"Prepared URLs for {len(df_filings)} RSS filings")

    # Initialize the FilingProcessor which will oversee the Extraction process
    # Use the template pattern that FilingProcessor.generate_filepaths() expects
    # Use a project-relative path instead of hardcoded system path
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

    logger.info(f"Starting to process {len(df_filings)} RSS filings...")
    for i, sec_filing in df_filings.iterrows():
        logger.info(
            f"Processing filing {i + 1}/{len(df_filings)}: {sec_filing.get('Form Type', 'Unknown')} for CIK {sec_filing.get('CIK', 'Unknown')}"
        )

        # Generate the resolved file paths to show actual directory
        filing_filepaths = filing_broker.generate_filepaths(sec_filing)
        resolved_dir = filing_filepaths["cik_directory"]
        logger.info(f"Filing CIK directory: {resolved_dir}")

        # Show detailed filing info if requested
        if show_entries:
            logger.info(f"   Company: {sec_filing.get('Company Name', 'N/A')}")
            logger.info(f"   Form: {sec_filing.get('Form Type', 'N/A')}")
            logger.info(f"   URL: {sec_filing.get('url', 'N/A')}")

        filing_broker.process(sec_filing)

    logger.info("All RSS filings processed successfully!")
    return 0


if __name__ == "__main__":
    main()
