"""Refactored PostgreSQL storage backend using shared components.

This is a lightweight facade that delegates to shared converters and query builders.
The original postgres.py (935 lines) has been refactored to use shared components,
reducing duplication while maintaining full API compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None  # type: ignore

from genai_spine.storage.schemas import (
    ExecutionCreate,
    ExecutionRecord,
    PromptCreate,
    PromptRecord,
    PromptUpdate,
    PromptVersionRecord,
)
from genai_spine.storage.shared import (
    PostgresQueryBuilder,
    ExecutionQueryBuilder,
    PromptQueryBuilder,
    content_changed,
    merge_update,
    row_to_execution,
    row_to_prompt,
    row_to_version,
    serialize_variables_list,
)

# Import schema from original module
from genai_spine.storage.postgres import SCHEMA_SQL


def _require_asyncpg() -> None:
    """Raise helpful error if asyncpg not installed."""
    if not HAS_ASYNCPG:
        raise ImportError(
            "PostgreSQL support requires asyncpg. Install with: pip install genai-spine[postgres]"
        )


# =============================================================================
# PostgreSQL Prompt Repository (Refactored)
# =============================================================================


class PostgresPromptRepository:
    """PostgreSQL implementation of PromptRepository using shared components."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._qb = PromptQueryBuilder(PostgresQueryBuilder())

    async def create(self, prompt: PromptCreate) -> PromptRecord:
        """Create a new prompt with initial version."""
        prompt_id = uuid4()
        version_id = uuid4()

        await self._conn.execute(
            """
            INSERT INTO prompts (
                id, slug, name, description, category, tags,
                system_prompt, user_prompt_template, variables,
                preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                is_system, is_public, is_active, created_by,
                version, current_version_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
            """,
            prompt_id,
            prompt.slug,
            prompt.name,
            prompt.description,
            prompt.category.value,
            prompt.tags,
            prompt.system_prompt,
            prompt.user_prompt_template,
            json.dumps(serialize_variables_list(prompt.variables)),
            prompt.preferred_provider,
            prompt.preferred_model,
            prompt.temperature,
            prompt.max_tokens,
            json.dumps(prompt.output_schema) if prompt.output_schema else None,
            prompt.is_system,
            prompt.is_public,
            True,
            prompt.created_by,
            1,
            version_id,
        )

        await self._conn.execute(
            """
            INSERT INTO prompt_versions (
                id, prompt_id, version, system_prompt, user_prompt_template, variables,
                preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                change_notes, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            version_id,
            prompt_id,
            1,
            prompt.system_prompt,
            prompt.user_prompt_template,
            json.dumps(serialize_variables_list(prompt.variables)),
            prompt.preferred_provider,
            prompt.preferred_model,
            prompt.temperature,
            prompt.max_tokens,
            json.dumps(prompt.output_schema) if prompt.output_schema else None,
            "Initial version",
            prompt.created_by,
        )

        return await self.get(prompt_id)  # type: ignore

    async def get(self, prompt_id: UUID) -> PromptRecord | None:
        """Get prompt by ID."""
        row = await self._conn.fetchrow("SELECT * FROM prompts WHERE id = $1", prompt_id)
        return row_to_prompt(row) if row else None

    async def get_by_slug(self, slug: str) -> PromptRecord | None:
        """Get prompt by slug."""
        row = await self._conn.fetchrow("SELECT * FROM prompts WHERE slug = $1", slug)
        return row_to_prompt(row) if row else None

    async def update(
        self, prompt_id: UUID, update: PromptUpdate, change_notes: str | None = None
    ) -> PromptRecord:
        """Update prompt, creating new version if content changes."""
        existing = await self.get(prompt_id)
        if not existing:
            raise ValueError(f"Prompt {prompt_id} not found")

        merged = merge_update(update, existing)
        new_version = existing.version
        new_version_id = existing.current_version_id

        if content_changed(update, existing):
            new_version = existing.version + 1
            new_version_id = uuid4()

            await self._conn.execute(
                """
                INSERT INTO prompt_versions (
                    id, prompt_id, version, system_prompt, user_prompt_template, variables,
                    preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                    change_notes, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                new_version_id,
                prompt_id,
                new_version,
                merged["system_prompt"],
                merged["user_prompt_template"],
                json.dumps(serialize_variables_list(merged["variables"])),
                merged["preferred_provider"],
                merged["preferred_model"],
                merged["temperature"],
                merged["max_tokens"],
                json.dumps(merged["output_schema"]) if merged["output_schema"] else None,
                change_notes,
                None,
            )

        await self._conn.execute(
            """
            UPDATE prompts SET
                name = $1, description = $2, category = $3, tags = $4,
                system_prompt = $5, user_prompt_template = $6, variables = $7,
                preferred_provider = $8, preferred_model = $9, temperature = $10,
                max_tokens = $11, output_schema = $12, is_public = $13,
                version = $14, current_version_id = $15, updated_at = now()
            WHERE id = $16
            """,
            merged["name"],
            merged["description"],
            merged["category"],
            list(merged["tags"]),
            merged["system_prompt"],
            merged["user_prompt_template"],
            json.dumps(serialize_variables_list(merged["variables"])),
            merged["preferred_provider"],
            merged["preferred_model"],
            merged["temperature"],
            merged["max_tokens"],
            json.dumps(merged["output_schema"]) if merged["output_schema"] else None,
            merged["is_public"],
            new_version,
            new_version_id,
            prompt_id,
        )

        return await self.get(prompt_id)  # type: ignore

    async def delete(self, prompt_id: UUID, soft: bool = True) -> bool:
        """Delete a prompt."""
        if soft:
            result = await self._conn.execute(
                "UPDATE prompts SET is_active = false, updated_at = now() WHERE id = $1",
                prompt_id,
            )
        else:
            result = await self._conn.execute("DELETE FROM prompts WHERE id = $1", prompt_id)
        return result != "DELETE 0" and result != "UPDATE 0"

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
        """List prompts with filtering."""
        count_result = self._qb.build_count_query(
            category=category,
            tags=tags,
            search=search,
            is_system=is_system,
            is_public=is_public,
            include_inactive=include_inactive,
        )
        count_row = await self._conn.fetchrow(count_result.sql, *count_result.params)
        total = count_row[0] if count_row else 0

        list_result = self._qb.build_list_query(
            category=category,
            tags=tags,
            search=search,
            is_system=is_system,
            is_public=is_public,
            include_inactive=include_inactive,
            limit=limit,
            offset=offset,
        )
        rows = await self._conn.fetch(list_result.sql, *list_result.params)
        prompts = [row_to_prompt(row) for row in rows]

        return prompts, total

    async def get_version(
        self, prompt_id: UUID, version: int | None = None
    ) -> PromptVersionRecord | None:
        """Get a specific version."""
        if version is None:
            prompt = await self.get(prompt_id)
            if not prompt:
                return None
            version = prompt.version

        row = await self._conn.fetchrow(
            "SELECT * FROM prompt_versions WHERE prompt_id = $1 AND version = $2",
            prompt_id,
            version,
        )
        return row_to_version(row) if row else None

    async def list_versions(self, prompt_id: UUID, limit: int = 50) -> list[PromptVersionRecord]:
        """List version history."""
        rows = await self._conn.fetch(
            "SELECT * FROM prompt_versions WHERE prompt_id = $1 ORDER BY version DESC LIMIT $2",
            prompt_id,
            limit,
        )
        return [row_to_version(row) for row in rows]

    async def rollback_to_version(self, prompt_id: UUID, version: int) -> PromptRecord:
        """Rollback to a previous version."""
        old_version = await self.get_version(prompt_id, version)
        if not old_version:
            raise ValueError(f"Version {version} not found for prompt {prompt_id}")

        update = PromptUpdate(
            system_prompt=old_version.system_prompt,
            user_prompt_template=old_version.user_prompt_template,
            variables=old_version.variables,
            preferred_provider=old_version.preferred_provider,
            preferred_model=old_version.preferred_model,
            temperature=old_version.temperature,
            max_tokens=old_version.max_tokens,
            output_schema=old_version.output_schema,
        )
        return await self.update(prompt_id, update, f"Rollback to version {version}")


# =============================================================================
# PostgreSQL Execution Repository (Refactored)
# =============================================================================


class PostgresExecutionRepository:
    """PostgreSQL implementation of ExecutionRepository using shared components."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn
        self._qb = ExecutionQueryBuilder(PostgresQueryBuilder())

    async def record(self, execution: ExecutionCreate) -> ExecutionRecord:
        """Record an execution."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO executions (
                prompt_id, prompt_version, capability,
                provider, model, input_tokens, output_tokens,
                cost_usd, latency_ms, success, error,
                user_id, session_id, request_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING *
            """,
            execution.prompt_id,
            execution.prompt_version,
            execution.capability,
            execution.provider,
            execution.model,
            execution.input_tokens,
            execution.output_tokens,
            execution.cost_usd,
            execution.latency_ms,
            execution.success,
            execution.error,
            execution.user_id,
            execution.session_id,
            execution.request_id,
        )
        return row_to_execution(row)

    async def get(self, execution_id: UUID) -> ExecutionRecord | None:
        """Get execution by ID."""
        row = await self._conn.fetchrow("SELECT * FROM executions WHERE id = $1", execution_id)
        return row_to_execution(row) if row else None

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
        """List executions with filtering."""
        count_result = self._qb.build_count_query(
            prompt_id=prompt_id,
            provider=provider,
            model=model,
            capability=capability,
            success=success,
            since=since,
            until=until,
        )
        count_row = await self._conn.fetchrow(count_result.sql, *count_result.params)
        total = count_row[0] if count_row else 0

        list_result = self._qb.build_list_query(
            prompt_id=prompt_id,
            provider=provider,
            model=model,
            capability=capability,
            success=success,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )
        rows = await self._conn.fetch(list_result.sql, *list_result.params)
        executions = [row_to_execution(row) for row in rows]

        return executions, total

    async def get_usage_stats(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        group_by: str = "day",
    ) -> list[dict[str, Any]]:
        """Get aggregated usage statistics."""
        result = self._qb.build_usage_stats_query(since=since, until=until, group_by=group_by)
        rows = await self._conn.fetch(result.sql, *result.params)
        return [dict(row) for row in rows]


# =============================================================================
# PostgreSQL Unit of Work (Refactored)
# =============================================================================


class PostgresUnitOfWork:
    """PostgreSQL implementation of UnitOfWork."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._transaction: asyncpg.Transaction | None = None
        self.prompts: PostgresPromptRepository
        self.executions: PostgresExecutionRepository

    async def __aenter__(self) -> PostgresUnitOfWork:
        self._conn = await self._pool.acquire()
        self._transaction = self._conn.transaction()
        await self._transaction.start()
        self.prompts = PostgresPromptRepository(self._conn)
        self.executions = PostgresExecutionRepository(self._conn)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
            if self._conn:
                await self._pool.release(self._conn)
                self._conn = None

    async def commit(self) -> None:
        if self._transaction:
            await self._transaction.commit()

    async def rollback(self) -> None:
        if self._transaction:
            await self._transaction.rollback()


# =============================================================================
# PostgreSQL Backend (Refactored)
# =============================================================================


class PostgresBackend:
    """PostgreSQL storage backend implementation."""

    def __init__(
        self,
        database_url: str,
        min_connections: int = 2,
        max_connections: int = 10,
    ):
        _require_asyncpg()
        self._database_url = database_url
        self._min_connections = min_connections
        self._max_connections = max_connections
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Initialize connection pool and create tables."""
        self._pool = await asyncpg.create_pool(
            self._database_url,
            min_size=self._min_connections,
            max_size=self._max_connections,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def health_check(self) -> bool:
        """Check if database is accessible."""
        if not self._pool:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    def unit_of_work(self) -> PostgresUnitOfWork:
        """Create a new unit of work."""
        if not self._pool:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        return PostgresUnitOfWork(self._pool)
