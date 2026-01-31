# GenAI Spine - Capture Spine Integration Guide

**Last Updated**: 2026-01-31
**Status**: Active Development

This document tracks GenAI Spine's integration requirements for supporting Capture Spine's productivity features. Keep this synchronized with `capture-spine/docs/features/productivity/`.

> **📖 Also See:**
> - [ECOSYSTEM_INTEGRATION.md](./ECOSYSTEM_INTEGRATION.md) - Full ecosystem integration (FeedSpine, Spine-Core, EntitySpine)
> - [entityspine](../../entityspine/) - Import `Result[T]`, `ExecutionContext`, `ErrorCategory` from here

---

## 🧱 Ecosystem Types for Capture Spine

Use these shared types from entityspine when implementing Capture Spine integrations:

```python
# genai_spine/capabilities/rewrite.py
from entityspine.domain.workflow import Result, Ok, Err, ExecutionContext

async def rewrite_content(
    content: str,
    mode: RewriteMode,
    ctx: ExecutionContext | None = None,
) -> Result[RewriteResult]:
    """Rewrite content using LLM."""
    ctx = ctx or ExecutionContext()
    try:
        response = await provider.complete(...)
        return Ok(RewriteResult(
            original=content,
            rewritten=response.content,
            execution_id=ctx.execution_id,
        ))
    except ProviderError as e:
        return Err(e)
```

---

## 📁 Reference Location

**Capture Spine Productivity Docs:**
```
capture-spine/docs/features/productivity/
├── 01-copilot-chat/      # Chat ingestion, intelligence
├── 02-message-enrichment/ # ⭐ HIGH PRIORITY - LLM rewriting
├── 03-knowledge-base/     # Starring, knowledge items
├── 04-todo-system/        # Task extraction
├── 05-file-management/    # File upload, linking
├── 06-pipelines/          # ⭐ HIGH PRIORITY - Automation
├── 07-infrastructure/     # LLM providers, SSE, search
└── 08-work-sessions/      # ⭐ HIGH PRIORITY - Commit generation
```

---

## Integration Matrix

### Required GenAI Capabilities

| Capture Spine Feature | GenAI Capability | Status | Priority |
|-----------------------|------------------|--------|----------|
| **Message Enrichment** | `/v1/rewrite` | ✅ Working | P0 |
| **Title Inference** | `/v1/infer-title` | ✅ Working | P0 |
| **Todo Extraction** | `/v1/extract` (extend) | 🟡 Exists, extend | P1 |
| **Content Summary** | `/v1/summarize` | ✅ Working | - |
| **Pipeline Steps** | `/v1/execute-prompt` | ✅ Working | P1 |
| **Commit Generation** | `/v1/generate-commit` | ✅ Working | P1 |
| **Entity Extraction** | `/v1/extract` | ✅ Working | - |
| **Classification** | `/v1/classify` | ✅ Working | - |

---

## Feature Details

### 1. Message Enrichment (02-message-enrichment/)

**Source Docs:**
- `02-message-enrichment/README.md` - Overview
- `02-message-enrichment/API.md` - Endpoint specs
- `02-message-enrichment/PROMPTS.md` - Prompt templates
- `02-message-enrichment/DATABASE.md` - Version storage

**Required GenAI Endpoints:**

```
POST /v1/rewrite
{
  "content": "but as a real example, i shuold be able to...",
  "mode": "clean",  // clean | format | organize | professional | summarize
  "context": "optional previous messages",
  "options": {
    "preserve_code_blocks": true,
    "max_length": null
  }
}

Response:
{
  "original": "...",
  "rewritten": "## Message Flow\n\nI want to implement...",
  "mode": "clean",
  "provider": "ollama",
  "model": "llama3.2:latest",
  "input_tokens": 150,
  "output_tokens": 320,
  "execution_id": "uuid"
}
```

```
POST /v1/infer-title
{
  "content": "long message content...",
  "max_words": 10
}

Response:
{
  "title": "Message Enrichment Pipeline Implementation",
  "provider": "ollama",
  "model": "llama3.2:latest"
}
```

