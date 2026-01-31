"""SQLAlchemy models for GenAI Spine storage."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Prompt(Base):
    """Prompt template for LLM operations.

    Prompts are versioned - each update creates a new PromptVersion record
    while keeping the prompt ID stable for references.
    """

    __tablename__ = "prompts"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Content (current version)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    variables: Mapped[list] = mapped_column(JSON, default=list)  # [{name, type, required, default}]

    # Visibility
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Built-in prompts
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Shared prompts
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)  # User ID

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    versions: Mapped[list["PromptVersion"]] = relationship(
        "PromptVersion", back_populates="prompt", cascade="all, delete-orphan"
    )
    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="prompt")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "category": self.category,
            "tags": self.tags,
            "variables": self.variables,
            "is_system": self.is_system,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PromptVersion(Base):
    """Immutable version record for a prompt.

    Every time a prompt is updated, a new version is created here.
    This enables rollback, audit trail, and A/B testing.
    """

    __tablename__ = "prompt_versions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Foreign key to prompt
    prompt_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Version number (1, 2, 3, ...)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Content snapshot (immutable)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, default=list)

    # Change tracking
    change_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="versions")

    __table_args__ = (UniqueConstraint("prompt_id", "version", name="uq_prompt_version"),)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "system_prompt": self.system_prompt,
            "user_prompt_template": self.user_prompt_template,
            "variables": self.variables,
            "change_notes": self.change_notes,
            "changed_by": self.changed_by,
            "created_at": self.created_at,
        }


class Execution(Base):
    """Record of a prompt execution.

    Tracks every LLM call for:
    - Cost tracking and budgeting
    - Performance monitoring
    - Audit trail
    - Usage analytics
    """

    __tablename__ = "executions"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # What was executed
    prompt_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    prompt_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capability: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # summarize, extract, classify, etc.

    # Provider details
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)

    # Cost (in USD)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 8), default=0)

    # Performance
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Context
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    prompt: Mapped["Prompt | None"] = relationship("Prompt", back_populates="executions")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "capability": self.capability,
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": float(self.cost_usd) if self.cost_usd else 0,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error": self.error,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at,
        }


class DailyCost(Base):
    """Aggregated daily costs by provider and model.

    Pre-aggregated for fast dashboard queries and budget enforcement.
    """

    __tablename__ = "daily_costs"

    # Composite primary key
    date: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), primary_key=True)
    model: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Aggregated metrics
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(12, 6), default=0)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Last update
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "provider": self.provider,
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": float(self.total_cost_usd) if self.total_cost_usd else 0,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "avg_latency_ms": self.avg_latency_ms,
        }


class UserLLMConfig(Base):
    """Per-user LLM configuration and API keys.

    Allows users to bring their own API keys and set preferences.
    API keys are encrypted at rest.
    """

    __tablename__ = "user_llm_configs"

    # Primary key (user_id)
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Preferences
    default_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # API Keys (encrypted)
    openai_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    anthropic_api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Budget limits
    daily_budget_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    monthly_budget_usd: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Feature flags
    allow_external_providers: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
