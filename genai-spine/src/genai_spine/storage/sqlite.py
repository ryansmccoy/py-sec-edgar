"""SQLite storage backend implementation.

Provides a lightweight, file-based storage backend ideal for:
- Local development
- Testing
- Single-user deployments
- Edge/embedded scenarios

Uses aiosqlite for async operations.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import aiosqlite

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
    VariableType,
)


# =============================================================================
# SQLite Schema
# =============================================================================

SCHEMA_SQL = """
-- Prompts table
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'custom',
    tags TEXT DEFAULT '[]',  -- JSON array

    -- Current version content (denormalized for convenience)
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    variables TEXT DEFAULT '[]',  -- JSON array

    -- LLM settings
    preferred_provider TEXT,
    preferred_model TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER,
    output_schema TEXT,  -- JSON

    -- Visibility
    is_system INTEGER DEFAULT 0,
    is_public INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_by TEXT,

    -- Versioning
    version INTEGER DEFAULT 1,
    current_version_id TEXT,

    -- Timestamps
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Prompt versions table (immutable)
CREATE TABLE IF NOT EXISTS prompt_versions (
    id TEXT PRIMARY KEY,
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Content snapshot
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    variables TEXT DEFAULT '[]',

    -- LLM settings snapshot
    preferred_provider TEXT,
    preferred_model TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER,
    output_schema TEXT,

    -- Metadata
    change_notes TEXT,
    created_by TEXT,
    created_at TEXT NOT NULL,

    UNIQUE(prompt_id, version)
);

