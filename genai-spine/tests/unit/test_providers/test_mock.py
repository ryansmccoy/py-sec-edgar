"""Unit tests for MockLLMProvider."""

from __future__ import annotations

import pytest

from genai_spine.providers.base import CompletionRequest


@pytest.mark.unit
class TestMockProvider:
    """Tests for MockLLMProvider fixture."""

    @pytest.mark.asyncio
    async def test_complete_default_response(self, mock_provider):
        """Provider returns default response for unknown prompts."""
        request = CompletionRequest(messages=[{"role": "user", "content": "Random question"}])

        response = await mock_provider.complete(request)

        assert response.content == "Mock response"
        assert response.success is True
        assert response.provider == "mock"

    @pytest.mark.asyncio
    async def test_complete_pattern_match(self, mock_provider):
        """Provider matches patterns in responses dict."""
        request = CompletionRequest(
            messages=[{"role": "user", "content": "Please summarize this article"}]
        )

        response = await mock_provider.complete(request)

        assert response.content == "This is a mock summary."

    @pytest.mark.asyncio
    async def test_complete_tracks_calls(self, mock_provider):
        """Provider tracks all calls for assertions."""
        request1 = CompletionRequest(messages=[{"role": "user", "content": "First"}])
        request2 = CompletionRequest(messages=[{"role": "user", "content": "Second"}])

        await mock_provider.complete(request1)
        await mock_provider.complete(request2)

        assert len(mock_provider.calls) == 2
        assert mock_provider.calls[0].messages[0]["content"] == "First"
        assert mock_provider.calls[1].messages[0]["content"] == "Second"

    @pytest.mark.asyncio
    async def test_list_models(self, mock_provider):
        """Provider lists mock models."""
        models = await mock_provider.list_models()

        assert "mock-model" in models
        assert "mock-model-large" in models

    @pytest.mark.asyncio
    async def test_health_check(self, mock_provider):
        """Provider health check returns True."""
        is_healthy = await mock_provider.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_token_counting(self, mock_provider):
        """Provider estimates token counts."""
        request = CompletionRequest(
            messages=[{"role": "user", "content": "one two three four five"}]
        )

        response = await mock_provider.complete(request)

        # Mock provider counts words as tokens
        assert response.input_tokens == 5
        assert response.output_tokens > 0
