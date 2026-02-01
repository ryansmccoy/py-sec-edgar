"""Refactored SQLite storage backend using shared components.

This is a lightweight facade that delegates to shared converters and query builders.
The original sqlite.py (936 lines) has been refactored to use shared components,
reducing duplication while maintaining full API compatibility.
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import aiosqlite

from genai_spine.storage.schemas import (
    ExecutionCreate,
    ExecutionRecord,
    PromptCreate,
    PromptRecord,
    PromptUpdate,
    PromptVersionRecord,
)
from genai_spine.storage.shared import (
    SQLiteQueryBuilder,
    ExecutionQueryBuilder,
    PromptQueryBuilder,
    content_changed,
    merge_update,
    row_to_execution,
    row_to_prompt,
    row_to_usage_stats,
    row_to_version,
    serialize_schema,
    serialize_tags,
    serialize_variables,
)

# Import schema from original module
from genai_spine.storage.sqlite import SCHEMA_SQL


# =============================================================================
# SQLite Prompt Repository (Refactored)
# =============================================================================


class SQLitePromptRepository:
    """SQLite implementation of PromptRepository using shared components."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        self._qb = PromptQueryBuilder(SQLiteQueryBuilder())

    async def create(self, prompt: PromptCreate) -> PromptRecord:
        """Create a new prompt with initial version."""
        now = datetime.now(UTC).isoformat()
        prompt_id = str(uuid4())
        version_id = str(uuid4())

        await self._conn.execute(
            """
            INSERT INTO prompts (
                id, slug, name, description, category, tags,
                system_prompt, user_prompt_template, variables,
                preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                is_system, is_public, is_active, created_by,
                version, current_version_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                prompt_id,
                prompt.slug,
                prompt.name,
                prompt.description,
                prompt.category.value,
                serialize_tags(prompt.tags),
                prompt.system_prompt,
                prompt.user_prompt_template,
                serialize_variables(prompt.variables),
                prompt.preferred_provider,
                prompt.preferred_model,
                prompt.temperature,
                prompt.max_tokens,
                serialize_schema(prompt.output_schema),
                int(prompt.is_system),
                int(prompt.is_public),
                1,
                prompt.created_by,
                1,
                version_id,
                now,
                now,
            ),
        )

        await self._conn.execute(
            """
            INSERT INTO prompt_versions (
                id, prompt_id, version, system_prompt, user_prompt_template, variables,
                preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                change_notes, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                version_id,
                prompt_id,
                1,
                prompt.system_prompt,
                prompt.user_prompt_template,
                serialize_variables(prompt.variables),
                prompt.preferred_provider,
                prompt.preferred_model,
                prompt.temperature,
                prompt.max_tokens,
                serialize_schema(prompt.output_schema),
                "Initial version",
                prompt.created_by,
                now,
            ),
        )

        return await self.get(UUID(prompt_id))  # type: ignore

    async def get(self, prompt_id: UUID) -> PromptRecord | None:
        """Get prompt by ID."""
        async with self._conn.execute(
            "SELECT * FROM prompts WHERE id = ?", (str(prompt_id),)
        ) as cursor:
            row = await cursor.fetchone()
            return row_to_prompt(row) if row else None

    async def get_by_slug(self, slug: str) -> PromptRecord | None:
        """Get prompt by slug."""
        async with self._conn.execute("SELECT * FROM prompts WHERE slug = ?", (slug,)) as cursor:
            row = await cursor.fetchone()
            return row_to_prompt(row) if row else None

    async def update(
        self, prompt_id: UUID, update: PromptUpdate, change_notes: str | None = None
    ) -> PromptRecord:
        """Update prompt, creating new version if content changes."""
        existing = await self.get(prompt_id)
        if not existing:
            raise ValueError(f"Prompt {prompt_id} not found")

        now = datetime.now(UTC).isoformat()
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
                    change_notes, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(new_version_id),
                    str(prompt_id),
                    new_version,
                    merged["system_prompt"],
                    merged["user_prompt_template"],
                    serialize_variables(merged["variables"]),
                    merged["preferred_provider"],
                    merged["preferred_model"],
                    merged["temperature"],
                    merged["max_tokens"],
                    serialize_schema(merged["output_schema"]),
                    change_notes,
                    None,
                    now,
                ),
            )

        await self._conn.execute(
            """
            UPDATE prompts SET
                name = ?, description = ?, category = ?, tags = ?,
                system_prompt = ?, user_prompt_template = ?, variables = ?,
                preferred_provider = ?, preferred_model = ?, temperature = ?,
                max_tokens = ?, output_schema = ?, is_public = ?,
                version = ?, current_version_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                merged["name"],
                merged["description"],
                merged["category"],
                serialize_tags(merged["tags"]),
                merged["system_prompt"],
                merged["user_prompt_template"],
                serialize_variables(merged["variables"]),
                merged["preferred_provider"],
                merged["preferred_model"],
                merged["temperature"],
                merged["max_tokens"],
                serialize_schema(merged["output_schema"]),
                int(merged["is_public"]),
                new_version,
                str(new_version_id),
                now,
                str(prompt_id),
            ),
        )

        return await self.get(prompt_id)  # type: ignore

    async def delete(self, prompt_id: UUID, soft: bool = True) -> bool:
        """Delete a prompt."""
        if soft:
            cursor = await self._conn.execute(
                "UPDATE prompts SET is_active = 0, updated_at = ? WHERE id = ?",
                (datetime.now(UTC).isoformat(), str(prompt_id)),
            )
        else:
            cursor = await self._conn.execute("DELETE FROM prompts WHERE id = ?", (str(prompt_id),))
        return cursor.rowcount > 0

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
        # Build count query
        count_result = self._qb.build_count_query(
            category=category,
            tags=tags,
            search=search,
            is_system=is_system,
            is_public=is_public,
            include_inactive=include_inactive,
        )
        async with self._conn.execute(count_result.sql, count_result.params) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

        # Build list query
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
        async with self._conn.execute(list_result.sql, list_result.params) as cursor:
            rows = await cursor.fetchall()
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

        async with self._conn.execute(
            "SELECT * FROM prompt_versions WHERE prompt_id = ? AND version = ?",
            (str(prompt_id), version),
        ) as cursor:
            row = await cursor.fetchone()
            return row_to_version(row) if row else None

    async def list_versions(self, prompt_id: UUID, limit: int = 50) -> list[PromptVersionRecord]:
        """List version history."""
        async with self._conn.execute(
            "SELECT * FROM prompt_versions WHERE prompt_id = ? ORDER BY version DESC LIMIT ?",
            (str(prompt_id), limit),
        ) as cursor:
            rows = await cursor.fetchall()
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
# SQLite Execution Repository (Refactored)
# =============================================================================


class SQLiteExecutionRepository:
    """SQLite implementation of ExecutionRepository using shared components."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        self._qb = ExecutionQueryBuilder(SQLiteQueryBuilder())

    async def record(self, execution: ExecutionCreate) -> ExecutionRecord:
        """Record an execution."""
        execution_id = str(uuid4())
        now = datetime.now(UTC).isoformat()

        await self._conn.execute(
            """
            INSERT INTO executions (
                id, prompt_id, prompt_version, capability,
                provider, model, input_tokens, output_tokens,
                cost_usd, latency_ms, success, error,
                user_id, session_id, request_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                str(execution.prompt_id) if execution.prompt_id else None,
                execution.prompt_version,
                execution.capability,
                execution.provider,
                execution.model,
                execution.input_tokens,
                execution.output_tokens,
                str(execution.cost_usd),
                execution.latency_ms,
                int(execution.success),
                execution.error,
                execution.user_id,
                execution.session_id,
                execution.request_id,
                now,
            ),
        )
        return await self.get(UUID(execution_id))  # type: ignore

    async def get(self, execution_id: UUID) -> ExecutionRecord | None:
        """Get execution by ID."""
        async with self._conn.execute(
            "SELECT * FROM executions WHERE id = ?", (str(execution_id),)
        ) as cursor:
            row = await cursor.fetchone()
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
        async with self._conn.execute(count_result.sql, count_result.params) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

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
        async with self._conn.execute(list_result.sql, list_result.params) as cursor:
            rows = await cursor.fetchall()
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
        async with self._conn.execute(result.sql, result.params) as cursor:
            rows = await cursor.fetchall()
            return [row_to_usage_stats(row) for row in rows]


# =============================================================================
# SQLite Unit of Work (Refactored)
# =============================================================================


class SQLiteUnitOfWork:
    """SQLite implementation of UnitOfWork."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        self.prompts = SQLitePromptRepository(conn)
        self.executions = SQLiteExecutionRepository(conn)

    async def __aenter__(self) -> SQLiteUnitOfWork:
        await self._conn.execute("BEGIN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        await self._conn.commit()

    async def rollback(self) -> None:
        await self._conn.rollback()


# =============================================================================
# SQLite Backend (Refactored)
# =============================================================================


class SQLiteBackend:
    """SQLite storage backend implementation."""

    def __init__(self, database_path: str | Path = ":memory:"):
        self._database_path = str(database_path)
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        self._conn = await aiosqlite.connect(self._database_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.commit()

    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def health_check(self) -> bool:
        """Check if database is accessible."""
        if not self._conn:
            return False
        try:
            async with self._conn.execute("SELECT 1") as cursor:
                await cursor.fetchone()
            return True
        except Exception:
            return False

    def unit_of_work(self) -> SQLiteUnitOfWork:
        """Create a new unit of work."""
        if not self._conn:
            raise RuntimeError("Backend not initialized. Call initialize() first.")
        return SQLiteUnitOfWork(self._conn)