**Rewrite Modes (from PROMPTS.md):**
| Mode | System Prompt Focus |
|------|---------------------|
| `clean` | Fix grammar, spelling, improve clarity |
| `format` | Add structure, headings, bullets |
| `organize` | Reorganize into logical sections |
| `professional` | Business tone |
| `summarize` | Condense to key points |
| `technical` | Technical documentation style |

---

### 2. Enrichment Pipelines (06-pipelines/)

**Source Docs:**
- `06-pipelines/README.md` - Pipeline overview
- `06-pipelines/SPEC.md` - Full specification

**Required GenAI Capability:**

Pipelines need to chain multiple LLM operations. GenAI Spine should support:

```
POST /v1/execute-prompt
{
  "prompt_slug": "rewrite-clean",  // or prompt_id
  "variables": {
    "content": "..."
  },
  "options": {
    "provider": "ollama",
    "model": "llama3.2:latest",
    "temperature": 0.7
  }
}
```

**Pipeline Step Types (GenAI must support):**
| Step Type | GenAI Endpoint |
|-----------|----------------|
| `llm_rewrite` | `/v1/rewrite` |
| `llm_summarize` | `/v1/summarize` |
| `llm_infer_title` | `/v1/infer-title` |
| `llm_extract_todos` | `/v1/extract` (type=todos) |
| `llm_classify` | `/v1/classify` |
| `llm_custom` | `/v1/execute-prompt` |

---

### 3. Work Session & Commit Generation (08-work-sessions/)

**Source Docs:**
- `08-work-sessions/README.md` - Overview
- `08-work-sessions/SPEC.md` - Full specification

**Required GenAI Capability:**

```
POST /v1/generate-commit
{
  "files": [
    {"path": "src/storage/postgres.py", "status": "modified", "diff": "..."},
    {"path": "docs/README.md", "status": "added"}
  ],
  "chat_context": [
    {"role": "user", "content": "implement postgres storage"},
    {"role": "assistant", "content": "..."}
  ],
  "options": {
    "style": "conventional",  // conventional | semantic | simple
    "max_length": 500,
    "include_scope": true
  }
}

Response:
{
  "commit_message": "feat(storage): add PostgreSQL backend with asyncpg\n\n- Implement connection pooling\n- Add transaction support\n- Create schema migrations",
  "feature_groups": [
    {
      "scope": "storage",
      "description": "PostgreSQL backend implementation",
      "files": ["src/storage/postgres.py", "src/storage/models.py"]
    }
  ],
  "suggested_tags": ["storage", "database", "postgres"]
}
```

---

### 4. LLM Provider Requirements (07-infrastructure/)

**Source Docs:**
- `07-infrastructure/LLM_PROVIDERS.md` - Provider specs
- `07-infrastructure/SSE_STREAMING.md` - Streaming

**GenAI must provide unified interface for:**

| Provider | GenAI Status | Notes |
|----------|--------------|-------|
| Ollama | ✅ Working | Local, primary for dev |
| OpenAI | ✅ Working | GPT-4o-mini default |
| Anthropic | 🔴 Planned | Claude models |
| Bedrock | 🔴 Planned | AWS managed |

**Required capabilities:**
- [ ] Streaming responses (SSE)
- [ ] Model listing per provider
- [ ] Cost tracking per request
- [ ] Execution history

---

## Database Alignment

### Capture Spine Tables (existing)

```sql
-- From capture-spine schema
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    slug VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    system_prompt TEXT,
    user_prompt_template TEXT,
    variables JSONB,
    -- ...
);

CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    prompt_id UUID REFERENCES prompts(id),
    version INTEGER,
    -- ... (immutable snapshot)
);

CREATE TABLE transformations (
    id UUID PRIMARY KEY,
    provider VARCHAR(100),
    model VARCHAR(100),
    prompt_id UUID,
    input_text TEXT,
    output_text TEXT,
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL,
    -- ...
);
```

### GenAI Spine Alignment

GenAI Spine's storage layer (protocols.py, schemas.py) is designed to be compatible:

| Capture Spine Table | GenAI Spine Equivalent |
|---------------------|------------------------|
| `prompts` | `PromptRecord` (compatible schema) |
| `prompt_versions` | `PromptVersionRecord` (immutable) |
| `transformations` | `ExecutionRecord` (similar fields) |

**Key compatibility points:**
- Same `{{variable}}` template syntax
- Same versioning approach (immutable versions)
- Same cost tracking fields
- Same provider/model tracking

