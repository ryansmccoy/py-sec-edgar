"""Shared components for GenAI-Spine storage backends.

This package provides common functionality shared between SQLite and PostgreSQL
storage implementations to eliminate code duplication.

Components:
- converters: Row-to-model and model-to-row conversions
- query_builders: Backend-agnostic SQL query building
- validators: Input validation helpers
"""

from genai_spine.storage.shared.converters import (
    deserialize_schema,
    deserialize_tags,
    deserialize_variables,
    parse_bool,
    parse_datetime,
    parse_decimal,
    parse_uuid,
    row_to_execution,
    row_to_prompt,
    row_to_usage_stats,
    row_to_version,
    serialize_schema,
    serialize_tags,
    serialize_variables,
    serialize_variables_list,
)
from genai_spine.storage.shared.query_builders import (
    BaseQueryBuilder,
    ExecutionQueryBuilder,
    PostgresQueryBuilder,
    PromptQueryBuilder,
    QueryResult,
    SQLiteQueryBuilder,
)
from genai_spine.storage.shared.validators import (
    content_changed,
    merge_update,
    validate_pagination,
    validate_prompt_create,
    validate_prompt_update,
    validate_uuid,
)

__all__ = [
    # Converters
    "deserialize_schema",
    "deserialize_tags",
    "deserialize_variables",
    "parse_bool",
    "parse_datetime",
    "parse_decimal",
    "parse_uuid",
    "row_to_execution",
    "row_to_prompt",
    "row_to_usage_stats",
    "row_to_version",
    "serialize_schema",
    "serialize_tags",
    "serialize_variables",
    "serialize_variables_list",
    # Query builders
    "BaseQueryBuilder",
    "ExecutionQueryBuilder",
    "PostgresQueryBuilder",
    "PromptQueryBuilder",
    "QueryResult",
    "SQLiteQueryBuilder",
    # Validators
    "content_changed",
    "merge_update",
    "validate_pagination",
    "validate_prompt_create",
    "validate_prompt_update",
    "validate_uuid",
]
