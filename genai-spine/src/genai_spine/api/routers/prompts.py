"""Prompt management endpoints.

Provides a REST API for managing prompts and their versions.
Uses the database-agnostic storage layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from genai_spine.api.deps import UnitOfWorkDep
from genai_spine.storage import (
    PromptCategory,
    PromptVariable,
)
from genai_spine.storage import (
    PromptCreate as StoragePromptCreate,
)
from genai_spine.storage import (
    PromptUpdate as StoragePromptUpdate,
)

router = APIRouter()


# =============================================================================
# API Models (separate from storage schemas for flexibility)
# =============================================================================


class VariableSchema(BaseModel):
    """Prompt variable definition."""

    name: str = Field(..., description="Variable name (used in template)")
    description: str | None = Field(None, description="Human-readable description")
    type: str = Field("string", description="Variable type hint")
    required: bool = Field(True, description="Whether variable is required")
    default: str | None = Field(None, description="Default value if not provided")


class PromptCreateRequest(BaseModel):
    """Request to create a new prompt."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    category: str = Field("custom", description="Prompt category")
    tags: list[str] = Field(default_factory=list)
    system_prompt: str | None = None
    user_prompt_template: str = Field(..., min_length=1)
    variables: list[VariableSchema] = Field(default_factory=list)
    preferred_provider: str | None = Field(None, description="Preferred LLM provider")
    preferred_model: str | None = Field(None, description="Preferred model")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    output_schema: dict | None = Field(None, description="Expected output JSON schema")
    is_public: bool = False


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt."""

    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    variables: list[VariableSchema] | None = None
    preferred_provider: str | None = None
    preferred_model: str | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, gt=0)
    output_schema: dict | None = None
    is_public: bool | None = None
    change_notes: str | None = Field(None, description="Notes about this update")


class PromptResponse(BaseModel):
    """Response containing prompt data."""

    id: UUID
    slug: str
    name: str
    description: str | None
    category: str
    tags: list[str]
    system_prompt: str | None
    user_prompt_template: str
    variables: list[VariableSchema]
    preferred_provider: str | None
    preferred_model: str | None
    temperature: float
    max_tokens: int | None
    output_schema: dict | None
    is_system: bool
    is_public: bool
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class PromptListResponse(BaseModel):
    """Response containing list of prompts."""

    prompts: list[PromptResponse]
    total: int
    limit: int
    offset: int


class PromptVersionResponse(BaseModel):
    """Response containing prompt version data."""

    id: UUID
    prompt_id: UUID
    version: int
    system_prompt: str | None
    user_prompt_template: str
    variables: list[VariableSchema]
    preferred_provider: str | None
    preferred_model: str | None
    temperature: float
    max_tokens: int | None
    change_notes: str | None
    created_at: datetime


# =============================================================================
# Conversion Helpers
# =============================================================================


def _variable_to_schema(v: PromptVariable) -> VariableSchema:
    """Convert storage PromptVariable to API VariableSchema."""
    return VariableSchema(
        name=v.name,
        description=v.description,
        type=v.type,
        required=v.required,
        default=v.default,
    )


def _schema_to_variable(s: VariableSchema) -> PromptVariable:
    """Convert API VariableSchema to storage PromptVariable."""
    return PromptVariable(
        name=s.name,
        description=s.description,
        type=s.type,
        required=s.required,
        default=s.default,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    uow: UnitOfWorkDep,
    category: str | None = Query(None, description="Filter by category"),
    tags: Annotated[list[str] | None, Query(description="Filter by tags")] = None,
    search: str | None = Query(None, description="Search in name/description"),
    is_system: bool | None = Query(None, description="Filter system prompts"),
    is_public: bool | None = Query(None, description="Filter public prompts"),
    include_inactive: bool = Query(False, description="Include soft-deleted prompts"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PromptListResponse:
    """List all prompts with optional filtering."""
    prompts, total = await uow.prompts.list(
        category=category,
        tags=tags,
        search=search,
        is_system=is_system,
        is_public=is_public,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )

    return PromptListResponse(
        prompts=[
            PromptResponse(
                id=p.id,
                slug=p.slug,
                name=p.name,
                description=p.description,
                category=p.category.value,
                tags=list(p.tags),
                system_prompt=p.system_prompt,
                user_prompt_template=p.user_prompt_template,
                variables=[_variable_to_schema(v) for v in p.variables],
                preferred_provider=p.preferred_provider,
                preferred_model=p.preferred_model,
                temperature=p.temperature,
                max_tokens=p.max_tokens,
                output_schema=p.output_schema,
                is_system=p.is_system,
                is_public=p.is_public,
                is_active=p.is_active,
                version=p.version,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in prompts
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    uow: UnitOfWorkDep,
    request: PromptCreateRequest,
) -> PromptResponse:
    """Create a new prompt."""
    # Check for duplicate slug
    existing = await uow.prompts.get_by_slug(request.slug)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Prompt with slug '{request.slug}' already exists",
        )

    # Convert to storage schema
    try:
        category = PromptCategory(request.category)
    except ValueError:
        category = PromptCategory.CUSTOM

    create_data = StoragePromptCreate(
        slug=request.slug,
        name=request.name,
        description=request.description,
        category=category,
        tags=request.tags,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        variables=[_schema_to_variable(v) for v in request.variables],
        preferred_provider=request.preferred_provider,
        preferred_model=request.preferred_model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        output_schema=request.output_schema,
        is_system=False,
        is_public=request.is_public,
    )

    prompt = await uow.prompts.create(create_data)

    return PromptResponse(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        tags=list(prompt.tags),
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=[_variable_to_schema(v) for v in prompt.variables],
        preferred_provider=prompt.preferred_provider,
        preferred_model=prompt.preferred_model,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        output_schema=prompt.output_schema,
        is_system=prompt.is_system,
        is_public=prompt.is_public,
        is_active=prompt.is_active,
        version=prompt.version,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.get("/slug/{slug}", response_model=PromptResponse)
async def get_prompt_by_slug(
    uow: UnitOfWorkDep,
    slug: str,
) -> PromptResponse:
    """Get a prompt by slug."""
    prompt = await uow.prompts.get_by_slug(slug)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptResponse(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        tags=list(prompt.tags),
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=[_variable_to_schema(v) for v in prompt.variables],
        preferred_provider=prompt.preferred_provider,
        preferred_model=prompt.preferred_model,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        output_schema=prompt.output_schema,
        is_system=prompt.is_system,
        is_public=prompt.is_public,
        is_active=prompt.is_active,
        version=prompt.version,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
) -> PromptResponse:
    """Get a prompt by ID."""
    prompt = await uow.prompts.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    return PromptResponse(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        tags=list(prompt.tags),
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=[_variable_to_schema(v) for v in prompt.variables],
        preferred_provider=prompt.preferred_provider,
        preferred_model=prompt.preferred_model,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        output_schema=prompt.output_schema,
        is_system=prompt.is_system,
        is_public=prompt.is_public,
        is_active=prompt.is_active,
        version=prompt.version,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
    request: PromptUpdateRequest,
) -> PromptResponse:
    """Update a prompt (creates new version if content changes)."""
    existing = await uow.prompts.get(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if existing.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system prompts")

    # Convert to storage update
    category = None
    if request.category is not None:
        try:
            category = PromptCategory(request.category)
        except ValueError:
            category = PromptCategory.CUSTOM

    variables = None
    if request.variables is not None:
        variables = [_schema_to_variable(v) for v in request.variables]

    update_data = StoragePromptUpdate(
        name=request.name,
        description=request.description,
        category=category,
        tags=request.tags,
        system_prompt=request.system_prompt,
        user_prompt_template=request.user_prompt_template,
        variables=variables,
        preferred_provider=request.preferred_provider,
        preferred_model=request.preferred_model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        output_schema=request.output_schema,
        is_public=request.is_public,
    )

    prompt = await uow.prompts.update(
        prompt_id,
        update_data,
        change_notes=request.change_notes,
    )

    return PromptResponse(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        tags=list(prompt.tags),
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=[_variable_to_schema(v) for v in prompt.variables],
        preferred_provider=prompt.preferred_provider,
        preferred_model=prompt.preferred_model,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        output_schema=prompt.output_schema,
        is_system=prompt.is_system,
        is_public=prompt.is_public,
        is_active=prompt.is_active,
        version=prompt.version,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
    hard: bool = Query(False, description="Permanently delete instead of soft delete"),
) -> None:
    """Delete a prompt (soft delete by default)."""
    existing = await uow.prompts.get(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if existing.is_system:
        raise HTTPException(status_code=403, detail="Cannot delete system prompts")

    await uow.prompts.delete(prompt_id, soft=not hard)


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_prompt_versions(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
    limit: int = Query(50, ge=1, le=200),
) -> list[PromptVersionResponse]:
    """List all versions of a prompt."""
    existing = await uow.prompts.get(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    versions = await uow.prompts.list_versions(prompt_id, limit=limit)

    return [
        PromptVersionResponse(
            id=v.id,
            prompt_id=v.prompt_id,
            version=v.version,
            system_prompt=v.system_prompt,
            user_prompt_template=v.user_prompt_template,
            variables=[_variable_to_schema(var) for var in v.variables],
            preferred_provider=v.preferred_provider,
            preferred_model=v.preferred_model,
            temperature=v.temperature,
            max_tokens=v.max_tokens,
            change_notes=v.change_notes,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get("/{prompt_id}/versions/{version}", response_model=PromptVersionResponse)
async def get_prompt_version(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
    version: int,
) -> PromptVersionResponse:
    """Get a specific version of a prompt."""
    v = await uow.prompts.get_version(prompt_id, version)
    if not v:
        raise HTTPException(status_code=404, detail="Version not found")

    return PromptVersionResponse(
        id=v.id,
        prompt_id=v.prompt_id,
        version=v.version,
        system_prompt=v.system_prompt,
        user_prompt_template=v.user_prompt_template,
        variables=[_variable_to_schema(var) for var in v.variables],
        preferred_provider=v.preferred_provider,
        preferred_model=v.preferred_model,
        temperature=v.temperature,
        max_tokens=v.max_tokens,
        change_notes=v.change_notes,
        created_at=v.created_at,
    )


@router.post("/{prompt_id}/rollback/{version}", response_model=PromptResponse)
async def rollback_prompt(
    uow: UnitOfWorkDep,
    prompt_id: UUID,
    version: int,
) -> PromptResponse:
    """Rollback a prompt to a previous version."""
    existing = await uow.prompts.get(prompt_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Prompt not found")

    if existing.is_system:
        raise HTTPException(status_code=403, detail="Cannot modify system prompts")

    try:
        prompt = await uow.prompts.rollback_to_version(prompt_id, version)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return PromptResponse(
        id=prompt.id,
        slug=prompt.slug,
        name=prompt.name,
        description=prompt.description,
        category=prompt.category.value,
        tags=list(prompt.tags),
        system_prompt=prompt.system_prompt,
        user_prompt_template=prompt.user_prompt_template,
        variables=[_variable_to_schema(v) for v in prompt.variables],
        preferred_provider=prompt.preferred_provider,
        preferred_model=prompt.preferred_model,
        temperature=prompt.temperature,
        max_tokens=prompt.max_tokens,
        output_schema=prompt.output_schema,
        is_system=prompt.is_system,
        is_public=prompt.is_public,
        is_active=prompt.is_active,
        version=prompt.version,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )
