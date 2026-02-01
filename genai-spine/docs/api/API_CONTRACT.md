# GenAI Spine API Contract

**Status:** Proposal
**Created:** 2026-01-31
**Version:** Draft 1.0

This document defines the API contract for GenAI Spine - designed to be **domain-agnostic** and reusable across all ecosystem applications.

---

## Design Philosophy

### 1. No Domain Logic in GenAI Spine

GenAI Spine is a **pure LLM service**. It knows about:
- Models, providers, and their capabilities
- Prompts, templates, and variable substitution
- Chat sessions and message history
- Cost tracking and usage metrics

It does **NOT** know about:
- SEC filings, articles, or financial entities
- Chat message "enrichment" semantics
- Work sessions or commit generation business logic
- Feed item classification categories

### 2. Parameterization Over Specialization

Instead of specialized endpoints, GenAI Spine provides generic building blocks:

```
❌ POST /v1/enrich-message           # Too specific
✅ POST /v1/execute-prompt           # Generic: pass prompt_slug="message-enrichment"

❌ POST /v1/summarize-article        # Too specific
✅ POST /v1/completions              # Generic: client sends summarization prompt

❌ POST /v1/classify-feed            # Too specific
✅ POST /v1/execute-prompt           # Generic: pass prompt_slug="content-classifier"
```

### 3. Consumer Owns Domain Context

```python
# capture-spine (consumer) knows the domain
async def enrich_message(message: ChatMessage) -> str:
    # Domain logic: choose mode based on message characteristics
    mode = "format" if message.has_code_blocks else "clean"

    # Call GenAI with domain context
    result = await genai.execute_prompt(
        slug="content-rewriter",
        variables={
            "content": message.content,
            "mode": mode,
            "preserve_code": True,
        }
    )
    return result.output
```

---

## API Specification

### Base URL

```
Production:  https://genai.spine.local/v1
Development: http://localhost:8100/v1
```

### Authentication

```http
Authorization: Bearer <token>
X-Request-ID: <ulid>  # Optional, for tracing
```

---

## Core Endpoints

### 1. Completions (Generic LLM Calls)

The fundamental building block. Any app can call this for any purpose.

```http
POST /v1/completions
Content-Type: application/json

{
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarize this text: ..."}
    ],
    "model": "gpt-4o",              // Required
    "provider": "openai",           // Optional, inferred from model
    "temperature": 0.7,             // Optional, default 0.7
    "max_tokens": 1000,             // Optional
    "response_format": "text"       // Optional: "text" | "json"
}
```

**Response:**
```json
{
    "id": "comp_01H...",
    "content": "Here is a summary...",
    "model": "gpt-4o",
    "provider": "openai",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 75,
        "total_tokens": 225
    },
    "cost_usd": 0.003375,
    "latency_ms": 1234
}
```

---

### 2. Execute Prompt (Template-Based)

Execute a saved prompt template with variable substitution.

```http
POST /v1/execute-prompt
Content-Type: application/json

{
    "prompt_id": "01H...",          // Either prompt_id
    "prompt_slug": "content-rewriter", // Or prompt_slug
    "variables": {                  // Template variables
        "content": "The quick brown fox...",
        "mode": "clean",
        "max_length": 500
    },
    "model": "gpt-4o-mini",         // Optional override
    "temperature": 0.5              // Optional override
}
```

**Response:**
```json
{
    "id": "exec_01H...",
    "prompt_id": "01H...",
    "prompt_version": 3,
    "output": "The swift brown fox...",
    "usage": {
        "input_tokens": 200,
        "output_tokens": 150
    },
    "cost_usd": 0.00045,
    "latency_ms": 890
}
```

---

### 3. Chat Sessions

Full conversational chat with persistence (VS Code Copilot style).

#### Create Session
```http
POST /v1/sessions
Content-Type: application/json

{
    "title": "Code Review Help",    // Optional
    "model": "claude-3-sonnet",     // Default model
    "provider": "anthropic",        // Optional
    "system_prompt": "You are a senior code reviewer.", // Optional
    "temperature": 0.7,             // Optional
    "metadata": {                   // Optional app-specific data
        "workspace": "py-sec-edgar",
        "source": "capture-spine"
    }
}
```

**Response:**
```json
{
    "id": "sess_01H...",
    "title": "Code Review Help",
    "model": "claude-3-sonnet",
    "provider": "anthropic",
    "message_count": 0,
    "created_at": "2026-01-31T12:00:00Z",
    "updated_at": null
}
```

#### Send Message
```http
POST /v1/sessions/{session_id}/messages
Content-Type: application/json

{
    "content": "Can you review this Python function?",
    "attachments": [                // Optional
        {
            "type": "text",
            "name": "utils.py",
            "content": "def calculate_cost(...):\n    ..."
        }
    ]
}
```

**Response:**
```json
{
    "id": "msg_01H...",
    "session_id": "sess_01H...",
    "role": "assistant",
    "content": "I'd be happy to review this function...",
    "model": "claude-3-sonnet",
    "usage": {
        "input_tokens": 500,
        "output_tokens": 300
    },
    "cost_usd": 0.0024,
    "latency_ms": 2100,
    "created_at": "2026-01-31T12:01:00Z"
}
```

