# GenAI Spine Consumer Quickstart

**Status:** 📋 Proposal
**Last Updated:** 2026-01-31

---

## Who Is This For?

You're building a feature in:
- **capture-spine** - Chat, LLM transforms, content enrichment
- **feedspine** - SEC filing summarization, extraction
- **entityspine** - Entity resolution, data enrichment
- **py-sec-edgar** - Document analysis, data extraction

You need LLM capabilities. **Use GenAI Spine.**

---

## Quick Start (5 minutes)

### 1. Install the SDK

```bash
pip install genai-spine-client
```

### 2. Initialize the Client

```python
from genai_spine_client import GenAIClient

# Development
client = GenAIClient(base_url="http://localhost:8100")

# Production (with API key)
client = GenAIClient(
    base_url="http://genai-spine:8100",
    api_key="gs_live_xxxxxxxxxxxx"
)
```

### 3. Make Your First Call

```python
# Simple completion
response = await client.complete(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4o-mini"
)
print(response.content)

# Execute a saved prompt
result = await client.execute_prompt(
    slug="summarizer",
    variables={"text": "Long document text here..."}
)
print(result.content)
```

---

## Common Use Cases by App

### capture-spine: Chat Feature

```python
# Create a chat session
session = await client.sessions.create(
    model="gpt-4o",
    system_prompt="You are a helpful assistant.",
    metadata={"user_id": "user_123", "feature": "chat"}
)

# Send messages
response = await client.sessions.send_message(
    session_id=session.id,
    content="What's the weather like?",
    metadata={"source": "web_ui"}
)

# History is maintained automatically
response2 = await client.sessions.send_message(
    session_id=session.id,
    content="What about tomorrow?"  # Context preserved
)
```

### capture-spine: Content Transform

```python
# Use a transform prompt
result = await client.execute_prompt(
    slug="content-rewriter",
    variables={
        "content": raw_message,
        "mode": "professional",
        "max_length": 500
    }
)
cleaned = result.content
```

### feedspine: Filing Summarization

```python
# Summarize an SEC filing
result = await client.execute_prompt(
    slug="summarizer",
    variables={
        "text": filing_text,
        "format": "bullets",
        "max_points": 10
    },
    model="claude-3-sonnet"  # Override default model
)
summary = result.content
```

### entityspine: Entity Extraction

```python
# Extract structured entities
result = await client.execute_prompt(
    slug="entity-extractor",
    variables={
        "text": document_text,
        "entity_types": ["person", "organization", "location"]
    },
    response_format={"type": "json_object"}
)
entities = json.loads(result.content)
```

---

## Passing Metadata Safely

Always include metadata for:
- **Audit trail** - Who requested what
- **Cost allocation** - Charge back to features
- **Debugging** - Trace issues across services

```python
# Good: Include useful metadata
result = await client.execute_prompt(
    slug="summarizer",
    variables={"text": content},
    metadata={
        "app": "capture-spine",
        "feature": "chat",
        "user_id": "user_123",      # For audit
        "conversation_id": "conv_abc",  # For tracing
        "request_source": "api"     # web_ui, api, batch, etc.
    }
)

# Access metadata in response
print(f"Request ID: {result.request_id}")
print(f"Model used: {result.model}")
print(f"Tokens: {result.usage.total_tokens}")
print(f"Cost: ${result.usage.cost:.4f}")
```

### What NOT to Put in Metadata

```python
# BAD: Don't include sensitive data
metadata={
    "api_key": "sk-xxx",        # ❌ Never
    "password": "secret",       # ❌ Never
    "ssn": "123-45-6789"        # ❌ Never
}

# GOOD: Include identifiers, not values
metadata={
    "user_id": "user_123",      # ✅ ID, not PII
    "document_id": "doc_456"    # ✅ Reference, not content
}
```

---

## Error Handling & Retry

### Basic Error Handling

```python
from genai_spine_client import (
    GenAIError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError
)

try:
    result = await client.execute_prompt(
        slug="summarizer",
        variables={"text": content}
    )
except ValidationError as e:
    # Your request is wrong - fix it
    logger.error(f"Bad request: {e.message}, field: {e.details.get('field')}")
    raise

except NotFoundError as e:
    # Prompt doesn't exist
    logger.error(f"Prompt '{slug}' not found")
    # Fallback to raw completion?
    result = await client.complete(messages=[...])

except RateLimitError as e:
    # Too many requests - back off
    logger.warning(f"Rate limited, retry after {e.retry_after}s")
    await asyncio.sleep(e.retry_after)
    result = await client.execute_prompt(...)  # Retry

except ProviderError as e:
    # LLM provider failed
    if e.is_retryable:
        # Transient error - retry with backoff
        await asyncio.sleep(2)
        result = await client.execute_prompt(...)
    else:
        # Permanent error (content filter, etc.)
        logger.error(f"Provider error: {e.provider_message}")
        raise
```

