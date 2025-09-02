"""Full Index SEC EDGAR workflow

Provides an interactive and scriptable command-line interface (CLI) to run the
"Full Index" ingestion workflow, and exposes a reusable function for API/frontend
integration.

Run examples:
- python -m sec_edgar_core.full_index_workflow run --help
- python -m sec_edgar_core.full_index_workflow interactive
"""
import logging

# Set up logging at the module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('logs/sec_edgar_main.log')  # File output
    ]
)

logger = logging.getLogger(__name__)

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from dataclasses import dataclass
from pprint import pprint
from typing import Any
from urllib.parse import urljoin

import click
import pandas as pd
import pyarrow.parquet as pq

import py_sec_edgar.feeds.full_index

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
    ticker_list: str | None = str(settings.ticker_list_filepath) if getattr(settings, 'ticker_list_filepath', None) else None
    form_filter: bool = True
    custom_forms: list[str] | None = None  # custom forms list to override settings.forms_list
    skip_if_exists: bool = True
    limit: int | None = None  # limit number of filings to process
    dry_run: bool = False        # don't process filings, just preview
    log_level: str = "INFO"      # DEBUG, INFO, WARNING, ERROR, CRITICAL


def set_log_level(level: str) -> None:
    """Set logger level dynamically for this module and root handlers."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logging.getLogger().setLevel(numeric_level)
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


def _filter_by_tickers(df_idx: pd.DataFrame, df_cik_tickers: pd.DataFrame, ticker_list_path: str | None) -> pd.DataFrame:
    if not ticker_list_path:
        return df_idx
    logger.info(f"Filtering by ticker list: {ticker_list_path}")
    try:
        tickers = pd.read_csv(ticker_list_path, header=None).iloc[:, 0].astype(str).str.strip().tolist()
    except Exception as e:
        logger.warning(f"Failed to read ticker list from {ticker_list_path}: {e}")
        return df_idx
    df_symbols = df_cik_tickers[df_cik_tickers['SYMBOL'].astype(str).isin(tickers)]
    logger.info(f"Filtered to {len(df_symbols)} companies from ticker list")
    cik_list = cik_column_to_list(df_symbols)
    out = df_idx[df_idx['CIK'].isin(cik_list)]
    logger.info(f"Filtered filings by CIK to {len(out)} rows")
    return out


def _apply_form_filter(df_idx: pd.DataFrame, enabled: bool, custom_forms: list[str] | None = None) -> pd.DataFrame:
    if not enabled:
        return df_idx
    # Use custom forms if provided, otherwise fall back to settings
    forms = custom_forms if custom_forms else getattr(settings, 'forms_list', None)
    if not forms:
        logger.info("Form filter enabled but no forms specified; skipping form filter")
        return df_idx
    logger.info(f"Filtering by forms: {forms}")
    out = df_idx[df_idx['Form Type'].isin(forms)]
    logger.info(f"Filtered to {len(out)} filings by form type")
    return out


def _prepare_filings_df(df_idx: pd.DataFrame) -> pd.DataFrame:
    # Create a new column with absolute URLs to filings
    return df_idx.assign(url=df_idx['Filename'].apply(lambda x: urljoin(settings.edgar_archives_url, x)))


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
        f"log_level={config.log_level})"
    )

    # 1) Download/refresh feeds
    logger.info("Updating full index feed...")
    py_sec_edgar.feeds.full_index.update_full_index_feed(skip_if_exists=config.skip_if_exists)
    logger.info("Full index feed update complete")

    # 2) Load base data
    df_cik_tickers = _load_cik_tickers()
    df_idx = _load_full_index_table()

    # 3) Apply filters
    df_idx = _apply_form_filter(df_idx, enabled=config.form_filter, custom_forms=config.custom_forms)
    df_idx = _filter_by_tickers(df_idx, df_cik_tickers, config.ticker_list)

    # 4) Prepare URLs
    df_filings = _prepare_filings_df(df_idx)

    # 5) Optional limit
    total_candidates = len(df_filings)
    if config.limit is not None and config.limit > 0:
        df_filings = df_filings.head(config.limit)
        logger.info(f"Applying limit: processing first {len(df_filings)} of {total_candidates} filings")
    else:
        logger.info(f"Processing all {total_candidates} filings")

    # 6) Process or preview
    processed = 0
    if config.dry_run:
        logger.info("Dry run: previewing filings without processing")
        preview_rows = min(5, len(df_filings))
        logger.info(f"Preview of first {preview_rows} filings:")
        for _, row in df_filings.head(preview_rows).iterrows():
            logger.info(f"- {row['Form Type']} | CIK {row['CIK']} | {row['Date Filed']} | {row['url']}")
    else:
        # Use a project-relative path for filing data
        filing_data_dir = str(settings.base_dir / "data" / "Archives" / "edgar" / "data")
        logger.info(f"Filing data directory: {filing_data_dir}")
        filing_broker = FilingProcessor(filing_data_dir=filing_data_dir, edgar_Archives_url=settings.edgar_archives_url)

        logger.info(f"Starting to process {len(df_filings)} filings...")
        for i, sec_filing in df_filings.iterrows():
            logger.info(
                f"Processing filing {processed+1}/{len(df_filings)}: {sec_filing['Form Type']} for CIK {sec_filing['CIK']}"
            )
            # Log filing details in a clean format
            logger.info(
                f"📄 {sec_filing['Company Name']} | {sec_filing['Form Type']} | "
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
@click.option("--ticker-list", type=str, default=str(settings.ticker_list_filepath) if getattr(settings, 'ticker_list_filepath', None) else None, help="Path to a CSV file with one ticker per line. Leave empty to skip ticker filtering.")
@click.option("--form-filter/--no-form-filter", default=True, help="Enable/disable filtering by settings.forms_list.")
@click.option("--skip-if-exists/--no-skip-if-exists", default=True, help="Skip downloading if files already exist.")
@click.option("--limit", type=int, default=0, show_default=True, help="Limit the number of filings to process (0 = no limit).")
@click.option("--dry-run/--no-dry-run", default=False, help="Only preview the filings; do not process.")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False), default="INFO", show_default=True)
@click.option("--json-output/--no-json-output", default=False, help="Print a JSON summary to stdout for programmatic consumption.")
@click.option("--use-queue/--no-use-queue", default=False, show_default=True, help="Enqueue this workflow as a task in the backend API instead of running locally.")
@click.option("--queue-priority", type=click.Choice(["low","normal","high"], case_sensitive=False), default="normal", show_default=True)
@click.option("--api-base", type=str, default=None, help="Override API base URL (e.g. http://127.0.0.1:8000). Uses SEC_API_BASE_URL or settings by default.")
def run_command(ticker_list: str | None, form_filter: bool, skip_if_exists: bool, limit: int, dry_run: bool, log_level: str, json_output: bool, use_queue: bool, queue_priority: str, api_base: str | None) -> None:
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
    use_ticker_filter = click.confirm("Filter by ticker list?", default=bool(getattr(settings, 'ticker_list_filepath', None)))
    ticker_list: str | None = None
    if use_ticker_filter:
        default_path = str(getattr(settings, 'ticker_list_filepath', '')) if getattr(settings, 'ticker_list_filepath', None) else ''
        ticker_list = click.prompt("Path to ticker list CSV (leave empty to cancel ticker filter)", default=default_path, type=str)
        if ticker_list:
            ticker_list = ticker_list.strip() or None
        if ticker_list:
            ticker_list = _validate_ticker_list_path(ticker_list)

    # Form filter toggle
    form_filter = click.confirm("Filter by forms from settings.forms_list?", default=True)

    # Skip if exists toggle
    skip_if_exists = click.confirm("Skip downloads if files already exist?", default=True)

    # Limit
    apply_limit = click.confirm("Limit number of filings to process?", default=False)
    limit: int | None = None
    if apply_limit:
        limit_val = click.prompt("Enter limit (integer > 0)", default=50, type=int)
        limit = max(1, int(limit_val))

    # Dry run
    dry_run = click.confirm("Dry run (preview only)?", default=False)

    # Log level
    log_level = click.prompt("Log level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False), default="INFO")

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
