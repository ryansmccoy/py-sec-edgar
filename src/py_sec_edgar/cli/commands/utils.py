"""
Utility commands for SEC EDGAR data management.
"""

import logging
from pathlib import Path

import click

from ...core.path_utils import safe_join

logger = logging.getLogger(__name__)


@click.group(name="utils")
def utils_group() -> None:
    """Utility commands for data management and maintenance."""
    pass


@utils_group.command("status")
def status() -> None:
    """Show system status and configuration."""
    from py_sec_edgar.settings import settings

    click.echo("=" * 50)
    click.echo("SEC EDGAR System Status")
    click.echo("=" * 50)

    # Settings info
    click.echo(f"Data Directory: {settings.sec_data_dir}")
    click.echo(f"Reference Directory: {settings.ref_dir}")
    click.echo(f"Forms List: {', '.join(settings.forms_list)}")
    click.echo(f"Default Tickers: {', '.join(settings.default_tickers)}")

    # Directory status
    click.echo("\nDirectory Status:")
    directories = [
        ("SEC Data", settings.sec_data_dir),
        ("EDGAR Data", settings.edgar_data_dir),
        ("Full Index", settings.full_index_data_dir),
        ("Daily Index", settings.daily_index_data_dir),
        ("Monthly Data", settings.monthly_data_dir),
        ("Reference Data", settings.ref_dir),
    ]

    for name, path in directories:
        exists = "✅" if path.exists() else "❌"
        click.echo(f"  {exists} {name}: {path}")

    # File status
    click.echo("\nKey Files:")
    files = [
        ("Company Tickers", settings.company_tickers_json),
        ("CIK Tickers", settings.cik_tickers_csv),
        ("Ticker List", settings.ticker_list_filepath),
        ("Merged Index", settings.merged_idx_filepath),
    ]

    for name, path in files:
        exists = "✅" if path.exists() else "❌"
        click.echo(f"  {exists} {name}: {path}")


@utils_group.command("clean")
@click.option(
    "--cache-only", is_flag=True, help="Only clean cache files, not downloaded data"
)
@click.option(
    "--confirm/--no-confirm", default=True, help="Confirm before deleting files"
)
def clean(cache_only: bool, confirm: bool) -> None:
    """Clean downloaded data and cache files."""
    import shutil

    from py_sec_edgar.settings import settings

    if cache_only:
        click.echo("Cleaning cache files only...")
        # Clean Python cache files and temporary data
        cache_dirs_cleaned = 0

        # Clean __pycache__ directories
        import os

        for root, dirs, files in os.walk(settings.base_dir):
            if "__pycache__" in dirs:
                pycache_path = safe_join(root, "__pycache__")
                shutil.rmtree(pycache_path)
                cache_dirs_cleaned += 1

        # Clean pytest cache if exists
        pytest_cache = settings.base_dir / ".pytest_cache"
        if pytest_cache.exists():
            shutil.rmtree(pytest_cache)
            cache_dirs_cleaned += 1

        # Clean ruff cache if exists
        ruff_cache = settings.base_dir / ".ruff_cache"
        if ruff_cache.exists():
            shutil.rmtree(ruff_cache)
            cache_dirs_cleaned += 1

        click.echo(f"✅ Cleaned {cache_dirs_cleaned} cache directories")
    else:
        click.echo("This will delete ALL downloaded SEC data!")

        if confirm and not click.confirm("Are you sure you want to continue?"):
            click.echo("Operation cancelled.")
            return

        try:
            if settings.sec_data_dir.exists():
                shutil.rmtree(settings.sec_data_dir)
                settings.ensure_directories()
                click.echo("✅ Cleaned all data directories")
            else:
                click.echo("No data directories found to clean")

        except Exception as e:
            logger.error(f"Failed to clean data: {e}")
            raise click.ClickException(str(e))


@utils_group.command("init")
@click.option(
    "--data-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Custom data directory location",
)
def init(data_dir: Path | None) -> None:
    """Initialize the SEC EDGAR data environment."""
    from py_sec_edgar.settings import settings

    click.echo("Initializing SEC EDGAR environment...")

    if data_dir:
        settings.sec_data_dir = data_dir
        click.echo(f"Using custom data directory: {data_dir}")

    try:
        # Create directories
        settings.ensure_directories()

        # Create default ticker list if it doesn't exist
        if not settings.ticker_list_filepath.exists():
            with open(settings.ticker_list_filepath, "w") as f:
                f.write("\n".join(settings.default_tickers))
            click.echo(f"Created default ticker list: {settings.ticker_list_filepath}")

        click.echo("✅ Environment initialized successfully")

        # Show status
        from py_sec_edgar.cli.commands.utils import status

        click.echo()
        ctx = click.get_current_context()
        ctx.invoke(status)

    except Exception as e:
        logger.error(f"Failed to initialize environment: {e}")
        raise click.ClickException(str(e))


@utils_group.command("validate")
def validate() -> None:
    """Validate the current installation and configuration."""
    import importlib

    from py_sec_edgar.settings import settings

    click.echo("Validating py-sec-edgar installation...")

    # Check dependencies
    required_modules = [
        "pandas",
        "requests",
        "bs4",
        "lxml",
        "feedparser",
        "pyarrow",
        "chardet",
        "pydantic",
        "click",
    ]

    missing_modules = []
    for module in required_modules:
        try:
            importlib.import_module(module)
            click.echo(f"✅ {module}")
        except ImportError:
            click.echo(f"❌ {module} - MISSING")
            missing_modules.append(module)

    if missing_modules:
        click.echo(f"\n❌ Missing dependencies: {', '.join(missing_modules)}")
        click.echo("Install with: uv add " + " ".join(missing_modules))
        return

    # Check configuration
    click.echo("\nValidating configuration...")

    # Check write permissions
    try:
        test_file = settings.sec_data_dir / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
        click.echo("✅ Data directory is writable")
    except Exception:
        click.echo("❌ Data directory is not writable")

    click.echo("\n✅ Installation validation complete")