### Recommended Retry Pattern

```python
from genai_spine_client import GenAIClient

# SDK handles retries automatically
client = GenAIClient(
    base_url="http://genai-spine:8100",
    max_retries=3,
    retry_delay=1.0,  # Initial delay
    retry_backoff=2.0  # Exponential backoff multiplier
)

# Or use explicit retry logic
async def with_retry(coro_func, max_attempts=3):
    last_error = None
    for attempt in range(max_attempts):
        try:
            return await coro_func()
        except RateLimitError as e:
            last_error = e
            await asyncio.sleep(e.retry_after or (2 ** attempt))
        except ProviderError as e:
            if not e.is_retryable:
                raise
            last_error = e
            await asyncio.sleep(2 ** attempt)
    raise last_error
```

---

## Multi-Model Review (Advanced)

For high-stakes decisions, use multiple models:

```python
# Step 1: Primary analysis with Claude
primary = await client.execute_prompt(
    slug="filing-analyzer",
    variables={"text": filing_text},
    model="claude-3-opus",
    metadata={"review_stage": "primary"}
)

# Step 2: Review with GPT-4
review = await client.execute_prompt(
    slug="analysis-reviewer",
    variables={
        "original_text": filing_text,
        "analysis": primary.content
    },
    model="gpt-4o",
    metadata={"review_stage": "secondary"}
)

# Step 3: Handle disagreements
if review.metadata.get("confidence") < 0.8:
    # Human review needed
    flag_for_review(filing_id, primary, review)
```

See [Multi-Model Review Workflow](../features/MULTI_MODEL_REVIEW_WORKFLOW.md) for full details.

---

## Performance Tips

### 1. Reuse the Client

```python
# GOOD: Create once, reuse
client = GenAIClient(base_url="http://genai-spine:8100")

async def process_item(item):
    return await client.execute_prompt(...)

# BAD: Creating client per request
async def process_item_bad(item):
    client = GenAIClient(...)  # ❌ Wasteful
    return await client.execute_prompt(...)
```

### 2. Use Appropriate Models

```python
# Quick tasks: Use fast/cheap models
result = await client.execute_prompt(
    slug="classifier",
    variables={"text": short_text},
    model="gpt-4o-mini"  # Fast, cheap
)

# Complex tasks: Use capable models
result = await client.execute_prompt(
    slug="legal-analyzer",
    variables={"text": contract_text},
    model="claude-3-opus"  # Expensive but thorough
)
```

### 3. Batch When Possible

```python
# If processing many items, consider streaming or batching
# (Future feature - not yet implemented)
```

---

## Debugging

### Check What's Available

```python
# List available models
models = await client.models.list()
for model in models:
    print(f"{model.id}: {model.provider} (${model.cost_per_1k_tokens})")

# List available prompts
prompts = await client.prompts.list()
for prompt in prompts:
    print(f"{prompt.slug}: {prompt.description}")
```

### Trace Requests

```python
# Enable debug logging
import logging
logging.getLogger("genai_spine_client").setLevel(logging.DEBUG)

# Every response has a request_id
result = await client.execute_prompt(...)
print(f"Request ID: {result.request_id}")  # Use this when reporting issues
```

---

## Checklist: Before You Ship

- [ ] Using SDK client, not raw HTTP
- [ ] Proper error handling for all GenAI calls
- [ ] Metadata includes app, feature, user context
- [ ] Retry logic for transient failures
- [ ] Appropriate model selection for task complexity
- [ ] No sensitive data in metadata
- [ ] Logging includes request_id for tracing

---

## See Also

- [API_CONTRACT.md](../api/API_CONTRACT.md) - Full API specification
- [API_TIERS.md](../api/API_TIERS.md) - Tier A vs Tier B endpoints
- [ERRORS.md](../api/ERRORS.md) - Error codes and handling
- [CAPTURE_SPINE_INTEGRATION_ANALYSIS.md](CAPTURE_SPINE_INTEGRATION_ANALYSIS.md) - Migration details
