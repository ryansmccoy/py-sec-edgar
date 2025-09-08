"""
🏢 py-sec-edgar: Professional SEC EDGAR Filing Processor

A comprehensive Python library for downloading, processing, and analyzing SEC EDGAR filings.
This package provides powerful workflows for accessing quarterly indexes, daily filings,
monthly XBRL data, and real-time RSS feeds from the SEC EDGAR database.

Key Features:
    📊 Multiple Data Sources: Full index, daily, monthly, and RSS feeds
    🔍 Smart Filtering: Filter by tickers, form types, date ranges, and more
    🚀 High Performance: Parallel processing and efficient data handling
    💾 Flexible Storage: Local file system with configurable paths
    🛠️ CLI Interface: Professional command-line tools for automation
    📋 Rich Logging: Comprehensive logging with progress tracking

Workflows Available:
    • full-index: Process quarterly SEC EDGAR indexes (comprehensive historical data)
    • daily: Process recent daily filings (last few days of activity)
    • monthly: Process monthly XBRL filings (structured financial data)
    • rss: Process real-time RSS feeds (latest filings with save/load/query)

Example Usage:
    ```python
    from py_sec_edgar import settings
    from py_sec_edgar.workflows.full_index_workflow import run_full_index_workflow, FullIndexConfig

    # Configure and run a workflow
    config = FullIndexConfig(
        ticker_list="path/to/tickers.csv",
        custom_forms=["10-K", "10-Q"],
        days_back=30
    )

    summary = run_full_index_workflow(config)
    print(f"Processed {summary['processed_count']} filings")
    ```

CLI Usage:
    ```bash
    # Download Apple's 10-K filings from recent quarters
    uv run python -m py_sec_edgar workflows full-index --tickers "AAPL" --forms "10-K"

    # Get recent 8-K filings and save to JSON
    uv run python -m py_sec_edgar workflows rss --forms "8-K" --count 100 --save-to-file recent_8k.json

    # Process daily filings for specific companies
    uv run python -m py_sec_edgar workflows daily --tickers "MSFT" "GOOGL" --days-back 5
    ```

Author: Ryan S. McCoy <github@ryansmccoy.com>
License: MIT
Repository: https://github.com/ryansmccoy/py-sec-edgar
"""

__version__ = "1.2.0"
__author__ = "Ryan S. McCoy"
__email__ = "github@ryansmccoy.com"
__license__ = "MIT"
__repository__ = "https://github.com/ryansmccoy/py-sec-edgar"

# Core configuration and settings
# Feed processors
# Modern search and programmatic interface
from .client import (
    SecEdgarClient,
    company,
    download,
    download_all,
    filings_summary,
    search,
    search_multiple_forms,
    search_portfolio,
)
from .core.models import FilingInfo, SearchResult
from .core.search_results import SearchResults
from .extract import extract
from .feeds import daily, full_index, monthly, rss

# Main processing classes
from .process import FilingProcessor
from .search_engine import FilingSearchEngine, FilingSearchError
from .settings import settings

# Utility functions
from .utilities import cik_column_to_list, file_size, format_filename
from .workflows.daily_workflow import main as run_daily_workflow

# Workflow functions for programmatic access
from .workflows.full_index_workflow import FullIndexConfig, run_full_index_workflow
from .workflows.rss_workflow import main as run_rss_workflow

__all__ = [
    # Core components
    "settings",
    "FilingProcessor",
    "extract",
    # Modern search interface
    "search",
    "download",
    "download_all",
    "company",
    "filings_summary",
    "search_portfolio",
    "search_multiple_forms",
    "SecEdgarClient",
    "FilingSearchEngine",
    "FilingSearchError",
    "FilingInfo",
    "SearchResult",
    "SearchResults",
    # Workflow functions
    "run_full_index_workflow",
    "run_daily_workflow",
    "run_rss_workflow",
    "FullIndexConfig",
    # Utilities
    "cik_column_to_list",
    "format_filename",
    "file_size",
    # Feed processors
    "full_index",
    "daily",
    "monthly",
    "rss",
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__repository__",
]
