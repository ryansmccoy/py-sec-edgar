"""
SEC EDGAR Workflows Module.

This module contains all workflow implementations for processing SEC EDGAR filings.
Each workflow is designed for specific use cases and data processing patterns.

Workflows:
    - full_index_workflow: Process quarterly EDGAR full index archives
    - daily_workflow: Process recent daily filings
    - monthly_workflow: Process monthly filing archives
    - rss_workflow: Process real-time RSS feeds

Example Usage:
    from py_sec_edgar.workflows.full_index_workflow import run_full_index_workflow
    from py_sec_edgar.workflows.daily_workflow import run_daily_workflow

    # Run individual workflows
    run_full_index_workflow(config)
    run_daily_workflow(config)
"""

from .daily_workflow import DailyConfig, run_daily_workflow
from .full_index_workflow import FullIndexConfig, run_full_index_workflow
from .monthly_workflow import main as run_monthly_workflow
from .rss_workflow import main as run_rss_workflow

__all__ = [
    "run_full_index_workflow",
    "FullIndexConfig",
    "run_daily_workflow",
    "DailyConfig",
    "run_monthly_workflow",
    "run_rss_workflow",
]
