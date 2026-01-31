"""OpenAI LLM provider."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import AsyncIterator

import httpx

from genai_spine.providers.base import CompletionRequest, CompletionResponse, LLMProvider
from genai_spine.settings import get_settings

logger = logging.getLogger(__name__)


# Cost per 1M tokens (input/output)
OPENAI_COSTS = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1-preview": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
}


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url

        if not self.api_key:
            raise ValueError("OpenAI API key required")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request via OpenAI."""
        started_at = datetime.now(UTC)
        settings = get_settings()
        model = request.model or settings.openai_default_model

        payload = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        if request.output_schema:
            payload["response_format"] = {"type": "json_object"}

        if request.stop:
            payload["stop"] = request.stop

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            # Parse JSON if requested
            parsed = None
            if request.output_schema:
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")

            # Calculate cost
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = self._calculate_cost(model, input_tokens, output_tokens)

            return CompletionResponse(
                content=content,
                parsed=parsed,
                provider="openai",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=True,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)
            logger.error(f"OpenAI HTTP error: {e}")
            return CompletionResponse(
                content="",
                provider="openai",
                model=model,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=False,
                error=f"HTTP {e.response.status_code}: {e.response.text}",
            )
        except Exception as e:
            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)
            logger.error(f"OpenAI error: {e}")
            return CompletionResponse(
                content="",
                provider="openai",
                model=model,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens from OpenAI."""
        settings = get_settings()
        model = request.model or settings.openai_default_model

        payload = {
            "model": model,
            "messages": request.messages,
            "temperature": request.temperature,
            "stream": True,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        async with self.client.stream("POST", "/chat/completions", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        """List available OpenAI models."""
        try:
            response = await self.client.get("/models")
            response.raise_for_status()
            data = response.json()
            # Filter to chat models
            chat_models = [
                m["id"] for m in data.get("data", []) if m["id"].startswith(("gpt-", "o1"))
            ]
            return sorted(chat_models)
        except Exception as e:
            logger.error(f"Failed to list OpenAI models: {e}")
            return list(OPENAI_COSTS.keys())

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for a request."""
        costs = OPENAI_COSTS.get(model, (0.0, 0.0))
        input_cost = Decimal(str(costs[0])) * input_tokens / 1_000_000
        output_cost = Decimal(str(costs[1])) * output_tokens / 1_000_000
        return input_cost + output_cost

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
