"""Execute prompt endpoint for pipeline support.

Provides a unified way to execute any stored prompt with variables,
supporting Capture Spine's pipeline feature.
"""

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep, UnitOfWorkDep
from genai_spine.api.tracking import record_execution

router = APIRouter()


# =============================================================================
# Execute Prompt
# =============================================================================


class ExecutePromptRequest(BaseModel):
    """Request to execute a stored prompt."""

    prompt_slug: str | None = Field(
        default=None,
        description="Prompt slug to execute (mutually exclusive with prompt_id)",
    )
    prompt_id: UUID | None = Field(
        default=None,
        description="Prompt UUID to execute (mutually exclusive with prompt_slug)",
    )
    variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Variables to substitute in the prompt template",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution options (provider, model, temperature, max_tokens)",
    )


class ExecutePromptResponse(BaseModel):
    """Response from prompt execution."""

    output: str
    prompt_slug: str
    prompt_name: str
    prompt_version: int
    variables_used: dict[str, Any]
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float | None = None
    cost_usd: float | None = None


def _substitute_variables(template: str, variables: dict[str, Any]) -> str:
    """Substitute variables in a prompt template.

    Supports {variable_name} syntax.
    """
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def _extract_required_variables(template: str) -> set[str]:
    """Extract variable names from a template."""
    # Find all {variable_name} patterns
    return set(re.findall(r"\{(\w+)\}", template))


@router.post("/execute-prompt", response_model=ExecutePromptResponse)
async def execute_prompt(
    request: ExecutePromptRequest,
    uow: UnitOfWorkDep,
    settings: SettingsDep,
    registry: RegistryDep,
) -> ExecutePromptResponse:
    """Execute a stored prompt with variable substitution.

    Looks up a prompt by slug or ID, substitutes provided variables,
    and executes it using the specified (or prompt's preferred) provider/model.

    This endpoint supports Capture Spine's pipeline feature, allowing
    dynamic prompt execution with variable content.

    **Options:**
    - `provider`: Override the LLM provider
    - `model`: Override the model
    - `temperature`: Override the temperature
    - `max_tokens`: Override max tokens

    **Example:**
    ```json
    {
      "prompt_slug": "rewrite-clean",
      "variables": {"content": "Text to rewrite..."},
      "options": {"provider": "ollama", "model": "llama3.2:latest"}
    }
    ```
    """
    # Validate request - must have either slug or id
    if not request.prompt_slug and not request.prompt_id:
        raise HTTPException(
            status_code=400,
            detail="Either prompt_slug or prompt_id must be provided",
        )

    if request.prompt_slug and request.prompt_id:
        raise HTTPException(
            status_code=400,
            detail="Provide either prompt_slug or prompt_id, not both",
        )

    # Fetch the prompt
    if request.prompt_slug:
        prompt = await uow.prompts.get_by_slug(request.prompt_slug)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with slug '{request.prompt_slug}' not found",
            )
    else:
        prompt = await uow.prompts.get(request.prompt_id)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"Prompt with ID '{request.prompt_id}' not found",
            )

    # Check for required variables
    required_vars = _extract_required_variables(prompt.user_prompt_template)
    if prompt.system_prompt:
        required_vars.update(_extract_required_variables(prompt.system_prompt))

    # Check for prompt-defined required variables
    for var in prompt.variables:
        if var.required and var.name not in request.variables:
            # Check for default value
            if var.default is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Required variable '{var.name}' not provided",
                )
            # Use default value
            request.variables[var.name] = var.default

    # Substitute variables
    user_prompt = _substitute_variables(
        prompt.user_prompt_template,
        request.variables,
    )
    system_prompt = None
    if prompt.system_prompt:
        system_prompt = _substitute_variables(
            prompt.system_prompt,
            request.variables,
        )

    # Determine provider and model
    options = request.options
    provider_name = (
        options.get("provider") or prompt.preferred_provider or settings.default_provider
    )
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider_name}' not available",
        )

    model = options.get("model") or prompt.preferred_model or settings.default_model

    temperature = options.get("temperature", prompt.temperature)
    max_tokens = options.get("max_tokens", prompt.max_tokens)

    # Execute the prompt
    response = await provider.complete(
        messages=[{"role": "user", "content": user_prompt}],
        model=model,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Track execution
    await record_execution(
        uow=uow,
        response=response,
        capability="execute-prompt",
        prompt_id=prompt.id,
        prompt_version=prompt.version,
        input_content=user_prompt,
        output_content=response.content,
    )

    return ExecutePromptResponse(
        output=response.content,
        prompt_slug=prompt.slug,
        prompt_name=prompt.name,
        prompt_version=prompt.version,
        variables_used=request.variables,
        provider=response.provider,
        model=response.model,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_ms=response.latency_ms,
        cost_usd=response.cost_usd,
    )
