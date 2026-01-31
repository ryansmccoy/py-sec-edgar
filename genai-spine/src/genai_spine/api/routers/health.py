"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from genai_spine import __version__
from genai_spine.api.deps import RegistryDep, SettingsDep

router = APIRouter()


@router.get("/health")
async def health_check() -> dict:
    """Basic health check."""
    return {
        "status": "healthy",
        "version": __version__,
    }


@router.get("/ready")
async def readiness_check(
    settings: SettingsDep,
    registry: RegistryDep,
) -> dict:
    """Readiness check - verifies providers are accessible."""
    provider_status = {}

    for provider_name in settings.available_providers:
        try:
            provider = registry.get(provider_name)
            if provider:
                is_healthy = await provider.health_check()
                provider_status[provider_name] = "healthy" if is_healthy else "unhealthy"
            else:
                provider_status[provider_name] = "not_configured"
        except Exception as e:
            provider_status[provider_name] = f"error: {str(e)}"

    all_healthy = all(s == "healthy" for s in provider_status.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "version": __version__,
        "providers": provider_status,
    }
