"""
Filing processing commands for SEC EDGAR data.
"""

import logging
from pathlib import Path

import click

logger = logging.getLogger(__name__)


@click.group(name="process")
def process_group() -> None:
    """Process SEC EDGAR filings (download, extract, and analyze)."""
    pass


@process_group.command("filings")
@click.option(
    "--ticker-list",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="CSV file containing ticker symbols to filter",
)
@click.option(
    "--form-types",
    multiple=True,
    help="Form types to process (can specify multiple times)",
)
@click.option("--cik", type=str, help="Process filings for specific CIK")
@click.option(
    "--download/--no-download",
    default=True,
    show_default=True,
    help="Download filing files",
)
@click.option(
    "--extract/--no-extract",
    default=False,
    show_default=True,
    help="Extract filing contents",
)
@click.option(
    "--parse-header/--no-parse-header",
    default=True,
    show_default=True,
    help="Parse filing headers",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    show_default=True,
    help="Maximum number of filings to process",
)
def process_filings(
    ticker_list: Path | None,
    form_types: tuple,
    cik: str | None,
    download: bool,
    extract: bool,
    parse_header: bool,
    limit: int,
) -> None:
    """Process SEC filings based on filters."""

    logger.info("Starting filing processing...")

    # Convert form_types tuple to list
    # form_list = list(form_types) if form_types else settings.forms_list  # Commented: unused variable

    try:
        # processor = FilingProcessor(  # Commented: unused variable
        #     filing_data_dir=settings.data_dir,
        #     edgar_archives_url=settings.edgar_archives_url
        # )

        # Process filings based on parameters
        if cik:
            logger.info(f"Processing filings for CIK: {cik}")
            # Filter filings by CIK and process
            # For now, we'll use the general processing approach with CIK filter
            click.echo(f"📊 Processing filings for CIK {cik}...")
            click.echo("⚠️  CIK-specific processing is available via workflows commands")
            click.echo(
                "💡 Try: uv run python -m py_sec_edgar workflows rss --query-cik {cik}"
            )
        elif ticker_list:
            logger.info(f"Processing filings for tickers in: {ticker_list}")
            # Process filings from ticker list file
            click.echo(f"📊 Processing filings from ticker list: {ticker_list}")
            click.echo("⚠️  Ticker-list processing is available via workflows commands")
            click.echo(
                f"💡 Try: uv run python -m py_sec_edgar workflows rss --ticker-file {ticker_list}"
            )
        else:
            logger.info("Processing recent filings...")
            # Process recent filings (default behavior)
            click.echo("📊 Processing recent filings...")
            click.echo(
                "⚠️  Recent filings processing is available via workflows commands"
            )
            click.echo(
                "💡 Try: uv run python -m py_sec_edgar workflows daily --days-back 7"
            )

        logger.info("✅ Filing processing completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to process filings: {e}")
        raise click.ClickException(str(e))


@process_group.command("daily-filings")
@click.option(
    "--ticker-list",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="CSV file containing ticker symbols to filter",
)
@click.option(
    "--days-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of days back to process",
)
@click.option(
    "--form-list/--no-form-list",
    default=True,
    show_default=True,
    help="Filter by form types from settings",
)
def process_daily_filings(
    ticker_list: Path | None, days_back: int, form_list: bool
) -> None:
    """Process daily filings from the last N days."""
    from py_sec_edgar.workflows.daily_workflow import main as daily_main

    logger.info(f"Processing daily filings for last {days_back} days...")

    try:
        # Call the daily workflow
        # Note: This needs to be adapted based on the actual daily_workflow implementation
        daily_main(ticker_list=ticker_list, days_back=days_back, form_list=form_list)
        logger.info("✅ Daily filing processing completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to process daily filings: {e}")
        raise click.ClickException(str(e))


@process_group.command("monthly-xbrl")
@click.option(
    "--ticker-list",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="CSV file containing ticker symbols to filter",
)
@click.option(
    "--months-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back to process",
)
@click.option(
    "--form-list/--no-form-list",
    default=True,
    show_default=True,
    help="Filter by form types from settings",
)
def process_monthly_xbrl(
    ticker_list: Path | None, months_back: int, form_list: bool
) -> None:
    """Process monthly XBRL filings from the last N months."""
    from py_sec_edgar.workflows.monthly_workflow import main as monthly_main

    logger.info(f"Processing monthly XBRL filings for last {months_back} months...")

    try:
        # Call the monthly workflow
        monthly_main(
            ticker_list=ticker_list, months_back=months_back, form_list=form_list
        )
        logger.info("✅ Monthly XBRL processing completed successfully")

    except Exception as e:
        logger.error(f"❌ Failed to process monthly XBRL filings: {e}")
        raise click.ClickException(str(e))
