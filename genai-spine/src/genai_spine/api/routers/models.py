"""Models endpoint - list available models."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from genai_spine.api.deps import RegistryDep, SettingsDep

router = APIRouter()


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    object: str = "model"
    created: int = 0
    owned_by: str
    provider: str


class ModelsResponse(BaseModel):
    """Response for /v1/models endpoint."""

    object: str = "list"
    data: list[ModelInfo]


@router.get("/models", response_model=ModelsResponse)
async def list_models(
    settings: SettingsDep,
    registry: RegistryDep,
) -> ModelsResponse:
    """List all available models across all providers.

    OpenAI-compatible endpoint.
    """
    models: list[ModelInfo] = []

    for provider_name in settings.available_providers:
        provider = registry.get(provider_name)
        if provider:
            try:
                provider_models = await provider.list_models()
                for model_id in provider_models:
                    models.append(
                        ModelInfo(
                            id=model_id,
                            owned_by=provider_name,
                            provider=provider_name,
                        )
                    )
            except Exception:
                # Skip providers that fail to list models
                pass

    return ModelsResponse(data=models)


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    registry: RegistryDep,
) -> ModelInfo:
    """Get information about a specific model.

    OpenAI-compatible endpoint.
    """
    # Try to find which provider owns this model
    for provider_name, provider in registry.providers.items():
        try:
            models = await provider.list_models()
            if model_id in models:
                return ModelInfo(
                    id=model_id,
                    owned_by=provider_name,
                    provider=provider_name,
                )
        except Exception:
            pass

    # Return a generic response if model not found in any provider
    return ModelInfo(
        id=model_id,
        owned_by="unknown",
        provider="unknown",
    )
