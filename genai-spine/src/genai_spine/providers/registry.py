"""Provider registry for managing LLM providers."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from genai_spine.settings import get_settings

if TYPE_CHECKING:
    from genai_spine.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for LLM providers.

    Manages provider instances and provides lookup by name.
    """

    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._initialized = False

    @property
    def providers(self) -> dict[str, LLMProvider]:
        """Get all registered providers."""
        if not self._initialized:
            self._initialize_providers()
        return self._providers

    def _initialize_providers(self) -> None:
        """Initialize providers based on configuration."""
        if self._initialized:
            return

        settings = get_settings()

        # Always try to initialize Ollama (it's local)
        try:
            from genai_spine.providers.ollama import OllamaProvider

            self._providers["ollama"] = OllamaProvider()
            logger.info("Initialized Ollama provider")
        except Exception as e:
            logger.warning(f"Failed to initialize Ollama provider: {e}")

        # Initialize OpenAI if API key provided
        if settings.openai_api_key:
            try:
                from genai_spine.providers.openai import OpenAIProvider

                self._providers["openai"] = OpenAIProvider()
                logger.info("Initialized OpenAI provider")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Anthropic if API key provided
        if settings.anthropic_api_key:
            try:
                from genai_spine.providers.anthropic import AnthropicProvider

                self._providers["anthropic"] = AnthropicProvider()
                logger.info("Initialized Anthropic provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")

        # Initialize Bedrock (uses IAM credentials)
        try:
            from genai_spine.providers.bedrock import BedrockProvider

            self._providers["bedrock"] = BedrockProvider()
            logger.info("Initialized Bedrock provider")
        except ImportError:
            logger.debug("Bedrock provider not available (boto3 not installed)")
        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock provider: {e}")

        self._initialized = True

    def get(self, name: str) -> LLMProvider | None:
        """Get a provider by name.

        Args:
            name: Provider name (ollama, openai, anthropic, bedrock)

        Returns:
            Provider instance or None if not found
        """
        return self.providers.get(name)

    def get_default(self) -> LLMProvider | None:
        """Get the default provider.

        Returns:
            Default provider instance or None
        """
        settings = get_settings()
        return self.get(settings.default_provider)

    def register(self, name: str, provider: LLMProvider) -> None:
        """Register a provider.

        Args:
            name: Provider name
            provider: Provider instance
        """
        self._providers[name] = provider
        logger.info(f"Registered provider: {name}")

    def unregister(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name
        """
        if name in self._providers:
            del self._providers[name]
            logger.info(f"Unregistered provider: {name}")

    async def close_all(self) -> None:
        """Close all provider connections."""
        for name, provider in self._providers.items():
            try:
                if hasattr(provider, "close"):
                    await provider.close()
                logger.info(f"Closed provider: {name}")
            except Exception as e:
                logger.warning(f"Error closing provider {name}: {e}")


@lru_cache
def get_registry() -> ProviderRegistry:
    """Get the singleton provider registry."""
    return ProviderRegistry()
