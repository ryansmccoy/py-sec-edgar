"""Full Index SEC EDGAR workflow

Provides an interactive and scriptable command-line interface (CLI) to run the
"Full Index" ingestion workflow, and exposes a reusable function for API/frontend
integration.

Run examples:
- python -m sec_edgar_core.full_index_workflow run --help
- python -m sec_edgar_core.full_index_workflow interactive
"""

import logging
from datetime import date

# Use centralized logging configuration (DRY solution)
from ..logging_utils import setup_workflow_logging

# Set up logging using centralized utility
logger = setup_workflow_logging(
    log_filename="full_index_workflow.log", log_level="INFO", force_reconfigure=False
)

import json
import os
from dataclasses import dataclass
from typing import Any

import click
import pandas as pd
import pyarrow.parquet as pq

import py_sec_edgar.feeds.full_index
from py_sec_edgar.core.url_utils import generate_filing_url, quarter_to_month_range

# Removed external API task submission - running locally only
# from .cli.task_submitter import maybe_enqueue_task
from ..process import FilingProcessor
from ..settings import settings
from ..utilities import cik_column_to_list

# ---------------------------
# Data structures and helpers
# ---------------------------


@dataclass
class FullIndexConfig:
    """Configuration for the Full Index workflow."""

    ticker_list: str | None = (
        str(settings.ticker_list_filepath)
        if getattr(settings, "ticker_list_filepath", None)
        else None
    )
    form_filter: bool = True
    custom_forms: list[str] | None = (
        None  # custom forms list to override settings.forms_list
    )
    skip_if_exists: bool = True
    limit: int | None = None  # limit number of filings to process
    dry_run: bool = False  # don't process filings, just preview
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    quarter: str | None = None  # specific quarter to process (e.g., "2025Q3")
    download: bool = True  # whether to download filings
    extract: bool = False  # whether to extract filing contents
    start_date: date | None = None  # start date for filtering filings
    end_date: date | None = None  # end date for filtering filings


def set_log_level(level: str) -> None:
    """Set logger level dynamically for this module and root handlers."""
    from ..logging_utils import get_workflow_logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Update the module logger
    module_logger = get_workflow_logger(__name__)
    module_logger.setLevel(numeric_level)

    # Update root logger and all handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)
    for h in logging.getLogger().handlers:
        h.setLevel(numeric_level)


def _load_cik_tickers() -> pd.DataFrame:
    logger.info("Loading CIK to ticker mapping...")
    df = pd.read_csv(str(settings.cik_tickers_csv))
    logger.info(f"Loaded {len(df)} CIK-ticker mappings")
    return df


def _load_full_index_table() -> pd.DataFrame:
    logger.info("Loading merged IDX files...")
    df = (
        pq.read_table(str(settings.merged_idx_filepath))
        .to_pandas()
        .sort_values("Date Filed", ascending=False)
    )
    logger.info(f"Loaded {len(df)} filing records")
    return df


def _filter_by_tickers(
    df_idx: pd.DataFrame, df_cik_tickers: pd.DataFrame, ticker_list_path: str | None
) -> pd.DataFrame:
    if not ticker_list_path:
        return df_idx
    logger.info(f"Filtering by ticker list: {ticker_list_path}")
    try:
        tickers = (
            pd.read_csv(ticker_list_path, header=None)
            .iloc[:, 0]
            .astype(str)
            .str.strip()
            .tolist()
        )
    except Exception as e:
        logger.warning(f"Failed to read ticker list from {ticker_list_path}: {e}")
        return df_idx
    df_symbols = df_cik_tickers[df_cik_tickers["SYMBOL"].astype(str).isin(tickers)]
    logger.info(f"Filtered to {len(df_symbols)} companies from ticker list")
    cik_list = cik_column_to_list(df_symbols)
    out = df_idx[df_idx["CIK"].isin(cik_list)]
    logger.info(f"Filtered filings by CIK to {len(out)} rows")
    return out


def _apply_form_filter(
    df_idx: pd.DataFrame, enabled: bool, custom_forms: list[str] | None = None
) -> pd.DataFrame:
    if not enabled:
        return df_idx
    # Use custom forms if provided, otherwise fall back to settings
    forms = custom_forms if custom_forms else getattr(settings, "forms_list", None)
    if not forms:
        logger.info("Form filter enabled but no forms specified; skipping form filter")
        return df_idx
    logger.info(f"Filtering by forms: {forms}")
    out = df_idx[df_idx["Form Type"].isin(forms)]
    logger.info(f"Filtered to {len(out)} filings by form type")
    return out


