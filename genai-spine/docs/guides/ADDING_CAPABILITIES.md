# Adding New Capabilities

> Guide for implementing new AI capabilities in GenAI Spine.

---

## Overview

A capability is a high-level AI operation like "summarize" or "extract entities."
Capabilities abstract the complexity of prompt engineering from API consumers.

---

## Capability Structure

```
capabilities/
├── __init__.py
├── summarization.py    # One file per capability
├── extraction.py
├── classification.py
└── your_new_capability.py
```

---

## Step-by-Step Guide

### 1. Create Capability File

```python
# capabilities/sentiment.py

"""Sentiment analysis capability."""

from __future__ import annotations

import logging
from typing import Any

from genai_spine.providers.base import CompletionRequest, LLMProvider

logger = logging.getLogger(__name__)


# System prompt - defines the AI's role
SENTIMENT_SYSTEM_PROMPT = """You are an expert at sentiment analysis.
Analyze text for emotional tone and provide accurate sentiment scores.

Guidelines:
- Consider context and nuance
- Distinguish between positive, negative, and neutral
- Provide confidence scores
- Handle sarcasm and irony carefully
"""

# User prompt template - Jinja2 syntax
SENTIMENT_USER_TEMPLATE = """Analyze the sentiment of the following text.
{granularity_instruction}

Return as JSON:
{{
    "sentiment": "positive" | "negative" | "neutral",
    "score": 0.0 to 1.0,
    "confidence": 0.0 to 1.0
}}

Text:
{content}

Analysis (JSON):"""
```

### 2. Implement Core Function

```python
async def analyze_sentiment(
    provider: LLMProvider,
    model: str,
    content: str,
    granularity: str = "document",
) -> dict[str, Any]:
    """Analyze sentiment of text content.

    Args:
        provider: LLM provider to use
        model: Model identifier
        content: Text to analyze
        granularity: "document", "sentence", or "aspect"

    Returns:
        Dict containing sentiment label, score, confidence

    Raises:
        RuntimeError: If analysis fails
    """
    granularity_instruction = ""
    if granularity == "sentence":
        granularity_instruction = "Analyze each sentence separately."
    elif granularity == "aspect":
        granularity_instruction = "Identify aspects and sentiment for each."

    user_prompt = SENTIMENT_USER_TEMPLATE.format(
        granularity_instruction=granularity_instruction,
        content=content,
    )

    request = CompletionRequest(
        messages=[
            {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.1,  # Low for consistent analysis
        output_schema={"type": "object"},  # Request JSON
    )

    response = await provider.complete(request)

    if not response.success:
        raise RuntimeError(f"Sentiment analysis failed: {response.error}")

    # Parse response
    result = _parse_sentiment_response(response.content)

    return {
        "sentiment": result["sentiment"],
        "score": result["score"],
        "confidence": result["confidence"],
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": float(response.cost_usd),
        }
    }


def _parse_sentiment_response(content: str) -> dict:
    """Parse LLM response into structured sentiment data."""
    import json

    # Handle markdown code blocks
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        # Fallback parsing
        return {"sentiment": "neutral", "score": 0.5, "confidence": 0.5}
```

### 3. Add API Endpoint

```python
# api/routers/capabilities.py

from genai_spine.capabilities.sentiment import analyze_sentiment

# Add to existing router or create new one

class SentimentRequest(BaseModel):
    content: str
    model: str | None = None
    granularity: str = "document"


class SentimentResponse(BaseModel):
    sentiment: str
    score: float
    confidence: float
    usage: dict


@router.post("/analyze/sentiment", response_model=SentimentResponse)
async def sentiment_endpoint(
    request: SentimentRequest,
    provider: LLMProvider = Depends(get_provider),
    settings: Settings = Depends(get_settings),
):
    """Analyze sentiment of text."""
    result = await analyze_sentiment(
        provider=provider,
        model=request.model or settings.default_model,
        content=request.content,
        granularity=request.granularity,
    )
    return SentimentResponse(**result)
```

### 4. Register Endpoint

```python
# api/app.py

from genai_spine.api.routers import capabilities

app.include_router(capabilities.router, prefix="/v1", tags=["capabilities"])
```

### 5. Add Prompt Template (Optional)

For user-customizable prompts:

```python
# When capability initializes, create default prompt
async def init_sentiment_prompt():
    """Initialize default sentiment analysis prompt."""
    await prompt_manager.create_if_not_exists(
        slug="analyze-sentiment",
        name="Analyze Sentiment",
        category="analysis",
        system_prompt=SENTIMENT_SYSTEM_PROMPT,
        user_prompt_template=SENTIMENT_USER_TEMPLATE,
        variables=[
            {"name": "content", "type": "string", "required": True},
            {"name": "granularity_instruction", "type": "string", "default": ""},
        ],
        is_system=True,
    )
```

### 6. Add Tests

```python
# tests/test_capabilities/test_sentiment.py

import pytest
from genai_spine.capabilities.sentiment import analyze_sentiment


@pytest.mark.asyncio
async def test_analyze_sentiment_positive(mock_provider):
    result = await analyze_sentiment(
        provider=mock_provider,
        model="test-model",
        content="This product is amazing! I love it!",
    )

    assert result["sentiment"] in ["positive", "negative", "neutral"]
    assert 0 <= result["score"] <= 1
    assert 0 <= result["confidence"] <= 1
    assert "usage" in result


@pytest.mark.asyncio
async def test_analyze_sentiment_with_granularity(mock_provider):
    result = await analyze_sentiment(
        provider=mock_provider,
        model="test-model",
        content="The food was great but the service was slow.",
        granularity="aspect",
    )

    assert result is not None
```

### 7. Update Documentation

Add to [capabilities/README.md](../capabilities/README.md):

```markdown
| Sentiment Analysis | 2 | ✅ | `capabilities/sentiment.py` |
```

---

## Capability Best Practices

### 1. Single Responsibility

Each capability does ONE thing well:
- ✅ `summarize_text` — summarizes text
- ❌ `process_document` — summarizes, extracts, classifies

### 2. Configurable Prompts

Use templates with variables:
```python
TEMPLATE = """Summarize in {max_sentences} sentences:
{content}"""
```

### 3. Low Temperature for Extraction

```python
# For deterministic outputs (extraction, analysis)
temperature=0.1

# For creative outputs (writing, brainstorming)
temperature=0.7
```

### 4. Structured Output

Request JSON mode for parseable results:
```python
request = CompletionRequest(
    # ...
    output_schema={"type": "object"}
)
```

### 5. Graceful Parsing

Handle malformed LLM responses:
```python
def _parse_response(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return _fallback_parse(content)
```

### 6. Include Usage Metadata

Always return token counts and costs:
```python
return {
    "result": ...,
    "usage": {
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "cost_usd": float(response.cost_usd),
    }
}
```

---

## Domain-Specific Capabilities

For domain capabilities, place in domain folder:

```
domains/
└── financial_markets/
    └── capabilities/
        ├── earnings_analysis.py
        └── risk_extraction.py
```

And extend core prompts:

```python
# Override system prompt for domain
FINANCIAL_SENTIMENT_SYSTEM_PROMPT = """You are a financial analyst...
"""
```

---

## Related Docs

- [../capabilities/](../capabilities/) — Capability tier docs
- [../core/PROMPT_MANAGEMENT.md](../core/PROMPT_MANAGEMENT.md) — Prompt templates
- [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md) — Adding LLM providers
