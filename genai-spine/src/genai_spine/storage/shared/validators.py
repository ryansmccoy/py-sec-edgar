"""Input validation helpers for GenAI-Spine storage.

Provides common validation logic shared between storage backends.
"""

from __future__ import annotations

from uuid import UUID

from genai_spine.storage.schemas import PromptCreate, PromptRecord, PromptUpdate


# =============================================================================
# Prompt Validation
# =============================================================================


def validate_prompt_create(prompt: PromptCreate) -> list[str]:
    """Validate prompt creation data.

    Returns list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if not prompt.slug:
        errors.append("Slug is required")
    elif len(prompt.slug) > 255:
        errors.append("Slug must be 255 characters or less")

    if not prompt.name:
        errors.append("Name is required")
    elif len(prompt.name) > 255:
        errors.append("Name must be 255 characters or less")

    if not prompt.user_prompt_template:
        errors.append("User prompt template is required")

    if prompt.temperature is not None:
        if prompt.temperature < 0 or prompt.temperature > 2:
            errors.append("Temperature must be between 0 and 2")

    return errors


def validate_prompt_update(
    prompt_id: UUID,
    update: PromptUpdate,
    existing: PromptRecord | None,
) -> list[str]:
    """Validate prompt update data.

    Returns list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if existing is None:
        errors.append(f"Prompt {prompt_id} not found")
        return errors

    if update.name is not None and len(update.name) > 255:
        errors.append("Name must be 255 characters or less")

    if update.temperature is not None:
        if update.temperature < 0 or update.temperature > 2:
            errors.append("Temperature must be between 0 and 2")

    return errors


def content_changed(update: PromptUpdate, existing: PromptRecord) -> bool:
    """Check if update contains content changes that require a new version."""
    return any(
        [
            update.system_prompt is not None and update.system_prompt != existing.system_prompt,
            update.user_prompt_template is not None
            and update.user_prompt_template != existing.user_prompt_template,
            update.variables is not None and update.variables != existing.variables,
            update.temperature is not None and update.temperature != existing.temperature,
            update.max_tokens is not None and update.max_tokens != existing.max_tokens,
            update.output_schema is not None and update.output_schema != existing.output_schema,
            update.preferred_provider is not None
            and update.preferred_provider != existing.preferred_provider,
            update.preferred_model is not None
            and update.preferred_model != existing.preferred_model,
        ]
    )


def merge_update(update: PromptUpdate, existing: PromptRecord) -> dict:
    """Merge update with existing record, returning complete field values.

    Returns dict with all fields needed for the update, using existing
    values where update provides None.
    """
    return {
        "name": update.name if update.name is not None else existing.name,
        "description": update.description
        if update.description is not None
        else existing.description,
        "category": (
            update.category.value if update.category is not None else existing.category.value
        ),
        "tags": update.tags if update.tags is not None else list(existing.tags),
        "system_prompt": (
            update.system_prompt if update.system_prompt is not None else existing.system_prompt
        ),
        "user_prompt_template": (
            update.user_prompt_template
            if update.user_prompt_template is not None
            else existing.user_prompt_template
        ),
        "variables": update.variables if update.variables is not None else existing.variables,
        "preferred_provider": (
            update.preferred_provider
            if update.preferred_provider is not None
            else existing.preferred_provider
        ),
        "preferred_model": (
            update.preferred_model
            if update.preferred_model is not None
            else existing.preferred_model
        ),
        "temperature": (
            update.temperature if update.temperature is not None else existing.temperature
        ),
        "max_tokens": (update.max_tokens if update.max_tokens is not None else existing.max_tokens),
        "output_schema": (
            update.output_schema if update.output_schema is not None else existing.output_schema
        ),
        "is_public": update.is_public if update.is_public is not None else existing.is_public,
    }


# =============================================================================
# UUID Validation
# =============================================================================


def validate_uuid(value: str | UUID | None, field_name: str) -> tuple[UUID | None, str | None]:
    """Validate and convert UUID value.

    Returns (uuid, error). If valid, error is None. If invalid, uuid is None.
    """
    if value is None:
        return None, None

    if isinstance(value, UUID):
        return value, None

    try:
        return UUID(value), None
    except (ValueError, TypeError):
        return None, f"Invalid UUID format for {field_name}: {value}"


# =============================================================================
# Pagination Validation
# =============================================================================


def validate_pagination(limit: int, offset: int) -> tuple[int, int, list[str]]:
    """Validate and normalize pagination parameters.

    Returns (limit, offset, errors).
    """
    errors: list[str] = []

    if limit < 0:
        errors.append("Limit must be non-negative")
        limit = 100
    elif limit > 1000:
        limit = 1000  # Cap at 1000

    if offset < 0:
        errors.append("Offset must be non-negative")
        offset = 0

    return limit, offset, errors
