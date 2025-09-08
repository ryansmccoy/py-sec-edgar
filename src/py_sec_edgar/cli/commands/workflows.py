"""
Complete workflow commands for SEC EDGAR processing.
"""

import logging
from pathlib import Path

import click

from ...settings import settings
from ..common import common_filter_options, parse_forms, parse_tickers

logger = logging.getLogger(__name__)


@click.group(name="workflows")
def workflows_group() -> None:
    """Run complete workflows that combine multiple operations."""
    pass


@workflows_group.command("full-index")
@common_filter_options
@click.option(
    "--start-date",
    type=str,
    help="Start date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format. Examples: 2024, 2024-01, 2024-01-01",
)
@click.option(
    "--end-date",
    type=str,
    help="End date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format. Examples: 2024, 2024-03, 2024-03-15",
)
@click.option(
    "--limit",
    type=int,
    help="Maximum number of filings to process (useful for testing or partial runs)",
)
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
def full_index_workflow(
    tickers: list[str],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: list[str],
    form: str | None,
    no_form_filter: bool,
    start_date: str | None,
    end_date: str | None,
    limit: int | None,
    download: bool,
    extract: bool,
) -> None:
    """
    Run the full index workflow (quarterly processing).

    Examples:
        py-sec-edgar workflows full-index --tickers NVDA AAPL --forms "10-K" "10-Q"
        py-sec-edgar workflows full-index --ticker-file tickers.csv --form "8-K"
        py-sec-edgar workflows full-index --no-ticker-filter --no-form-filter
    """

    # Parse ticker and form filters
    ticker_list = parse_tickers(tickers, ticker_file, no_ticker_filter)
    form_list = parse_forms(forms, form, no_form_filter)

    logger.info("Starting full index workflow...")
    if ticker_list:
        logger.info(f"Filtering by tickers: {ticker_list}")
    else:
        logger.info("No ticker filtering (processing all tickers)")

    if form_list:
        logger.info(f"Filtering by forms: {form_list}")
    else:
        logger.info("No form filtering (processing all forms)")

    try:
        from py_sec_edgar.cli.common import expand_date_range, validate_date_range
        from py_sec_edgar.workflows.full_index_workflow import (
            FullIndexConfig,
            run_full_index_workflow,
        )

        # Parse and validate date range
        start_date_obj, end_date_obj = expand_date_range(start_date, end_date)
        validate_date_range(start_date_obj, end_date_obj)

        if start_date_obj:
            logger.info(f"Filtering by start date: {start_date_obj}")
        if end_date_obj:
            logger.info(f"Filtering by end date: {end_date_obj}")
        if limit:
            logger.info(f"Limiting to {limit} filings")

        # Create temporary ticker file if needed
        temp_ticker_file = None
        if ticker_list:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                for ticker in ticker_list:
                    f.write(f"{ticker}\n")
                temp_ticker_file = f.name

        # Create configuration for the workflow
        config = FullIndexConfig(
            ticker_list=temp_ticker_file,
            form_filter=bool(form_list),  # Enable form filter if forms specified
            custom_forms=form_list,  # Pass the custom forms list
            skip_if_exists=True,  # Always skip existing for safety
            limit=limit,  # Pass limit parameter
            dry_run=False,  # Not a dry run
            log_level="INFO",  # Standard log level
            download=download,  # Pass download parameter
            extract=extract,  # Pass extract parameter
            start_date=start_date_obj,  # Pass start date
            end_date=end_date_obj,  # Pass end date
        )

        # Run the workflow directly
        summary = run_full_index_workflow(config)

        # Clean up temp file
        if temp_ticker_file:
            import os

            os.unlink(temp_ticker_file)

        logger.info("SUCCESS: Full index workflow completed successfully")
        logger.info(f"Summary: {summary}")

    except Exception as e:
        logger.error(f"❌ Full index workflow failed: {e}")
        # Clean up temp file in case of error
        if "temp_ticker_file" in locals() and temp_ticker_file:
            try:
                import os

                os.unlink(temp_ticker_file)
            except:
                pass
        raise click.ClickException(str(e))


