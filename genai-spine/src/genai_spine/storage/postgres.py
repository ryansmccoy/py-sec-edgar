"""PostgreSQL storage backend implementation.

Provides a production-ready storage backend with:
- Connection pooling (asyncpg)
- Full JSONB support
- Proper transaction management
- Compatible with Capture Spine's existing tables

Requires: pip install genai-spine[postgres]
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

try:
    import asyncpg

    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False
    asyncpg = None  # type: ignore

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
)


def _require_asyncpg() -> None:
    """Raise helpful error if asyncpg not installed."""
    if not HAS_ASYNCPG:
        raise ImportError(
            "PostgreSQL support requires asyncpg. Install with: pip install genai-spine[postgres]"
        )


# =============================================================================
# PostgreSQL Schema (Compatible with Capture Spine)
# =============================================================================

SCHEMA_SQL = """
-- Prompts table (matches Capture Spine structure)
CREATE TABLE IF NOT EXISTS prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'custom',
    tags TEXT[] DEFAULT '{}',

    -- Current version content (denormalized)
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]',

    -- LLM settings
    preferred_provider VARCHAR(100),
    preferred_model VARCHAR(100),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,
    output_schema JSONB,

    -- Visibility
    is_system BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(36),

    -- Versioning
    version INTEGER DEFAULT 1,
    current_version_id UUID,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Prompt versions table (immutable, matches Capture Spine)
CREATE TABLE IF NOT EXISTS prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,

    -- Content snapshot
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]',

    -- LLM settings snapshot
    preferred_provider VARCHAR(100),
    preferred_model VARCHAR(100),
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER,
    output_schema JSONB,

    -- Metadata
    change_notes TEXT,
    created_by VARCHAR(36),
    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(prompt_id, version)
);

