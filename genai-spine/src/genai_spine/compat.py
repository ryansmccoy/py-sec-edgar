"""
Compatibility layer for ecosystem integration.

Provides optional imports from entityspine and spine-core packages.
Falls back to local implementations if packages are not installed.

Usage:
    from genai_spine.compat import Result, Ok, Err, ExecutionContext
    from genai_spine.compat import HAS_ENTITYSPINE, ErrorCategory

Install ecosystem types:
    pip install genai-spine[ecosystem]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Generic, TypeVar
import uuid


# =============================================================================
# Try importing from entityspine (preferred)
# =============================================================================

try:
    from entityspine.domain.workflow import (
        ExecutionContext,
        new_execution_context,
        Ok,
        Err,
        TaskStatus,
        WorkflowStatus,
        QualityStatus,
    )
    from entityspine.domain.errors import ErrorCategory, ErrorContext

    # Type alias - entityspine uses union type
    Result = Ok | Err
    HAS_ENTITYSPINE = True

except ImportError:
    # =============================================================================
    # Fallback: Compatible local implementations
    # =============================================================================

    HAS_ENTITYSPINE = False

    T = TypeVar("T")
    U = TypeVar("U")

    class ErrorCategory(str, Enum):
        """Error categories for classification (entityspine-compatible)."""

        # Infrastructure errors (usually transient)
        NETWORK = "NETWORK"
        DATABASE = "DATABASE"
        STORAGE = "STORAGE"

        # Source/data errors
        SOURCE = "SOURCE"
        PARSE = "PARSE"
        VALIDATION = "VALIDATION"

        # Configuration errors (never retryable)
        CONFIG = "CONFIG"
        AUTH = "AUTH"

        # Application errors
        PIPELINE = "PIPELINE"

        # Internal errors
        INTERNAL = "INTERNAL"
        UNKNOWN = "UNKNOWN"

    @dataclass
    class ErrorContext:
        """Additional context for an error."""

        pipeline: str | None = None
        workflow: str | None = None
        step: str | None = None
        execution_id: str | None = None
        metadata: dict[str, Any] = field(default_factory=dict)

        def to_dict(self) -> dict[str, Any]:
            result = {}
            for key in ["pipeline", "workflow", "step", "execution_id"]:
                value = getattr(self, key)
                if value is not None:
                    result[key] = value
            if self.metadata:
                result.update(self.metadata)
            return result

    @dataclass(frozen=True, slots=True)
    class Ok(Generic[T]):
        """Successful result containing a value."""

        value: T

        def is_ok(self) -> bool:
            return True

        def is_err(self) -> bool:
            return False

        def unwrap(self) -> T:
            return self.value

        def unwrap_or(self, default: T) -> T:
            return self.value

        def unwrap_or_else(self, f: Callable[[Exception], T]) -> T:
            return self.value

        def map(self, f: Callable[[T], U]) -> "Ok[U] | Err[U]":
            return Ok(f(self.value))

        def flat_map(self, f: Callable[[T], "Ok[U] | Err[U]"]) -> "Ok[U] | Err[U]":
            return f(self.value)

        def map_err(self, f: Callable[[Exception], Exception]) -> "Ok[T] | Err[T]":
            return self

    @dataclass(frozen=True, slots=True)
    class Err(Generic[T]):
        """Failed result containing an error."""

        error: Exception

        def is_ok(self) -> bool:
            return False

        def is_err(self) -> bool:
            return True

        def unwrap(self) -> T:
            raise self.error

        def unwrap_or(self, default: T) -> T:
            return default

        def unwrap_or_else(self, f: Callable[[Exception], T]) -> T:
            return f(self.error)

        def map(self, f: Callable[[T], U]) -> "Ok[U] | Err[U]":
            return Err(self.error)

        def flat_map(self, f: Callable[[T], "Ok[U] | Err[U]"]) -> "Ok[U] | Err[U]":
            return Err(self.error)

        def map_err(self, f: Callable[[Exception], Exception]) -> "Ok[T] | Err[T]":
            return Err(f(self.error))

    # Type alias
    Result = Ok | Err

    class TaskStatus(str, Enum):
        """Status of a task."""

        PENDING = "PENDING"
        RUNNING = "RUNNING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"
        SKIPPED = "SKIPPED"

    class WorkflowStatus(str, Enum):
        """Status of a workflow."""

        PENDING = "PENDING"
        RUNNING = "RUNNING"
        PAUSED = "PAUSED"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"
        CANCELLED = "CANCELLED"

    class QualityStatus(str, Enum):
        """Outcome of a quality check."""

        PASS = "PASS"
        WARN = "WARN"
        FAIL = "FAIL"

    @dataclass
    class ExecutionContext:
        """Context passed through execution for lineage tracking."""

        execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
        batch_id: str | None = None
        parent_execution_id: str | None = None
        workflow_name: str | None = None
        started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
        metadata: dict[str, Any] = field(default_factory=dict)

        def child(self, workflow_name: str | None = None) -> "ExecutionContext":
            """Create child context for sub-operation."""
            return ExecutionContext(
                batch_id=self.batch_id,
                parent_execution_id=self.execution_id,
                workflow_name=workflow_name,
            )

        def with_metadata(self, **kwargs: Any) -> "ExecutionContext":
            """Create copy with additional metadata."""
            new_meta = {**self.metadata, **kwargs}
            return ExecutionContext(
                execution_id=self.execution_id,
                batch_id=self.batch_id,
                parent_execution_id=self.parent_execution_id,
                workflow_name=self.workflow_name,
                started_at=self.started_at,
                metadata=new_meta,
            )

        @property
        def is_root(self) -> bool:
            """True if this is a root execution (no parent)."""
            return self.parent_execution_id is None

        @property
        def elapsed_seconds(self) -> float:
            """Seconds since execution started."""
            return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def new_execution_context(
        batch_id: str | None = None,
        workflow_name: str | None = None,
        **metadata: Any,
    ) -> ExecutionContext:
        """Create new root execution context."""
        return ExecutionContext(
            batch_id=batch_id,
            workflow_name=workflow_name,
            metadata=metadata,
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Feature flag
    "HAS_ENTITYSPINE",
    # Result pattern
    "Result",
    "Ok",
    "Err",
    # Execution tracking
    "ExecutionContext",
    "new_execution_context",
    # Status enums
    "TaskStatus",
    "WorkflowStatus",
    "QualityStatus",
    # Error classification
    "ErrorCategory",
    "ErrorContext",
]
