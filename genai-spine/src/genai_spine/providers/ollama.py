"""Ollama LLM provider."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import AsyncIterator

import httpx

from genai_spine.providers.base import CompletionRequest, CompletionResponse, LLMProvider
from genai_spine.settings import get_settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""

    name = "ollama"

    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.ollama_url
        self.timeout = timeout or settings.ollama_timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Execute a completion request via Ollama."""
        started_at = datetime.now(UTC)
        settings = get_settings()
        model = request.model or settings.default_model

        # Convert messages to Ollama format
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in request.messages]

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }

        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        # Request JSON format if schema provided
        if request.output_schema:
            payload["format"] = "json"

        try:
            response = await self.client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)

            content = data["message"]["content"]

            # Parse JSON if requested
            parsed = None
            if request.output_schema:
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")

            # Ollama provides token counts in response
            input_tokens = data.get("prompt_eval_count", 0)
            output_tokens = data.get("eval_count", 0)

            return CompletionResponse(
                content=content,
                parsed=parsed,
                provider="ollama",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=True,
                raw_response=data,
            )

        except httpx.HTTPStatusError as e:
            completed_at = datetime.now(UTC)
            latency_ms = int((completed_at - started_at).total_seconds() * 1000)
            logger.error(f"Ollama HTTP error: {e}")
            return CompletionResponse(
                content="",
                provider="ollama",
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
            logger.error(f"Ollama error: {e}")
            return CompletionResponse(
                content="",
                provider="ollama",
                model=model,
                started_at=started_at,
                completed_at=completed_at,
                latency_ms=latency_ms,
                success=False,
                error=str(e),
            )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        """Stream completion tokens from Ollama."""
        settings = get_settings()
        model = request.model or settings.default_model

        messages = [{"role": msg["role"], "content": msg["content"]} for msg in request.messages]

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": request.temperature,
            },
        }

        if request.max_tokens:
            payload["options"]["num_predict"] = request.max_tokens

        async with self.client.stream("POST", "/api/chat", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue

    async def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
