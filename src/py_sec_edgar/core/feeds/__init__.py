"""
Feed abstraction layer for py-sec-edgar

This package provides the abstract interfaces and registry pattern
for managing SEC EDGAR feed operations.
"""

from .base import AbstractFeed
from .registry import FeedRegistry

__all__ = ["AbstractFeed", "FeedRegistry"]
