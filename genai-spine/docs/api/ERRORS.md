# GenAI Spine Error Handling

**Status:** ✅ Active
**Last Updated:** 2026-01-31

---

## Error Response Format

All errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "model",
      "reason": "Model 'gpt-5' not found"
    },
    "request_id": "req_abc123xyz"
  }
}
```

---

## Error Codes

### Client Errors (4xx)

| HTTP | Code | Description | Retry? |
|------|------|-------------|--------|
| 400 | `VALIDATION_ERROR` | Invalid request body/params | No - fix request |
| 400 | `INVALID_PROMPT_VARIABLES` | Missing/wrong prompt variables | No - fix variables |
| 401 | `UNAUTHORIZED` | Missing or invalid API key | No - check credentials |
| 403 | `FORBIDDEN` | Valid key, insufficient scope | No - check permissions |
| 404 | `NOT_FOUND` | Resource doesn't exist | No |
| 404 | `PROMPT_NOT_FOUND` | Prompt slug not found | No |
| 404 | `SESSION_NOT_FOUND` | Chat session not found | No |
| 404 | `MODEL_NOT_FOUND` | Requested model unavailable | No - use different model |
| 409 | `CONFLICT` | Resource state conflict | Maybe - re-fetch first |
| 422 | `UNPROCESSABLE_ENTITY` | Semantically invalid | No - fix request |
| 429 | `RATE_LIMITED` | Too many requests | Yes - with backoff |

### Server Errors (5xx)

| HTTP | Code | Description | Retry? |
|------|------|-------------|--------|
| 500 | `INTERNAL_ERROR` | Unexpected server error | Yes - with backoff |
| 502 | `PROVIDER_ERROR` | Upstream LLM provider failed | Yes - maybe different model |
| 503 | `SERVICE_UNAVAILABLE` | Service temporarily down | Yes - with backoff |
| 504 | `PROVIDER_TIMEOUT` | LLM provider timed out | Yes - maybe smaller request |

---

## Provider-Specific Errors

When an LLM provider returns an error, we wrap it:

```json
{
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "OpenAI API error",
    "details": {
      "provider": "openai",
      "provider_code": "context_length_exceeded",
      "provider_message": "This model's maximum context length is 128000 tokens..."
    },
    "request_id": "req_abc123xyz"
  }
}
```

### Common Provider Errors

| Provider Error | GenAI Code | Recommended Action |
|----------------|------------|-------------------|
| `context_length_exceeded` | `PROVIDER_ERROR` | Reduce input size |
| `rate_limit_exceeded` | `RATE_LIMITED` | Backoff and retry |
| `invalid_api_key` | `PROVIDER_ERROR` | Check provider config |
| `model_not_found` | `MODEL_NOT_FOUND` | Use supported model |
| `content_filter` | `PROVIDER_ERROR` | Modify content |

---

## Retry Strategies

### Recommended Backoff

```python
import asyncio
from genai_spine_client import GenAIClient, RateLimitError, ProviderError

async def with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait = e.retry_after or (2 ** attempt)
            await asyncio.sleep(wait)
        except ProviderError as e:
            if not e.is_retryable or attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### SDK Built-in Retry

```python
client = GenAIClient(
    base_url="http://genai-spine:8100",
    max_retries=3,
    retry_on=[429, 502, 503, 504]
)
```

---

## Error Handling Examples

### Python SDK

```python
from genai_spine_client import (
    GenAIClient,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError
)

client = GenAIClient(base_url="http://genai-spine:8100")

try:
    result = await client.execute_prompt(
        slug="summarizer",
        variables={"text": content}
    )
except ValidationError as e:
    # Fix the request
    print(f"Invalid request: {e.message}")
    print(f"Field: {e.details.get('field')}")
except NotFoundError as e:
    # Prompt doesn't exist
    print(f"Prompt not found: {e.message}")
except RateLimitError as e:
    # Back off and retry
    print(f"Rate limited. Retry after {e.retry_after}s")
except ProviderError as e:
    # LLM provider issue
    print(f"Provider {e.provider} error: {e.provider_message}")
```

### TypeScript SDK

```typescript
import { GenAIClient, ValidationError, NotFoundError } from 'genai-spine-client';

const client = new GenAIClient({ baseUrl: 'http://genai-spine:8100' });

try {
  const result = await client.executePrompt({
    slug: 'summarizer',
    variables: { text: content }
  });
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Invalid request:', error.message);
  } else if (error instanceof NotFoundError) {
    console.error('Prompt not found');
  } else {
    throw error;
  }
}
```

---

## Request Tracing

Every response includes a request ID for debugging:

```http
HTTP/1.1 200 OK
X-Request-ID: req_abc123xyz
```

Include this ID when reporting issues:

```python
try:
    result = await client.complete(...)
except GenAIError as e:
    logger.error(f"GenAI error: {e.message}, request_id={e.request_id}")
```

---

## See Also

- [API_CONTRACT.md](API_CONTRACT.md) - Full API specification
- [AUTH.md](AUTH.md) - Authentication errors
- [API_TIERS.md](API_TIERS.md) - Endpoint stability tiers
