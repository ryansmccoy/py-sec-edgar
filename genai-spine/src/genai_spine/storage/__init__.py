"""Storage module for GenAI Spine.

Provides database-agnostic storage with multiple backend support:
- SQLite (default, for development/testing)
- PostgreSQL (production)
- More backends can be added (Elasticsearch, etc.)

Usage:
    # Using factory (recommended)
    from genai_spine.storage import create_backend, BackendType

    backend = create_backend(BackendType.SQLITE, "prompts.db")
    await backend.initialize()

    async with backend.unit_of_work() as uow:
        prompt = await uow.prompts.get_by_slug("rewrite-clean")
        ...

    # Direct instantiation
    from genai_spine.storage.sqlite import SQLiteBackend
    from genai_spine.storage.postgres import PostgresBackend

    # SQLite
    backend = SQLiteBackend("prompts.db")

    # PostgreSQL
    backend = PostgresBackend("postgresql://user:pass@localhost/genai")
"""

from enum import Enum
from typing import TYPE_CHECKING

# Legacy exports (SQLAlchemy-based, to be deprecated)
from genai_spine.storage.models import (
    DailyCost,
    Execution,
    Prompt,
    PromptVersion,
)

# New protocol-based exports
from genai_spine.storage.protocols import (
    ExecutionRepository,
    PromptRepository,
    StorageBackend,
    UnitOfWork,
)
from genai_spine.storage.schemas import (
    ExecutionCreate,
    ExecutionRecord,
    PromptCategory,
    PromptCreate,
    PromptRecord,
    PromptUpdate,
    PromptVariable,
    PromptVersionRecord,
    SessionCreate,
    SessionMessageCreate,
    SessionMessageRecord,
    SessionRecord,
    UsageStats,
)

if TYPE_CHECKING:
    from genai_spine.storage.postgres import PostgresBackend
    from genai_spine.storage.sqlite import SQLiteBackend


class BackendType(str, Enum):
    """Available storage backend types."""

    SQLITE = "sqlite"
    POSTGRES = "postgres"
    POSTGRESQL = "postgresql"  # Alias
    MEMORY = "memory"  # In-memory SQLite


def create_backend(
    backend_type: BackendType | str,
    connection_string: str | None = None,
    **kwargs,
) -> StorageBackend:
    """Factory function to create storage backends.

    Args:
        backend_type: Type of backend to create
        connection_string: Database connection string or path
        **kwargs: Backend-specific options

    Returns:
        Configured storage backend (not yet initialized)

    Example:
        # SQLite with file
        backend = create_backend(BackendType.SQLITE, "prompts.db")

        # In-memory SQLite
        backend = create_backend(BackendType.MEMORY)

        # PostgreSQL
        backend = create_backend(
            BackendType.POSTGRES,
            "postgresql://user:pass@localhost/genai",
            min_connections=5,
            max_connections=20,
        )

        # Then initialize
        await backend.initialize()
    """
    if isinstance(backend_type, str):
        backend_type = BackendType(backend_type.lower())

    if backend_type in (BackendType.SQLITE, BackendType.MEMORY):
        from genai_spine.storage.sqlite import SQLiteBackend

        db_path = ":memory:" if backend_type == BackendType.MEMORY else connection_string
        if db_path is None:
            raise ValueError("SQLite backend requires a database path")
        return SQLiteBackend(db_path)

    elif backend_type in (BackendType.POSTGRES, BackendType.POSTGRESQL):
        from genai_spine.storage.postgres import PostgresBackend

        if connection_string is None:
            raise ValueError("PostgreSQL backend requires a connection string")
        return PostgresBackend(
            connection_string,
            min_connections=kwargs.get("min_connections", 2),
            max_connections=kwargs.get("max_connections", 10),
        )

    else:
        raise ValueError(f"Unsupported backend type: {backend_type}")


__all__ = [
    # Factory
    "create_backend",
    "BackendType",
    # Protocols
    "StorageBackend",
    "UnitOfWork",
    "PromptRepository",
    "ExecutionRepository",
    # Schemas
    "PromptCategory",
    "PromptVariable",
    "PromptCreate",
    "PromptUpdate",
    "PromptRecord",
    "PromptVersionRecord",
    "ExecutionCreate",
    "ExecutionRecord",
    "UsageStats",
    # Legacy (deprecated)
    "DailyCost",
    "Execution",
    "Prompt",
    "PromptVersion",
]
