"""
Main CLI entry point for py-sec-edgar.

This module provides a unified command-line interface for all SEC EDGAR operations.
"""

import logging
from datetime import datetime
from pathlib import Path

import click

from py_sec_edgar.cli.commands.feeds import feeds_group
from py_sec_edgar.cli.commands.filters import filters_group
from py_sec_edgar.cli.commands.process import process_group
from py_sec_edgar.cli.commands.search import search_group
from py_sec_edgar.cli.commands.utils import utils_group
from py_sec_edgar.cli.commands.workflows import workflows_group
from py_sec_edgar.logging_utils import setup_logging
from py_sec_edgar.settings import settings

# Configure logging with file output in logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)  # Create logs directory if it doesn't exist
log_file = logs_dir / f"sec_edgar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
setup_logging(log_file=str(log_file))
logger = logging.getLogger(__name__)


@click.group(name="py-sec-edgar")
@click.version_option(version="1.2.0")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Set logging level",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    help="Override default data directory",
)
@click.pass_context
def cli(ctx: click.Context, log_level: str, data_dir: Path | None) -> None:
    """
    SEC EDGAR Filing Processor

    A comprehensive tool for downloading, processing, and analyzing SEC EDGAR filings.
    """
    # Ensure that ctx.obj exists and is a dict (used for passing data between commands)
    ctx.ensure_object(dict)

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))

    # Override data directory if provided
    if data_dir:
        settings.sec_data_dir = str(data_dir)
        settings.ensure_directories()

    ctx.obj["settings"] = settings
    logger.info(f"py-sec-edgar v1.1.0 - Log level: {log_level}")


# Register command groups

# Register command groups
cli.add_command(feeds_group)
cli.add_command(filters_group)
cli.add_command(process_group)
cli.add_command(workflows_group)
cli.add_command(utils_group)
cli.add_command(search_group)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