@workflows_group.command("daily")
@common_filter_options
@click.option(
    "--days-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of days back to process (alternative to start/end dates)",
)
@click.option(
    "--start-date",
    type=str,
    help="Start date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format. Overrides --days-back if specified.",
)
@click.option(
    "--end-date",
    type=str,
    help="End date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format. Defaults to today if not specified.",
)
@click.option(
    "--limit",
    type=int,
    help="Maximum number of filings to process (useful for testing or partial runs)",
)
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
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    show_default=True,
    help="Skip download if files already exist",
)
def daily_workflow(
    tickers: list[str],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: list[str],
    form: str | None,
    no_form_filter: bool,
    days_back: int,
    start_date: str | None,
    end_date: str | None,
    limit: int | None,
    download: bool,
    extract: bool,
    skip_if_exists: bool,
) -> None:
    """
    Run the daily workflow (recent filings processing).

    Examples:
        py-sec-edgar workflows daily --tickers NVDA AAPL --days-back 3
        py-sec-edgar workflows daily --forms "8-K" --days-back 7
        py-sec-edgar workflows daily --ticker-file tickers.csv --form "10-Q"
    """

    # Parse ticker and form filters
    ticker_list = parse_tickers(tickers, ticker_file, no_ticker_filter)
    form_list = parse_forms(forms, form, no_form_filter)

    logger.info(f"Starting daily workflow for last {days_back} days...")
    if ticker_list:
        logger.info(f"Filtering by tickers: {ticker_list}")
    else:
        logger.info("No ticker filtering (processing all tickers)")

    if form_list:
        logger.info(f"Filtering by forms: {form_list}")
    else:
        logger.info("No form filtering (processing all forms)")

    try:
        from datetime import date, timedelta

        from py_sec_edgar.cli.common import expand_date_range, validate_date_range
        from py_sec_edgar.workflows.daily_workflow import main as daily_main_func

        # Parse and validate date range
        if start_date or end_date:
            # If dates are specified, use them instead of days_back
            start_date_obj, end_date_obj = expand_date_range(start_date, end_date)
            validate_date_range(start_date_obj, end_date_obj)

            if not end_date_obj:
                end_date_obj = date.today()
            if not start_date_obj:
                start_date_obj = end_date_obj - timedelta(days=days_back)

            # Convert to days_back equivalent for compatibility
            days_back_calculated = (end_date_obj - start_date_obj).days + 1
            logger.info(
                f"Using date range: {start_date_obj} to {end_date_obj} ({days_back_calculated} days)"
            )
        else:
            days_back_calculated = days_back
            logger.info(f"Using days back: {days_back_calculated}")

        if limit:
            logger.info(f"Limiting to {limit} filings")

        # Create temporary ticker file if needed
        temp_ticker_file = None
        if ticker_list:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                for ticker in ticker_list:
                    f.write(f"{ticker}\n")
                temp_ticker_file = f.name

        # Build arguments for the daily workflow command
        args = [
            "--days-back",
            str(days_back_calculated),
            "--ticker-list",
            temp_ticker_file
            if temp_ticker_file
            else str(settings.ticker_list_filepath),
        ]

        # Handle form filtering
        if form_list:
            args.extend(["--custom-forms", ",".join(form_list)])
        else:
            args.append("--form-list=false")

        # Handle download and extract flags
        if not download:
            args.append("--no-download")
        if extract:
            args.append("--extract")

        # Handle limit
        if limit:
            args.extend(["--limit", str(limit)])

        # Run the workflow command
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(daily_main_func, args, catch_exceptions=False)

        # Clean up temp file
        if temp_ticker_file:
            import os

            os.unlink(temp_ticker_file)

        if result.exit_code != 0:
            raise Exception(f"Daily workflow failed: {result.output}")

        logger.info("SUCCESS: Daily workflow completed successfully")

    except Exception as e:
        logger.error(f"❌ Daily workflow failed: {e}")
        # Clean up temp file in case of error
        if "temp_ticker_file" in locals() and temp_ticker_file:
            try:
                import os

                os.unlink(temp_ticker_file)
            except:
                pass
        raise click.ClickException(str(e))


