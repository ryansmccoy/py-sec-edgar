"""Text completions endpoint - OpenAI compatible."""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep
from genai_spine.providers.base import CompletionRequest

router = APIRouter()


class CompletionRequestBody(BaseModel):
    """Request body for text completion."""

    model: str
    prompt: str | list[str]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    stop: str | list[str] | None = None
    echo: bool = False
    user: str | None = None


class CompletionChoice(BaseModel):
    """A single completion choice."""

    text: str
    index: int
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(BaseModel):
    """Response from text completion."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[CompletionChoice]
    usage: UsageInfo


@router.post("/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequestBody,
    settings: SettingsDep,
    registry: RegistryDep,
) -> CompletionResponse:
    """Create a text completion.

    OpenAI-compatible endpoint for text completion models.
    """
    # Handle single prompt or list
    prompt = request.prompt if isinstance(request.prompt, str) else request.prompt[0]

    # Determine provider
    provider_name = settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    # Convert to chat format (most modern models are chat-based)
    internal_request = CompletionRequest(
        messages=[{"role": "user", "content": prompt}],
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    try:
        response = await provider.complete(internal_request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Completion failed: {str(e)}",
        )

    return CompletionResponse(
        id=f"cmpl-{uuid4().hex[:24]}",
        created=int(time.time()),
        model=response.model,
        choices=[
            CompletionChoice(
                text=response.content,
                index=0,
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=response.input_tokens,
            completion_tokens=response.output_tokens,
            total_tokens=response.input_tokens + response.output_tokens,
        ),
    )
