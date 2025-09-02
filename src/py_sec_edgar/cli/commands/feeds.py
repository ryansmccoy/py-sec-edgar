"""
Feed management commands for SEC EDGAR data.
"""

import logging

import click

logger = logging.getLogger(__name__)


@click.group(name="feeds")
def feeds_group() -> None:
    """Manage SEC EDGAR data feeds (download and update index files)."""
    pass


@feeds_group.command("update-full-index")
@click.option(
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    show_default=True,
    help="Skip download if files already exist"
)
@click.option(
    "--save-csv/--no-save-csv",
    default=True,
    show_default=True,
    help="Convert IDX files to CSV format"
)
def update_full_index(skip_if_exists: bool, save_csv: bool) -> None:
    """Download and update the full index feed."""
    from py_sec_edgar.feeds.full_index import update_full_index_feed

    logger.info("Updating full index feed...")
    try:
        update_full_index_feed(save_idx_as_csv=save_csv, skip_if_exists=skip_if_exists)
        logger.info("✅ Full index feed updated successfully")
    except Exception as e:
        logger.error(f"❌ Failed to update full index feed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-daily-index")
@click.option(
    "--days-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of days back to process"
)
@click.option(
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    show_default=True,
    help="Skip download if files already exist"
)
def update_daily_index(days_back: int, skip_if_exists: bool) -> None:
    """Download and update daily index feeds."""
    from py_sec_edgar.feeds.daily import update_daily_index_feed

    logger.info(f"Updating daily index feed for last {days_back} days...")
    try:
        update_daily_index_feed(days_back=days_back, skip_if_exists=skip_if_exists)
        logger.info("✅ Daily index feed updated successfully")
    except Exception as e:
        logger.error(f"❌ Failed to update daily index feed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-monthly-xbrl")
