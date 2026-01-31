# Adding New Providers

> Guide for implementing new LLM provider integrations.

---

## Overview

Providers are implementations of the `LLMProvider` abstract interface. Each provider handles:
- Authentication with the LLM service
- Request/response transformation
- Streaming support
- Cost calculation

---

## Provider Interface

```python
# providers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CompletionRequest:
    """Unified request format."""
    messages: list[dict]
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    output_schema: dict | None = None


@dataclass
class CompletionResponse:
    """Unified response format."""
    content: str
    model: str
    success: bool
    error: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    raw_response: dict | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute completion request."""
        pass

    @abstractmethod
    async def stream_complete(
        self, request: CompletionRequest
    ) -> AsyncIterator[str]:
        """Execute streaming completion request."""
        pass

    @abstractmethod
    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost for tokens used."""
        pass
```

---

## Step-by-Step Guide

### 1. Create Provider File

```python
# providers/groq.py

"""Groq provider for ultra-fast inference."""

import httpx
from genai_spine.providers.base import (
    CompletionRequest,
    CompletionResponse,
    LLMProvider,
)


# Pricing per million tokens (as of 2024)
GROQ_PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}
```

### 2. Implement Provider Class

```python
class GroqProvider(LLMProvider):
    """Groq cloud provider for ultra-fast inference."""

    def __init__(self, api_key: str, base_url: str | None = None):
        """Initialize Groq provider.

        Args:
            api_key: Groq API key
            base_url: Override API URL (optional)
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.groq.com/openai/v1"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute completion request against Groq API."""
        client = await self._get_client()

        # Transform to Groq/OpenAI format
        payload = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        # Groq supports response_format for JSON
        if request.output_schema:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await client.post(
                "/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            return CompletionResponse(
                content=content,
                model=data.get("model", request.model),
                success=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self.calculate_cost(
                    request.model, input_tokens, output_tokens
                ),
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            return CompletionResponse(
                content="",
                model=request.model,
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            return CompletionResponse(
                content="",
                model=request.model,
                success=False,
                error=str(e),
            )

    async def stream_complete(
        self, request: CompletionRequest
    ) -> AsyncIterator[str]:
        """Stream completion from Groq API."""
        client = await self._get_client()

        payload = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": True,
        }

        async with client.stream(
            "POST",
            "/chat/completions",
            json=payload,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    delta = chunk["choices"][0].get("delta", {})
                    if content := delta.get("content"):
                        yield content

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost based on Groq pricing."""
        pricing = GROQ_PRICING.get(model, {"input": 0.5, "output": 0.5})

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

### 3. Register Provider

```python
# providers/registry.py

from genai_spine.providers.groq import GroqProvider

PROVIDER_REGISTRY = {
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "groq": GroqProvider,  # Add new provider
}


def get_provider(provider_name: str, settings: Settings) -> LLMProvider:
    """Get provider instance by name."""
    if provider_name == "groq":
        return GroqProvider(api_key=settings.groq_api_key)
    # ... other providers
```

### 4. Add Configuration

```python
# settings.py

class Settings(BaseSettings):
    # ... existing settings

    # Groq settings
    groq_api_key: str | None = None
    groq_default_model: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_prefix="GENAI_",
        env_file=".env",
    )
```

### 5. Add Tests

```python
# tests/test_providers/test_groq.py

import pytest
from genai_spine.providers.groq import GroqProvider, GROQ_PRICING


def test_calculate_cost():
    provider = GroqProvider(api_key="test")

    # 1000 input + 500 output tokens
    cost = provider.calculate_cost(
        "llama-3.3-70b-versatile",
        input_tokens=1000,
        output_tokens=500,
    )

    expected = (1000 / 1_000_000 * 0.59) + (500 / 1_000_000 * 0.79)
    assert abs(cost - expected) < 0.0001


@pytest.mark.asyncio
async def test_complete_integration(groq_api_key):
    """Integration test (requires GROQ_API_KEY env var)."""
    if not groq_api_key:
        pytest.skip("GROQ_API_KEY not set")

    provider = GroqProvider(api_key=groq_api_key)

    response = await provider.complete(CompletionRequest(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "Say hello"}],
    ))

    assert response.success
    assert "hello" in response.content.lower()
    await provider.close()
```

---

## Provider Checklist

When adding a new provider, ensure:

- [ ] Implements `LLMProvider` interface
- [ ] Handles authentication (API keys, etc.)
- [ ] Transforms requests to provider format
- [ ] Parses responses to `CompletionResponse`
- [ ] Calculates costs accurately
- [ ] Handles errors gracefully
- [ ] Supports streaming (if available)
- [ ] Cleans up resources (`close()` method)
- [ ] Added to registry
- [ ] Configuration in settings
- [ ] Unit and integration tests
- [ ] Pricing documented

---

## Common Patterns

### OpenAI-Compatible APIs

Many providers use OpenAI-compatible APIs:
- Groq ✅
- Together AI ✅
- Anyscale ✅
- Local vLLM ✅

For these, you can often extend `OpenAIProvider`:

```python
class TogetherProvider(OpenAIProvider):
    """Together AI - uses OpenAI-compatible API."""

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.together.xyz/v1",
        )

    def calculate_cost(self, model, input_tokens, output_tokens):
        # Override with Together pricing
        return together_calculate_cost(model, input_tokens, output_tokens)
```

### AWS Bedrock

Bedrock uses AWS SDK, not HTTP:

```python
class BedrockProvider(LLMProvider):
    def __init__(self, region: str = "us-east-1"):
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=region)
```

### Local Models

For local models (Ollama, llama.cpp):

```python
class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    def calculate_cost(self, model, input_tokens, output_tokens):
        return 0.0  # Local = free
```

---

## Related Docs

- [../architecture/PROVIDERS.md](../architecture/PROVIDERS.md) — Provider architecture
- [../core/COST_TRACKING.md](../core/COST_TRACKING.md) — Cost tracking system
- [ADDING_CAPABILITIES.md](ADDING_CAPABILITIES.md) — Adding capabilities
