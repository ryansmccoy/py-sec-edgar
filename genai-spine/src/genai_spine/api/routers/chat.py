"""Chat completions endpoint - OpenAI compatible."""

from __future__ import annotations

import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep
from genai_spine.providers.base import CompletionRequest

router = APIRouter()


class ChatMessage(BaseModel):
    """A message in a chat conversation."""

    role: str  # "system", "user", "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    """Request body for chat completion."""

    model: str
    messages: list[ChatMessage]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    stop: str | list[str] | None = None
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    user: str | None = None


class ChatCompletionChoice(BaseModel):
    """A single completion choice."""

    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class UsageInfo(BaseModel):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Response from chat completion."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    settings: SettingsDep,
    registry: RegistryDep,
) -> ChatCompletionResponse:
    """Create a chat completion.

    OpenAI-compatible endpoint for chat-based models.
    """
    # Determine provider from model name or use default
    provider_name = _get_provider_for_model(request.model, settings, registry)
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    # Convert to internal request format
    internal_request = CompletionRequest(
        messages=[{"role": m.role, "content": m.content} for m in request.messages],
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

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid4().hex[:24]}",
        created=int(time.time()),
        model=response.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response.content),
                finish_reason="stop",
            )
        ],
        usage=UsageInfo(
            prompt_tokens=response.input_tokens,
            completion_tokens=response.output_tokens,
            total_tokens=response.input_tokens + response.output_tokens,
        ),
    )


def _get_provider_for_model(
    model: str,
    settings: SettingsDep,
    registry: RegistryDep,
) -> str:
    """Determine which provider to use for a given model."""
    # Check if model name indicates a specific provider
    model_lower = model.lower()

    if model_lower.startswith("gpt-") or model_lower.startswith("o1"):
        return "openai"
    elif model_lower.startswith("claude-"):
        return "anthropic"
    elif model_lower.startswith("amazon.") or model_lower.startswith("anthropic."):
        return "bedrock"
    elif ":" in model:  # Ollama format like "llama3.2:latest"
        return "ollama"

    # Fall back to default provider
    return settings.default_provider
