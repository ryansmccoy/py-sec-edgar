"""Dependency injection for API routes."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends

from genai_spine.providers.registry import ProviderRegistry, get_registry
from genai_spine.settings import Settings, get_settings
from genai_spine.storage import (
    BackendType,
    StorageBackend,
    UnitOfWork,
    create_backend,
)

# =============================================================================
# Core Dependencies
# =============================================================================

# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[ProviderRegistry, Depends(get_registry)]


# =============================================================================
# Storage Dependencies
# =============================================================================

# Global backend instance (initialized at startup)
_storage_backend: StorageBackend | None = None


async def get_storage_backend() -> StorageBackend:
    """Get the storage backend instance.

    The backend is initialized at application startup via the
    storage_backend_lifespan context manager.

    Raises:
        RuntimeError: If backend not initialized
    """
    if _storage_backend is None:
        raise RuntimeError(
            "Storage backend not initialized. "
            "Ensure storage_backend_lifespan is used in app lifecycle."
        )
    return _storage_backend


async def get_unit_of_work() -> AsyncIterator[UnitOfWork]:
    """Dependency that provides a unit of work for request scope.

    Usage in routes:
        @router.get("/prompts/{slug}")
        async def get_prompt(
            slug: str,
            uow: UnitOfWorkDep,
        ):
            prompt = await uow.prompts.get_by_slug(slug)
            ...
    """
    backend = await get_storage_backend()
    async with backend.unit_of_work() as uow:
        yield uow


# Type aliases for storage DI
StorageBackendDep = Annotated[StorageBackend, Depends(get_storage_backend)]
UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


@asynccontextmanager
async def storage_backend_lifespan(settings: Settings) -> AsyncIterator[StorageBackend]:
    """Lifecycle manager for storage backend.

    Usage in main.py:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            settings = get_settings()
            async with storage_backend_lifespan(settings) as backend:
                yield {"storage": backend}

    Args:
        settings: Application settings with database config

    Yields:
        Initialized storage backend
    """
    global _storage_backend

    # Determine backend type from settings
    backend_type = BackendType(settings.storage_backend)

    if backend_type in (BackendType.POSTGRES, BackendType.POSTGRESQL):
        backend = create_backend(
            BackendType.POSTGRES,
            settings.database_url,
            min_connections=settings.db_pool_min,
            max_connections=settings.db_pool_max,
        )
    elif backend_type == BackendType.MEMORY:
        backend = create_backend(BackendType.MEMORY)
    else:
        # Default to SQLite
        backend = create_backend(
            BackendType.SQLITE,
            settings.sqlite_path or "genai_spine.db",
        )

    # Initialize backend
    await backend.initialize()
    _storage_backend = backend

    try:
        yield backend
    finally:
        # Cleanup
        await backend.close()
        _storage_backend = None


def init_storage_backend(backend: StorageBackend) -> None:
    """Manually set the storage backend (for testing).

    Args:
        backend: Pre-configured storage backend
    """
    global _storage_backend
    _storage_backend = backend


def clear_storage_backend() -> None:
    """Clear the storage backend reference (for testing)."""
    global _storage_backend
    _storage_backend = None
