"""Execution tracking helper for recording LLM calls.

Provides a reusable function to record executions after any LLM call.
"""

from __future__ import annotations

import logging
from uuid import UUID

from genai_spine.capabilities.cost import calculate_cost
from genai_spine.providers.base import CompletionResponse
from genai_spine.storage import UnitOfWork
from genai_spine.storage.schemas import ExecutionCreate

logger = logging.getLogger(__name__)


async def record_execution(
    uow: UnitOfWork,
    response: CompletionResponse,
    capability: str,
    prompt_id: UUID | None = None,
    prompt_version: int | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    request_id: str | None = None,
    input_content: str | None = None,
    output_content: str | None = None,
) -> None:
    """Record an LLM execution to the database.

    Call this after every LLM call to track usage, costs, and performance.

    Args:
        uow: Unit of work for database access
        response: The completion response from the LLM provider
        capability: The capability name (summarize, extract, rewrite, etc.)
        prompt_id: Optional prompt UUID if using a stored prompt
        prompt_version: Optional prompt version number
        user_id: Optional user identifier
        session_id: Optional session identifier
        request_id: Optional request identifier
        input_content: Optional input content for debugging
        output_content: Optional output content for debugging
    """
    try:
        # Recalculate cost using our centralized pricing
        cost = calculate_cost(
            response.model,
            response.input_tokens,
            response.output_tokens,
        )

        execution = ExecutionCreate(
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            capability=capability,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=cost,
            latency_ms=response.latency_ms,
            success=response.success,
            error=response.error,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            input_content=input_content[:1000] if input_content else None,  # Truncate
            output_content=output_content[:1000] if output_content else None,  # Truncate
        )

        await uow.executions.record(execution)
        logger.debug(
            f"Recorded execution: {capability} via {response.provider}/{response.model} "
            f"({response.input_tokens}+{response.output_tokens} tokens, ${cost})"
        )

    except Exception as e:
        # Don't fail the request if tracking fails
        logger.warning(f"Failed to record execution: {e}")


async def record_execution_from_result(
    uow: UnitOfWork,
    result: dict,
    capability: str,
    prompt_id: UUID | None = None,
    prompt_version: int | None = None,
    input_content: str | None = None,
) -> None:
    """Record an execution from a capability result dict.

    Many capability functions return dicts with provider, model, tokens, etc.
    This helper extracts those fields.

    Args:
        uow: Unit of work for database access
        result: Dict with provider, model, input_tokens, output_tokens, etc.
        capability: The capability name
        prompt_id: Optional prompt UUID
        prompt_version: Optional prompt version number
        input_content: Optional input content
    """
    try:
        provider = result.get("provider", "unknown")
        model = result.get("model", "unknown")
        input_tokens = result.get("input_tokens", 0)
        output_tokens = result.get("output_tokens", 0)
        latency_ms = result.get("latency_ms", 0)

        cost = calculate_cost(model, input_tokens, output_tokens)

        execution = ExecutionCreate(
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            capability=capability,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            success=True,
            input_content=input_content[:1000] if input_content else None,
        )

        await uow.executions.record(execution)
        logger.debug(
            f"Recorded execution: {capability} via {provider}/{model} "
            f"({input_tokens}+{output_tokens} tokens, ${cost})"
        )

    except Exception as e:
        logger.warning(f"Failed to record execution: {e}")
