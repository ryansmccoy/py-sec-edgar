# Documentation Best Practices in the Age of AI Coding Assistants

> How to write documentation that works well with VS Code Copilot, Claude, and other AI tools.

---

## Core Philosophy

### Code IS Documentation

In 2026, with AI assistants that can read and understand code, the balance has shifted:

| Traditional Approach | AI-Era Approach |
|---------------------|-----------------|
| Extensive markdown docs | Excellent docstrings + minimal markdown |
| Docs often outdated | Code is always current |
| Duplicate information | Single source of truth |
| Manual sync required | AI extracts from code |

**Rule of thumb:** If it can be a docstring, make it a docstring.

---

## What Goes Where

### ✅ In Code (Docstrings)

```python
async def summarize_text(
    provider: LLMProvider,
    model: str,
    content: str,
    max_sentences: int = 3,
    focus: str | None = None,
    output_format: str = "paragraph",
) -> dict[str, Any]:
    """Summarize text content using an LLM.

    This capability uses the configured provider to generate concise summaries.
    Supports multiple output formats and optional focus areas.

    Args:
        provider: LLM provider instance (Ollama, OpenAI, etc.)
        model: Model identifier (e.g., "llama3.2:latest", "gpt-4o-mini")
        content: Text to summarize (no length limit, chunked automatically)
        max_sentences: Maximum sentences in summary (default: 3)
        focus: Optional focus area (e.g., "financial metrics", "key dates")
        output_format: "paragraph" or "bullet_points"

    Returns:
        Dict containing:
        - summary: The generated summary text
        - key_points: List of key points (if bullet_points format)
        - word_count: Number of words in summary
        - compression_ratio: Original/summary length ratio
        - usage: Token counts and cost info

    Raises:
        RuntimeError: If the LLM request fails

    Example:
        >>> result = await summarize_text(
        ...     provider=ollama,
        ...     model="llama3.2:latest",
        ...     content="Long article text...",
        ...     max_sentences=3,
        ...     output_format="bullet_points"
        ... )
        >>> print(result["summary"])
        • Key point one
        • Key point two
        • Key point three

    Note:
        For financial content, consider using the financial-markets domain
        capabilities which include sector-specific terminology handling.
    """
```

### ✅ In Markdown Docs

- **Architecture decisions** — Why we chose X over Y
- **Capability matrices** — Overview of what exists
- **Integration guides** — How systems connect
- **Roadmaps** — What's planned vs. built
- **Diagrams** — ASCII art, mermaid charts

### ❌ Don't Duplicate

- Parameter descriptions (use docstrings)
- Function signatures (use docstrings)
- Error handling details (use docstrings)
- Usage examples that exist in tests

---

## Markdown Best Practices for AI

### 1. Use Consistent Headers

```markdown
# Feature Name

> One-line description

---

## Overview
## Configuration
## Usage
## API Reference
## Examples
```

AI tools can navigate consistent structures.

### 2. Use Tables for Structured Data

```markdown
| Capability | Tier | Status | Module |
|------------|------|--------|--------|
| Summarization | 1 | ✅ | `capabilities/summarization.py` |
| Entity Extraction | 1 | ✅ | `capabilities/extraction.py` |
```

Tables are machine-readable and scannable.

### 3. Use Code Blocks with Language Tags

```python
# Good - language specified
response = await client.post("/v1/summarize", json={...})
```

```
# Bad - no language tag
response = await client.post("/v1/summarize", json={...})
```

### 4. Link to Source Files

```markdown
See [capabilities/summarization.py](../src/genai_spine/capabilities/summarization.py)
```

AI can follow links to get more context.

### 5. Use Status Indicators

| Symbol | Meaning |
|--------|---------|
| ✅ | Complete |
| 🟡 | In Progress |
| 🔴 | Not Started |
| ⚠️ | Deprecated |

---

## File Organization

### Small, Focused Files

```
# Bad
docs/
└── EVERYTHING.md  # 2000 lines

# Good
docs/
├── capabilities/
│   ├── TIER_1_BASIC.md       # 100 lines
│   ├── TIER_2_INTERMEDIATE.md # 100 lines
│   └── TIER_3_ADVANCED.md     # 100 lines
```

**Why?** AI assistants can load focused files into context more effectively.

### Predictable Naming

