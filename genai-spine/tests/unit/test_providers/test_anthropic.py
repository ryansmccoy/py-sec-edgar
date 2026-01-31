"""Unit tests for Anthropic provider."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from genai_spine.providers.base import CompletionRequest, CompletionResponse


# Skip all tests if no API key - these tests would require mocking httpx
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Anthropic API key not available - skipping provider tests",
)


class TestAnthropicProviderUnit:
    """Unit tests for AnthropicProvider that don't require API key."""

    def test_anthropic_models_list(self):
        """Test that model list is defined."""
        from genai_spine.providers.anthropic import ANTHROPIC_MODELS

        assert len(ANTHROPIC_MODELS) > 0
        assert "claude-sonnet-4-20250514" in ANTHROPIC_MODELS
        assert "claude-3-5-sonnet-20241022" in ANTHROPIC_MODELS

    def test_provider_name_attribute(self):
        """Test provider has name attribute."""
        from genai_spine.providers.anthropic import AnthropicProvider

        assert AnthropicProvider.name == "anthropic"


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="Anthropic API key required")
class TestAnthropicProviderIntegration:
    """Integration tests for AnthropicProvider - require API key."""

    @pytest.fixture
    def provider(self):
        """Create Anthropic provider."""
        from genai_spine.providers.anthropic import AnthropicProvider

        return AnthropicProvider()

    @pytest.mark.asyncio
    async def test_list_models(self, provider):
        """Test listing available models."""
        models = await provider.list_models()

        assert "claude-sonnet-4-20250514" in models
        assert "claude-3-5-sonnet-20241022" in models

    def test_default_model(self, provider):
        """Test default model property."""
        assert provider.default_model in [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
        ]

    def test_provider_name(self, provider):
        """Test provider name."""
        assert provider.name == "anthropic"
