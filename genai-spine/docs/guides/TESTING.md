# Testing Guide

> Testing standards and patterns for GenAI Spine.

---

## Testing Philosophy

1. **Test behavior, not implementation** — Mock at boundaries, not internals
2. **Fast feedback loop** — Unit tests < 1 second, integration < 10 seconds
3. **Realistic fixtures** — Use real LLM responses captured as fixtures
4. **Coverage targets** — 80% for core, 60% for capabilities

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Fast, isolated tests
│   ├── test_providers/
│   ├── test_capabilities/
│   └── test_core/
├── integration/             # Tests with real services
│   ├── test_api.py
│   └── test_providers_live.py
├── fixtures/                # Captured responses
│   ├── ollama_responses/
│   └── openai_responses/
└── e2e/                     # End-to-end scenarios
    └── test_workflows.py
```

---

## Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (requires services)
pytest tests/integration/ -v --run-integration

# With coverage
pytest --cov=genai_spine --cov-report=html

# Single file
pytest tests/unit/test_capabilities/test_summarization.py -v
```

---

## Writing Tests

### Unit Test Pattern

```python
# tests/unit/test_capabilities/test_summarization.py

import pytest
from genai_spine.capabilities.summarization import summarize_text


@pytest.fixture
def mock_provider(mocker):
    """Mock LLM provider with canned response."""
    provider = mocker.Mock()
    provider.complete = mocker.AsyncMock(return_value=CompletionResponse(
        content="This is a summary.",
        model="test-model",
        success=True,
        input_tokens=100,
        output_tokens=20,
        cost_usd=0.001,
    ))
    return provider


@pytest.mark.asyncio
async def test_summarize_text_basic(mock_provider):
    """Test basic summarization returns expected structure."""
    result = await summarize_text(
        provider=mock_provider,
        model="test-model",
        content="Long text to summarize...",
        max_sentences=3,
    )

    assert "summary" in result
    assert "usage" in result
    assert result["usage"]["input_tokens"] == 100


@pytest.mark.asyncio
async def test_summarize_text_handles_failure(mock_provider):
    """Test summarization handles provider failure gracefully."""
    mock_provider.complete.return_value = CompletionResponse(
        content="",
        model="test-model",
        success=False,
        error="Rate limited",
    )

    with pytest.raises(RuntimeError, match="Rate limited"):
        await summarize_text(
            provider=mock_provider,
            model="test-model",
            content="...",
        )
```

### Integration Test Pattern

```python
# tests/integration/test_api.py

import pytest
from httpx import AsyncClient
from genai_spine.api.app import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health endpoint returns healthy."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_summarize_endpoint(client):
    """Test summarization endpoint with real provider."""
    response = await client.post("/v1/summarize", json={
        "content": "This is a test document with multiple sentences. It has information. We want a summary.",
        "max_sentences": 2,
    })
    assert response.status_code == 200
    assert "summary" in response.json()
```

### Fixture Capture Pattern

```python
# tests/fixtures/capture_fixtures.py

"""Run manually to capture real LLM responses as fixtures."""

import json
from pathlib import Path


async def capture_ollama_response():
    """Capture real Ollama response for fixture."""
    provider = OllamaProvider(base_url="http://localhost:11434")

    response = await provider.complete(CompletionRequest(
        model="llama3.2:latest",
        messages=[{"role": "user", "content": "Summarize: The quick brown fox."}],
    ))

    fixture_path = Path("tests/fixtures/ollama_responses/summarize_basic.json")
    fixture_path.write_text(json.dumps({
        "content": response.content,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }, indent=2))
```

---

## Test Markers

```python
# pytest.ini or pyproject.toml

[tool.pytest.ini_options]
markers = [
    "unit: Fast unit tests",
    "integration: Tests requiring external services",
    "slow: Tests that take > 10 seconds",
    "ollama: Tests requiring Ollama",
    "openai: Tests requiring OpenAI API key",
]
```

Usage:
```bash
# Skip slow tests
pytest -m "not slow"

# Only Ollama tests
pytest -m "ollama"
```

---

## Mocking Guidelines

### ✅ Mock at Boundaries

```python
# Good: Mock the provider interface
mock_provider.complete.return_value = ...
```

### ❌ Don't Mock Internals

```python
# Bad: Mocking internal implementation details
mocker.patch("genai_spine.capabilities.summarization._parse_response")
```

### ✅ Use Fixtures for Complex Data

```python
@pytest.fixture
def sample_10k_content():
    """Load sample 10-K content from fixture."""
    return Path("tests/fixtures/sample_10k.txt").read_text()
```

---

## Coverage Requirements

| Module | Target | Rationale |
|--------|--------|-----------|
| `providers/` | 80% | Core reliability |
| `capabilities/` | 70% | Business logic |
| `api/routers/` | 60% | Integration tested |
| `storage/` | 80% | Data integrity |
| `core/` | 80% | Infrastructure |

---

## CI Integration

```yaml
# .github/workflows/test.yml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: pip install -e ".[dev]"
    - name: Run unit tests
      run: pytest tests/unit/ --cov=genai_spine --cov-fail-under=70
```

---

## Related Docs

- [CONVENTIONS.md](CONVENTIONS.md) — Code conventions
- [ARCHITECTURE_ALIGNMENT.md](ARCHITECTURE_ALIGNMENT.md) — Architecture rules