-- Executions table (similar to Capture Spine's transformations)
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was executed
    prompt_id UUID REFERENCES prompts(id) ON DELETE SET NULL,
    prompt_version INTEGER,
    capability VARCHAR(50),

    -- Provider details
    provider VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,

    -- Token usage
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,

    -- Cost
    cost_usd DECIMAL(12, 8) DEFAULT 0,

    -- Performance
    latency_ms INTEGER DEFAULT 0,

    -- Status
    success BOOLEAN DEFAULT true,
    error TEXT,

    -- Context
    user_id VARCHAR(36),
    session_id VARCHAR(36),
    request_id VARCHAR(36),

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompts_slug ON prompts(slug);
CREATE INDEX IF NOT EXISTS idx_prompts_category ON prompts(category);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_prompts_is_active ON prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_executions_prompt_id ON executions(prompt_id);
CREATE INDEX IF NOT EXISTS idx_executions_provider ON executions(provider);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions(created_at);
CREATE INDEX IF NOT EXISTS idx_executions_capability ON executions(capability);
"""


# =============================================================================
# Helper Functions
# =============================================================================


def _parse_variables(data: list | None) -> list[PromptVariable]:
    """Parse JSONB variables to PromptVariable list."""
    if not data:
        return []
    return [PromptVariable(**v) for v in data]


def _serialize_variables(variables: list[PromptVariable]) -> list[dict]:
    """Serialize PromptVariable list to JSONB-compatible format."""
    return [v.model_dump() for v in variables]


def _row_to_prompt(row: asyncpg.Record) -> PromptRecord:
    """Convert database row to PromptRecord."""
    return PromptRecord(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        category=PromptCategory(row["category"]),
        tags=list(row["tags"]) if row["tags"] else [],
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=_parse_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=dict(row["output_schema"]) if row["output_schema"] else None,
        is_system=row["is_system"],
        is_public=row["is_public"],
        is_active=row["is_active"],
        created_by=row["created_by"],
        version=row["version"],
        current_version_id=row["current_version_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_version(row: asyncpg.Record) -> PromptVersionRecord:
    """Convert database row to PromptVersionRecord."""
    return PromptVersionRecord(
        id=row["id"],
        prompt_id=row["prompt_id"],
        version=row["version"],
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=_parse_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=dict(row["output_schema"]) if row["output_schema"] else None,
        change_notes=row["change_notes"],
        created_by=row["created_by"],
        created_at=row["created_at"],
    )


def _row_to_execution(row: asyncpg.Record) -> ExecutionRecord:
    """Convert database row to ExecutionRecord."""
    return ExecutionRecord(
        id=row["id"],
        prompt_id=row["prompt_id"],
        prompt_version=row["prompt_version"],
        capability=row["capability"],
        provider=row["provider"],
        model=row["model"],
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        cost_usd=Decimal(str(row["cost_usd"])) if row["cost_usd"] else Decimal("0"),
        latency_ms=row["latency_ms"],
        success=row["success"],
        error=row["error"],
        user_id=row["user_id"],
        session_id=row["session_id"],
        request_id=row["request_id"],
        created_at=row["created_at"],
    )


# =============================================================================
# PostgreSQL Prompt Repository
# =============================================================================


class PostgresPromptRepository:
    """PostgreSQL implementation of PromptRepository."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def create(self, prompt: PromptCreate) -> PromptRecord:
        """Create a new prompt with initial version."""
        prompt_id = uuid4()
        version_id = uuid4()

        # Insert prompt
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
            json.dumps(_serialize_variables(prompt.variables)),
            prompt.preferred_provider,
            prompt.preferred_model,
            prompt.temperature,
            prompt.max_tokens,
            json.dumps(prompt.output_schema) if prompt.output_schema else None,
            prompt.is_system,
            prompt.is_public,
            True,  # is_active
            prompt.created_by,
            1,  # version
            version_id,
        )

        # Insert initial version
        await self._conn.execute(
            """
            INSERT INTO prompt_versions (
                id, prompt_id, version,
                system_prompt, user_prompt_template, variables,
                preferred_provider, preferred_model, temperature, max_tokens, output_schema,
                change_notes, created_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            version_id,
            prompt_id,
            1,
            prompt.system_prompt,
            prompt.user_prompt_template,
            json.dumps(_serialize_variables(prompt.variables)),
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
        row = await self._conn.fetchrow(
            "SELECT * FROM prompts WHERE id = $1",
            prompt_id,
        )
        if row:
            return _row_to_prompt(row)
        return None

    async def get_by_slug(self, slug: str) -> PromptRecord | None:
        """Get prompt by slug."""
        row = await self._conn.fetchrow(
            "SELECT * FROM prompts WHERE slug = $1",
            slug,
        )
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
                    change_notes, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """,
                new_version_id,
                prompt_id,
                new_version,
                update.system_prompt
                if update.system_prompt is not None
                else existing.system_prompt,
                update.user_prompt_template
                if update.user_prompt_template is not None
                else existing.user_prompt_template,
                json.dumps(
                    _serialize_variables(
                        update.variables if update.variables is not None else existing.variables
                    )
                ),
                update.preferred_provider
                if update.preferred_provider is not None
                else existing.preferred_provider,
                update.preferred_model
                if update.preferred_model is not None
                else existing.preferred_model,
                update.temperature if update.temperature is not None else existing.temperature,
                update.max_tokens if update.max_tokens is not None else existing.max_tokens,
                json.dumps(
                    update.output_schema
                    if update.output_schema is not None
                    else existing.output_schema
                )
                if (update.output_schema is not None or existing.output_schema is not None)
                else None,
                change_notes,
                None,  # created_by - TODO: get from context
            )

        # Update prompt record
        await self._conn.execute(
            """
            UPDATE prompts SET
                name = $1,
                description = $2,
                category = $3,
                tags = $4,
                system_prompt = $5,
                user_prompt_template = $6,
                variables = $7,
                preferred_provider = $8,
                preferred_model = $9,
                temperature = $10,
                max_tokens = $11,
                output_schema = $12,
                is_public = $13,
                version = $14,
                current_version_id = $15,
                updated_at = now()
            WHERE id = $16
            """,
            update.name if update.name is not None else existing.name,
            update.description if update.description is not None else existing.description,
            (update.category.value if update.category is not None else existing.category.value),
            update.tags if update.tags is not None else list(existing.tags),
            update.system_prompt if update.system_prompt is not None else existing.system_prompt,
            update.user_prompt_template
            if update.user_prompt_template is not None
            else existing.user_prompt_template,
            json.dumps(
                _serialize_variables(
                    update.variables if update.variables is not None else existing.variables
                )
            ),
            update.preferred_provider
            if update.preferred_provider is not None
            else existing.preferred_provider,
            update.preferred_model
            if update.preferred_model is not None
            else existing.preferred_model,
            update.temperature if update.temperature is not None else existing.temperature,
            update.max_tokens if update.max_tokens is not None else existing.max_tokens,
            json.dumps(
                update.output_schema if update.output_schema is not None else existing.output_schema
            )
            if (update.output_schema is not None or existing.output_schema is not None)
            else None,
            update.is_public if update.is_public is not None else existing.is_public,
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
            result = await self._conn.execute(
                "DELETE FROM prompts WHERE id = $1",
                prompt_id,
            )
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
        conditions = []
        params: list[Any] = []
        param_count = 0

        if not include_inactive:
            conditions.append("is_active = true")

        if category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(category)

        if is_system is not None:
            param_count += 1
            conditions.append(f"is_system = ${param_count}")
            params.append(is_system)

        if is_public is not None:
            param_count += 1
            conditions.append(f"is_public = ${param_count}")
            params.append(is_public)

        if search:
            param_count += 1
            conditions.append(f"(name ILIKE ${param_count} OR description ILIKE ${param_count})")
            params.append(f"%{search}%")

        if tags:
            param_count += 1
            conditions.append(f"tags && ${param_count}")  # PostgreSQL array overlap
            params.append(tags)

        where_clause = " AND ".join(conditions) if conditions else "true"

        # Get total count
        count_row = await self._conn.fetchrow(
            f"SELECT COUNT(*) FROM prompts WHERE {where_clause}",
            *params,
        )
        total = count_row[0] if count_row else 0

        # Get paginated results
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        rows = await self._conn.fetch(
            f"""
            SELECT * FROM prompts
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
            """,
            *params,
            limit,
            offset,
        )
        prompts = [_row_to_prompt(row) for row in rows]

        return prompts, total

    async def get_version(
        self,
        prompt_id: UUID,
        version: int | None = None,
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
        if row:
            return _row_to_version(row)
        return None

    async def list_versions(
        self,
        prompt_id: UUID,
        limit: int = 50,
    ) -> list[PromptVersionRecord]:
        """List version history."""
        rows = await self._conn.fetch(
            """
            SELECT * FROM prompt_versions
            WHERE prompt_id = $1
            ORDER BY version DESC
            LIMIT $2
            """,
            prompt_id,
            limit,
        )
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
# PostgreSQL Execution Repository
# =============================================================================


class PostgresExecutionRepository:
    """PostgreSQL implementation of ExecutionRepository."""

    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

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
        return _row_to_execution(row)

    async def get(self, execution_id: UUID) -> ExecutionRecord | None:
        """Get execution by ID."""
        row = await self._conn.fetchrow(
            "SELECT * FROM executions WHERE id = $1",
            execution_id,
        )
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
        param_count = 0

        if prompt_id:
            param_count += 1
            conditions.append(f"prompt_id = ${param_count}")
            params.append(prompt_id)

        if provider:
            param_count += 1
            conditions.append(f"provider = ${param_count}")
            params.append(provider)

        if model:
            param_count += 1
            conditions.append(f"model = ${param_count}")
            params.append(model)

        if capability:
            param_count += 1
            conditions.append(f"capability = ${param_count}")
            params.append(capability)

        if success is not None:
            param_count += 1
            conditions.append(f"success = ${param_count}")
            params.append(success)

        if since:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(since)

        if until:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(until)

        where_clause = " AND ".join(conditions) if conditions else "true"

        # Get total count
        count_row = await self._conn.fetchrow(
            f"SELECT COUNT(*) FROM executions WHERE {where_clause}",
            *params,
        )
        total = count_row[0] if count_row else 0

        # Get paginated results
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count

        rows = await self._conn.fetch(
            f"""
            SELECT * FROM executions
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
            """,
            *params,
            limit,
            offset,
        )
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
        param_count = 0

        if since:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(since)

        if until:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(until)

        where_clause = " AND ".join(conditions) if conditions else "true"

        # Determine grouping
        if group_by == "provider":
            group_col = "provider"
            select_col = "provider as period"
        elif group_by == "model":
            group_col = "model"
            select_col = "model as period"
        else:  # day
            group_col = "date(created_at)"
            select_col = "date(created_at)::text as period"

        rows = await self._conn.fetch(
            f"""
            SELECT
                {select_col},
                COUNT(*) as total_requests,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_requests,
                SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(latency_ms) as avg_latency_ms,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms
            FROM executions
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY period DESC
            """,
            *params,
        )
        return [dict(row) for row in rows]


# =============================================================================
# PostgreSQL Unit of Work
# =============================================================================


class PostgresUnitOfWork:
    """PostgreSQL implementation of UnitOfWork."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._transaction: asyncpg.Transaction | None = None
        self.prompts: PostgresPromptRepository
        self.executions: PostgresExecutionRepository

    async def __aenter__(self) -> "PostgresUnitOfWork":
        """Acquire connection and start transaction."""
        self._conn = await self._pool.acquire()
        self._transaction = self._conn.transaction()
        await self._transaction.start()
        self.prompts = PostgresPromptRepository(self._conn)
        self.executions = PostgresExecutionRepository(self._conn)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Commit or rollback and release connection."""
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
        """Commit transaction."""
        if self._transaction:
            await self._transaction.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        if self._transaction:
            await self._transaction.rollback()


# =============================================================================
# PostgreSQL Storage Backend
# =============================================================================


class PostgresBackend:
    """PostgreSQL storage backend implementation."""

    def __init__(
        self,
        database_url: str,
        min_connections: int = 2,
        max_connections: int = 10,
    ):
        """Initialize PostgreSQL backend.

        Args:
            database_url: PostgreSQL connection URL
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """
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

        # Create schema
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
