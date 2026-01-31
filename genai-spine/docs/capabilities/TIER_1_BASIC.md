# Tier 1: Basic Capabilities

> Core functionality required for MVP. These must work reliably before advancing to higher tiers.

---

## Overview

| # | Capability | Description | Status | Module |
|---|------------|-------------|--------|--------|
| 1 | Text Completion | Basic prompt → response | ✅ | `api/routers/completions.py` |
| 2 | Chat Completion | Multi-turn conversation | ✅ | `api/routers/chat.py` |
| 3 | Text Summarization | Long text → concise summary | ✅ | `capabilities/summarization.py` |
| 4 | Text Classification | Content → category | ✅ | `capabilities/classification.py` |
| 5 | Entity Extraction | Text → structured entities | ✅ | `capabilities/extraction.py` |
| 6 | Key Point Extraction | Document → bullet points | 🟡 | `capabilities/extraction.py` |
| 7 | Template Fill | Template + vars → output | ✅ | `prompts/renderer.py` |
| 8 | Prompt Management | CRUD for prompts | ✅ | `api/routers/prompts.py` |
| 9 | Prompt Versioning | Immutable version history | ✅ | `storage/models.py` |
| 10 | Cost Tracking | Per-request token costs | 🟡 | `providers/*/` |
| 11 | Provider Abstraction | Unified provider interface | ✅ | `providers/base.py` |
| 12 | Model Listing | List available models | ✅ | `api/routers/models.py` |
| 13 | Health Checks | Service health endpoints | ✅ | `api/routers/health.py` |
| 14 | JSON Mode | Structured output | ✅ | `providers/*/` |
| 15 | Error Handling | Graceful failure + retry | 🟡 | `core/exceptions.py` |

---

## 1. Text Completion

**Endpoint:** `POST /v1/completions`

Basic prompt-in, text-out completion. Foundation for all other capabilities.

```python
response = await client.post("/v1/completions", json={
    "prompt": "Explain quantum computing in simple terms.",
    "model": "llama3.2:latest",
    "max_tokens": 500,
    "temperature": 0.7
})
```

**Use cases:**
- Freeform questions
- Creative writing
- Code generation
- Simple transformations

---

## 2. Chat Completion

**Endpoint:** `POST /v1/chat/completions`

OpenAI-compatible multi-turn conversation API.

```python
response = await client.post("/v1/chat/completions", json={
    "model": "llama3.2:latest",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language..."},
        {"role": "user", "content": "Show me an example."}
    ]
})
```

**Use cases:**
- Interactive assistants
- Multi-turn reasoning
- Context-aware responses

---

## 3. Text Summarization

**Endpoint:** `POST /v1/summarize`

Compress long text into concise summaries.

```python
response = await client.post("/v1/summarize", json={
    "content": "Long article text here...",
    "max_sentences": 3,
    "focus": "key findings",
    "output_format": "bullet_points"  # or "paragraph"
})
```

**Response:**
```json
{
    "summary": "• Point one\n• Point two\n• Point three",
    "key_points": ["Point one", "Point two", "Point three"],
    "word_count": 45,
    "compression_ratio": 0.85,
    "usage": {"input_tokens": 1200, "output_tokens": 60}
}
```

**Use cases:**
- Article digests
- Document previews
- Meeting note summaries

---

## 4. Text Classification

**Endpoint:** `POST /v1/classify`

Assign content to predefined categories.

```python
response = await client.post("/v1/classify", json={
    "content": "Apple announced record iPhone sales...",
    "categories": ["technology", "finance", "healthcare", "politics"],
    "multi_label": True,
    "min_confidence": 0.5
})
```

**Response:**
```json
{
    "classifications": [
        {"category": "technology", "confidence": 0.92},
        {"category": "finance", "confidence": 0.78}
    ],
    "primary_category": "technology"
}
```

**Use cases:**
- Content routing
- Topic assignment
- Spam detection

---

## 5. Entity Extraction (NER)

**Endpoint:** `POST /v1/extract`

Extract named entities from text.

```python
response = await client.post("/v1/extract", json={
    "content": "Tim Cook, CEO of Apple Inc., announced...",
    "entity_types": ["PERSON", "ORG", "ROLE", "DATE", "MONEY"],
    "include_context": True
})
```

**Response:**
```json
{
    "entities": [
        {"text": "Tim Cook", "type": "PERSON", "start": 0, "end": 8},
        {"text": "CEO", "type": "ROLE", "start": 10, "end": 13},
        {"text": "Apple Inc.", "type": "ORG", "start": 17, "end": 27}
    ]
}
```