#### List Sessions
```http
GET /v1/sessions?limit=20&offset=0&source=capture-spine
```

#### Get Session with Messages
```http
GET /v1/sessions/{session_id}?include_messages=true
```

---

### 4. Prompts (CRUD)

Manage reusable prompt templates.

#### Create Prompt
```http
POST /v1/prompts
Content-Type: application/json

{
    "name": "Content Rewriter",
    "slug": "content-rewriter",
    "description": "Rewrite content in various modes",
    "category": "transformation",
    "system_prompt": "You are a professional editor...",
    "user_prompt_template": "Rewrite the following in {{mode}} mode:\n\n{{content}}",
    "variables": [
        {
            "name": "content",
            "type": "text",
            "required": true,
            "description": "Content to rewrite"
        },
        {
            "name": "mode",
            "type": "enum",
            "required": true,
            "options": ["clean", "format", "organize", "summarize"],
            "default": "clean"
        }
    ],
    "default_model": "gpt-4o-mini",
    "default_temperature": 0.7,
    "tags": ["rewriting", "editing"],
    "is_public": true
}
```

#### List Prompts
```http
GET /v1/prompts?category=transformation&tags=editing&search=rewrite
```

#### Get Prompt with Versions
```http
GET /v1/prompts/{prompt_id}?include_versions=true
```

---

### 5. Models & Providers

Discover available models.

```http
GET /v1/models
```

**Response:**
```json
{
    "models": [
        {
            "id": "gpt-4o",
            "provider": "openai",
            "display_name": "GPT-4o",
            "context_window": 128000,
            "supports_vision": true,
            "supports_streaming": true,
            "pricing": {
                "input_per_1m": 5.00,
                "output_per_1m": 15.00
            }
        },
        {
            "id": "claude-3-sonnet-20240229",
            "provider": "anthropic",
            "display_name": "Claude 3 Sonnet",
            "context_window": 200000,
            "supports_vision": true,
            "supports_streaming": true,
            "pricing": {
                "input_per_1m": 3.00,
                "output_per_1m": 15.00
            }
        }
    ]
}
```

---

### 6. Usage & Cost Tracking

```http
GET /v1/usage?start_date=2026-01-01&end_date=2026-01-31&group_by=model
```

**Response:**
```json
{
    "period": {
        "start": "2026-01-01",
        "end": "2026-01-31"
    },
    "total_cost_usd": 45.67,
    "total_requests": 1234,
    "total_tokens": {
        "input": 500000,
        "output": 250000
    },
    "by_model": [
        {
            "model": "gpt-4o",
            "provider": "openai",
            "requests": 500,
            "cost_usd": 30.00
        },
        {
            "model": "claude-3-sonnet",
            "provider": "anthropic",
            "requests": 734,
            "cost_usd": 15.67
        }
    ]
}
```

---

## Error Responses

All errors follow this format:

```json
{
    "error": {
        "code": "PROVIDER_ERROR",
        "message": "OpenAI API rate limit exceeded",
        "details": {
            "provider": "openai",
            "retry_after": 60
        }
    }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request body |
| `NOT_FOUND` | 404 | Resource not found |
| `PROVIDER_ERROR` | 502 | Upstream LLM provider error |
| `RATE_LIMITED` | 429 | Too many requests |
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Python SDK Interface

```python
from genai_spine_client import GenAIClient

client = GenAIClient(
    base_url="http://localhost:8100",
    api_key="...",  # Optional
)

# Direct completion
response = await client.complete(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4o",
)

# Execute prompt
result = await client.execute_prompt(
    slug="content-rewriter",
    variables={"content": text, "mode": "clean"},
)

# Chat session
session = await client.sessions.create(model="claude-3-sonnet")
message = await session.send("Review this code", attachments=[...])

# List prompts
prompts = await client.prompts.list(category="transformation")
```

---

## TypeScript SDK Interface

```typescript
import { GenAIClient } from '@genai-spine/client';

const client = new GenAIClient({
    baseUrl: 'http://localhost:8100',
});

// Direct completion
const response = await client.complete({
    messages: [{ role: 'user', content: 'Hello' }],
    model: 'gpt-4o',
});

// Execute prompt
const result = await client.executePrompt({
    slug: 'content-rewriter',
    variables: { content: text, mode: 'clean' },
});

// Chat session
const session = await client.sessions.create({ model: 'claude-3-sonnet' });
const message = await session.send('Review this code', { attachments: [...] });
```

---

## Related Documents

- [CAPTURE_SPINE_INTEGRATION_ANALYSIS.md](CAPTURE_SPINE_INTEGRATION_ANALYSIS.md) - Migration analysis
- [../features/GENAI_ADMIN_UI.md](../features/GENAI_ADMIN_UI.md) - Admin interface
- [../../STATUS.md](../../STATUS.md) - Current implementation status
