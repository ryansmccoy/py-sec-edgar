"""GenAI Spine Client - Typed HTTP wrapper for GenAI Spine API.

This is NOT a published package. Copy or reference directly.

Usage:
    from genai_spine_client import GenAIClient

    client = GenAIClient(base_url="http://localhost:8100")

    # Chat completion
    response = await client.chat_complete(
        messages=[{"role": "user", "content": "Hello!"}],
        model="gpt-4o-mini"
    )

    # Execute prompt
    result = await client.execute_prompt(
        slug="summarizer",
        variables={"text": content}
    )
"""

from genai_spine_client.client import GenAIClient
from genai_spine_client.types import (
    # Request types
    ChatMessage,
    ChatCompletionRequest,
    ExecutePromptRequest,
    # Response types
    ChatCompletionResponse,
    ExecutePromptResponse,
    ModelInfo,
    PromptInfo,
    UsageInfo,
    # Errors
    GenAIError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError,
)

__all__ = [
    # Client
    "GenAIClient",
    # Request types
    "ChatMessage",
    "ChatCompletionRequest",
    "ExecutePromptRequest",
    # Response types
    "ChatCompletionResponse",
    "ExecutePromptResponse",
    "ModelInfo",
    "PromptInfo",
    "UsageInfo",
    # Errors
    "GenAIError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ProviderError",
]
