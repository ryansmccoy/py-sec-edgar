"""Anthropic Claude LLM provider."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import AsyncIterator

import httpx

from genai_spine.capabilities.cost import calculate_cost
from genai_spine.providers.base import CompletionRequest, CompletionResponse, LLMProvider
from genai_spine.settings import get_settings

logger = logging.getLogger(__name__)


# Supported Anthropic models
ANTHROPIC_MODELS = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""

    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.default_model = settings.anthropic_default_model

        if not self.api_key:
            raise ValueError("Anthropic API key required")

        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request via Anthropic."""
        started_at = datetime.now(UTC)
        model = request.model or self.default_model

        # Extract system prompt from messages or use separately
        system_prompt = None
        messages = []

        for msg in request.messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if request.temperature is not None:
            payload["temperature"] = request.temperature

        if request.stop:
            payload["stop_sequences"] = request.stop

        try:
            response = await self.client.post("/v1/messages", json=payload)
            response.raise_for_status()
            data = response.json()

            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Extract content from response
            content_blocks = data.get("content", [])
            content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            # Parse JSON if requested
            parsed = None
            if request.output_schema:
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")

            # Calculate cost
            cost = calculate_cost(model, input_tokens, output_tokens)

            return CompletionResponse(
                content=content,
                parsed=parsed,
                provider="anthropic",
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
            logger.error(f"Anthropic HTTP error: {e}")
            return CompletionResponse(
                content="",
                provider="anthropic",
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
            logger.error(f"Anthropic error: {e}")
            return CompletionResponse(
                content="",
                provider="anthropic",
                model=model,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens from Anthropic."""
        model = request.model or self.default_model

        # Extract system prompt from messages
        system_prompt = None
        messages = []

        for msg in request.messages:
            if msg.get("role") == "system":
                system_prompt = msg.get("content", "")
            else:
                messages.append(
                    {
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", ""),
                    }
                )

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if request.temperature is not None:
            payload["temperature"] = request.temperature

        async with self.client.stream("POST", "/v1/messages", json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        event_type = data.get("type")

                        if event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                        elif event_type == "message_stop":
                            break
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        """List available Anthropic models."""
        # Anthropic doesn't have a models endpoint, return known models
        return ANTHROPIC_MODELS

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
