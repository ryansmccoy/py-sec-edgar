# GenAI Spine Integration Architecture

**Status:** Proposal
**Created:** 2026-01-31
**Last Updated:** 2026-01-31

This document analyzes the current LLM architecture in capture-spine and proposes three options for integrating with the centralized GenAI Spine service.

---

## Current State Analysis

### Capture-Spine LLM Infrastructure

Capture-spine currently has its own LLM infrastructure:

```
capture-spine/app/
├── llm/
│   ├── __init__.py        # Public API exports
│   ├── cost.py            # Cost calculation
│   ├── prompts.py         # Prompt templates
│   ├── types.py           # Request/response types
│   └── providers/
│       ├── base.py        # LLMClient protocol, LLMConfig
│       ├── openai.py      # OpenAI client
│       ├── anthropic.py   # Anthropic client
│       ├── ollama.py      # Ollama client
│       └── bedrock.py     # AWS Bedrock client
└── features/
    ├── chat/              # Chat conversations (like VS Code Copilot)
    │   ├── service.py     # ChatService - orchestrates LLM calls
    │   ├── repository.py  # DB persistence
    │   └── models.py      # Pydantic models
    └── llm_transform/     # Generic content transformation
        ├── service.py     # LLMTransformService
        ├── repository.py  # Prompt storage, history
        └── models.py      # TransformRequest, etc.
```

### Duplication Issues

| Component | capture-spine | genai-spine | Notes |
|-----------|---------------|-------------|-------|
| Provider clients | ✅ 4 providers | ✅ 3 providers | Duplicated code |
| Cost tracking | ✅ Basic | ✅ Full | Different implementations |
| Prompt storage | ✅ PostgreSQL | ✅ SQLite/PostgreSQL | Duplicated tables |
| Chat sessions | ✅ Full | ❌ Proposed | Only in capture-spine |
| LLM Transform | ✅ Full | ❌ | Only in capture-spine |

### What Should Move to GenAI Spine

| Feature | Move? | Rationale |
|---------|-------|-----------|
| Provider clients | ✅ Yes | Central management, single point of API keys |
| Cost tracking | ✅ Yes | Unified cost view across all apps |
| Prompt library | ✅ Yes | Share prompts across apps |
| Chat sessions | ✅ Yes | Generic chat capability for any app |
| LLM Transform | ✅ Yes | Generic transformation, not capture-specific |
| Work session commits | Keep contract | Domain logic stays in capture-spine |

---

## Design Principles

### 1. Domain-Agnostic Endpoints

GenAI Spine endpoints should NOT contain domain-specific logic:

```
❌ BAD: POST /v1/generate-article-summary     # Domain-specific
❌ BAD: POST /v1/categorize-sec-filings       # Domain-specific
❌ BAD: POST /v1/enrich-chat-message          # Domain-specific

✅ GOOD: POST /v1/completions                 # Generic
✅ GOOD: POST /v1/execute-prompt              # Generic with prompt_id
✅ GOOD: POST /v1/chat/sessions/{id}/messages # Generic chat
```

### 2. Contract-Based Integration

```python
# capture-spine calls genai-spine with domain context
response = await genai_client.execute_prompt(
    prompt_slug="message-enrichment",  # GenAI owns the prompt
    variables={
        "content": message.content,    # capture-spine provides data
        "mode": "clean",               # Domain-specific choice
    }
)
```

### 3. Single Source of Truth

| Concern | Owner | Consumers |
|---------|-------|-----------|
| LLM providers & API keys | genai-spine | All apps |
| Cost tracking | genai-spine | All apps |
| Prompt templates | genai-spine | All apps |
| Chat session storage | genai-spine | All apps |
| Domain logic (what to transform) | Each app | N/A |

---

## Three Architecture Options

### Option A: HTTP Client (Lightweight)