---

## Implementation Checklist

### P0 - This Week

- [ ] **Rewrite capability** (`capabilities/rewrite.py`)
  - [ ] `RewriteMode` enum (clean, format, organize, professional, summarize)
  - [ ] `rewrite_content()` function
  - [ ] Default prompts in seed.py
  - [ ] API endpoint `/v1/rewrite`

- [ ] **Title inference capability**
  - [ ] `infer_title()` function
  - [ ] API endpoint `/v1/infer-title`

- [ ] **Execute prompt capability**
  - [ ] `/v1/execute-prompt` endpoint
  - [ ] Variable substitution
  - [ ] Execution tracking

### P1 - Next 2 Weeks

- [ ] **Commit generation** (`capabilities/commit.py`)
  - [ ] `generate_commit_message()` function
  - [ ] File diff analysis
  - [ ] Chat context integration
  - [ ] Conventional commit format

- [ ] **Pipeline support**
  - [ ] Step execution API
  - [ ] Chaining support
  - [ ] Error handling

- [ ] **Additional providers**
  - [ ] Anthropic provider
  - [ ] Bedrock provider

- [ ] **Streaming support**
  - [ ] SSE endpoint
  - [ ] Token-by-token streaming

---

## API Mapping

### How Capture Spine will call GenAI Spine

```python
# capture-spine/app/services/enrichment.py

import httpx

GENAI_URL = "http://localhost:8100"

async def enrich_message(message_id: str, content: str, mode: str):
    """Call GenAI Spine to rewrite message."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GENAI_URL}/v1/rewrite",
            json={
                "content": content,
                "mode": mode,
                "options": {"preserve_code_blocks": True}
            }
        )
        result = response.json()

        # Store version in capture-spine DB
        await store_message_version(
            message_id=message_id,
            content=result["rewritten"],
            source="llm_enrichment",
            model=result["model"],
            provider=result["provider"],
        )

        return result
```

---

## Sync Checklist

When Capture Spine productivity docs change:

1. [ ] Review `02-message-enrichment/` for new prompts or modes
2. [ ] Review `06-pipelines/` for new step types
3. [ ] Review `07-infrastructure/` for provider changes
4. [ ] Review `08-work-sessions/` for commit generation changes
5. [ ] Update this document
6. [ ] Update GenAI Spine TODO.md
7. [ ] Create/update relevant capabilities

---

## 🔗 Ecosystem Integration Opportunities

GenAI Spine serves more than just Capture Spine. See [ECOSYSTEM_INTEGRATION.md](./ECOSYSTEM_INTEGRATION.md) for details on:

### FeedSpine Integration
| Capability | Endpoint | Description |
|------------|----------|-------------|
| `LLMEnricher` | `/v1/enrich` | Unified enricher for Bronze→Silver promotion |
| Story Clustering | `/v1/cluster-stories` | Group related articles into story threads |
| Semantic Dedup | `/v1/check-duplicate` | Detect semantic duplicates beyond hash matching |

### Spine-Core Integration
| Capability | Endpoint | Description |
|------------|----------|-------------|
| Quality Explanation | `/v1/explain-failure` | Human-readable explanations for QualityRunner failures |
| Error Diagnosis | `/v1/diagnose-error` | Diagnose pipeline errors with suggested fixes |

### EntitySpine Integration
| Capability | Endpoint | Description |
|------------|----------|-------------|
| Entity Disambiguation | `/v1/disambiguate` | Resolve ambiguous entity mentions |
| Identifier Suggestion | `/v1/suggest-identifier` | Suggest CUSIP/LEI/ISIN for entities |

---

## References

- [Ecosystem Integration Guide](./ECOSYSTEM_INTEGRATION.md) - Full ecosystem integration specs
- [Capture Spine Productivity README](../../capture-spine/docs/features/productivity/README.md)
- [Message Enrichment API Spec](../../capture-spine/docs/features/productivity/02-message-enrichment/API.md)
- [Pipeline Spec](../../capture-spine/docs/features/productivity/06-pipelines/SPEC.md)
- [LLM Providers Spec](../../capture-spine/docs/features/productivity/07-infrastructure/LLM_PROVIDERS.md)