@click.option(
    "--months-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back to process"
)
@click.option(
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    show_default=True,
    help="Skip download if files already exist"
)
def update_monthly_xbrl(months_back: int, skip_if_exists: bool) -> None:
    """Download and update monthly XBRL feeds."""
    from py_sec_edgar.feeds.monthly import update_monthly_xbrl_feed

    logger.info(f"Updating monthly XBRL feed for last {months_back} months...")
    try:
        update_monthly_xbrl_feed(months_back=months_back, skip_if_exists=skip_if_exists)
        logger.info("✅ Monthly XBRL feed updated successfully")
    except Exception as e:
        logger.error(f"❌ Failed to update monthly XBRL feed: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("fetch-recent-rss")
@click.option(
    "--count",
    type=int,
    default=100,
    show_default=True,
    help="Number of recent filings to fetch"
)
@click.option(
    "--form-type",
    type=str,
    help="Specific form type to filter (e.g., 8-K, 10-K)"
)
@click.option(
    "--save-json/--no-save-json",
    default=True,
    show_default=True,
    help="Save filings data as JSON file"
)
@click.option(
    "--save-csv/--no-save-csv",
    default=False,
    show_default=True,
    help="Save filings data as CSV file"
)
def fetch_recent_rss(count: int, form_type: str | None, save_json: bool, save_csv: bool) -> None:
    """Fetch recent filings from SEC EDGAR RSS feeds."""
    import json
    import csv
    from pathlib import Path
    from datetime import datetime
    from py_sec_edgar.feeds.recent_filings import fetch_recent_rss_filings
    from py_sec_edgar.settings import settings

    logger.info(f"Fetching {count} recent filings from RSS...")
    if form_type:
        logger.info(f"Filtering for form type: {form_type}")

    try:
        filings = fetch_recent_rss_filings(count=count, form_type=form_type)
        logger.info(f"✅ Fetched {len(filings)} recent filings")
        
        if not filings:
            logger.warning("No filings to save")
            return
        
        # Create output directory
        output_dir = settings.edgar_data_dir / "rss_feeds"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Save as JSON
        if save_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"recent_filings_{timestamp}.json"
            if form_type:
                json_filename = f"recent_filings_{form_type}_{timestamp}.json"
            
            json_path = output_dir / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(filings, f, indent=2, ensure_ascii=False, default=str)
            saved_files.append(str(json_path))
            logger.info(f"📄 Saved JSON: {json_path}")
        
        # Save as CSV
        if save_csv and filings:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"recent_filings_{timestamp}.csv"
            if form_type:
                csv_filename = f"recent_filings_{form_type}_{timestamp}.csv"
            
            csv_path = output_dir / csv_filename
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                if filings:
                    writer = csv.DictWriter(f, fieldnames=filings[0].keys())
                    writer.writeheader()
                    writer.writerows(filings)
            saved_files.append(str(csv_path))
            logger.info(f"📊 Saved CSV: {csv_path}")
        
        # Summary
        if saved_files:
            logger.info(f"📁 Output directory: {output_dir}")
            logger.info(f"💿 Files saved: {len(saved_files)}")
        
        # Display sample data
        if filings:
            logger.info("📋 Sample filing:")
            sample = filings[0]
            logger.info(f"   Company: {sample.get('company_name', 'N/A')}")
            logger.info(f"   Form: {sample.get('form_type', 'N/A')}")
            logger.info(f"   Filed: {sample.get('filed_date', 'N/A')}")
            logger.info(f"   URL: {sample.get('filing_url', 'N/A')}")
        
    except Exception as e:
        logger.error(f"❌ Failed to fetch recent RSS filings: {e}")
        raise click.ClickException(str(e))


@feeds_group.command("update-all")
@click.option(
    "--skip-if-exists/--no-skip-if-exists",
    default=True,
    show_default=True,
    help="Skip download if files already exist"
)
@click.option(
    "--days-back",
    type=int,
    default=5,
    show_default=True,
    help="Number of days back for daily index"
)
@click.option(
    "--months-back",
    type=int,
    default=1,
    show_default=True,
    help="Number of months back for monthly XBRL"
)
@click.option(
    "--rss-count",
    type=int,
    default=100,
    show_default=True,
    help="Number of recent filings to fetch from RSS"
)
@click.option(
    "--skip-rss",
    is_flag=True,
    help="Skip RSS feed updates"
)
@click.option(
    "--skip-daily",
    is_flag=True,
    help="Skip daily index updates"
)
@click.option(
    "--skip-monthly",
    is_flag=True,
    help="Skip monthly XBRL updates"
)
@click.option(
    "--skip-full-index",
    is_flag=True,
    help="Skip full index updates"
)
def update_all(
    skip_if_exists: bool,
    days_back: int,
    months_back: int,
    rss_count: int,
    skip_rss: bool,
    skip_daily: bool,
    skip_monthly: bool,
    skip_full_index: bool
) -> None:
    """Update all SEC EDGAR data feeds in sequence.
    
    This command runs all feed update operations:
    1. Daily index (recent business days)
    2. Monthly XBRL (recent months) 
    3. Full index (quarterly data)
    4. Recent RSS filings
    
    Use --skip-* flags to exclude specific feeds.
    """
    logger.info("🚀 Starting comprehensive feed update...")
    
    operations = []
    if not skip_daily:
        operations.append(("Daily Index", "update_daily_index", {"days_back": days_back, "skip_if_exists": skip_if_exists}))
    if not skip_monthly:
        operations.append(("Monthly XBRL", "update_monthly_xbrl", {"months_back": months_back, "skip_if_exists": skip_if_exists}))
    if not skip_full_index:
        operations.append(("Full Index", "update_full_index", {"skip_if_exists": skip_if_exists, "save_csv": True}))
    if not skip_rss:
        operations.append(("RSS Feeds", "fetch_recent_rss", {"count": rss_count, "form_type": None}))
    
    total_operations = len(operations)
    logger.info(f"Will run {total_operations} feed update operations")
    
    results = {}
    for i, (name, func_name, kwargs) in enumerate(operations, 1):
        logger.info(f"[{i}/{total_operations}] Updating {name}...")
        try:
            if func_name == "update_daily_index":
                from py_sec_edgar.feeds.daily import update_daily_index_feed
                update_daily_index_feed(**kwargs)
            elif func_name == "update_monthly_xbrl":
                from py_sec_edgar.feeds.monthly import update_monthly_xbrl_feed
                update_monthly_xbrl_feed(**kwargs)
            elif func_name == "update_full_index":
                from py_sec_edgar.feeds.full_index import update_full_index_feed
                update_full_index_feed(**kwargs)
            elif func_name == "fetch_recent_rss":
                from py_sec_edgar.feeds.recent_filings import fetch_recent_rss_filings
                fetch_recent_rss_filings(**kwargs)
            
            results[name] = "✅ Success"
            logger.info(f"✅ {name} completed successfully")
        except Exception as e:
            results[name] = f"❌ Failed: {str(e)}"
            logger.error(f"❌ {name} failed: {e}")
            # Continue with other operations even if one fails
            continue
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 FEED UPDATE SUMMARY")
    logger.info("="*50)
    for operation, result in results.items():
        logger.info(f"  {operation}: {result}")
    
    failed_count = sum(1 for result in results.values() if result.startswith("❌"))
    if failed_count == 0:
        logger.info(f"\n🎉 All {total_operations} feed updates completed successfully!")
    else:
        logger.warning(f"\n⚠️  {failed_count} out of {total_operations} operations failed")
        if failed_count == total_operations:
            raise click.ClickException("All feed update operations failed")