**Supported entity types:**
- `PERSON` — People names
- `ORG` — Organizations, companies
- `LOCATION` — Places, addresses
- `DATE` — Dates, time periods
- `MONEY` — Monetary amounts
- `PERCENT` — Percentages
- `EVENT` — Named events
- `PRODUCT` — Product names

---

## 6. Key Point Extraction

**Endpoint:** `POST /v1/extract` (with `extraction_type: "key_points"`)

Extract main points from documents.

```python
response = await client.post("/v1/extract", json={
    "content": "Long document text...",
    "extraction_type": "key_points",
    "max_points": 5
})
```

**Use cases:**
- Executive summaries
- Meeting highlights
- Report takeaways

---

## 7. Template Fill

**Endpoint:** `POST /v1/prompts/{id}/render`

Render prompt template with variable substitution.

```python
# Create template
await client.post("/v1/prompts", json={
    "name": "Email Draft",
    "slug": "email-draft",
    "user_prompt_template": "Write a {{tone}} email to {{recipient}} about {{topic}}.",
    "variables": [
        {"name": "tone", "type": "string", "default": "professional"},
        {"name": "recipient", "type": "string", "required": True},
        {"name": "topic", "type": "string", "required": True}
    ]
})

# Render
response = await client.post("/v1/prompts/email-draft/render", json={
    "variables": {
        "recipient": "the team",
        "topic": "Q4 results"
    }
})
```

---

## 8-9. Prompt Management & Versioning

**Endpoints:** `GET/POST/PUT/DELETE /v1/prompts`

Full CRUD with automatic version history.

```python
# Create
prompt = await client.post("/v1/prompts", json={...})

# Update (creates new version)
await client.put(f"/v1/prompts/{prompt_id}", json={...})

# Get version history
versions = await client.get(f"/v1/prompts/{prompt_id}/versions")
```

**Features:**
- Immutable version history
- Rollback support
- A/B testing preparation
- Audit trail

---

## 10. Cost Tracking

Track token usage and costs per request.

```python
# Every response includes usage
{
    "content": "...",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 85,
        "cost_usd": 0.0023,
        "provider": "openai",
        "model": "gpt-4o-mini"
    }
}
```

**Aggregated:**
```python
GET /v1/costs?start_date=2026-01-01&end_date=2026-01-31
```

---

## 11. Provider Abstraction

Unified interface across providers:

```python
from genai_spine.providers import get_provider

# Same code works with any provider
provider = get_provider("ollama")  # or "openai", "anthropic", "bedrock"
response = await provider.complete(request)
```

**Supported providers:**
| Provider | Status | Models |
|----------|--------|--------|
| Ollama | ✅ | llama3.2, qwen2.5, mistral, etc. |
| OpenAI | ✅ | gpt-4o, gpt-4o-mini, o1, etc. |
| Anthropic | 🔴 | Claude Sonnet, Haiku |
| Bedrock | 🔴 | Claude, Nova |

---

## 12. Model Listing

**Endpoint:** `GET /v1/models`

List available models across providers.

```json
{
    "models": [
        {"id": "llama3.2:latest", "provider": "ollama", "context_length": 128000},
        {"id": "gpt-4o-mini", "provider": "openai", "context_length": 128000}
    ]
}
```

---

## 13. Health Checks

**Endpoints:** `GET /health`, `GET /ready`

```json
// /health
{"status": "healthy", "version": "0.1.0"}

// /ready
{
    "status": "ready",
    "providers": {
        "ollama": {"status": "connected", "models": 3},
        "openai": {"status": "connected"}
    },
    "database": {"status": "connected"}
}
```

---

## 14. JSON Mode

Request structured JSON output.

```python
response = await client.post("/v1/chat/completions", json={
    "model": "llama3.2:latest",
    "messages": [{"role": "user", "content": "List 3 fruits as JSON"}],
    "response_format": {"type": "json_object"}
})
# Response content is valid JSON
```

---

## 15. Error Handling

Graceful failures with actionable errors.

```json
{
    "error": {
        "code": "provider_unavailable",
        "message": "Ollama server not responding",
        "provider": "ollama",
        "retry_after": 30,
        "fallback_available": true
    }
}
```

---

## Implementation Priority

1. ✅ Text/Chat Completion (foundation)
2. ✅ Summarization, Classification, Extraction (core capabilities)
3. ✅ Prompt Management (infrastructure)
4. 🟡 Cost Tracking (complete persistence)
5. 🟡 Error Handling (add retry logic)