```
FEATURE_NAME.md           # Feature documentation
FEATURE_NAME_GUIDE.md     # How-to guide
FEATURE_NAME_API.md       # API reference (if not in docstrings)
```

---

## Docstring Standards

### Module Level

```python
"""Summarization capability for GenAI Spine.

This module provides text summarization using LLM providers.
Supports multiple output formats and configurable compression.

Capabilities:
    - summarize_text: Summarize any text content
    - summarize_document: Summarize with document structure awareness
    - summarize_batch: Batch summarization for multiple texts

Configuration:
    Environment variables:
    - GENAI_SUMMARIZATION_MAX_TOKENS: Default max tokens (default: 500)
    - GENAI_SUMMARIZATION_TEMPERATURE: Default temperature (default: 0.3)

Example:
    >>> from genai_spine.capabilities import summarization
    >>> result = await summarization.summarize_text(provider, model, content)
"""
```

### Class Level

```python
class PromptManager:
    """Manages prompt templates with versioning and rendering.

    The PromptManager handles CRUD operations for prompts, maintains
    version history, and renders templates with variable substitution.

    Attributes:
        storage: Storage backend (SQLite, PostgreSQL)
        cache: Optional cache for rendered prompts

    Thread Safety:
        All public methods are async and thread-safe.

    Example:
        >>> manager = PromptManager(storage=sqlite_storage)
        >>> prompt = await manager.create(name="summarize", template="...")
        >>> rendered = await manager.render(prompt.id, {"content": text})
    """
```

### Function Level

Follow Google-style docstrings (shown earlier).

---

## When to Update Docs

### Must Update

- [ ] New capability added → Update capability tier doc
- [ ] New provider added → Update PROVIDERS.md
- [ ] API endpoint changed → Update relevant integration doc
- [ ] Breaking change → Update migration guide

### Can Skip

- Bug fixes (unless behavior change)
- Internal refactoring
- Test additions
- Dependency updates

---

## AI-Friendly Patterns

### Pattern: Capability Registry

```python
# In code
CAPABILITIES = {
    "summarize": {
        "tier": 1,
        "function": summarize_text,
        "description": "Summarize text content",
        "input_schema": SummarizeRequest,
        "output_schema": SummarizeResponse,
    },
    # ... more capabilities
}
```

AI can read this registry to understand available capabilities.

### Pattern: Feature Flags

```python
class Features(BaseSettings):
    """Feature flags for GenAI Spine.

    Each flag controls a capability or behavior.
    Flags are read from environment with GENAI_ prefix.
    """
    enable_rag: bool = False  # RAG retrieval
    enable_streaming: bool = True  # SSE streaming
    enable_cost_tracking: bool = True  # Track token costs
    enable_caching: bool = False  # Response caching
```

### Pattern: Self-Documenting Enums

```python
class CapabilityTier(IntEnum):
    """Capability maturity tiers.

    Tiers indicate implementation priority and complexity:
    - BASIC: Core functionality, must-have for MVP
    - INTERMEDIATE: Enhanced features, common use cases
    - ADVANCED: Complex features, power users
    - MINDBLOWING: Future vision, experimental
    """
    BASIC = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    MINDBLOWING = 4
```

---

## Anti-Patterns

### ❌ Outdated Examples

```markdown
# Don't do this
```python
# This example may be outdated
result = old_function_name(...)
```
```

Instead, reference tests which are always current:

```markdown
See [tests/test_summarization.py](../tests/test_summarization.py) for working examples.
```

### ❌ Duplicating Type Hints

```markdown
# Don't do this
## Parameters
- content (str): The text to summarize
- max_sentences (int): Maximum sentences
```

The function signature already has this info.

### ❌ Huge Monolithic Docs

Split into focused files. AI context windows are large but not infinite.

---

## Tooling

### Generate Docs from Code

```bash
# Future: auto-generate capability matrix from code
python scripts/generate_capability_docs.py
```

### Validate Doc Links

```bash
# Check for broken links
markdown-link-check docs/**/*.md
```

### Lint Docstrings

```bash
# Ensure docstrings follow standards
pydocstyle src/
```

---

## Summary

| Principle | Action |
|-----------|--------|
| Code is truth | Prioritize docstrings |
| Small files | Split by feature |
| Machine readable | Tables, code blocks, consistent structure |
| Link don't copy | Reference source files and tests |
| Update atomically | Change docs with code in same commit |

**Remember:** The best documentation is code that doesn't need documentation.
