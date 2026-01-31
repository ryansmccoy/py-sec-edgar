"""Unit tests for provider registry."""

from __future__ import annotations

import pytest

from genai_spine.providers.base import LLMProvider
from genai_spine.providers.registry import ProviderRegistry


@pytest.mark.unit
class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_register_provider(self, mock_provider):
        """Can register a provider."""
        registry = ProviderRegistry()

        registry.register("test", mock_provider)

        assert "test" in registry._providers
        assert registry.get("test") is mock_provider

    def test_get_unknown_provider(self):
        """Getting unknown provider returns None."""
        registry = ProviderRegistry()

        result = registry.get("nonexistent")

        assert result is None

    def test_list_empty_registry(self):
        """Empty registry has no providers initially."""
        registry = ProviderRegistry()
        registry._initialized = True  # Skip auto-initialization

        result = list(registry._providers.keys())

        assert result == []

    def test_list_multiple_providers(self, mock_provider):
        """List returns all registered provider names."""
        registry = ProviderRegistry()
        registry._initialized = True  # Skip auto-initialization
        registry.register("provider1", mock_provider)
        registry.register("provider2", mock_provider)

        result = list(registry._providers.keys())

        assert set(result) == {"provider1", "provider2"}

    def test_register_overwrites(self, mock_provider):
        """Re-registering same name overwrites."""
        registry = ProviderRegistry()

        # Create another mock provider
        class OtherProvider(LLMProvider):
            name = "other"

            async def complete(self, request):
                pass

            async def list_models(self):
                return []

        other = OtherProvider()

        registry.register("test", mock_provider)
        registry.register("test", other)

        assert registry.get("test") is other
