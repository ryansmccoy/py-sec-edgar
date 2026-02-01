"""Base LLM provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4


@dataclass
class CompletionRequest:
    """Request for LLM completion."""

    messages: list[dict[str, str]]  # [{"role": "user", "content": "..."}]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    output_schema: dict | None = None  # For structured output (JSON mode)
    stop: list[str] | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class CompletionResponse:
    """Response from LLM completion."""

    # Core response
    content: str
    parsed: Any | None = None  # Parsed JSON if output_schema provided

    # Request tracking
    request_id: UUID = field(default_factory=uuid4)

    # Provider info
    provider: str = ""
    model: str = ""

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0

    # Cost tracking
    cost_usd: Decimal = field(default_factory=lambda: Decimal("0"))

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    latency_ms: int = 0

    # Status
    success: bool = True
    error: str | None = None

    # Raw response for debugging
    raw_response: dict = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All provider implementations must extend this class.
    """

    name: str = "base"

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request.

        Args:
            request: The completion request

        Returns:
            CompletionResponse with content, tokens, cost, timing
        """
        pass

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens.

        Default implementation falls back to non-streaming.
        Override in subclasses for true streaming support.

        Args:
            request: The completion request

        Yields:
            Individual tokens as they're generated
        """
        response = await self.complete(request)
        yield response.content

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List available models for this provider.

        Returns:
            List of model identifiers
        """
        pass

    async def health_check(self) -> bool:
        """Check if the provider is accessible.

        Returns:
            True if provider is healthy
        """
        try:
            await self.list_models()
            return True
        except Exception:
            return False