@workflows_group.command("monthly")
@common_filter_options
@click.option(
    "--months-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back to process (alternative to start/end dates)",
)
@click.option(
    "--start-date",
    type=str,
    help="Start date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format.",
)
@click.option(
    "--end-date",
    type=str,
    help="End date for processing. Supports: YYYY, YYYY-MM, or YYYY-MM-DD format.",
)
@click.option("--limit", type=int, help="Maximum number of filings to process")
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
def monthly_workflow(
    tickers: list[str],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: list[str],
    form: str | None,
    no_form_filter: bool,
    months_back: int,
    start_date: str | None,
    end_date: str | None,
    limit: int | None,
    download: bool,
    extract: bool,
) -> None:
    """
    Run the monthly workflow (XBRL processing).

    Examples:
        py-sec-edgar workflows monthly --tickers NVDA AAPL --months-back 3
        py-sec-edgar workflows monthly --forms "10-K" "10-Q" --months-back 6
        py-sec-edgar workflows monthly --ticker-file tickers.csv --form "8-K"
    """

    # Parse ticker and form filters
    ticker_list = parse_tickers(tickers, ticker_file, no_ticker_filter)
    form_list = parse_forms(forms, form, no_form_filter)

    logger.info(f"Starting monthly workflow for last {months_back} months...")
    if ticker_list:
        logger.info(f"Filtering by tickers: {ticker_list}")
    else:
        logger.info("No ticker filtering (processing all tickers)")

    if form_list:
        logger.info(f"Filtering by forms: {form_list}")
    else:
        logger.info("No form filtering (processing all forms)")

    try:
        from click.testing import CliRunner

        from py_sec_edgar.workflows.monthly_workflow import main as monthly_main_cmd

        # Build arguments for the monthly workflow command
        args = ["--months-back", str(months_back)]

        # Handle ticker filtering
        if ticker_list:
            # Create a temporary file with tickers for the workflow
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                for ticker in ticker_list:
                    f.write(f"{ticker}\n")
                temp_ticker_file = f.name
            args.extend(["--ticker-list", temp_ticker_file])

        # Handle form filtering - the workflow expects boolean for form_list
        if not form_list:
            args.append("--form-list=false")

        # Run the workflow command
        runner = CliRunner()
        result = runner.invoke(monthly_main_cmd, args, catch_exceptions=False)

        # Clean up temp file
        if ticker_list:
            import os

            os.unlink(temp_ticker_file)

        if result.exit_code != 0:
            raise Exception(f"Monthly workflow failed: {result.output}")

        logger.info("SUCCESS: Monthly workflow completed successfully")

    except Exception as e:
        logger.error(f"❌ Monthly workflow failed: {e}")
        raise click.ClickException(str(e))