def _prepare_filings_df(df_idx: pd.DataFrame) -> pd.DataFrame:
    # Create a new column with absolute URLs to filings
    return df_idx.assign(url=df_idx["Filename"].apply(generate_filing_url))


def _update_specific_quarter(year: int, qtr: int, skip_if_exists: bool = True) -> None:
    """Download full index data for a specific quarter."""
    logger.info(f"Downloading full index data for {year} Q{qtr}")

    # Use the existing full index update but only for specific quarter
    # This would require modifying the full_index module to support single quarter
    # For now, we'll fall back to standard update and filter later
    py_sec_edgar.feeds.full_index.update_full_index_feed(skip_if_exists=skip_if_exists)
    logger.info(f"Full index update completed for {year} Q{qtr}")


def _filter_by_date_range(
    df_idx: pd.DataFrame, start_date: date | None, end_date: date | None
) -> pd.DataFrame:
    """Filter dataframe by date range."""
    if not start_date and not end_date:
        return df_idx

    import pandas as pd

    # Convert Date Filed to datetime if it's not already
    if "Date Filed" in df_idx.columns:
        # Make a copy to avoid modifying the original
        df_filtered = df_idx.copy()

        # Ensure the column is datetime
        df_filtered["Date Filed"] = pd.to_datetime(df_filtered["Date Filed"])

        # Apply date filters
        if start_date:
            start_timestamp = pd.Timestamp(start_date)
            df_filtered = df_filtered[df_filtered["Date Filed"] >= start_timestamp]
            logger.info(f"Filtering filings from {start_date} onwards")

        if end_date:
            end_timestamp = pd.Timestamp(end_date)
            df_filtered = df_filtered[df_filtered["Date Filed"] <= end_timestamp]
            logger.info(f"Filtering filings up to {end_date}")

        logger.info(f"Date filter: {len(df_idx)} -> {len(df_filtered)} filings")
        return df_filtered
    else:
        logger.warning(
            "'Date Filed' column not found in dataframe - skipping date filter"
        )
        return df_idx


