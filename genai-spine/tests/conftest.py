"""Pytest configuration and shared fixtures for GenAI Spine tests."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, AsyncGenerator, Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from genai_spine.api.app import create_app
from genai_spine.providers.base import CompletionRequest, CompletionResponse, LLMProvider
from genai_spine.providers.registry import ProviderRegistry
from genai_spine.settings import Settings

if TYPE_CHECKING:
    from fastapi import FastAPI


# =============================================================================
# Event Loop
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Settings
# =============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Test settings with in-memory database."""
    return Settings(
        api_host="127.0.0.1",
        api_port=8100,
        default_provider="mock",
        default_model="mock-model",
        database_url="sqlite+aiosqlite:///:memory:",
        debug=True,
    )


# =============================================================================
# Mock Provider
# =============================================================================


class MockLLMProvider(LLMProvider):
    """Mock provider for testing."""

    name = "mock"

    def __init__(self, responses: dict[str, str] | None = None):
        """Initialize with optional canned responses.

        Args:
            responses: Dict mapping prompt patterns to responses.
        """
        self.responses = responses or {}
        self.calls: list[CompletionRequest] = []

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Return mock completion."""
        self.calls.append(request)

        # Check for pattern match
        user_content = request.messages[-1].get("content", "") if request.messages else ""
        response_text = "Mock response"

        for pattern, response in self.responses.items():
            if pattern.lower() in user_content.lower():
                response_text = response
                break

        return CompletionResponse(
            content=response_text,
            provider=self.name,
            model=request.model or "mock-model",
            input_tokens=len(user_content.split()),
            output_tokens=len(response_text.split()),
            success=True,
        )

    async def list_models(self) -> list[str]:
        """Return mock models."""
        return ["mock-model", "mock-model-large"]

    async def health_check(self) -> bool:
        """Always healthy."""
        return True


@pytest.fixture
def mock_provider() -> MockLLMProvider:
    """Create mock provider with default responses."""
    return MockLLMProvider(
        responses={
            "summarize": "This is a mock summary.",
            "extract": '{"entities": []}',
            "classify": '{"category": "general"}',
            "rewrite": "This is the rewritten, cleaned version.",
            "title": "Mock Generated Title",
        }
    )


@pytest.fixture
def mock_registry(mock_provider: MockLLMProvider) -> ProviderRegistry:
    """Create registry with mock provider."""
    registry = ProviderRegistry()
    registry.register("mock", mock_provider)
    return registry


# =============================================================================
# Application
# =============================================================================


@pytest.fixture
async def app(
    test_settings: Settings, mock_provider: MockLLMProvider
) -> AsyncGenerator[FastAPI, None]:
    """Create test application with initialized storage."""
    from genai_spine.api import deps as deps_module
    from genai_spine.storage import create_backend, BackendType
    from genai_spine.providers.registry import ProviderRegistry, get_registry

    # Create mock registry with mock provider
    mock_registry = ProviderRegistry()
    mock_registry._initialized = True  # Skip auto-initialization
    mock_registry.register("mock", mock_provider)
    mock_registry.register("ollama", mock_provider)  # In case tests use default

    # Create and initialize storage backend
    backend = create_backend(BackendType.MEMORY)
    await backend.initialize()

    # Set the global backend in deps module
    original_backend = deps_module._storage_backend
    deps_module._storage_backend = backend

    # Create app without settings override - we'll override dependencies instead
    application = create_app()

    # Override dependencies using FastAPI's mechanism
    from genai_spine.settings import get_settings

    async def override_get_unit_of_work():
        async with backend.unit_of_work() as uow:
            yield uow

    def override_get_settings():
        return test_settings

    def override_get_registry():
        return mock_registry

    application.dependency_overrides[deps_module.get_unit_of_work] = override_get_unit_of_work
    application.dependency_overrides[get_settings] = override_get_settings
    application.dependency_overrides[get_registry] = override_get_registry

    yield application

    # Cleanup
    application.dependency_overrides.clear()
    deps_module._storage_backend = original_backend
    await backend.close()


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# =============================================================================
# Sample Data
# =============================================================================


@pytest.fixture
def sample_message() -> str:
    """Sample user message for testing."""
    return """
    ok so like i was thinking about the project and we should probaly add some
    tests for the new featuers we added yesterday. also the documentaiton needs
    updating becuase the api changed and i dont want users to get confused when
    they try to use it.
    """


@pytest.fixture
def sample_article() -> str:
    """Sample article for testing."""
    return """
    Apple Inc. announced record quarterly revenue of $123 billion for Q4 2025,
    driven by strong iPhone 16 sales and growth in its services segment. CEO
    Tim Cook highlighted the company's commitment to AI innovation, with the
    Apple Intelligence features driving significant user engagement.

    The company's stock rose 3% in after-hours trading following the announcement.
    Analysts from Goldman Sachs and Morgan Stanley maintained their buy ratings,
    with price targets of $250 and $260 respectively.
    """


@pytest.fixture
def sample_prompt_create() -> dict:
    """Sample prompt creation data."""
    return {
        "name": "Test Summarizer",
        "slug": f"test-summarizer-{uuid4().hex[:8]}",
        "description": "Test prompt for summarization",
        "system_prompt": "You are a helpful summarizer.",
        "user_prompt_template": "Summarize this in {{max_sentences}} sentences:\n\n{{content}}",
        "category": "summarization",
        "tags": ["test", "summary"],
        "variables": [
            {"name": "content", "type": "string", "required": True},
            {"name": "max_sentences", "type": "integer", "default": 3},
        ],
    }


# =============================================================================
# Markers
# =============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Fast unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may require services)")
    config.addinivalue_line("markers", "slow: Slow tests (> 10 seconds)")
    config.addinivalue_line("markers", "ollama: Tests requiring Ollama service")
