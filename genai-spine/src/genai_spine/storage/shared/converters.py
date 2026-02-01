"""Row-to-model and model-to-row converters.

Provides unified conversion logic shared between SQLite and PostgreSQL backends.
Each backend may have slight differences in how data is stored (e.g., JSON strings
vs JSONB, TEXT vs native arrays), so converters accept raw values and handle
the backend-specific deserialization.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from genai_spine.storage.schemas import (
    ExecutionRecord,
    PromptCategory,
    PromptRecord,
    PromptVariable,
    PromptVersionRecord,
)


# =============================================================================
# Type Protocols for Row Objects
# =============================================================================


class RowLike(Protocol):
    """Protocol for row objects that support dict-like access."""

    def __getitem__(self, key: str) -> Any: ...


# =============================================================================
# Serialization Helpers
# =============================================================================


def serialize_variables(variables: list[PromptVariable]) -> str:
    """Serialize variables to JSON string (for SQLite)."""
    return json.dumps([v.model_dump() for v in variables])


def serialize_variables_list(variables: list[PromptVariable]) -> list[dict]:
    """Serialize variables to list of dicts (for PostgreSQL JSONB)."""
    return [v.model_dump() for v in variables]


def serialize_tags(tags: list[str]) -> str:
    """Serialize tags to JSON string (for SQLite)."""
    return json.dumps(tags)


def serialize_schema(schema: dict | None) -> str | None:
    """Serialize output schema to JSON string."""
    if schema is None:
        return None
    return json.dumps(schema)


# =============================================================================
# Deserialization Helpers
# =============================================================================


def deserialize_variables(data: str | list | None) -> list[PromptVariable]:
    """Deserialize variables from JSON string or list.

    Handles both SQLite (JSON string) and PostgreSQL (list) formats.
    """
    if not data:
        return []
    if isinstance(data, str):
        data = json.loads(data)
    return [PromptVariable(**v) for v in data]


def deserialize_tags(data: str | list | None) -> list[str]:
    """Deserialize tags from JSON string or array.

    Handles both SQLite (JSON string) and PostgreSQL (native array) formats.
    """
    if not data:
        return []
    if isinstance(data, str):
        return json.loads(data)
    return list(data)


def deserialize_schema(data: str | dict | None) -> dict | None:
    """Deserialize output schema from JSON string or dict.

    Handles both SQLite (JSON string) and PostgreSQL (JSONB) formats.
    """
    if not data:
        return None
    if isinstance(data, str):
        return json.loads(data)
    return dict(data)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse datetime from string or return as-is if already datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def parse_uuid(value: str | UUID | None) -> UUID | None:
    """Parse UUID from string or return as-is if already UUID."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(value)


def parse_decimal(value: str | Decimal | float | None) -> Decimal:
    """Parse Decimal from string, float, or return as-is."""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def parse_bool(value: int | bool | None) -> bool:
    """Parse boolean from int (SQLite) or bool (PostgreSQL)."""
    if value is None:
        return False
    return bool(value)


# =============================================================================
# Row to Model Converters
# =============================================================================


def row_to_prompt(row: RowLike) -> PromptRecord:
    """Convert database row to PromptRecord.

    Works with both SQLite (aiosqlite.Row) and PostgreSQL (asyncpg.Record).
    """
    return PromptRecord(
        id=parse_uuid(row["id"]),  # type: ignore
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        category=PromptCategory(row["category"]),
        tags=deserialize_tags(row["tags"]),
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=deserialize_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=deserialize_schema(row["output_schema"]),
        is_system=parse_bool(row["is_system"]),
        is_public=parse_bool(row["is_public"]),
        is_active=parse_bool(row["is_active"]),
        created_by=row["created_by"],
        version=row["version"],
        current_version_id=parse_uuid(row["current_version_id"]),  # type: ignore
        created_at=parse_datetime(row["created_at"]),  # type: ignore
        updated_at=parse_datetime(row["updated_at"]),  # type: ignore
    )


def row_to_version(row: RowLike) -> PromptVersionRecord:
    """Convert database row to PromptVersionRecord.

    Works with both SQLite and PostgreSQL.
    """
    return PromptVersionRecord(
        id=parse_uuid(row["id"]),  # type: ignore
        prompt_id=parse_uuid(row["prompt_id"]),  # type: ignore
        version=row["version"],
        system_prompt=row["system_prompt"],
        user_prompt_template=row["user_prompt_template"],
        variables=deserialize_variables(row["variables"]),
        preferred_provider=row["preferred_provider"],
        preferred_model=row["preferred_model"],
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        output_schema=deserialize_schema(row["output_schema"]),
        change_notes=row["change_notes"],
        created_by=row["created_by"],
        created_at=parse_datetime(row["created_at"]),  # type: ignore
    )


def row_to_execution(row: RowLike) -> ExecutionRecord:
    """Convert database row to ExecutionRecord.

    Works with both SQLite and PostgreSQL.
    """
    return ExecutionRecord(
        id=parse_uuid(row["id"]),  # type: ignore
        prompt_id=parse_uuid(row["prompt_id"]) if row["prompt_id"] else None,
        prompt_version=row["prompt_version"],
        capability=row["capability"],
        provider=row["provider"],
        model=row["model"],
        input_tokens=row["input_tokens"],
        output_tokens=row["output_tokens"],
        cost_usd=parse_decimal(row["cost_usd"]),
        latency_ms=row["latency_ms"],
        success=parse_bool(row["success"]),
        error=row["error"],
        user_id=row["user_id"],
        session_id=row["session_id"],
        request_id=row["request_id"],
        created_at=parse_datetime(row["created_at"]),  # type: ignore
    )


# =============================================================================
# Usage Stats Converter
# =============================================================================


def row_to_usage_stats(row: RowLike) -> dict[str, Any]:
    """Convert usage stats row to dictionary.

    Normalizes the output from both SQLite and PostgreSQL aggregations.
    """
    return {
        "period": row["period"],
        "total_requests": row["total_requests"],
        "successful_requests": row["successful_requests"],
        "failed_requests": row["failed_requests"],
        "total_input_tokens": row["total_input_tokens"],
        "total_output_tokens": row["total_output_tokens"],
        "total_cost_usd": float(row["total_cost_usd"]) if row["total_cost_usd"] else 0.0,
        "avg_latency_ms": float(row["avg_latency_ms"]) if row["avg_latency_ms"] else 0.0,
    }
