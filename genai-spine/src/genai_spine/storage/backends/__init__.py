"""Refactored storage backends for GenAI-Spine.

This package provides lightweight facades that use shared components
for common functionality. The backends maintain full API compatibility
with the original implementations while eliminating code duplication.

Usage:
    # SQLite (always available)
    from genai_spine.storage.backends import SQLiteBackend

    # PostgreSQL (requires asyncpg)
    try:
        from genai_spine.storage.backends import PostgresBackend
    except ImportError:
        PostgresBackend = None  # asyncpg not installed
"""

from genai_spine.storage.backends.sqlite import (
    SQLiteBackend,
    SQLiteExecutionRepository,
    SQLitePromptRepository,
    SQLiteUnitOfWork,
)

# PostgreSQL is optional (requires asyncpg)
try:
    from genai_spine.storage.backends.postgres import (
        PostgresBackend,
        PostgresExecutionRepository,
        PostgresPromptRepository,
        PostgresUnitOfWork,
    )

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    PostgresBackend = None  # type: ignore
    PostgresExecutionRepository = None  # type: ignore
    PostgresPromptRepository = None  # type: ignore
    PostgresUnitOfWork = None  # type: ignore

__all__ = [
    # SQLite (always available)
    "SQLiteBackend",
    "SQLiteExecutionRepository",
    "SQLitePromptRepository",
    "SQLiteUnitOfWork",
    # PostgreSQL (optional)
    "PostgresBackend",
    "PostgresExecutionRepository",
    "PostgresPromptRepository",
    "PostgresUnitOfWork",
    "HAS_POSTGRES",
]
