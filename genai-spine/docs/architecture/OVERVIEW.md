# GenAI Spine Architecture Overview

> High-level architecture and design principles.

---

## Design Principles

### 1. Provider Agnostic

GenAI Spine abstracts LLM providers behind a unified interface:

```python
# Same code works with any provider
provider = get_provider("ollama")  # or "openai", "anthropic", "bedrock"
response = await provider.complete(request)
```

### 2. Capability-Centric

AI operations are organized as capabilities, not raw API calls:

```python
# High-level capability
await client.post("/v1/summarize", json={"content": text})

# Not low-level prompt engineering
await client.post("/v1/chat/completions", json={"messages": [...]})
```

### 3. Domain Extensible

Core is domain-agnostic; domains add specialization:

```
Core: summarize, extract, classify (generic)
Domain: summarize-10k, extract-financial-metrics (specialized)
```

### 4. Infrastructure Included

Built-in support for:
- Prompt management with versioning
- Cost tracking and budgets
- Response caching
- Provider fallback/routing

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           API Layer                                  │
│   FastAPI routers: /health, /v1/*, /v1/prompts, /v1/rag            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                         Capability Layer                             │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│   │ Summarize   │  │  Extract    │  │  Classify   │  │   RAG     │ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                          Core Layer                                  │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│   │  Prompts    │  │    Cost     │  │   Cache     │  │ Routing   │ │
│   │  Manager    │  │  Tracker    │  │   Layer     │  │  Engine   │ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                        Provider Layer                                │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│   │   Ollama    │  │   OpenAI    │  │  Anthropic  │  │  Bedrock  │ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────────┐
│                        Storage Layer                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│   │   SQLite    │  │  PostgreSQL │  │    Redis    │  │  Vector   │ │
│   │  (prompts)  │  │  (scale)    │  │  (cache)    │  │  (RAG)    │ │
│   └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow

```
1. Request → API Router
2. API Router → Capability Handler
3. Capability Handler:
   a. Load prompt template (Prompt Manager)
   b. Render template with variables
   c. Check cache (Cache Layer)
   d. If cache miss:
      - Select provider (Routing Engine)
      - Execute request (Provider Layer)
      - Track cost (Cost Tracker)
      - Cache response (Cache Layer)
4. Return response with usage metadata
```

---

## Module Structure

```
src/genai_spine/
├── __init__.py
├── main.py                 # Entry point
├── settings.py             # Configuration
│
├── api/                    # API Layer
│   ├── app.py              # FastAPI factory
│   ├── deps.py             # Dependencies
│   └── routers/            # Endpoint handlers
│       ├── health.py
│       ├── chat.py
│       ├── completions.py
│       ├── capabilities.py
│       ├── prompts.py
│       └── models.py
│
├── capabilities/           # Capability Layer
│   ├── summarization.py
│   ├── extraction.py
│   ├── classification.py
│   └── __init__.py
│
├── core/                   # Core Layer
│   ├── prompts/
│   │   ├── manager.py
│   │   ├── renderer.py
│   │   └── versioning.py
│   ├── cost.py
│   ├── cache.py
│   └── routing.py
│
├── providers/              # Provider Layer
│   ├── base.py             # Abstract interface
│   ├── registry.py
│   ├── ollama.py
│   ├── openai.py
│   ├── anthropic.py
│   └── bedrock.py
│
├── storage/                # Storage Layer
│   ├── models.py           # SQLAlchemy models
│   ├── sqlite.py
│   └── postgres.py
│
└── domains/                # Domain Extensions
    └── financial_markets/
        ├── __init__.py
        ├── prompts/
        └── schemas/
```

---

## Data Flow

### Completion Request

```
POST /v1/chat/completions
{
    "model": "llama3.2:latest",
    "messages": [...]
}

→ chat.router.chat_completion()
→ provider = registry.get_provider("ollama")
→ response = await provider.complete(request)
→ cost_tracker.record(response.usage)
→ return response
```

### Capability Request

```
POST /v1/summarize
{
    "content": "...",
    "max_sentences": 3
}

→ capabilities.router.summarize()
→ prompt = prompt_manager.get("summarize-article")
→ rendered = prompt_renderer.render(prompt, {"content": ...})
→ provider = routing_engine.select(strategy="cost_optimized")
→ response = await provider.complete(rendered)
→ result = parse_summarization_response(response)
→ return result
```

---

## Configuration

All configuration via environment variables with `GENAI_` prefix:

| Category | Variables |
|----------|-----------|
| API | `GENAI_API_HOST`, `GENAI_API_PORT`, `GENAI_DEBUG` |
| Providers | `GENAI_DEFAULT_PROVIDER`, `GENAI_OLLAMA_URL`, `GENAI_OPENAI_API_KEY` |
| Storage | `GENAI_DATABASE_URL`, `GENAI_REDIS_URL` |
| Costs | `GENAI_BUDGET_DAILY`, `GENAI_BUDGET_ACTION` |
| Cache | `GENAI_CACHE_ENABLED`, `GENAI_CACHE_TTL` |

See [settings.py](../../src/genai_spine/settings.py) for full list.

---

## Related Docs

- [TIERS.md](TIERS.md) — Deployment tier options
- [PROVIDERS.md](PROVIDERS.md) — Provider abstraction details
- [../core/](../core/) — Core component docs
