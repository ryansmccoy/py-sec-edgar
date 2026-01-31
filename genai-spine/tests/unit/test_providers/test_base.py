"""Unit tests for base provider abstraction."""

from __future__ import annotations

from decimal import Decimal

import pytest

from genai_spine.providers.base import CompletionRequest, CompletionResponse


class TestCompletionRequest:
    """Tests for CompletionRequest dataclass."""

    def test_minimal_request(self):
        """Create request with only required fields."""
        request = CompletionRequest(messages=[{"role": "user", "content": "Hello"}])

        assert request.messages == [{"role": "user", "content": "Hello"}]
        assert request.model is None
        assert request.temperature == 0.7
        assert request.max_tokens is None

    def test_full_request(self):
        """Create request with all fields."""
        request = CompletionRequest(
            messages=[
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hello"},
            ],
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000,
            output_schema={"type": "object"},
            stop=["END"],
            metadata={"user_id": "123"},
        )

        assert len(request.messages) == 2
        assert request.model == "gpt-4"
        assert request.temperature == 0.5
        assert request.max_tokens == 1000
        assert request.output_schema == {"type": "object"}
        assert request.stop == ["END"]
        assert request.metadata == {"user_id": "123"}


class TestCompletionResponse:
    """Tests for CompletionResponse dataclass."""

    def test_minimal_response(self):
        """Create response with only content."""
        response = CompletionResponse(content="Hello back!")

        assert response.content == "Hello back!"
        assert response.success is True
        assert response.input_tokens == 0
        assert response.output_tokens == 0
        assert response.cost_usd == Decimal("0")

    def test_full_response(self):
        """Create response with all fields."""
        response = CompletionResponse(
            content="Generated text",
            parsed={"key": "value"},
            provider="openai",
            model="gpt-4",
            input_tokens=50,
            output_tokens=100,
            cost_usd=Decimal("0.01"),
            latency_ms=500,
            success=True,
        )

        assert response.content == "Generated text"
        assert response.parsed == {"key": "value"}
        assert response.provider == "openai"
        assert response.model == "gpt-4"
        assert response.input_tokens == 50
        assert response.output_tokens == 100
        assert response.cost_usd == Decimal("0.01")
        assert response.latency_ms == 500

    def test_error_response(self):
        """Create error response."""
        response = CompletionResponse(
            content="",
            success=False,
            error="API rate limit exceeded",
        )

        assert response.content == ""
        assert response.success is False
        assert response.error == "API rate limit exceeded"
