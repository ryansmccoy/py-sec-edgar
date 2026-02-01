"""Type definitions for GenAI Spine Client.

These mirror the API schemas for type safety.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Common Types
# =============================================================================


class ChatMessage(BaseModel):
    """A message in a chat conversation."""

    role: str  # "system", "user", "assistant"
    content: str


class UsageInfo(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None = None


# =============================================================================
# Chat Completion Types
# =============================================================================


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion."""

    model: str
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo

    @property
    def content(self) -> str:
        """Get the content of the first choice."""
        if self.choices:
            return self.choices[0].message.content
        return ""


# =============================================================================
# Execute Prompt Types
# =============================================================================


class ExecutePromptRequest(BaseModel):
    """Request to execute a stored prompt."""

    prompt_slug: str | None = None
    prompt_id: UUID | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)


class ExecutePromptResponse(BaseModel):
    """Response from prompt execution."""

    output: str
    prompt_slug: str
    prompt_name: str
    prompt_version: int
    variables_used: dict[str, Any]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float | None = None
    cost_usd: float | None = None


# =============================================================================
# Model Types
# =============================================================================


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    name: str
    provider: str
    context_length: int | None = None
    input_cost_per_1k: float | None = None
    output_cost_per_1k: float | None = None
    capabilities: list[str] = Field(default_factory=list)


class ModelsResponse(BaseModel):
    """Response from list models endpoint."""

    models: list[ModelInfo]


# =============================================================================
# Prompt Types
# =============================================================================


class PromptVariable(BaseModel):
    """Prompt variable definition."""

    name: str
    description: str | None = None
    type: str = "string"
    required: bool = True
    default: str | None = None


class PromptInfo(BaseModel):
    """Information about a prompt."""

    id: UUID
    slug: str
    name: str
    description: str | None = None
    category: str = "custom"
    tags: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    user_prompt_template: str
    variables: list[PromptVariable] = Field(default_factory=list)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    version: int = 1
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PromptsListResponse(BaseModel):
    """Response from list prompts endpoint."""

    prompts: list[PromptInfo]
    total: int
    limit: int
    offset: int


class PromptCreateRequest(BaseModel):
    """Request to create a new prompt."""

    name: str
    slug: str
    description: str | None = None
    category: str = "custom"
    tags: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    user_prompt_template: str
    variables: list[PromptVariable] = Field(default_factory=list)
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


# =============================================================================
# Session Types (Chat Sessions - Tier A)
# =============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create a chat session."""

    model: str
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionInfo(BaseModel):
    """Information about a chat session."""

    id: UUID
    model: str
    system_prompt: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime


class SessionMessageRequest(BaseModel):
    """Request to send a message in a session."""

    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionMessageResponse(BaseModel):
    """Response from sending a message."""

    id: UUID
    session_id: UUID
    role: str
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float | None = None
    created_at: datetime


# =============================================================================
# Usage Types
# =============================================================================


class UsageStatsResponse(BaseModel):
    """Response from usage stats endpoint."""

    total_requests: int
    total_tokens: int
    total_cost_usd: float
    by_provider: dict[str, dict[str, Any]] = Field(default_factory=dict)
    by_model: dict[str, dict[str, Any]] = Field(default_factory=dict)
    period_start: datetime | None = None
    period_end: datetime | None = None


# =============================================================================
# Error Types
# =============================================================================


class ErrorDetail(BaseModel):
    """Error detail from API."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class GenAIError(Exception):
    """Base exception for GenAI client errors."""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
        request_id: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.request_id = request_id
        self.status_code = status_code


class ValidationError(GenAIError):
    """Request validation failed."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)


class NotFoundError(GenAIError):
    """Resource not found."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, code="NOT_FOUND", **kwargs)


class RateLimitError(GenAIError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs):
        super().__init__(message, code="RATE_LIMITED", **kwargs)
        self.retry_after = retry_after


class ProviderError(GenAIError):
    """LLM provider error."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        provider_code: str | None = None,
        provider_message: str | None = None,
        is_retryable: bool = False,
        **kwargs,
    ):
        super().__init__(message, code="PROVIDER_ERROR", **kwargs)
        self.provider = provider
        self.provider_code = provider_code
        self.provider_message = provider_message
        self.is_retryable = is_retryable
