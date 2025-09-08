"""
Modern SEC EDGAR Feed Management Commands

Consolidated, sync-first feed management with rich output and better user experience.
This replaces both feeds.py and feeds_enhanced.py with a single, clean implementation.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from py_sec_edgar.core.feed_manager import FilingFeedError, FilingFeedManager

logger = logging.getLogger(__name__)
console = Console()


@click.group(name="feeds")
def feeds_group() -> None:
    """Manage SEC EDGAR data feeds (download and update index files)."""
    pass


def _display_filing_samples(filings: list[dict[str, Any]], count: int = 3) -> None:
    """Display sample filings in a nice table format."""
    if not filings:
        console.print("📭 No filings found")
        return

    # Create table for sample filings
    table = Table(
        title=f"📄 Recent Filings (showing {min(count, len(filings))} of {len(filings)})"
    )
    table.add_column("Ticker", style="cyan", width=8)
    table.add_column("Company", style="blue", width=25)
    table.add_column("Form", style="green", width=8)
    table.add_column("Filed", style="yellow", width=12)
    table.add_column("Description", style="white", width=40)

    for filing in filings[:count]:
        ticker = filing.get("ticker", "N/A")[:7]
        company = filing.get("company_name", "N/A")[:24]
        form_type = filing.get("form_type", "N/A")
        filed_date = filing.get("filed_date", "N/A")
        description = filing.get("description", filing.get("filing_name", "N/A"))[:39]

        table.add_row(ticker, company, form_type, filed_date, description)

    console.print(table)


def _display_operation_summary(operation: str, result: Any, duration: float) -> None:
    """Display operation summary with consistent formatting."""
    if hasattr(result, "success") and result.success:
        items = getattr(result, "items_processed", 0)
        console.print(
            f"✅ {operation} completed: {items} items processed ({duration:.1f}s)"
        )
    else:
        error_msg = "Unknown error"
        if hasattr(result, "errors") and result.errors:
            error_msg = result.errors[0]
        console.print(f"❌ {operation} failed: {error_msg}")


@feeds_group.command("fetch-rss")
@click.option(
    "--count",
    type=int,
    default=20,
    show_default=True,
    help="Number of recent filings to fetch (max 400)",
)
@click.option(
    "--form-type", type=str, help="Filter by specific form type (e.g., 8-K, 10-K, 10-Q)"
)
@click.option("--ticker", type=str, help="Filter by company ticker symbol")
@click.option("--company", type=str, help="Filter by company name (partial match)")
@click.option("--save-json", type=click.Path(), help="Save results to JSON file")
@click.option("--save-csv", type=click.Path(), help="Save results to CSV file")
@click.option(
    "--show-samples",
    type=int,
    default=5,
    help="Number of sample filings to display (0 to hide)",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress detailed output")
def fetch_rss(
    count: int,
    form_type: str | None,
    ticker: str | None,
    company: str | None,
    save_json: str | None,
    save_csv: str | None,
    show_samples: int,
    quiet: bool,
) -> None:
    """Fetch recent SEC filings from RSS feed with rich output."""

    if not quiet:
        console.print(
            Panel(f"🚀 Fetching {count} Recent SEC Filings", style="bold blue")
        )

    manager = FilingFeedManager(console=console if not quiet else None)

    try:
        # Fetch filings
        result = manager.fetch_rss(
            count=count, form_type=form_type, company=company, show_progress=not quiet
        )

        if not result.success:
            error_msg = result.errors[0] if result.errors else "Unknown error"
            raise click.ClickException(f"RSS fetch failed: {error_msg}")

        filings = result.data if result.data else []

        # Filter by ticker if specified
        if ticker and filings:
            ticker_upper = ticker.upper()
            filings = [
                f for f in filings if f.get("ticker", "").upper() == ticker_upper
            ]

        if not quiet:
            console.print(f"📊 Successfully fetched {len(filings)} filings")

            # Show sample filings
            if show_samples > 0 and filings:
                _display_filing_samples(filings, show_samples)

        # Save to files if requested
        if save_json and filings:
            json_path = Path(save_json)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(filings, f, indent=2, ensure_ascii=False, default=str)
            console.print(f"💾 Saved to JSON: {json_path}")

        if save_csv and filings:
            csv_path = Path(save_csv)
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                if filings:
                    writer = csv.DictWriter(f, fieldnames=filings[0].keys())
                    writer.writeheader()
                    writer.writerows(filings)
            console.print(f"📊 Saved to CSV: {csv_path}")

        if not quiet:
            console.print("✅ RSS fetch operation completed successfully")

    except FilingFeedError as e:
        logger.error(f"RSS fetch failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-full-index")
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    show_default=True,
    help="Skip download if files already exist",
)
@click.option(
    "--save-csv/--no-save-csv",
    default=True,
    show_default=True,
    help="Convert IDX files to CSV format",
)
@click.option(
    "--merge/--no-merge",
    default=True,
    show_default=True,
    help="Merge index files after update",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
@click.option(
    "--start-year",
    type=int,
    help="Start year for historical data download (e.g., 2015)",
)
@click.option(
    "--end-year",
    type=int,
    help="End year for historical data download (defaults to current year)",
)
@click.option(
    "--last-5-years", is_flag=True, help="Download last 5 years of data (quick setup)"
)
@click.option(
    "--last-10-years",
    is_flag=True,
    help="Download last 10 years of data (comprehensive setup)",
)
@click.option(
    "--all-available",
    is_flag=True,
    help="Download all available historical data (1993-present, very large)",
)
def update_full_index(
    skip_existing: bool,
    save_csv: bool,
    merge: bool,
    quiet: bool,
    start_year: int | None,
    end_year: int | None,
    last_5_years: bool,
    last_10_years: bool,
    all_available: bool,
) -> None:
    """Download and update the full SEC EDGAR index feed.

    IMPORTANT: IDX files are updated quarterly by the SEC. Full index files are
    rebuilt weekly (Saturday mornings) to incorporate corrections. For the most
    current filings, use the search commands which access real-time SEC APIs.

    Examples:

      # Default: Download recent data (last ~2 years)
      py-sec-edgar feeds update-full-index

      # Download specific range
      py-sec-edgar feeds update-full-index --start-year 2015 --end-year 2020

      # Quick setups for common scenarios
      py-sec-edgar feeds update-full-index --last-5-years
      py-sec-edgar feeds update-full-index --last-10-years

      # Download everything (large download!)
      py-sec-edgar feeds update-full-index --all-available
    """

    # Handle date range options
    from datetime import datetime

    current_year = datetime.now().year

    # Validate conflicting options
    date_options = [start_year is not None, last_5_years, last_10_years, all_available]
    if sum(date_options) > 1:
        raise click.ClickException(
            "Cannot specify multiple date range options simultaneously"
        )

    # Set date range based on options
    custom_start_date = None
    custom_end_date = None

    if last_5_years:
        custom_start_date = f"1/1/{current_year - 5}"
        custom_end_date = f"12/31/{current_year}"
        if not quiet:
            console.print(
                f"[cyan]📅 Downloading last 5 years ({current_year - 5}-{current_year})[/cyan]"
            )

    elif last_10_years:
        custom_start_date = f"1/1/{current_year - 10}"
        custom_end_date = f"12/31/{current_year}"
        if not quiet:
            console.print(
                f"[cyan]📅 Downloading last 10 years ({current_year - 10}-{current_year})[/cyan]"
            )

    elif all_available:
        custom_start_date = "1/1/1993"  # SEC EDGAR started in 1993
        custom_end_date = f"12/31/{current_year}"
        if not quiet:
            console.print(
                f"[yellow]⚠️  Downloading ALL available data (1993-{current_year}) - This is a very large download![/yellow]"
            )
            if not click.confirm("Continue with full historical download?"):
                console.print("Download cancelled.")
                return

    elif start_year is not None:
        end_yr = end_year or current_year
        custom_start_date = f"1/1/{start_year}"
        custom_end_date = f"12/31/{end_yr}"
        if not quiet:
            console.print(
                f"[cyan]📅 Downloading custom range ({start_year}-{end_yr})[/cyan]"
            )

    # Show estimated download size warning for large ranges
    if custom_start_date and not quiet:
        years = (end_year or current_year) - (start_year or current_year - 2)
        if years > 5:
            estimated_size = years * 50  # Rough estimate: ~50MB per year
            console.print(
                f"[yellow]💾 Estimated download size: ~{estimated_size}MB ({years} years)[/yellow]"
            )

    if not quiet:
        console.print(Panel("🏗️ Updating Full SEC EDGAR Index", style="bold green"))

    manager = FilingFeedManager(console=console if not quiet else None)

    try:
        result = manager.update_full_index(
            save_csv=save_csv,
            skip_existing=skip_existing,
            merge_after_update=merge,
            show_progress=not quiet,
            custom_start_date=custom_start_date,
            custom_end_date=custom_end_date,
        )

        if not quiet:
            _display_operation_summary("Full index update", result, result.duration)

            if result.success and hasattr(result, "metadata"):
                metadata = result.metadata
                console.print(
                    f"📁 CSV conversion: {'✅ Enabled' if metadata.get('save_csv') else '❌ Disabled'}"
                )
                console.print(
                    f"🔗 Index merging: {'✅ Enabled' if metadata.get('merge_after_update') else '❌ Disabled'}"
                )

    except FilingFeedError as e:
        logger.error(f"Full index update failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-daily")
@click.option(
    "--days-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of days back to process",
)
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    show_default=True,
    help="Skip download if files already exist",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
def update_daily(days_back: int, skip_existing: bool, quiet: bool) -> None:
    """Download and update daily SEC filing index feeds."""

    if not quiet:
        console.print(
            Panel(f"📅 Updating Daily Index ({days_back} days back)", style="bold cyan")
        )

    manager = FilingFeedManager(console=console if not quiet else None)

    try:
        result = manager.update_daily(
            days_back=days_back, skip_existing=skip_existing, show_progress=not quiet
        )

        if not quiet:
            _display_operation_summary("Daily index update", result, result.duration)

    except FilingFeedError as e:
        logger.error(f"Daily index update failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-monthly")
@click.option(
    "--months-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back to process",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
def update_monthly(months_back: int, quiet: bool) -> None:
    """Download and update monthly XBRL data feeds."""

    if not quiet:
        console.print(
            Panel(
                f"📊 Updating Monthly XBRL ({months_back} months back)",
                style="bold magenta",
            )
        )

    manager = FilingFeedManager(console=console if not quiet else None)

    try:
        result = manager.update_monthly(
            months_back=months_back, show_progress=not quiet
        )

        if not quiet:
            _display_operation_summary("Monthly XBRL update", result, result.duration)

    except FilingFeedError as e:
        logger.error(f"Monthly XBRL update failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-all")
@click.option(
    "--daily-days",
    type=int,
    default=1,
    show_default=True,
    help="Number of days back for daily index",
)
@click.option(
    "--monthly-months",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back for monthly XBRL",
)
@click.option(
    "--rss-count",
    type=int,
    default=50,
    show_default=True,
    help="Number of recent filings to fetch from RSS",
)
@click.option(
    "--skip-existing/--no-skip-existing",
    default=True,
    show_default=True,
    help="Skip download if files already exist",
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
def update_all(
    daily_days: int,
    monthly_months: int,
    rss_count: int,
    skip_existing: bool,
    quiet: bool,
) -> None:
    """Update all SEC EDGAR data feeds sequentially."""

    if not quiet:
        console.print(Panel("🚀 Updating All SEC EDGAR Feeds", style="bold blue"))

    manager = FilingFeedManager(console=console if not quiet else None)

    try:
        results = manager.update_all(
            daily_days=daily_days,
            monthly_months=monthly_months,
            rss_count=rss_count,
            skip_existing=skip_existing,
            show_progress=not quiet,
        )

        # Results are already displayed by the manager
        successful = sum(1 for r in results.values() if r.success)
        total = len(results)

        if not quiet:
            if successful == total:
                console.print("🎉 All feed operations completed successfully!")
            else:
                console.print(
                    f"⚠️ {successful}/{total} feed operations completed successfully"
                )

    except FilingFeedError as e:
        logger.error(f"Batch feed update failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("status")
@click.option("--save-json", type=click.Path(), help="Save status to JSON file")
@click.option("--quiet", "-q", is_flag=True, help="Show minimal output")
def status(save_json: str | None, quiet: bool) -> None:
    """Display comprehensive feed system status."""

    if not quiet:
        console.print(Panel("📊 SEC EDGAR Feed System Status", style="bold blue"))

    manager = FilingFeedManager(console=console)

    try:
        status_info = manager.get_system_status()

        if not quiet:
            manager.display_status(status_info)

        if save_json:
            json_path = Path(save_json)
            json_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert status to JSON-serializable format
            json_data = {}
            for feed_type, feed_status in status_info.items():
                json_data[feed_type.value] = feed_status

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

            console.print(f"💾 Status saved to: {json_path}")

    except FilingFeedError as e:
        logger.error(f"Status check failed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("health-check")
@click.option(
    "--fix-issues", is_flag=True, help="Attempt to fix detected issues automatically"
)
def health_check(fix_issues: bool) -> None:
    """Perform comprehensive health check of feed system."""

    console.print(Panel("🔍 Performing Feed System Health Check", style="bold yellow"))

    manager = FilingFeedManager(console=console)

    try:
        status_info = manager.get_system_status()

        # Analyze health
        issues = []
        healthy_feeds = []

        for feed_type, feed_status in status_info.items():
            status_val = feed_status.get("status", "unknown")
            if status_val in ["available", "ready"]:
                healthy_feeds.append(feed_type)
            else:
                issues.append((feed_type, feed_status))

        # Display results
        if healthy_feeds:
            console.print(f"✅ Healthy feeds ({len(healthy_feeds)}):")
            for feed in healthy_feeds:
                feed_name = feed.value.replace("_", " ").title()
                console.print(f"  • {feed_name}")

        if issues:
            console.print(f"\n⚠️ Issues detected ({len(issues)}):")
            for feed_type, feed_status in issues:
                feed_name = feed_type.value.replace("_", " ").title()
                status_val = feed_status.get("status", "unknown")
                console.print(f"  • {feed_name}: {status_val}")
                if "error" in feed_status:
                    console.print(f"    - {feed_status['error']}")

            if fix_issues:
                console.print("\n🔧 Attempting to fix issues...")

                for feed_type, feed_status in issues:
                    status_val = feed_status.get("status", "unknown")
                    if status_val == "missing":
                        feed_name = feed_type.value.replace("_", " ").title()
                        console.print(f"  Updating missing feed: {feed_name}")
                        try:
                            if feed_type.value == "full_index":
                                manager.update_full_index(show_progress=False)
                            elif feed_type.value == "daily_index":
                                manager.update_daily(days_back=1, show_progress=False)
                            elif feed_type.value == "monthly_xbrl":
                                manager.update_monthly(
                                    months_back=1, show_progress=False
                                )
                            console.print(f"    ✅ Fixed: {feed_name}")
                        except Exception as e:
                            console.print(f"    ❌ Failed to fix {feed_name}: {e}")
            else:
                console.print("\n💡 To attempt automatic fixes, run with --fix-issues")
        else:
            console.print("🎉 All feeds are healthy!")

    except FilingFeedError as e:
        logger.error(f"Health check failed: {e}")
        raise click.ClickException(str(e))


# For backward compatibility, provide aliases for common commands
@feeds_group.command("rss")
def rss_alias():
    """Alias for fetch-rss with default parameters."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(fetch_rss, [])
    if result.exit_code != 0:
        raise click.ClickException("RSS fetch failed")


@feeds_group.command("full-index")
def full_index_alias():
    """Alias for update-full-index with default parameters."""
    from click.testing import CliRunner

    runner = CliRunner()
    result = runner.invoke(update_full_index, [])
    if result.exit_code != 0:
        raise click.ClickException("Full index update failed")
