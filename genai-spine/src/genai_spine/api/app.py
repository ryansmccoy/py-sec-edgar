"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genai_spine import __version__
from genai_spine.api.routers import (
    capabilities,
    chat,
    commit,
    completions,
    execute,
    health,
    models,
    prompts,
    rewrite,
    usage,
)
from genai_spine.api.deps import storage_backend_lifespan
from genai_spine.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"🚀 GenAI Spine v{__version__} starting...")
    print(f"   Default provider: {settings.default_provider}")
    print(f"   Default model: {settings.default_model}")
    print(f"   Available providers: {settings.available_providers}")
    print(f"   Storage backend: {settings.storage_backend}")

    # Initialize storage backend
    async with storage_backend_lifespan(settings) as backend:
        print(f"   Storage initialized: {type(backend).__name__}")
        yield

    # Shutdown
    print("👋 GenAI Spine shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="GenAI Spine",
        description="Unified GenAI service for the Spine ecosystem",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(models.router, prefix="/v1", tags=["models"])
    app.include_router(completions.router, prefix="/v1", tags=["completions"])
    app.include_router(chat.router, prefix="/v1", tags=["chat"])
    app.include_router(capabilities.router, prefix="/v1", tags=["capabilities"])
    app.include_router(prompts.router, prefix="/v1/prompts", tags=["prompts"])

    # New capability routers (P0 - Wire up existing code)
    app.include_router(rewrite.router, prefix="/v1", tags=["rewrite"])
    app.include_router(commit.router, prefix="/v1", tags=["commit"])
    app.include_router(execute.router, prefix="/v1", tags=["execute"])

    # Usage and cost tracking (P1)
    app.include_router(usage.router, prefix="/v1", tags=["usage"])

    return app