**Summary:** capture-spine calls genai-spine via HTTP REST API.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPTURE-SPINE                                │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐      │
│  │  Chat Feature  │   │ LLM Transform  │   │ Work Sessions  │      │
│  │  (UI + Logic)  │   │  (UI + Logic)  │   │ (Domain Logic) │      │
│  └───────┬────────┘   └───────┬────────┘   └───────┬────────┘      │
│          │                    │                    │               │
│          └────────────────────┼────────────────────┘               │
│                               │                                    │
│                    ┌──────────▼──────────┐                         │
│                    │  GenAI Client       │                         │
│                    │  (httpx wrapper)    │                         │
│                    └──────────┬──────────┘                         │
└───────────────────────────────┼────────────────────────────────────┘
                                │ HTTP
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENAI-SPINE                                  │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐      │
│  │  Completions   │   │  Chat API      │   │  Prompts API   │      │
│  │  /v1/complete  │   │  /v1/sessions  │   │  /v1/prompts   │      │
│  └───────┬────────┘   └───────┬────────┘   └───────┬────────┘      │
│          │                    │                    │               │
│          └────────────────────┼────────────────────┘               │
│                               │                                    │
│                    ┌──────────▼──────────┐                         │
│                    │  Provider Router    │                         │
│                    │  Ollama│OpenAI│...  │                         │
│                    └────────────────────-┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Simple to implement
- Clear service boundary
- Independent scaling
- Easy to test

**Cons:**
- Network latency for every call
- Need to handle HTTP errors
- Requires genai-spine to be running

**Implementation Effort:** 2-3 days

---

### Option B: Client Module (Recommended)

**Summary:** Use the `genai_spine_client` module from `genai-spine/client/`. Copy it or reference it directly - **no publishing required**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPTURE-SPINE                                │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐      │
│  │  Chat Feature  │   │ LLM Transform  │   │ Work Sessions  │      │
│  │  (UI + Logic)  │   │  (UI + Logic)  │   │ (Domain Logic) │      │
│  └───────┬────────┘   └───────┬────────┘   └───────┬────────┘      │
│          │                    │                    │               │
│          └────────────────────┼────────────────────┘               │
│                               │                                    │
│                    ┌──────────▼──────────┐                         │
│                    │  genai_spine_client │ ◄─── copy or local path │
│                    │  (httpx + Pydantic) │                         │
│                    └──────────┬──────────┘                         │
└───────────────────────────────┼────────────────────────────────────┘
                                │ HTTP (under the hood)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GENAI-SPINE (Docker)                         │
└─────────────────────────────────────────────────────────────────────┘
```

**What the client module is:**
- Just **httpx + Pydantic types** - no magic
- Located at `genai-spine/client/genai_spine_client/`
- Can be copied into any app or referenced via local path

**How to use it:**

```bash
# Option 1: Copy the folder
cp -r genai-spine/client/genai_spine_client capture-spine/app/

# Option 2: Local path install
pip install -e ../genai-spine/client

# Option 3: In requirements.txt
genai-spine-client @ file:///path/to/genai-spine/client
```

**Client Example:**
```python
from genai_spine_client import GenAIClient

# Initialize once (GenAI Spine runs in Docker)
client = GenAIClient(base_url="http://localhost:8100")

# Chat completion (OpenAI-compatible)
response = await client.chat_complete(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4o-mini"
)

# Execute prompt
result = await client.execute_prompt(
    slug="message-enrichment",
    variables={"content": text, "mode": "clean"}
)

# Chat sessions (stateful)
session = await client.create_session(model="gpt-4o")
reply = await client.send_message(session.id, "Explain this code")
```

**Pros:**
- Type-safe API with Pydantic models
- Automatic retry/error handling
- No publishing required - just copy or reference
- GenAI Spine service runs in Docker (local or AWS)

**Cons:**
- Manual sync if API changes (mitigated by local path install)
- Still requires GenAI Spine service to be running

**Implementation Effort:** 1 week

---

### Option C: Shared Library (Monorepo)

**Summary:** Extract LLM core into shared package within workspace.

```
py-sec-edgar/
├── packages/
│   └── genai-core/                    # Shared LLM primitives
│       ├── providers/                 # Provider clients
│       ├── types/                     # Request/response types
│       └── cost.py                    # Cost calculation
├── genai-spine/                       # API service
│   └── uses genai-core
├── capture-spine/                     # Full-stack app
│   └── uses genai-core directly OR via genai-spine API
└── feedspine/
    └── uses genai-core directly OR via genai-spine API