-- Executions table
CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,

    -- What was executed
    prompt_id TEXT REFERENCES prompts(id) ON DELETE SET NULL,
    prompt_version INTEGER,
    capability TEXT,

    -- Provider details
    provider TEXT NOT NULL,
    model TEXT NOT NULL,

    -- Token usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,

    -- Cost
    cost_usd TEXT DEFAULT '0',  -- Store as text for precision

    -- Performance
    latency_ms INTEGER DEFAULT 0,

    -- Status
    success INTEGER DEFAULT 1,
    error TEXT,

    -- Context
    user_id TEXT,
    session_id TEXT,
    request_id TEXT,

    -- Timestamp
    created_at TEXT NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prompts_slug ON prompts(slug);
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_executions_prompt_id ON executions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_executions_provider ON executions(provider);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions(created_at);
"""


# =============================================================================
# Helper Functions
# =============================================================================


def _serialize_variables(variables: list[PromptVariable]) -> str:
    """Serialize variables to JSON string."""
    return json.dumps([v.model_dump() for v in variables])


def _deserialize_variables(json_str: str | None) -> list[PromptVariable]:
    """Deserialize variables from JSON string."""
    if not json_str:
        return []
    data = json.loads(json_str)
    return [PromptVariable(**v) for v in data]


def _serialize_tags(tags: list[str]) -> str:
    """Serialize tags to JSON string."""
    return json.dumps(tags)


def _deserialize_tags(json_str: str | None) -> list[str]:
    """Deserialize tags from JSON string."""
    if not json_str:
        return []
    return json.loads(json_str)


def _serialize_schema(schema: dict | None) -> str | None:
    """Serialize output schema to JSON string."""
    if schema is None:
        return None
    return json.dumps(schema)


def _deserialize_schema(json_str: str | None) -> dict | None:
    """Deserialize output schema from JSON string."""
    if not json_str:
        return None
    return json.loads(json_str)


def _row_to_prompt(row: aiosqlite.Row) -> PromptRecord:
    """Convert database row to PromptRecord."""
    return PromptRecord(
        id=UUID(row["id"]),
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        category=PromptCategory(row["category"]),
        tags=_deserialize_tags(row["tags"]),
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=_deserialize_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=_deserialize_schema(row["output_schema"]),
        is_system=bool(row["is_system"]),
        is_public=bool(row["is_public"]),
        is_active=bool(row["is_active"]),
        created_by=row["created_by"],
        version=row["version"],
        current_version_id=UUID(row["current_version_id"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def _row_to_version(row: aiosqlite.Row) -> PromptVersionRecord:
    """Convert database row to PromptVersionRecord."""
    return PromptVersionRecord(
        id=UUID(row["id"]),
        prompt_id=UUID(row["prompt_id"]),
        version=row["version"],
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=_deserialize_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=_deserialize_schema(row["output_schema"]),
        change_notes=row["change_notes"],
        created_by=row["created_by"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_execution(row: aiosqlite.Row) -> ExecutionRecord:
    """Convert database row to ExecutionRecord."""
    from decimal import Decimal

    return ExecutionRecord(
        id=UUID(row["id"]),
        prompt_id=UUID(row["prompt_id"]) if row["prompt_id"] else None,
        prompt_version=row["prompt_version"],
        capability=row["capability"],
        provider=row["provider"],
        model=row["model"],
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        cost_usd=Decimal(row["cost_usd"]),
        latency_ms=row["latency_ms"],
        success=bool(row["success"]),
        error=row["error"],
        user_id=row["user_id"],
        session_id=row["session_id"],
        request_id=row["request_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


# =============================================================================
# SQLite Prompt Repository
# =============================================================================


class SQLitePromptRepository:
    """SQLite implementation of PromptRepository."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def create(self, prompt: PromptCreate) -> PromptRecord:
        """Create a new prompt with initial version."""
        now = datetime.utcnow().isoformat()
        prompt_id = str(uuid4())
        version_id = str(uuid4())

        # Insert prompt
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
                _serialize_tags(prompt.tags),
                prompt.system_prompt,
                prompt.user_prompt_template,
                _serialize_variables(prompt.variables),
                prompt.preferred_provider,
                prompt.preferred_model,
                prompt.temperature,
                prompt.max_tokens,
                _serialize_schema(prompt.output_schema),
                int(prompt.is_system),
                int(prompt.is_public),
                1,  # is_active
                prompt.created_by,
                1,  # version
                version_id,
                now,
                now,
            ),
        )

        # Insert initial version
        await self._conn.execute(
            """
            INSERT INTO prompt_versions (
                id, prompt_id, version,
                system_prompt, user_prompt_template, variables,
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
                _serialize_variables(prompt.variables),
                prompt.preferred_provider,
                prompt.preferred_model,
                prompt.temperature,
                prompt.max_tokens,
                _serialize_schema(prompt.output_schema),
                "Initial version",
                prompt.created_by,
                now,
            ),
        )

        return await self.get(UUID(prompt_id))  # type: ignore

    async def get(self, prompt_id: UUID) -> PromptRecord | None:
        """Get prompt by ID."""
        async with self._conn.execute(
            "SELECT * FROM prompts WHERE id = ?",
            (str(prompt_id),),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _row_to_prompt(row)
            return None

    async def get_by_slug(self, slug: str) -> PromptRecord | None:
        """Get prompt by slug."""
        async with self._conn.execute(
            "SELECT * FROM prompts WHERE slug = ?",
            (slug,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _row_to_prompt(row)
            return None

    async def update(
        self,
        prompt_id: UUID,
        update: PromptUpdate,
        change_notes: str | None = None,
    ) -> PromptRecord:
        """Update prompt, creating new version if content changes."""
        existing = await self.get(prompt_id)
        if not existing:
            raise ValueError(f"Prompt {prompt_id} not found")

        now = datetime.utcnow().isoformat()

        # Determine what changed
        content_changed = any(
            [
                update.system_prompt is not None and update.system_prompt != existing.system_prompt,
                update.user_prompt_template is not None
                and update.user_prompt_template != existing.user_prompt_template,
                update.variables is not None and update.variables != existing.variables,
                update.temperature is not None and update.temperature != existing.temperature,
                update.max_tokens is not None and update.max_tokens != existing.max_tokens,
                update.output_schema is not None and update.output_schema != existing.output_schema,
                update.preferred_provider is not None
                and update.preferred_provider != existing.preferred_provider,
                update.preferred_model is not None
                and update.preferred_model != existing.preferred_model,
            ]
        )

        # Build update fields
        new_version = existing.version
        new_version_id = existing.current_version_id

        if content_changed:
            # Create new version
            new_version = existing.version + 1
            new_version_id = uuid4()

            await self._conn.execute(
                """
                INSERT INTO prompt_versions (
                    id, prompt_id, version,
                    system_prompt, user_prompt_template, variables,
                    preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                    change_notes, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(new_version_id),
                    str(prompt_id),
                    new_version,
                    update.system_prompt
                    if update.system_prompt is not None
                    else existing.system_prompt,
                    update.user_prompt_template
                    if update.user_prompt_template is not None
                    else existing.user_prompt_template,
                    _serialize_variables(
                        update.variables if update.variables is not None else existing.variables
                    ),
                    update.preferred_provider
                    if update.preferred_provider is not None
                    else existing.preferred_provider,
                    update.preferred_model
                    if update.preferred_model is not None
                    else existing.preferred_model,
                    update.temperature if update.temperature is not None else existing.temperature,
                    update.max_tokens if update.max_tokens is not None else existing.max_tokens,
                    _serialize_schema(
                        update.output_schema
                        if update.output_schema is not None
                        else existing.output_schema
                    ),
                    change_notes,
                    None,  # created_by - TODO: get from context
                    now,
                ),
            )

        # Update prompt record
        await self._conn.execute(
            """
            UPDATE prompts SET
                name = ?,
                description = ?,
                category = ?,
                tags = ?,
                system_prompt = ?,
                user_prompt_template = ?,
                variables = ?,
                preferred_provider = ?,
                preferred_model = ?,
                temperature = ?,
                max_tokens = ?,
                output_schema = ?,
                is_public = ?,
                version = ?,
                current_version_id = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                update.name if update.name is not None else existing.name,
                update.description if update.description is not None else existing.description,
                (update.category.value if update.category is not None else existing.category.value),
                _serialize_tags(update.tags if update.tags is not None else existing.tags),
                update.system_prompt
                if update.system_prompt is not None
                else existing.system_prompt,
                update.user_prompt_template
                if update.user_prompt_template is not None
                else existing.user_prompt_template,
                _serialize_variables(
                    update.variables if update.variables is not None else existing.variables
                ),
                update.preferred_provider
                if update.preferred_provider is not None
                else existing.preferred_provider,
                update.preferred_model
                if update.preferred_model is not None
                else existing.preferred_model,
                update.temperature if update.temperature is not None else existing.temperature,
                update.max_tokens if update.max_tokens is not None else existing.max_tokens,
                _serialize_schema(
                    update.output_schema
                    if update.output_schema is not None
                    else existing.output_schema
                ),
                int(update.is_public if update.is_public is not None else existing.is_public),
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
                (datetime.utcnow().isoformat(), str(prompt_id)),
            )
        else:
            cursor = await self._conn.execute(
                "DELETE FROM prompts WHERE id = ?",
                (str(prompt_id),),
            )
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
        conditions = []
        params: list[Any] = []

        if not include_inactive:
            conditions.append("is_active = 1")

        if category:
            conditions.append("category = ?")
            params.append(category)

        if is_system is not None:
            conditions.append("is_system = ?")
            params.append(int(is_system))

        if is_public is not None:
            conditions.append("is_public = ?")
            params.append(int(is_public))

        if search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if tags:
            # SQLite JSON containment is limited, use LIKE for simplicity
            tag_conditions = [f"tags LIKE ?" for _ in tags]
            conditions.append(f"({' OR '.join(tag_conditions)})")
            params.extend([f'%"{tag}"%' for tag in tags])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        async with self._conn.execute(
            f"SELECT COUNT(*) FROM prompts WHERE {where_clause}",
            params,
        ) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

        # Get paginated results
        async with self._conn.execute(
            f"""
            SELECT * FROM prompts
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ) as cursor:
            rows = await cursor.fetchall()
            prompts = [_row_to_prompt(row) for row in rows]

        return prompts, total

    async def get_version(
        self,
        prompt_id: UUID,
        version: int | None = None,
    ) -> PromptVersionRecord | None:
        """Get a specific version."""
        if version is None:
            # Get current version
            prompt = await self.get(prompt_id)
            if not prompt:
                return None
            version = prompt.version

        async with self._conn.execute(
            "SELECT * FROM prompt_versions WHERE prompt_id = ? AND version = ?",
            (str(prompt_id), version),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _row_to_version(row)
            return None

    async def list_versions(
        self,
        prompt_id: UUID,
        limit: int = 50,
    ) -> list[PromptVersionRecord]:
        """List version history."""
        async with self._conn.execute(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_id = ?
            ORDER BY version DESC
            LIMIT ?
            """,
            (str(prompt_id), limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [_row_to_version(row) for row in rows]

    async def rollback_to_version(
        self,
        prompt_id: UUID,
        version: int,
    ) -> PromptRecord:
        """Rollback to a previous version."""
        old_version = await self.get_version(prompt_id, version)
        if not old_version:
            raise ValueError(f"Version {version} not found for prompt {prompt_id}")

        # Create update from old version
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

        return await self.update(
            prompt_id,
            update,
            change_notes=f"Rollback to version {version}",
        )


# =============================================================================
# SQLite Execution Repository
# =============================================================================


class SQLiteExecutionRepository:
    """SQLite implementation of ExecutionRepository."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def record(self, execution: ExecutionCreate) -> ExecutionRecord:
        """Record an execution."""
        execution_id = str(uuid4())
        now = datetime.utcnow().isoformat()

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
            "SELECT * FROM executions WHERE id = ?",
            (str(execution_id),),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return _row_to_execution(row)
            return None

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
        conditions = []
        params: list[Any] = []

        if prompt_id:
            conditions.append("prompt_id = ?")
            params.append(str(prompt_id))

        if provider:
            conditions.append("provider = ?")
            params.append(provider)

        if model:
            conditions.append("model = ?")
            params.append(model)

        if capability:
            conditions.append("capability = ?")
            params.append(capability)

        if success is not None:
            conditions.append("success = ?")
            params.append(int(success))

        if since:
            conditions.append("created_at >= ?")
            params.append(since.isoformat())

        if until:
            conditions.append("created_at <= ?")
            params.append(until.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        async with self._conn.execute(
            f"SELECT COUNT(*) FROM executions WHERE {where_clause}",
            params,
        ) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

        # Get paginated results
        async with self._conn.execute(
            f"""
            SELECT * FROM executions
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ) as cursor:
            rows = await cursor.fetchall()
            executions = [_row_to_execution(row) for row in rows]

        return executions, total

    async def get_usage_stats(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        group_by: str = "day",
    ) -> list[dict[str, Any]]:
        """Get aggregated usage statistics."""
        conditions = []
        params: list[Any] = []

        if since:
            conditions.append("created_at >= ?")
            params.append(since.isoformat())

        if until:
            conditions.append("created_at <= ?")
            params.append(until.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Determine grouping
        if group_by == "provider":
            group_col = "provider"
            select_col = "provider as period"
        elif group_by == "model":
            group_col = "model"
            select_col = "model as period"
        else:  # day
            group_col = "date(created_at)"
            select_col = "date(created_at) as period"

        async with self._conn.execute(
            f"""
            SELECT
                {select_col},
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(CAST(cost_usd AS REAL)) as total_cost_usd,
                AVG(latency_ms) as avg_latency_ms
            FROM executions
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY period DESC
            """,
            params,
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "period": row["period"],
                    "total_requests": row["total_requests"],
                    "successful_requests": row["successful_requests"],
                    "failed_requests": row["failed_requests"],
                    "total_input_tokens": row["total_input_tokens"],
                    "total_output_tokens": row["total_output_tokens"],
                    "total_cost_usd": row["total_cost_usd"],
                    "avg_latency_ms": row["avg_latency_ms"],
                }
                for row in rows
            ]


# =============================================================================
# SQLite Unit of Work
# =============================================================================


class SQLiteUnitOfWork:
    """SQLite implementation of UnitOfWork."""

    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn
        self.prompts = SQLitePromptRepository(conn)
        self.executions = SQLiteExecutionRepository(conn)

    async def __aenter__(self) -> "SQLiteUnitOfWork":
        """Begin transaction."""
        await self._conn.execute("BEGIN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit or rollback based on exception."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commit transaction."""
        await self._conn.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self._conn.rollback()


# =============================================================================
# SQLite Storage Backend
# =============================================================================


class SQLiteBackend:
    """SQLite storage backend implementation."""

    def __init__(self, database_path: str | Path = ":memory:"):
        """Initialize SQLite backend.

        Args:
            database_path: Path to SQLite database file, or ":memory:" for in-memory.
        """
        self._database_path = str(database_path)
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Initialize database and create tables."""
        self._conn = await aiosqlite.connect(self._database_path)
        self._conn.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self._conn.execute("PRAGMA foreign_keys = ON")

        # Create schema
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