def _filter_by_quarter(df_idx: pd.DataFrame, quarter_str: str) -> pd.DataFrame:
    """Filter dataframe to only include filings from specified quarter."""
    import re
    from datetime import datetime

    # Parse quarter (e.g., "2025Q3" -> year=2025, qtr=3)
    match = re.match(r"^(\d{4})Q([1-4])$", quarter_str)
    if not match:
        logger.warning(f"Invalid quarter format: {quarter_str}")
        return df_idx

    year = int(match.group(1))
    qtr = int(match.group(2))

    # Define quarter date ranges using unified utility
    quarter_start_month, quarter_end_month = quarter_to_month_range(qtr)

    start_date = datetime(year, quarter_start_month, 1)
    if quarter_end_month == 12:
        end_date = datetime(year + 1, 1, 1)  # Start of next year
    else:
        end_date = datetime(year, quarter_end_month + 1, 1)  # Start of next month

    logger.info(
        f"Filtering filings for {quarter_str}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    # Convert Date Filed to datetime if it's not already
    if "Date Filed" in df_idx.columns:
        df_idx = df_idx.copy()
        df_idx["Date Filed"] = pd.to_datetime(df_idx["Date Filed"])

        # Filter by date range
        mask = (df_idx["Date Filed"] >= start_date) & (df_idx["Date Filed"] < end_date)
        df_filtered = df_idx[mask]

        logger.info(f"Filtered to {len(df_filtered)} filings for {quarter_str}")
        return df_filtered
    else:
        logger.warning("'Date Filed' column not found in dataframe")
        return df_idx


def run_full_index_workflow(config: FullIndexConfig) -> dict[str, Any]:
    """Run the Full Index workflow with the provided configuration.

    Returns a summary dictionary with counts and basic metadata for easy
    consumption by an API or UI layer.
    """
    set_log_level(config.log_level)

    logger.info("Starting SEC EDGAR Full Index processing...")
    logger.info(
        f"Config(ticker_list={config.ticker_list}, form_filter={config.form_filter}, "
        f"skip_if_exists={config.skip_if_exists}, limit={config.limit}, dry_run={config.dry_run}, "
        f"log_level={config.log_level}, quarter={config.quarter})"
    )

    # 1) Download/refresh feeds
    logger.info("Updating full index feed...")
    if config.quarter:
        # Parse quarter (e.g., "2025Q3" -> year=2025, qtr=3)
        import re

        match = re.match(r"^(\d{4})Q([1-4])$", config.quarter)
        if not match:
            raise ValueError(
                f"Invalid quarter format: {config.quarter}. Expected format: YYYYQN (e.g., 2025Q3)"
            )

        year, qtr = match.groups()
        year = int(year)
        qtr = int(qtr)

        logger.info(f"Processing specific quarter: {year} Q{qtr}")

        # Download specific quarter data
        _update_specific_quarter(year, qtr, config.skip_if_exists)
    else:
        # Standard full index update (multiple quarters)
        py_sec_edgar.feeds.full_index.update_full_index_feed(
            skip_if_exists=config.skip_if_exists
        )

    logger.info("Full index feed update complete")

    # 2) Load base data
    df_cik_tickers = _load_cik_tickers()
    df_idx = _load_full_index_table()

    # 3) Apply quarter filter if specified
    if config.quarter:
        df_idx = _filter_by_quarter(df_idx, config.quarter)

    # 4) Apply other filters
    df_idx = _apply_form_filter(
        df_idx, enabled=config.form_filter, custom_forms=config.custom_forms
    )
    df_idx = _filter_by_tickers(df_idx, df_cik_tickers, config.ticker_list)

    # 5) Apply date range filter if specified
    if config.start_date or config.end_date:
        df_idx = _filter_by_date_range(df_idx, config.start_date, config.end_date)

    # 6) Prepare URLs
    df_filings = _prepare_filings_df(df_idx)

    # 7) Optional limit
    total_candidates = len(df_filings)
    if config.limit is not None and config.limit > 0:
        df_filings = df_filings.head(config.limit)
        logger.info(
            f"Applying limit: processing first {len(df_filings)} of {total_candidates} filings"
        )
    else:
        logger.info(f"Processing all {total_candidates} filings")

    # 7) Process or preview
    processed = 0
    if config.dry_run:
        logger.info("Dry run: previewing filings without processing")
        preview_rows = min(5, len(df_filings))
        logger.info(f"Preview of first {preview_rows} filings:")
        for _, row in df_filings.head(preview_rows).iterrows():
            logger.info(
                f"- {row['Form Type']} | CIK {row['CIK']} | {row['Date Filed']} | {row['url']}"
            )
    else:
        # Use a project-relative path for filing data with template patterns
        filing_data_dir = str(
            settings.base_dir
            / "data"
            / "Archives"
            / "edgar"
            / "data"
            / "CIK"
            / "FOLDER"
        )
        logger.info(f"Filing data directory template: {filing_data_dir}")
        filing_broker = FilingProcessor(
            filing_data_dir=filing_data_dir,
            edgar_Archives_url=settings.edgar_archives_url,
            download=config.download,
            extract=config.extract,
        )

        logger.info(f"Starting to process {len(df_filings)} filings...")
        for i, sec_filing in df_filings.iterrows():
            logger.info(
                f"Processing filing {processed + 1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}"
            )
            # Log filing details in a clean format
            logger.info(
                f"FILING: {sec_filing['Company Name']} | {sec_filing['Form Type']} | "
                f"Filed: {sec_filing['Date Filed']} | File: {sec_filing['Filename'].split('/')[-1]}"
            )
            filing_broker.process(sec_filing)
            processed += 1

    summary: dict[str, Any] = {
        "total_candidates": total_candidates,
        "processed_count": processed,
        "limited": bool(config.limit and config.limit > 0),
        "dry_run": config.dry_run,
    }
    logger.info(f"Workflow complete. Summary: {summary}")
    return summary


# -------------
# Click-based CLI
# -------------


@click.group()
def cli() -> None:
    """SEC EDGAR Full Index CLI.

    Use 'run' for non-interactive execution, or 'interactive' to be prompted.
    """
    pass


def _validate_ticker_list_path(path: str | None) -> str | None:
    if not path:
        return None
    if not os.path.exists(path):
        raise click.ClickException(f"Ticker list file not found: {path}")
    return path


@cli.command("run")
@click.option(
    "--ticker-list",
    type=str,
    default=str(settings.ticker_list_filepath)
    if getattr(settings, "ticker_list_filepath", None)
    else None,
    help="Path to a CSV file with one ticker per line. Leave empty to skip ticker filtering.",
)
@click.option(
    "--form-filter/--no-form-filter",
    default=True,
    help="Enable/disable filtering by settings.forms_list.",
)
@click.option(
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    help="Skip downloading if files already exist.",
)
@click.option(
    "--limit",
    type=int,
    default=0,
    show_default=True,
    help="Limit the number of filings to process (0 = no limit).",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Only preview the filings; do not process.",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    show_default=True,
)
@click.option(
    "--json-output/--no-json-output",
    default=False,
    help="Print a JSON summary to stdout for programmatic consumption.",
)
@click.option(
    "--use-queue/--no-use-queue",
    default=False,
    show_default=True,
    help="Enqueue this workflow as a task in the backend API instead of running locally.",
)
@click.option(
    "--queue-priority",
    type=click.Choice(["low", "normal", "high"], case_sensitive=False),
    default="normal",
    show_default=True,
)
@click.option(
    "--api-base",
    type=str,
    default=None,
    help="Override API base URL (e.g. http://127.0.0.1:8000). Uses SEC_API_BASE_URL or settings by default.",
)
def run_command(
    ticker_list: str | None,
    form_filter: bool,
    skip_if_exists: bool,
    limit: int,
    dry_run: bool,
    log_level: str,
    json_output: bool,
    use_queue: bool,
    queue_priority: str,
    api_base: str | None,
) -> None:
    """Run the workflow with provided options (non-interactive)."""
    ticker_list = _validate_ticker_list_path(ticker_list) if ticker_list else None
    cfg = FullIndexConfig(
        ticker_list=ticker_list,
        form_filter=form_filter,
        skip_if_exists=skip_if_exists,
        limit=limit if limit and limit > 0 else None,
        dry_run=dry_run,
        log_level=log_level,
    )
    # Simplified: removed external API task submission, running locally only
    # enqueued = maybe_enqueue_task(
    #     use_queue=use_queue,
    #     name="full_index_workflow",
    #     parameters={
    #         "ticker_list": ticker_list,
    #         "form_filter": form_filter,
    #         "skip_if_exists": skip_if_exists,
    #         "limit": cfg.limit,
    #         "dry_run": dry_run,
    #         "log_level": log_level,
    #     },
    #     priority=queue_priority.lower(),
    #     json_output=json_output,
    #     api_base=api_base,
    # )
    # if enqueued:
    #     return

    # Always run locally

    click.echo("\nRunning Full Index workflow...\n")
    summary = run_full_index_workflow(cfg)
    if json_output:
        click.echo(json.dumps(summary, default=str))


@cli.command("interactive")
def interactive_command() -> None:
    """Prompt for options and run the workflow interactively."""
    click.echo("Interactive Full Index workflow setup:\n")

    # Ticker list path (optional)
    use_ticker_filter = click.confirm(
        "Filter by ticker list?",
        default=bool(getattr(settings, "ticker_list_filepath", None)),
    )
    ticker_list: str | None = None
    if use_ticker_filter:
        default_path = (
            str(getattr(settings, "ticker_list_filepath", ""))
            if getattr(settings, "ticker_list_filepath", None)
            else ""
        )
        ticker_list = click.prompt(
            "Path to ticker list CSV (leave empty to cancel ticker filter)",
            default=default_path,
            type=str,
        )
        if ticker_list:
            ticker_list = ticker_list.strip() or None
        if ticker_list:
            ticker_list = _validate_ticker_list_path(ticker_list)

    # Form filter toggle
    form_filter = click.confirm(
        "Filter by forms from settings.forms_list?", default=True
    )

    # Skip if exists toggle
    skip_if_exists = click.confirm(
        "Skip downloads if files already exist?", default=True
    )

    # Limit
    apply_limit = click.confirm("Limit number of filings to process?", default=False)
    limit: int | None = None
    if apply_limit:
        limit_val = click.prompt("Enter limit (integer > 0)", default=50, type=int)
        limit = max(1, int(limit_val))

    # Dry run
    dry_run = click.confirm("Dry run (preview only)?", default=False)

    # Log level
    log_level = click.prompt(
        "Log level",
        type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
        ),
        default="INFO",
    )

    cfg = FullIndexConfig(
        ticker_list=ticker_list,
        form_filter=form_filter,
        skip_if_exists=skip_if_exists,
        limit=limit,
        dry_run=dry_run,
        log_level=log_level,
    )
    # Simplified: removed external API task submission, always running locally
    # use_queue = click.confirm("Enqueue this as a backend task instead of running locally?", default=False)
    # if use_queue:
    #     enqueued = maybe_enqueue_task(...)
    #     if enqueued:
    #         return

    click.echo("\nRunning Full Index workflow...\n")
    run_full_index_workflow(cfg)


def main() -> None:
    """Entry point that preserves prior behavior when invoked as a module."""
    cli()


if __name__ == "__main__":
    main()