```

**Pros:**
- No network latency for embedded use
- Single source of truth for types
- Can use directly or via API

**Cons:**
- Complex dependency management
- All apps must update together
- Blurs service boundaries

**Implementation Effort:** 2 weeks

---

## Recommendation: Option B (Client Module)

**Rationale:**

1. **Clean separation:** GenAI Spine service runs in Docker, consumer apps just import the client
2. **No publishing required:** Copy the module or use local path install
3. **Type safety:** Pydantic models for IDE autocomplete
4. **Flexibility:** Can switch to direct HTTP if needed
5. **Testability:** Mock the client for unit tests

**The client is just convenience.** The real architecture is:
- GenAI Spine service running in Docker (local dev or AWS)
- Consumer apps make HTTP calls to it
- The client module is just a typed wrapper around those HTTP calls

---

## API Contract Design

### Core Endpoints (Domain-Agnostic)

```yaml
# Completions (generic LLM calls)
POST /v1/completions
  - messages: [{role, content}]
  - model: string
  - provider: string (optional)
  - temperature: float (optional)
  - max_tokens: int (optional)

# Execute saved prompt
POST /v1/execute-prompt
  - prompt_id: UUID | null
  - prompt_slug: string | null
  - variables: dict
  - model: string (optional)

# Chat sessions
POST /v1/sessions                    # Create session
GET  /v1/sessions                    # List sessions
GET  /v1/sessions/{id}               # Get session
POST /v1/sessions/{id}/messages      # Send message
GET  /v1/sessions/{id}/messages      # Get history

# Prompts (CRUD)
POST /v1/prompts
GET  /v1/prompts
GET  /v1/prompts/{id}
PUT  /v1/prompts/{id}
DELETE /v1/prompts/{id}
GET  /v1/prompts/{id}/versions

# Models & Pricing
GET  /v1/models
GET  /v1/pricing
POST /v1/estimate-cost

# Usage tracking
GET  /v1/usage
```

### What's NOT in GenAI Spine

```yaml
# Domain-specific logic stays in each app:

# capture-spine owns:
POST /api/work-sessions/{id}/generate-commit  # Calls genai-spine internally

# feedspine owns:
POST /api/articles/{id}/summarize             # Calls genai-spine internally

# py-sec-edgar owns:
POST /api/filings/{id}/extract-entities       # Calls genai-spine internally
```

---

## Migration Plan

### Phase 1: Client Library (Week 1)
- [ ] Create `genai_spine_client` package in genai-spine
- [ ] Implement async HTTP client wrapper
- [ ] Add type definitions matching API

### Phase 2: Chat Migration (Week 2)
- [ ] Add `/v1/sessions` endpoints to genai-spine
- [ ] Migrate chat schema from capture-spine
- [ ] Update capture-spine to use client

### Phase 3: LLM Transform Migration (Week 3)
- [ ] Migrate prompt storage to genai-spine
- [ ] Update capture-spine LLM Transform to use client
- [ ] Deprecate capture-spine's `app/llm/` package

### Phase 4: Remove Duplication (Week 4)
- [ ] Remove capture-spine's provider implementations
- [ ] Remove capture-spine's cost tracking
- [ ] Update all tests

---

## Next Steps

1. **Review this proposal** - Confirm Option B is acceptable
2. **Define SDK API** - Create detailed client interface
3. **Create migration checklist** - Break down each phase
4. **Implement client library** - Start with core functionality

---

## Related Documents

- [GENAI_ADMIN_UI.md](../features/GENAI_ADMIN_UI.md) - Admin interface spec
- [MULTI_MODEL_REVIEW_WORKFLOW.md](../features/MULTI_MODEL_REVIEW_WORKFLOW.md) - Review workflow
- [STATUS.md](../../STATUS.md) - Current GenAI Spine status
