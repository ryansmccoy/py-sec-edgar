"""SQL query builders for GenAI-Spine storage backends.

Provides backend-agnostic query building with extensions for SQLite and PostgreSQL
specific features. The base QueryBuilder handles common patterns while subclasses
add backend-specific SQL syntax.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


# =============================================================================
# Query Result Types
# =============================================================================


@dataclass
class QueryResult:
    """Result of building a query with parameters."""

    sql: str
    params: list[Any] = field(default_factory=list)


# =============================================================================
# Base Query Builder
# =============================================================================


class BaseQueryBuilder(ABC):
    """Abstract base class for SQL query builders.

    Subclasses implement backend-specific parameter placeholders and SQL syntax.
    """

    @abstractmethod
    def placeholder(self, index: int) -> str:
        """Return parameter placeholder for the given index.

        SQLite uses ? (ignores index), PostgreSQL uses $1, $2, etc.
        """
        ...

    @abstractmethod
    def bool_value(self, value: bool) -> Any:
        """Convert boolean to backend-specific representation.

        SQLite uses 0/1, PostgreSQL uses true/false.
        """
        ...

    @abstractmethod
    def array_contains(self, column: str, param_index: int) -> str:
        """Return SQL for array containment check.

        SQLite uses LIKE with JSON, PostgreSQL uses && operator.
        """
        ...

    @abstractmethod
    def date_extract(self, column: str) -> str:
        """Return SQL for extracting date from timestamp.

        SQLite uses date(), PostgreSQL uses date()::text.
        """
        ...

    @abstractmethod
    def ilike_pattern(self, column: str, param_index: int) -> str:
        """Return SQL for case-insensitive pattern matching."""
        ...

    def uuid_param(self, value: UUID) -> Any:
        """Convert UUID to backend-specific format."""
        return str(value)

    def datetime_param(self, value: datetime) -> Any:
        """Convert datetime to backend-specific format."""
        return value.isoformat()


# =============================================================================
# SQLite Query Builder
# =============================================================================


class SQLiteQueryBuilder(BaseQueryBuilder):
    """SQLite-specific query builder."""

    def placeholder(self, index: int) -> str:
        """SQLite uses ? for all placeholders."""
        return "?"

    def bool_value(self, value: bool) -> int:
        """SQLite stores booleans as 0/1."""
        return 1 if value else 0

    def array_contains(self, column: str, param_index: int) -> str:
        """SQLite uses LIKE for JSON array containment."""
        return f"{column} LIKE ?"

    def date_extract(self, column: str) -> str:
        """SQLite date() function."""
        return f"date({column})"

    def ilike_pattern(self, column: str, param_index: int) -> str:
        """SQLite LIKE is case-insensitive by default for ASCII."""
        return f"{column} LIKE ?"

    def datetime_param(self, value: datetime) -> str:
        """SQLite stores timestamps as ISO strings."""
        return value.isoformat()


# =============================================================================
# PostgreSQL Query Builder
# =============================================================================


class PostgresQueryBuilder(BaseQueryBuilder):
    """PostgreSQL-specific query builder."""

    def placeholder(self, index: int) -> str:
        """PostgreSQL uses $1, $2, etc."""
        return f"${index}"

    def bool_value(self, value: bool) -> bool:
        """PostgreSQL uses native boolean."""
        return value

    def array_contains(self, column: str, param_index: int) -> str:
        """PostgreSQL array overlap operator."""
        return f"{column} && ${param_index}"

    def date_extract(self, column: str) -> str:
        """PostgreSQL date extraction with text cast."""
        return f"date({column})::text"

    def ilike_pattern(self, column: str, param_index: int) -> str:
        """PostgreSQL ILIKE for case-insensitive matching."""
        return f"{column} ILIKE ${param_index}"

    def uuid_param(self, value: UUID) -> UUID:
        """PostgreSQL asyncpg handles UUID natively."""
        return value

    def datetime_param(self, value: datetime) -> datetime:
        """PostgreSQL asyncpg handles datetime natively."""
        return value


# =============================================================================
# Prompt Query Builders
# =============================================================================


class PromptQueryBuilder:
    """Builds queries for prompt operations."""

    def __init__(self, backend: BaseQueryBuilder):
        self._backend = backend

    def build_list_query(
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
    ) -> QueryResult:
        """Build query for listing prompts with filters."""
        conditions: list[str] = []
        params: list[Any] = []
        param_index = 0

        if not include_inactive:
            conditions.append(f"is_active = {self._backend.bool_value(True)}")

        if category:
            param_index += 1
            conditions.append(f"category = {self._backend.placeholder(param_index)}")
            params.append(category)

        if is_system is not None:
            param_index += 1
            conditions.append(f"is_system = {self._backend.placeholder(param_index)}")
            params.append(self._backend.bool_value(is_system))

        if is_public is not None:
            param_index += 1
            conditions.append(f"is_public = {self._backend.placeholder(param_index)}")
            params.append(self._backend.bool_value(is_public))

        if search:
            param_index += 1
            pattern_cond = self._backend.ilike_pattern("name", param_index)
            param_index += 1
            desc_cond = self._backend.ilike_pattern("description", param_index)
            conditions.append(f"({pattern_cond} OR {desc_cond})")
            params.extend([f"%{search}%", f"%{search}%"])

        if tags:
            if isinstance(self._backend, SQLiteQueryBuilder):
                # SQLite: use LIKE for each tag
                tag_conditions = []
                for tag in tags:
                    param_index += 1
                    tag_conditions.append(f"tags LIKE {self._backend.placeholder(param_index)}")
                    params.append(f'%"{tag}"%')
                conditions.append(f"({' OR '.join(tag_conditions)})")
            else:
                # PostgreSQL: use array overlap
                param_index += 1
                conditions.append(self._backend.array_contains("tags", param_index))
                params.append(tags)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Count query
        count_sql = f"SELECT COUNT(*) FROM prompts WHERE {where_clause}"

        # List query
        param_index += 1
        limit_ph = self._backend.placeholder(param_index)
        param_index += 1
        offset_ph = self._backend.placeholder(param_index)

        list_sql = f"""
            SELECT * FROM prompts
            WHERE {where_clause}
            ORDER BY updated_at DESC
            LIMIT {limit_ph} OFFSET {offset_ph}
        """

        return QueryResult(
            sql=list_sql,
            params=params + [limit, offset],
        )

    def build_count_query(
        self,
        *,
        category: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        is_system: bool | None = None,
        is_public: bool | None = None,
        include_inactive: bool = False,
    ) -> QueryResult:
        """Build count query for prompts with same filters."""
        # Reuse the list query builder logic but return count query
        result = self.build_list_query(
            category=category,
            tags=tags,
            search=search,
            is_system=is_system,
            is_public=is_public,
            include_inactive=include_inactive,
            limit=1,
            offset=0,
        )
        # Extract WHERE clause from the list query
        where_start = result.sql.find("WHERE")
        where_end = result.sql.find("ORDER BY")
        where_clause = result.sql[where_start:where_end].strip()

        count_sql = f"SELECT COUNT(*) FROM prompts {where_clause}"
        # Remove limit/offset params
        count_params = result.params[:-2]

        return QueryResult(sql=count_sql, params=count_params)


# =============================================================================
# Execution Query Builders
# =============================================================================


class ExecutionQueryBuilder:
    """Builds queries for execution operations."""

    def __init__(self, backend: BaseQueryBuilder):
        self._backend = backend

    def build_list_query(
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
    ) -> QueryResult:
        """Build query for listing executions with filters."""
        conditions: list[str] = []
        params: list[Any] = []
        param_index = 0

        if prompt_id:
            param_index += 1
            conditions.append(f"prompt_id = {self._backend.placeholder(param_index)}")
            params.append(self._backend.uuid_param(prompt_id))

        if provider:
            param_index += 1
            conditions.append(f"provider = {self._backend.placeholder(param_index)}")
            params.append(provider)

        if model:
            param_index += 1
            conditions.append(f"model = {self._backend.placeholder(param_index)}")
            params.append(model)

        if capability:
            param_index += 1
            conditions.append(f"capability = {self._backend.placeholder(param_index)}")
            params.append(capability)

        if success is not None:
            param_index += 1
            conditions.append(f"success = {self._backend.placeholder(param_index)}")
            params.append(self._backend.bool_value(success))

        if since:
            param_index += 1
            conditions.append(f"created_at >= {self._backend.placeholder(param_index)}")
            params.append(self._backend.datetime_param(since))

        if until:
            param_index += 1
            conditions.append(f"created_at <= {self._backend.placeholder(param_index)}")
            params.append(self._backend.datetime_param(until))

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        param_index += 1
        limit_ph = self._backend.placeholder(param_index)
        param_index += 1
        offset_ph = self._backend.placeholder(param_index)

        list_sql = f"""
            SELECT * FROM executions
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_ph} OFFSET {offset_ph}
        """

        return QueryResult(sql=list_sql, params=params + [limit, offset])

    def build_count_query(
        self,
        *,
        prompt_id: UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
        capability: str | None = None,
        success: bool | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> QueryResult:
        """Build count query for executions."""
        result = self.build_list_query(
            prompt_id=prompt_id,
            provider=provider,
            model=model,
            capability=capability,
            success=success,
            since=since,
            until=until,
            limit=1,
            offset=0,
        )
        where_start = result.sql.find("WHERE")
        where_end = result.sql.find("ORDER BY")
        where_clause = result.sql[where_start:where_end].strip()

        count_sql = f"SELECT COUNT(*) FROM executions {where_clause}"
        count_params = result.params[:-2]

        return QueryResult(sql=count_sql, params=count_params)

    def build_usage_stats_query(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        group_by: str = "day",
    ) -> QueryResult:
        """Build aggregated usage statistics query."""
        conditions: list[str] = []
        params: list[Any] = []
        param_index = 0

        if since:
            param_index += 1
            conditions.append(f"created_at >= {self._backend.placeholder(param_index)}")
            params.append(self._backend.datetime_param(since))

        if until:
            param_index += 1
            conditions.append(f"created_at <= {self._backend.placeholder(param_index)}")
            params.append(self._backend.datetime_param(until))

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Determine grouping column
        if group_by == "provider":
            group_col = "provider"
            select_col = "provider as period"
        elif group_by == "model":
            group_col = "model"
            select_col = "model as period"
        else:  # day
            group_col = self._backend.date_extract("created_at")
            select_col = f"{group_col} as period"

        # Build success condition based on backend
        if isinstance(self._backend, SQLiteQueryBuilder):
            success_case = "CASE WHEN success = 1 THEN 1 ELSE 0 END"
            failed_case = "CASE WHEN success = 0 THEN 1 ELSE 0 END"
            cost_sum = "SUM(CAST(cost_usd AS REAL))"
        else:
            success_case = "CASE WHEN success THEN 1 ELSE 0 END"
            failed_case = "CASE WHEN NOT success THEN 1 ELSE 0 END"
            cost_sum = "SUM(cost_usd)"

        sql = f"""
            SELECT
                {select_col},
                COUNT(*) as total_requests,
                SUM({success_case}) as successful_requests,
                SUM({failed_case}) as failed_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                {cost_sum} as total_cost_usd,
                AVG(latency_ms) as avg_latency_ms
            FROM executions
            WHERE {where_clause}
            GROUP BY {group_col}
            ORDER BY period DESC
        """

        return QueryResult(sql=sql, params=params)
