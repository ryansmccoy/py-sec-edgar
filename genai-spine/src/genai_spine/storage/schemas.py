"""Storage schemas - Pydantic models for storage layer.

These are the data transfer objects used between the API layer and storage.
They're separate from SQLAlchemy models to maintain clean layer boundaries.

Design principles:
- Immutable where possible (frozen=True for records)
- Clear separation: Create, Update, Record patterns
- Compatible with Capture Spine's existing schemas
- JSON-serializable for any backend
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Enums (Compatible with Capture Spine)
# =============================================================================


class PromptCategory(str, Enum):
    """Prompt categories - matches Capture Spine."""

    ORGANIZATION = "organization"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    EXTRACTION = "extraction"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    REWRITE = "rewrite"  # Added for GenAI Spine
    CLASSIFICATION = "classification"
    CUSTOM = "custom"


class VariableType(str, Enum):
    """Variable types for prompt templates."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    ENUM = "enum"


# =============================================================================
# Prompt Variable Schema
# =============================================================================


class PromptVariable(BaseModel):
    """Definition of a template variable.

    Compatible with Capture Spine's PromptVariable.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Variable name used in template")
    description: str | None = Field(None, description="Human-readable description")
    type: VariableType = Field(VariableType.STRING, description="Variable type")
    required: bool = Field(False, description="Whether variable is required")
    default: Any | None = Field(None, description="Default value if not provided")
    options: list[str] | None = Field(None, description="Valid options for enum type")


# =============================================================================
# Prompt Schemas
# =============================================================================


class PromptCreate(BaseModel):
    """Data for creating a new prompt."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    category: PromptCategory = PromptCategory.CUSTOM
    tags: list[str] = Field(default_factory=list)

    # Content
    system_prompt: str | None = None
    user_prompt_template: str = Field(..., min_length=1)
    variables: list[PromptVariable] = Field(default_factory=list)

    # LLM settings
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int | None = None
    output_schema: dict[str, Any] | None = None

    # Visibility
    is_system: bool = False
    is_public: bool = False
    created_by: str | None = None  # User ID


class PromptUpdate(BaseModel):
    """Data for updating a prompt.

    All fields optional - only provided fields are updated.
    Content changes (system_prompt, user_prompt_template, variables)
    trigger a new version.
    """

    name: str | None = None
    description: str | None = None
    category: PromptCategory | None = None
    tags: list[str] | None = None

    # Content (changes create new version)
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    variables: list[PromptVariable] | None = None

    # LLM settings (changes create new version)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    output_schema: dict[str, Any] | None = None

    # Visibility
    is_public: bool | None = None


class PromptRecord(BaseModel):
    """Complete prompt record from storage.

    This is what's returned from repository operations.
    Includes current version content for convenience.
    """

    model_config = ConfigDict(frozen=True)

    # Identity
    id: UUID
    slug: str
    name: str
    description: str | None
    category: PromptCategory
    tags: list[str]

    # Current version content
    system_prompt: str | None
    user_prompt_template: str
    variables: list[PromptVariable]

    # LLM settings
    preferred_provider: str | None
    preferred_model: str | None
    temperature: float
    max_tokens: int | None
    output_schema: dict[str, Any] | None

    # Visibility & ownership
    is_system: bool
    is_public: bool
    is_active: bool
    created_by: str | None

    # Versioning
    version: int
    current_version_id: UUID

    # Timestamps
    created_at: datetime
    updated_at: datetime


class PromptVersionRecord(BaseModel):
    """Immutable version record.

    Every content change creates a new version.
    Versions are never modified after creation.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    prompt_id: UUID
    version: int

    # Content snapshot
    system_prompt: str | None
    user_prompt_template: str
    variables: list[PromptVariable]

    # LLM settings snapshot
    preferred_provider: str | None
    preferred_model: str | None
    temperature: float
    max_tokens: int | None
    output_schema: dict[str, Any] | None

    # Metadata
    change_notes: str | None
    created_by: str | None
    created_at: datetime


# =============================================================================
# Execution Schemas
# =============================================================================


class ExecutionCreate(BaseModel):
    """Data for recording an execution."""

    # What was executed
    prompt_id: UUID | None = None
    prompt_version: int | None = None
    capability: str | None = None  # summarize, extract, rewrite, etc.

    # Provider details
    provider: str
    model: str

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0

    # Cost (in USD)
    cost_usd: Decimal = Field(default=Decimal("0"))

    # Performance
    latency_ms: int = 0

    # Status
    success: bool = True
    error: str | None = None

    # Context
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    # Optional: input/output for debugging
    input_content: str | None = None
    output_content: str | None = None


class ExecutionRecord(BaseModel):
    """Complete execution record from storage."""

    model_config = ConfigDict(frozen=True)

    id: UUID

    # What was executed
    prompt_id: UUID | None
    prompt_version: int | None
    capability: str | None

    # Provider details
    provider: str
    model: str

    # Token usage
    input_tokens: int
    output_tokens: int

    # Cost
    cost_usd: Decimal

    # Performance
    latency_ms: int

    # Status
    success: bool
    error: str | None

    # Context
    user_id: str | None
    session_id: str | None
    request_id: str | None

    # Timestamp
    created_at: datetime


# =============================================================================
# Usage Stats Schema
# =============================================================================


class UsageStats(BaseModel):
    """Aggregated usage statistics."""

    model_config = ConfigDict(frozen=True)

    period: str  # e.g., "2026-01-31" or "2026-01"
    provider: str | None = None
    model: str | None = None

    total_requests: int
    successful_requests: int
    failed_requests: int

    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: Decimal

    avg_latency_ms: float
    p95_latency_ms: float | None = None
