"""Storage protocols - Abstract interfaces for database-agnostic storage.

This module defines the contracts (protocols) for all storage operations.
Implementations can use PostgreSQL, SQLite, Elasticsearch, or any backend.

Design principles:
- Protocol-based (PEP 544) for structural subtyping
- Async-first for all I/O operations
- No implementation details leak into protocols
- Compatible with Capture Spine's existing patterns
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable
from uuid import UUID

if TYPE_CHECKING:
    from genai_spine.storage.schemas import (
        ExecutionCreate,
        ExecutionRecord,
        PromptCreate,
        PromptRecord,
        PromptUpdate,
        PromptVersionRecord,
    )


# =============================================================================
# Prompt Repository Protocol
# =============================================================================


@runtime_checkable
class PromptRepository(Protocol):
    """Abstract interface for prompt storage.

    Implementations must provide all methods for a complete prompt management
    system including CRUD, versioning, and querying.

    Compatible with Capture Spine's prompt tables:
    - prompts (with current_version_id reference)
    - prompt_versions (immutable version records)
    """

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    async def create(self, prompt: PromptCreate) -> PromptRecord:
        """Create a new prompt with initial version.

        Args:
            prompt: Prompt creation data

        Returns:
            Created prompt record with ID and version info

        Raises:
            DuplicateError: If slug already exists
        """
        ...

    @abstractmethod
    async def get(self, prompt_id: UUID) -> PromptRecord | None:
        """Get prompt by ID.

        Args:
            prompt_id: Prompt UUID

        Returns:
            Prompt record or None if not found
        """
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> PromptRecord | None:
        """Get prompt by unique slug.

        Args:
            slug: URL-safe identifier (e.g., "rewrite-clean")

        Returns:
            Prompt record or None if not found
        """
        ...

    @abstractmethod
    async def update(
        self,
        prompt_id: UUID,
        update: PromptUpdate,
        change_notes: str | None = None,
    ) -> PromptRecord:
        """Update a prompt, creating new version if content changes.

        Following Capture Spine pattern:
        - Metadata changes (name, tags) update prompt directly
        - Content changes (system_prompt, user_prompt_template) create new version

        Args:
            prompt_id: Prompt UUID
            update: Fields to update
            change_notes: Description of changes (for version history)

        Returns:
            Updated prompt record

        Raises:
            NotFoundError: If prompt doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, prompt_id: UUID, soft: bool = True) -> bool:
        """Delete a prompt.

        Args:
            prompt_id: Prompt UUID
            soft: If True, set is_active=False; if False, hard delete

        Returns:
            True if deleted, False if not found
        """
        ...

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    async def list(
        self,
        *,
        category: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        is_system: bool | None = None,
        is_public: bool | None = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PromptRecord], int]:
        """List prompts with filtering.

        Args:
            category: Filter by category
            tags: Filter by any of these tags
            search: Search in name and description
            is_system: Filter system/user prompts
            is_public: Filter public/private prompts
            include_inactive: Include soft-deleted prompts
            limit: Max results to return
            offset: Pagination offset

        Returns:
            Tuple of (prompts, total_count)
        """
        ...

    # -------------------------------------------------------------------------
    # Version Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_version(
        self,
        prompt_id: UUID,
        version: int | None = None,
    ) -> PromptVersionRecord | None:
        """Get a specific version of a prompt.

        Args:
            prompt_id: Prompt UUID
            version: Version number (None = current version)

        Returns:
            Version record or None if not found
        """
        ...

    @abstractmethod
    async def list_versions(
        self,
        prompt_id: UUID,
        limit: int = 50,
    ) -> list[PromptVersionRecord]:
        """List version history for a prompt.

        Args:
            prompt_id: Prompt UUID
            limit: Max versions to return (newest first)

        Returns:
            List of version records, newest first
        """
        ...

    @abstractmethod
    async def rollback_to_version(
        self,
        prompt_id: UUID,
        version: int,
    ) -> PromptRecord:
        """Rollback prompt to a previous version.

        Creates a new version with content from the specified version.

        Args:
            prompt_id: Prompt UUID
            version: Version number to rollback to

        Returns:
            Updated prompt record with new version

        Raises:
            NotFoundError: If prompt or version doesn't exist
        """
        ...


# =============================================================================
# Execution Repository Protocol
# =============================================================================


@runtime_checkable
class ExecutionRepository(Protocol):
    """Abstract interface for execution/transformation tracking.

    Tracks every LLM call for:
    - Cost tracking and budgeting
    - Performance monitoring
    - Audit trail
    - Usage analytics

    Compatible with Capture Spine's transformations table.
    """

    @abstractmethod
    async def record(self, execution: ExecutionCreate) -> ExecutionRecord:
        """Record an execution.

        Args:
            execution: Execution data

        Returns:
            Created execution record
        """
        ...

    @abstractmethod
    async def get(self, execution_id: UUID) -> ExecutionRecord | None:
        """Get execution by ID.

        Args:
            execution_id: Execution UUID

        Returns:
            Execution record or None
        """
        ...

    @abstractmethod
    async def list(
        self,
        *,
        prompt_id: UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
        capability: str | None = None,
        success: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ExecutionRecord], int]:
        """List executions with filtering.

        Args:
            prompt_id: Filter by prompt
            provider: Filter by provider
            model: Filter by model
            capability: Filter by capability (summarize, extract, etc.)
            success: Filter by success/failure
            since: Filter by start time
            until: Filter by end time
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (executions, total_count)
        """
        ...

    @abstractmethod
    async def get_usage_stats(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        group_by: str = "day",  # day, provider, model
    ) -> list[dict[str, Any]]:
        """Get aggregated usage statistics.

        Args:
            since: Start of period
            until: End of period
            group_by: Grouping dimension

        Returns:
            List of aggregated stats
        """
        ...


# =============================================================================
# Unit of Work Protocol (for transactions)
# =============================================================================


@runtime_checkable
class UnitOfWork(Protocol):
    """Abstract interface for transaction management.

    Provides a way to group multiple repository operations into
    a single transaction that can be committed or rolled back.
    """

    prompts: PromptRepository
    executions: ExecutionRepository

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        """Enter transaction context."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit transaction context, committing or rolling back."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...


# =============================================================================
# Storage Backend Protocol
# =============================================================================


@runtime_checkable
class StorageBackend(Protocol):
    """Abstract interface for storage backend lifecycle.

    Manages connection pools, initialization, and health checks.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend.

        Creates tables, runs migrations, seeds default data.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close connections and clean up resources."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage is healthy and accessible."""
        ...

    @abstractmethod
    def unit_of_work(self) -> UnitOfWork:
        """Create a new unit of work for transaction management."""
        ...
