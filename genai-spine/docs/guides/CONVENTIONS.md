# Code Conventions

> Coding standards and style guide for GenAI Spine.

---

## Language & Runtime

- **Python 3.12+** — Use modern syntax
- **Type hints** — Required for all public APIs
- **Async-first** — All I/O operations should be async

---

## Formatting

### Tools

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/
```

### Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]  # Line length handled by formatter

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
```

---

## Naming Conventions

### Files

| Type | Convention | Example |
|------|------------|---------|
| Module | `snake_case.py` | `prompt_manager.py` |
| Test | `test_*.py` | `test_summarization.py` |
| Fixture | Descriptive | `sample_10k.txt` |

### Code

| Type | Convention | Example |
|------|------------|---------|
| Function | `snake_case` | `async def summarize_text()` |
| Class | `PascalCase` | `class PromptManager:` |
| Constant | `UPPER_SNAKE` | `DEFAULT_TEMPERATURE = 0.7` |
| Private | `_prefix` | `def _parse_response():` |
| Type var | `T`, `K`, `V` | `T = TypeVar("T")` |

### Variables

```python
# ✅ Good: Descriptive names
completion_response = await provider.complete(request)
input_token_count = response.usage.prompt_tokens

# ❌ Bad: Abbreviations, single letters
cr = await provider.complete(r)
itc = response.usage.prompt_tokens
```

---

## Import Organization

```python
# Standard library
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

# Third-party
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

# Local
from genai_spine.providers.base import CompletionRequest
from genai_spine.settings import Settings
```

Use `ruff` to auto-sort imports.

---

## Type Hints

### Required For

```python
# ✅ Function signatures
async def summarize_text(
    provider: LLMProvider,
    model: str,
    content: str,
    max_sentences: int = 3,
) -> dict[str, Any]:
    ...

# ✅ Class attributes
class PromptTemplate:
    name: str
    system_prompt: str
    variables: list[str]
```

### Optional For

```python
# Local variables with obvious types
response = await provider.complete(request)  # Type is clear
```

### Modern Syntax

```python
# ✅ Use built-in generics (3.9+)
def process(items: list[str]) -> dict[str, int]:
    ...

# ❌ Avoid typing module when possible
from typing import List, Dict
def process(items: List[str]) -> Dict[str, int]:
    ...

# ✅ Use | for unions (3.10+)
def get_model(name: str | None = None) -> str:
    ...

# ❌ Avoid Union
from typing import Union, Optional
def get_model(name: Optional[str] = None) -> str:
    ...
```

---

## Docstrings

### Google Style

```python
async def summarize_text(
    provider: LLMProvider,
    model: str,
    content: str,
    max_sentences: int = 3,
) -> dict[str, Any]:
    """Summarize text content using an LLM.

    Args:
        provider: LLM provider to use for completion.
        model: Model identifier (e.g., "llama3.2:latest").
        content: Text content to summarize.
        max_sentences: Maximum sentences in summary. Defaults to 3.

    Returns:
        Dict containing:
            - summary: The generated summary text
            - usage: Token usage and cost information

    Raises:
        RuntimeError: If the LLM provider fails.
        ValueError: If content is empty.

    Example:
        >>> result = await summarize_text(provider, "llama3.2", "Long text...")
        >>> print(result["summary"])
    """
```

### Module Docstrings

```python
"""Summarization capability for GenAI Spine.

This module provides text summarization using configurable LLM providers.
Supports various summarization modes including extractive and abstractive.

Typical usage:
    from genai_spine.capabilities.summarization import summarize_text

    result = await summarize_text(provider, model, content)
"""
```

---

## Error Handling

### Custom Exceptions

```python
# exceptions.py
class GenAISpineError(Exception):
    """Base exception for GenAI Spine."""
    pass

class ProviderError(GenAISpineError):
    """Error from LLM provider."""
    pass

class BudgetExceededError(GenAISpineError):
    """Cost budget exceeded."""
    pass
```

### Usage

```python
# ✅ Specific exceptions with context
if not response.success:
    raise ProviderError(f"Provider {provider_name} failed: {response.error}")

# ✅ Catch specific exceptions
try:
    result = await provider.complete(request)
except httpx.TimeoutException:
    raise ProviderError("Request timed out") from None

# ❌ Avoid bare except
try:
    ...
except:  # Bad!
    pass
```

---

## Async Patterns

### Always Await

```python
# ✅ Await async calls
response = await provider.complete(request)

# ❌ Don't forget await (creates coroutine object)
response = provider.complete(request)  # Bug!
```

### Concurrent Execution

```python
# ✅ Run independent operations concurrently
import asyncio

results = await asyncio.gather(
    provider1.complete(request1),
    provider2.complete(request2),
)

# ❌ Don't run sequentially when parallel is possible
result1 = await provider1.complete(request1)
result2 = await provider2.complete(request2)  # Wasted time
```

### Resource Cleanup

```python
# ✅ Use async context managers
async with httpx.AsyncClient() as client:
    response = await client.get(url)

# Or ensure cleanup
client = httpx.AsyncClient()
try:
    response = await client.get(url)
finally:
    await client.aclose()
```

---

## Logging

### Setup

```python
import logging

logger = logging.getLogger(__name__)
```

### Levels

| Level | Use For |
|-------|---------|
| `DEBUG` | Detailed diagnostics |
| `INFO` | Normal operations |
| `WARNING` | Recoverable issues |
| `ERROR` | Failures |

### Patterns

```python
# ✅ Use structured logging
logger.info("Summarization complete", extra={
    "model": model,
    "input_tokens": response.input_tokens,
    "output_tokens": response.output_tokens,
})

# ✅ Log exceptions with traceback
try:
    result = await risky_operation()
except Exception:
    logger.exception("Operation failed")
    raise

# ❌ Don't use print for logging
print(f"Processing {filename}")  # Bad!
```

---

## Configuration

### Use Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    openai_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="GENAI_",
        env_file=".env",
    )
```

### Access via Dependency Injection

```python
# ✅ Inject settings
def get_provider(settings: Settings = Depends(get_settings)):
    return OllamaProvider(base_url=settings.ollama_url)

# ❌ Don't read env vars directly in functions
def get_provider():
    url = os.environ.get("GENAI_OLLAMA_URL")  # Bad!
```

---

## Related Docs

- [TESTING.md](TESTING.md) — Testing standards
- [ARCHITECTURE_ALIGNMENT.md](ARCHITECTURE_ALIGNMENT.md) — Architecture rules
