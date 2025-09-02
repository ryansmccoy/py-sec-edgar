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

__version__ = "1.1.0"
__author__ = "Ryan S. McCoy"
__email__ = "github@ryansmccoy.com"
__license__ = "MIT"
__repository__ = "https://github.com/ryansmccoy/py-sec-edgar"

# Core configuration and settings
from .settings import settings

# Main processing classes
from .process import FilingProcessor
from .extract import extract

# Workflow functions for programmatic access
from .workflows.full_index_workflow import run_full_index_workflow, FullIndexConfig
from .workflows.daily_workflow import main as run_daily_workflow
from .workflows.rss_workflow import main as run_rss_workflow

# Utility functions
from .utilities import (
    cik_column_to_list,
    format_filename,
    file_size
)

# Feed processors
from .feeds import full_index, daily, monthly, recent_filings

__all__ = [
    # Core components
    "settings",
    "FilingProcessor", 
    "extract",
    
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
    "recent_filings",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__repository__"
]