@workflows_group.command("rss")
@common_filter_options
@click.option(
    "--count",
    type=int,
    default=100,
    show_default=True,
    help="Number of recent filings to fetch",
)
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
    "--list-only",
    is_flag=True,
    help="Just list the RSS filings without processing them",
)
@click.option(
    "--save-to-file", type=str, help="Save RSS data to file (e.g., rss_data.json)"
)
@click.option(
    "--load-from-file", type=str, help="Load RSS data from file instead of fetching"
)
@click.option(
    "--query-cik", type=str, help="Filter by specific CIK when loading from file"
)
@click.option(
    "--query-ticker", type=str, help="Filter by specific ticker when loading from file"
)
@click.option(
    "--query-form", type=str, help="Filter by specific form when loading from file"
)
@click.option("--pretty-print", is_flag=True, help="Pretty print the RSS file content")
@click.option(
    "--show-entries", is_flag=True, help="Show detailed RSS entries with all fields"
)
@click.option(
    "--search-text", type=str, help="Search for text in company names or descriptions"
)
def rss_workflow(
    tickers: list[str],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: list[str],
    form: str | None,
    no_form_filter: bool,
    count: int,
    download: bool,
    extract: bool,
    list_only: bool,
    save_to_file: str | None,
    load_from_file: str | None,
    query_cik: str | None,
    query_ticker: str | None,
    query_form: str | None,
    pretty_print: bool,
    show_entries: bool,
    search_text: str | None,
) -> None:
    """
    Run the RSS workflow (recent filings from RSS feeds).

    Examples:
        py-sec-edgar workflows rss --tickers NVDA AAPL --count 50
        py-sec-edgar workflows rss --form "8-K" --count 200
        py-sec-edgar workflows rss --ticker-file tickers.csv --forms "10-K" "10-Q"
        py-sec-edgar workflows rss --no-ticker-filter --no-form-filter --count 500
    """

    # Handle pretty-print functionality first
    if pretty_print and load_from_file:
        logger.info(f"Pretty printing RSS file: {load_from_file}")
        try:
            import json

            with open(load_from_file) as f:
                data = json.load(f)

            click.echo("\n" + "=" * 80)
            click.echo(f"📄 RSS FILE PRETTY PRINT: {load_from_file}")
            click.echo("=" * 80)
            click.echo(json.dumps(data, indent=2, default=str))
            click.echo("=" * 80)
            return
        except Exception as e:
            logger.error(f"Failed to pretty print file: {e}")
            raise click.ClickException(str(e))

    # When loading from file, disable default filtering unless explicitly requested
    if load_from_file:
        # Only apply CLI filters if explicitly provided (not defaults)
        if not tickers and not ticker_file and not no_ticker_filter:
            no_ticker_filter = True  # Force no ticker filtering when loading from file
        if not forms and not form and not no_form_filter:
            no_form_filter = True  # Force no form filtering when loading from file

    # Parse ticker and form filters
    ticker_list = parse_tickers(tickers, ticker_file, no_ticker_filter)
    form_list = parse_forms(forms, form, no_form_filter)

    logger.info(f"Starting RSS workflow for {count} recent filings...")
    if ticker_list:
        logger.info(f"Filtering by tickers: {ticker_list}")
    else:
        logger.info("No ticker filtering (processing all tickers)")

    if form_list:
        logger.info(f"Filtering by forms: {form_list}")
    else:
        logger.info("No form filtering (processing all forms)")

    try:
        from click.testing import CliRunner

        from py_sec_edgar.workflows.rss_workflow import main as rss_main_cmd

        # Build arguments for the RSS workflow command
        args = ["--count", str(count)]

        # Handle ticker filtering
        if ticker_list:
            # Create a temporary file with tickers for the workflow
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                for ticker in ticker_list:
                    f.write(f"{ticker}\n")
                temp_ticker_file = f.name
            args.extend(["--ticker-list", temp_ticker_file])
        else:
            # Pass empty string to indicate no ticker filtering
            args.extend(["--ticker-list", ""])

        # Handle form filtering - the workflow expects boolean for form_list
        if not form_list:
            args.append("--form-list=false")

        # If only one form specified, use form-type
        if form_list and len(form_list) == 1:
            args.extend(["--form-type", form_list[0]])

        # Handle download and extract flags
        if not download:
            args.append("--no-download")
        if extract:
            args.append("--extract")

        # Handle list-only flag
        if list_only:
            args.append("--list-only")

        # Handle file operations
        if save_to_file:
            args.extend(["--save-to-file", save_to_file])

        if load_from_file:
            args.extend(["--load-from-file", load_from_file])

        # Handle query filters
        if query_cik:
            args.extend(["--query-cik", query_cik])

        if query_ticker:
            args.extend(["--query-ticker", query_ticker])

        if query_form:
            args.extend(["--query-form", query_form])

        # Handle show entries and search text
        if show_entries:
            args.append("--show-entries")
        if search_text:
            args.extend(["--search-text", search_text])

        # Run the workflow command
        runner = CliRunner()
        result = runner.invoke(rss_main_cmd, args, catch_exceptions=False)

        # Clean up temp file
        if ticker_list:
            import os

            os.unlink(temp_ticker_file)

        if result.exit_code != 0:
            raise Exception(f"RSS workflow failed: {result.output}")

        logger.info("SUCCESS: RSS workflow completed successfully")

    except Exception as e:
        logger.error(f"❌ RSS workflow failed: {e}")
        raise click.ClickException(str(e))
