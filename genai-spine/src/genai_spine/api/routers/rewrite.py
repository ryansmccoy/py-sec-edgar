"""Rewrite and title inference endpoints.

Exposes the rewrite capability for Capture Spine's Message Enrichment feature.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep, UnitOfWorkDep
from genai_spine.api.tracking import record_execution_from_result
from genai_spine.capabilities.rewrite import (
    RewriteMode,
    infer_title,
    rewrite_content,
)

router = APIRouter()


# =============================================================================
# Rewrite Content
# =============================================================================


class RewriteRequest(BaseModel):
    """Request to rewrite content."""

    content: str = Field(..., description="The content to rewrite")
    mode: RewriteMode = Field(
        default=RewriteMode.CLEAN,
        description="Rewrite mode: clean, format, organize, professional, casual, summarize, technical",
    )
    context: str | None = Field(
        default=None,
        description="Optional context from previous messages",
    )
    preserve_code_blocks: bool = Field(
        default=True,
        description="Whether to preserve code blocks unchanged",
    )
    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Override temperature (0.0-2.0)",
    )
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class RewriteResponse(BaseModel):
    """Response from rewrite operation."""

    original: str
    rewritten: str
    mode: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float | None = None
    cost_usd: float | None = None


@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite(
    request: RewriteRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> RewriteResponse:
    """Rewrite content using the specified mode.

    Supports multiple rewrite modes:
    - **clean**: Fix grammar, spelling, improve clarity
    - **format**: Add structure with headings, bullets, lists
    - **organize**: Reorganize into logical sections
    - **professional**: Business/formal tone
    - **casual**: Friendly, conversational tone
    - **summarize**: Condense to key points
    - **technical**: Technical documentation style

    Used by Capture Spine's Message Enrichment feature.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    model = request.model or settings.default_model

    result = await rewrite_content(
        provider=provider,
        content=request.content,
        mode=request.mode,
        model=model,
        context=request.context,
        preserve_code_blocks=request.preserve_code_blocks,
        temperature=request.temperature,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result,
        capability=f"rewrite-{request.mode.value}",
        input_content=request.content,
    )

    return RewriteResponse(**result)


# =============================================================================
# Infer Title
# =============================================================================


class InferTitleRequest(BaseModel):
    """Request to infer a title from content."""

    content: str = Field(..., description="The content to generate a title for")
    max_words: int = Field(
        default=10,
        ge=3,
        le=20,
        description="Maximum words in the title",
    )
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class InferTitleResponse(BaseModel):
    """Response from title inference."""

    title: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


@router.post("/infer-title", response_model=InferTitleResponse)
async def infer_title_endpoint(
    request: InferTitleRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> InferTitleResponse:
    """Generate a title for content.

    Creates a concise, descriptive title suitable for:
    - Message titles
    - Document headings
    - Search-friendly labels

    Used by Capture Spine's "Infer Title" feature.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    model = request.model or settings.default_model

    result = await infer_title(
        provider=provider,
        content=request.content,
        max_words=request.max_words,
        model=model,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result,
        capability="infer-title",
        input_content=request.content,
    )

    return InferTitleResponse(**result)
