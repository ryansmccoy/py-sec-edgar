"""Commit message generation endpoint.

Exposes the commit generation capability for Capture Spine's Work Sessions feature.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep, UnitOfWorkDep
from genai_spine.api.tracking import record_execution_from_result
from genai_spine.capabilities.commit import (
    CommitStyle,
    generate_commit_message,
)

router = APIRouter()


# =============================================================================
# Generate Commit Message
# =============================================================================


class FileChange(BaseModel):
    """A file change for commit message generation."""

    path: str = Field(..., description="File path relative to repository root")
    status: str = Field(
        default="modified",
        description="Change status: added, modified, deleted, renamed",
    )
    diff: str | None = Field(
        default=None,
        description="Optional diff content for context",
    )


class ChatMessage(BaseModel):
    """A chat message for commit context."""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")


class GenerateCommitRequest(BaseModel):
    """Request to generate a commit message."""

    files: list[FileChange] = Field(
        ...,
        min_length=1,
        description="List of file changes",
    )
    chat_context: list[ChatMessage] | None = Field(
        default=None,
        description="Optional chat context for richer commit messages",
    )
    style: CommitStyle = Field(
        default=CommitStyle.CONVENTIONAL,
        description="Commit message style: conventional, semantic, simple",
    )
    include_scope: bool = Field(
        default=True,
        description="Include scope in conventional commits",
    )
    max_length: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Maximum message length",
    )
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class FeatureGroup(BaseModel):
    """A group of related file changes."""

    scope: str
    description: str
    files: list[str]


class GenerateCommitResponse(BaseModel):
    """Response from commit message generation."""

    commit_message: str
    feature_groups: list[FeatureGroup]
    suggested_tags: list[str]
    files_analyzed: int
    provider: str
    model: str
    input_tokens: int
    output_tokens: int


@router.post("/generate-commit", response_model=GenerateCommitResponse)
async def generate_commit(
    request: GenerateCommitRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> GenerateCommitResponse:
    """Generate a commit message from file changes and chat context.

    Analyzes file changes and optional chat context to create a well-organized
    commit message. Supports multiple styles:

    - **conventional**: feat(scope): description (Conventional Commits)
    - **semantic**: type: description (Semantic Commits)
    - **simple**: Plain descriptive message

    Returns the commit message along with:
    - Feature groups for organizing related changes
    - Suggested tags based on file paths and content

    Used by Capture Spine's Work Session "Generate Commit" feature.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    model = request.model or settings.default_model

    # Convert Pydantic models to dicts for the capability function
    files = [f.model_dump() for f in request.files]
    chat_context = [m.model_dump() for m in request.chat_context] if request.chat_context else None

    result = await generate_commit_message(
        provider=provider,
        files=files,
        chat_context=chat_context,
        style=request.style,
        include_scope=request.include_scope,
        max_length=request.max_length,
        model=model,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result,
        capability="generate-commit",
    )

    return GenerateCommitResponse(
        commit_message=result["commit_message"],
        feature_groups=[FeatureGroup(**g) for g in result["feature_groups"]],
        suggested_tags=result["suggested_tags"],
        files_analyzed=result["files_analyzed"],
        provider=result["provider"],
        model=result["model"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
    )
