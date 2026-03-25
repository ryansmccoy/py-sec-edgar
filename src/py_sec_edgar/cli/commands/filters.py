"""Data filtering and analysis commands for SEC EDGAR filings.

Provides fast preview, filtering, and export capabilities without full processing.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

import click
import feedparser
import pandas as pd
import pyarrow.parquet as pq

import py_sec_edgar.feeds.daily
import py_sec_edgar.feeds.monthly
from py_sec_edgar.cli.common import standard_form_options, standard_ticker_options
from py_sec_edgar.settings import settings
from py_sec_edgar.utilities import cik_column_to_list

logger = logging.getLogger(__name__)


@click.group()
def filters_group() -> None:
    """Filter and analyze SEC EDGAR data."""
    pass


@filters_group.command(name="daily")
@click.option("--start-date", type=str, default=None, help="Start date YYYY-MM-DD")
@click.option("--end-date", type=str, default=None, help="End date YYYY-MM-DD")
@click.option(
    "--days-back",
    type=int,
    default=730,
    show_default=True,
    help="How many days back to load when dates not provided (~2 years).",
)
@standard_ticker_options
@standard_form_options
@click.option(
    "--limit",
    type=int,
    default=50,
    show_default=True,
    help="Limit rows for display/output",
)
@click.option(
    "--json-output/--table-output",
    default=False,
    show_default=True,
    help="Print JSON summary instead of table",
)
@click.option(
    "--include-urls/--no-urls",
    default=False,
    show_default=True,
    help="Include filing URLs in output",
)
@click.option(
    "--save-csv",
    type=click.Path(),
    default=None,
    help="Save filtered results to CSV file",
)
@click.option(
    "--interactive/--no-interactive",
    default=False,
    show_default=True,
    help="Interactive parameter selection",
)
def filter_daily(
    start_date: str | None,
    end_date: str | None,
    days_back: int,
    tickers: tuple[str, ...],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: tuple[str, ...],
    form: tuple[str, ...],
    form_file: Path | None,
    no_form_filter: bool,
    limit: int,
    json_output: bool,
    include_urls: bool,
    save_csv: Path | None,
    interactive: bool,
) -> None:
    """Filter daily index filings by date range, forms, and/or ticker list."""

    if interactive:
        start_date = (
            click.prompt(
                "Start date (YYYY-MM-DD, empty to skip)",
                default=start_date or "",
                type=str,
            )
            or None
        )
        end_date = (
            click.prompt(
                "End date (YYYY-MM-DD, empty to skip)", default=end_date or "", type=str
            )
            or None
        )
        if not start_date and not end_date:
            days_back = click.prompt("Days back", default=days_back, type=int)

    # Ensure daily files are available
    logger.info("📊 Preparing daily filings filter...")
    py_sec_edgar.feeds.daily.update_daily_files(
        start_date=start_date, end_date=end_date, days_back=days_back
    )

    # Load CIK mapping
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))

    # Collect daily data
    from py_sec_edgar.feeds.daily import generate_daily_index_urls_and_filepaths

    daily_frames = []

    # Establish iteration window
    if start_date and end_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        current = end_dt
        while current >= start_dt:
            target_date = current
            current -= timedelta(days=1)
            if target_date.weekday() >= 5:  # Skip weekends
                continue
            daily_files = generate_daily_index_urls_and_filepaths(target_date)
            for _, filepath in daily_files:
                if os.path.exists(filepath) and "master" in filepath:
                    try:
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
                        )
                        df_daily["Date Filed"] = pd.to_datetime(df_daily["Date Filed"])
                        daily_frames.append(df_daily)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load {filepath}: {e}")
                        continue
    else:
        for days_ago in range(days_back):
            target_date = datetime.now() - timedelta(days=days_ago)
            if target_date.weekday() >= 5:  # Skip weekends
                continue
            daily_files = generate_daily_index_urls_and_filepaths(target_date)
            for _, filepath in daily_files:
                if os.path.exists(filepath) and "master" in filepath:
                    try:
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
                        )
                        df_daily["Date Filed"] = pd.to_datetime(df_daily["Date Filed"])
                        daily_frames.append(df_daily)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load {filepath}: {e}")
                        continue

    if not daily_frames:
        click.echo("❌ No daily filings found for the specified window.", err=True)
        return

    df = pd.concat(daily_frames, ignore_index=True).sort_values(
        "Date Filed", ascending=False
    )
    logger.info(f"📈 Loaded {len(df)} daily filing records")

    # Apply filtering
    df = _apply_filters(
        df,
        df_cik_tickers,
        tickers,
        ticker_file,
        no_ticker_filter,
        forms,
        form,
        form_file,
        no_form_filter,
    )

    # Generate URLs if requested
    if include_urls:
        df = df.assign(
            url=df["Filename"].apply(lambda x: urljoin(settings.edgar_archives_url, x))
        )

    # Output results
    _output_results(df, limit, json_output, save_csv, "daily")


@filters_group.command(name="full-index")
@standard_ticker_options
@standard_form_options
@click.option(
    "--limit",
    type=int,
    default=50,
    show_default=True,
    help="Limit rows for display/output",
)
@click.option(
    "--json-output/--table-output",
    default=False,
    show_default=True,
    help="Print JSON summary instead of table",
)
@click.option(
    "--include-urls/--no-urls",
    default=False,
    show_default=True,
    help="Include filing URLs in output",
)
@click.option(
    "--save-csv",
    type=click.Path(),
    default=None,
    help="Save filtered results to CSV file",
)
def filter_full_index(
    tickers: tuple[str, ...],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: tuple[str, ...],
    form: tuple[str, ...],
    form_file: Path | None,
    no_form_filter: bool,
    limit: int,
    json_output: bool,
    include_urls: bool,
    save_csv: Path | None,
) -> None:
    """Filter the full quarterly index by forms and/or ticker list."""

    logger.info("📊 Loading full index data...")

    # Load data
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))
    df_idx = (
        pq.read_table(str(settings.merged_idx_filepath))
        .to_pandas()
        .sort_values("Date Filed", ascending=False)
    )

    logger.info(f"📈 Loaded {len(df_idx)} full index records")

    # Apply filtering
    df_idx = _apply_filters(
        df_idx,
        df_cik_tickers,
        tickers,
        ticker_file,
        no_ticker_filter,
        forms,
        form,
        form_file,
        no_form_filter,
    )

    # Generate URLs if requested
    if include_urls:
        df_idx = df_idx.assign(
            url=df_idx["Filename"].apply(
                lambda x: urljoin(settings.edgar_archives_url, x)
            )
        )

    # Output results
    _output_results(df_idx, limit, json_output, save_csv, "full-index")


@filters_group.command(name="monthly-xbrl")
@click.option(
    "--months-back",
    type=int,
    default=24,
    show_default=True,
    help="How many months back to include (~2 years)",
)
@standard_ticker_options
@standard_form_options
@click.option(
    "--limit",
    type=int,
    default=50,
    show_default=True,
    help="Limit rows for display/output (0 for all)",
)
@click.option(
    "--json-output/--table-output",
    default=False,
    show_default=True,
    help="Print JSON summary instead of table",
)
@click.option(
    "--include-urls/--no-urls",
    default=False,
    show_default=True,
    help="Include filing URLs in output",
)
@click.option(
    "--save-csv",
    type=click.Path(),
    default=None,
    help="Save filtered results to CSV file",
)
@click.option(
    "--interactive/--no-interactive",
    default=False,
    show_default=True,
    help="Interactive parameter selection",
)
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="INFO",
    show_default=True,
    help="Set logging level",
)
def filter_monthly_xbrl(
    months_back: int,
    tickers: tuple[str, ...],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: tuple[str, ...],
    form: tuple[str, ...],
    form_file: Path | None,
    no_form_filter: bool,
    limit: int,
    json_output: bool,
    include_urls: bool,
    save_csv: Path | None,
    interactive: bool,
    log_level: str,
) -> None:
    """Filter monthly XBRL RSS-derived filings with forms/tickers."""

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if interactive:
        months_back = click.prompt("Months back", type=int, default=months_back)
        ticker_prompt = click.prompt(
            "Ticker list (comma-separated, empty to skip)",
            default="",
            show_default=False,
        )
        if ticker_prompt.strip():
            tickers = tuple(ticker_prompt.split(","))
        no_form_filter = not click.confirm(
            "Apply form type filter?", default=not no_form_filter
        )
        include_urls = click.confirm("Include filing URLs?", default=include_urls)
        limit = click.prompt("Preview limit (0 for all)", type=int, default=limit)

    logger.info("📊 Ensuring monthly XBRL feeds are current...")
    py_sec_edgar.feeds.monthly.download_and_flatten_monthly_xbrl_filings_list()

    # Load data
    df_cik_tickers = pd.read_csv(str(settings.cik_tickers_csv))

    from py_sec_edgar.feeds.monthly import generate_monthly_index_url_and_filepaths

    monthly_frames = []

    for months_ago in range(months_back):
        target_date = datetime.now() - timedelta(days=months_ago * 30)
        _, filepath = generate_monthly_index_url_and_filepaths(target_date)
        if os.path.exists(filepath):
            try:
                feed = feedparser.parse(filepath)
                rows = []
                for entry in feed.entries:
                    rows.append(
                        {
                            "CIK": entry.get("edgar_cik", ""),
                            "Company Name": entry.get("edgar_companyname", ""),
                            "Form Type": entry.get("edgar_formtype", ""),
                            "Date Filed": entry.get("edgar_fileddate", ""),
                            "Filename": entry.get("edgar_xbrlfile", ""),
                            "Title": entry.get("title", ""),
                            "Link": entry.get("link", ""),
                        }
                    )
                if rows:
                    dfm = pd.DataFrame(rows)
                    dfm["Date Filed"] = pd.to_datetime(
                        dfm["Date Filed"], errors="coerce"
                    )
                    dfm = dfm.dropna(subset=["Date Filed"])
                    monthly_frames.append(dfm)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse {filepath}: {e}")

    if not monthly_frames:
        click.echo("❌ No monthly XBRL rows found for window.", err=True)
        return

    df = pd.concat(monthly_frames, ignore_index=True).sort_values(
        "Date Filed", ascending=False
    )
    logger.info(f"📈 Loaded {len(df)} monthly XBRL records")

    # Apply filtering
    df = _apply_filters(
        df,
        df_cik_tickers,
        tickers,
        ticker_file,
        no_ticker_filter,
        forms,
        form,
        form_file,
        no_form_filter,
    )

    # Handle XBRL-specific URLs
    if include_urls:
        if "Link" in df.columns and not df["Link"].isna().all():
            df["url"] = df["Link"]
        else:
            df["url"] = df["Filename"].apply(
                lambda x: urljoin(settings.edgar_archives_url, x) if pd.notna(x) else ""
            )

    # Output results
    _output_results(
        df, limit if limit > 0 else len(df), json_output, save_csv, "monthly-xbrl"
    )


def _apply_filters(
    df: pd.DataFrame,
    df_cik_tickers: pd.DataFrame,
    tickers: tuple[str, ...],
    ticker_file: Path | None,
    no_ticker_filter: bool,
    forms: tuple[str, ...],
    form: tuple[str, ...],
    form_file: Path | None,
    no_form_filter: bool,
) -> pd.DataFrame:
    """Apply ticker and form filtering to dataframe."""

    # Form filtering
    if not no_form_filter:
        # Combine all form inputs
        all_forms = set(forms)
        all_forms.update(form)

        # Add forms from file
        if form_file and form_file.exists():
            with open(form_file) as f:
                file_forms = [line.strip() for line in f if line.strip()]
                all_forms.update(file_forms)

        # Use settings default if no forms specified
        if not all_forms and hasattr(settings, "forms_list") and settings.forms_list:
            all_forms = set(settings.forms_list)

        if all_forms:
            df = df[df["Form Type"].isin(all_forms)]
            logger.info(f"🔍 Form filter applied: {len(df)} records remaining")

    # Ticker filtering
    if not no_ticker_filter:
        # Combine all ticker inputs
        all_tickers = set()
        all_tickers.update(tickers)

        # Parse comma-separated tickers
        for ticker_group in tickers:
            if "," in ticker_group:
                all_tickers.update(t.strip().upper() for t in ticker_group.split(","))

        # Add tickers from file
        if ticker_file and ticker_file.exists():
            ticker_df = pd.read_csv(ticker_file, header=None)
            file_tickers = (
                ticker_df.iloc[:, 0].astype(str).str.strip().str.upper().tolist()
            )
            all_tickers.update(file_tickers)

        if all_tickers:
            # Filter CIK mapping by tickers
            df_symbols = df_cik_tickers[
                df_cik_tickers["SYMBOL"].astype(str).str.upper().isin(all_tickers)
            ]
            cik_list = cik_column_to_list(df_symbols)

            # Convert CIK column to numeric for comparison
            df["CIK"] = pd.to_numeric(df["CIK"], errors="coerce")
            df = df[df["CIK"].isin(cik_list)]
            logger.info(f"🔍 Ticker filter applied: {len(df)} records remaining")

    return df


def _output_results(
    df: pd.DataFrame,
    limit: int,
    json_output: bool,
    save_csv: Path | None,
    data_type: str,
) -> None:
    """Output filtered results in requested format."""

    total = len(df)
    preview = df.head(max(1, limit)) if limit > 0 else df

    if save_csv:
        preview.to_csv(save_csv, index=False)
        logger.info(f"💾 Saved filtered preview to {save_csv}")

    summary = {
        "data_type": data_type,
        "total_filtered_rows": int(total),
        "preview_rows": int(len(preview)),
        "columns": list(preview.columns),
    }

    if json_output:
        click.echo(json.dumps(summary, default=str, indent=2))
    else:
        click.echo(f"\n📊 **{data_type.upper()} FILTER RESULTS**")
        click.echo(f"Total filtered records: {total:,}")
        click.echo(f"Showing preview: {len(preview):,} records")
        click.echo("\n" + preview.to_string(index=False))
