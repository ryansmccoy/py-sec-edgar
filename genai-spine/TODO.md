# GenAI Spine - Implementation TODO

**Last Updated:** 2026-01-31
**Status:** Active Development

> **📖 Integration Guides:**
> - [docs/CAPTURE_SPINE_INTEGRATION.md](docs/CAPTURE_SPINE_INTEGRATION.md) - Capture Spine feature mapping
> - [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) - FeedSpine, Spine-Core, EntitySpine opportunities
> - [prompts/PARALLEL_AGENT_PROMPT.md](prompts/PARALLEL_AGENT_PROMPT.md) - Agent guidance for parallel development

---

## Executive Summary

GenAI Spine is the unified AI service for the Spine ecosystem. This TODO tracks implementation priorities, with focus on supporting:

1. **Core Service** — Multi-provider LLM abstraction, prompt management
2. **Capture Spine Integration** — Message Enrichment, Enrichment Pipelines, Work Sessions
3. **Ecosystem Support** — EntitySpine, FeedSpine, Spine-Core (see ECOSYSTEM_INTEGRATION.md)

**Reference:** `capture-spine/docs/features/productivity/` for feature requirements.

---

## Implementation Status

### ✅ Completed

| Component | Status | Notes |
|-----------|--------|-------|
| Project structure | ✅ | FastAPI, SQLAlchemy, proper layout |
| Provider abstraction | ✅ | base.py, ollama.py, openai.py |
| Provider registry | ✅ | Dynamic provider loading |
| Settings/config | ✅ | Pydantic Settings |
| Storage models | ✅ | Prompt, PromptVersion, Execution, DailyCost |
| Basic API routers | ✅ | health, models, completions, capabilities, prompts |
| Summarization | ✅ | /v1/summarize endpoint |
| Extraction | ✅ | /v1/extract endpoint |
| Classification | ✅ | /v1/classify endpoint |
| Docker setup | ✅ | Dockerfile, docker-compose.yml |
| Documentation structure | ✅ | docs/ with good organization |
| Alignment prompts | ✅ | prompts/ with review templates |
| **Storage abstraction** | ✅ | Protocol-based, database-agnostic |
| **SQLite backend** | ✅ | For dev/testing |
| **PostgreSQL backend** | ✅ | For production (asyncpg) |
| **Rewrite capability** | ✅ | `capabilities/rewrite.py` - RewriteMode, rewrite_content() |
| **Title inference** | ✅ | `capabilities/rewrite.py` - infer_title() |
| **Commit generation** | ✅ | `capabilities/commit.py` - generate_commit_message() |
| **Tests setup** | ✅ | conftest.py, unit tests for storage |
| **Prompts router (DB)** | ✅ | Uses repository pattern, not in-memory |
| **Default prompts** | ✅ | Seed module with built-in prompts |
| **Integration guide** | ✅ | docs/CAPTURE_SPINE_INTEGRATION.md |
| **Rewrite API endpoint** | ✅ | `/v1/rewrite` - all rewrite modes |
| **Title API endpoint** | ✅ | `/v1/infer-title` - title generation |
| **Commit API endpoint** | ✅ | `/v1/generate-commit` - commit message generation |
| **Execute Prompt endpoint** | ✅ | `/v1/execute-prompt` - pipeline support |
| **Storage lifecycle** | ✅ | app.py lifespan with storage_backend_lifespan |
| **Cost tracking** | ✅ | `capabilities/cost.py` - model pricing and calculate_cost() |
| **Execution tracking** | ✅ | `api/tracking.py` - records every LLM call |
| **Usage endpoint** | ✅ | `/v1/usage` - stats, pricing, cost estimation |
| **Anthropic provider** | ✅ | `providers/anthropic.py` - Claude models |

### 🟡 In Progress

| Component | Status | Priority | Notes |
|-----------|--------|----------|-------|
| Alembic migrations | 🟡 | P1 | For production schema evolution |

### ❌ Not Started (Core)

| Component | Priority | Effort | Notes |
|-----------|----------|--------|-------|
| Bedrock provider | P1 | Medium | AWS SDK integration |
| Streaming support | P1 | Medium | SSE for chat |
| Redis caching | P2 | Medium | Response caching |
| Rate limiting | P2 | Small | Per-provider limits |

### ❌ Not Started (Capture Spine Support)

| Component | Priority | Effort | Notes |
|-----------|----------|--------|-------|
| Version comparison | P1 | Small | Side-by-side diff |
| Batch processing | P2 | Medium | Process multiple items |

### ❌ Not Started (Ecosystem Integration)

| Component | Priority | Effort | Notes |
|-----------|----------|--------|-------|
| **entityspine dependency** | P1 | Small | Optional import for Result[T], ExecutionContext |
| **Error classification** | P1 | Small | Use EntitySpine's ErrorCategory |
| **spine-core patterns** | P2 | Medium | Pipeline base class, QualityRunner |
| **FeedSpine LLMEnricher** | P2 | Medium | Enricher using GenAI endpoints |
| Idempotency layer | P2 | Medium | Cache by content hash |
| Quality validation | P2 | Medium | Validate LLM outputs |

**See:** [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) for type mapping and patterns.

---

## Priority Breakdown

### P0 — Required for MVP ✅ COMPLETE

1. **~~Database integration~~** ✅ COMPLETE
   - [x] Protocol-based storage abstraction
   - [x] SQLite backend for development
   - [x] PostgreSQL backend for production
   - [x] Unit of Work pattern for transactions
   - [x] PromptRepository with full CRUD
   - [x] ExecutionRepository for tracking

2. **~~Rewrite capability~~** ✅ COMPLETE (for Message Enrichment)
   - [x] Add RewriteMode enum (CLEAN, FORMAT, ORGANIZE, etc.)
   - [x] rewrite_content() function
   - [x] Support multiple rewrite modes
   - [x] Wire up to `/v1/rewrite` endpoint

3. **~~Title inference capability~~** ✅ COMPLETE
   - [x] infer_title() function
   - [ ] Wire up to `/v1/infer-title` endpoint

4. **~~Tests setup~~** ✅ COMPLETE
   - [x] Create tests/ directory structure
   - [x] Add conftest.py with fixtures
   - [x] Unit tests for providers
   - [x] Unit tests for storage layer

5. **~~API Integration~~** ✅ COMPLETE
   - [x] Update main.py with storage lifecycle
   - [x] Add rewrite endpoint (`/v1/rewrite`)
   - [x] Add title endpoint (`/v1/infer-title`)
   - [x] Add commit endpoint (`/v1/generate-commit`)
   - [x] Add execute-prompt endpoint (`/v1/execute-prompt`)
   - [ ] Integration tests for API (remaining)

### P1 — Required for Production (Next 2 Weeks)

5. **Execution tracking**
   - [ ] Record every LLM call to executions table
   - [ ] Link to prompt_id and prompt_version
   - [ ] Track tokens, cost, latency
   - [ ] Add `/v1/executions` endpoint for history

6. **Cost tracking**
   - [ ] Aggregate daily costs by provider/model
   - [ ] Add cost estimation before execution
   - [ ] Budget enforcement (optional)
   - [ ] Add `/v1/usage` endpoint for stats

7. **Additional providers**
   - [ ] Anthropic provider (Claude)
   - [ ] Bedrock provider (AWS)
   - [ ] Provider health checks

8. **Pipeline execution** (for Enrichment Pipelines)
   - [ ] Pipeline data model (Pipeline, PipelineStep, PipelineRun)
   - [ ] Pipeline execution engine
   - [ ] Step registry with built-in steps
   - [ ] `/v1/pipelines` CRUD endpoints
   - [ ] `/v1/pipelines/{id}/execute` endpoint

9. **Streaming**
   - [ ] SSE streaming for chat completions
   - [ ] Streaming for long-running capabilities

### P2 — Nice to Have (Next Month)

10. **Caching**
    - [ ] Redis integration
    - [ ] Response caching with TTL
    - [ ] Cache invalidation

11. **Advanced capabilities**
    - [ ] Document comparison
    - [ ] Multi-document synthesis
    - [ ] Structured data extraction

12. **Observability**
    - [ ] Structured logging
    - [ ] Metrics endpoint
    - [ ] Tracing integration

---

## Feature: Rewrite Capability (P0)

**Supports:** Message Enrichment in Capture Spine

### API Design

```
POST /v1/rewrite

Request:
{
    "content": "original rambling text...",
    "mode": "clean",  // clean | format | organize | summarize
    "model": "llama3.2:latest",  // optional
    "provider": "ollama",  // optional
    "options": {
        "preserve_code_blocks": true,
        "include_context": ["previous message 1", "previous message 2"],
        "output_format": "markdown"
    }
}

Response:
{
    "original": "original rambling text...",
    "rewritten": "## Clean Version\n\nWell-organized content...",
    "changes_summary": "Fixed typos, organized into sections",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 200,
        "cost_usd": 0.0003
    }
}
```

### Rewrite Modes

| Mode | Prompt Focus | Use Case |
|------|--------------|----------|
| `clean` | Fix typos, grammar, clarity | Quick cleanup |
| `format` | Add markdown structure | Make readable |
| `organize` | Restructure into logical sections | Long messages |
| `summarize` | Condense to key points | Verbose content |

### Built-in Prompts

Need to add these to the default prompt library:

```yaml
- slug: rewrite-clean
  name: Clean & Fix
  system_prompt: |
    You are a helpful editor. Clean up the user's message by fixing typos,
    grammar, and improving clarity. Keep the original meaning intact.
  user_prompt_template: |
    Clean up this message:

    {{content}}

- slug: rewrite-format
  name: Format with Markdown
  system_prompt: |
    You are a helpful formatter. Add appropriate markdown structure to make
    the content more readable. Use headers, lists, and code blocks where appropriate.
  user_prompt_template: |
    Format this with markdown:

    {{content}}

- slug: rewrite-organize
  name: Organize into Sections
  system_prompt: |
    You are a helpful organizer. Restructure the content into logical sections
    with clear headers. Group related ideas together.
  user_prompt_template: |
    Organize this into logical sections:

    {{content}}
```

---

## Feature: Title Inference (P0)

**Supports:** Message Enrichment in Capture Spine

### API Design

```
POST /v1/infer-title

Request:
{
    "content": "long message content...",
    "max_length": 80,  // optional
    "style": "descriptive",  // descriptive | action | question
    "model": "llama3.2:latest"  // optional
}

Response:
{
    "title": "Message Enrichment Feature - LLM Rewrite Workflow",
    "alternatives": [
        "Implementing LLM-Based Message Cleanup",
        "Chat Message Rewriting System Design"
    ],
    "usage": {...}
}
```

---

## Feature: Pipeline Execution (P1)

**Supports:** Enrichment Pipelines in Capture Spine

### Data Model

```python
class Pipeline(Base):
    """Pipeline definition."""
    id: str
    name: str
    description: str
    status: str  # active | paused | draft
    trigger_config: dict  # What triggers this pipeline
    steps: list[PipelineStep]
    settings: dict
    created_at: datetime
    updated_at: datetime

class PipelineStep(Base):
    """Step in a pipeline."""
    id: str
    pipeline_id: str
    order: int
    step_type: str  # llm_rewrite | llm_summarize | extract | classify | ...
    name: str
    config: dict
    error_handling: str  # continue | stop | retry

class PipelineRun(Base):
    """Execution of a pipeline."""
    id: str
    pipeline_id: str
    status: str  # pending | running | completed | failed
    input_data: dict
    output_data: dict
    step_results: list[StepResult]
    started_at: datetime
    completed_at: datetime
    error: str | None
```

### Built-in Steps

| Step Type | Description | Config |
|-----------|-------------|--------|
| `llm_rewrite` | Rewrite content | mode, model, prompt_slug |
| `llm_summarize` | Summarize content | max_sentences, focus |
| `llm_extract` | Extract entities | entity_types, schema |
| `llm_classify` | Classify content | categories |
| `llm_custom` | Custom prompt | prompt_slug, variables |
| `condition` | Branch on condition | expression |
| `transform` | Transform data | jq_expression |
| `webhook` | Call external API | url, method |

### API Endpoints

```
# Pipeline CRUD
GET    /v1/pipelines
POST   /v1/pipelines
GET    /v1/pipelines/{id}
PUT    /v1/pipelines/{id}
DELETE /v1/pipelines/{id}

# Pipeline execution
POST   /v1/pipelines/{id}/execute
GET    /v1/pipelines/{id}/runs
GET    /v1/pipeline-runs/{run_id}
```

---

## Test Plan

### Directory Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_providers/
│   │   ├── test_base.py
│   │   ├── test_ollama.py
│   │   └── test_openai.py
│   ├── test_capabilities/
│   │   ├── test_summarization.py
│   │   ├── test_extraction.py
│   │   ├── test_classification.py
│   │   └── test_rewrite.py
│   └── test_storage/
│       └── test_models.py
├── integration/
│   ├── test_api/
│   │   ├── test_completions.py
│   │   ├── test_capabilities.py
│   │   ├── test_prompts.py
│   │   └── test_pipelines.py
│   └── test_providers/
│       └── test_ollama_live.py  # Requires running Ollama
└── fixtures/
    └── sample_prompts.yaml
```

### Coverage Targets

| Module | Target |
|--------|--------|
| providers/ | 80% |
| capabilities/ | 80% |
| api/routers/ | 70% |
| storage/ | 70% |

---

## Next Actions

1. **Today:**
   - [ ] Create tests/ directory with conftest.py
   - [ ] Wire up `/v1/rewrite` endpoint
   - [ ] Wire up `/v1/infer-title` endpoint
   - [ ] Wire up `/v1/generate-commit` endpoint

2. **This Week:**
   - [ ] Add lifespan handler to main.py for storage
   - [ ] Create `/v1/execute-prompt` for pipelines
   - [ ] Basic tests for new endpoints

3. **Next Week:**
   - [ ] Execution tracking
   - [ ] Cost aggregation
   - [ ] Pipeline model and basic execution

---

## 🌐 Ecosystem Integration Roadmap

See [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) for full details.

### Phase 2: FeedSpine Support (Week 2)

| Task | Endpoint | Priority |
|------|----------|----------|
| LLMEnricher class | `/v1/enrich` | P1 |
| Story clustering | `/v1/cluster-stories` | P1 |
| Semantic dedup | `/v1/check-duplicate` | P2 |

### Phase 3: Spine-Core Support (Week 3)

| Task | Endpoint | Priority |
|------|----------|----------|
| Quality explanation | `/v1/explain-failure` | P2 |
| Error diagnosis | `/v1/diagnose-error` | P3 |

### Phase 4: EntitySpine Support (Week 4)

| Task | Endpoint | Priority |
|------|----------|----------|
| Entity disambiguation | `/v1/disambiguate` | P2 |
| Identifier suggestion | `/v1/suggest-identifier` | P3 |

---

## References

- [GENAI_SERVICE_DESIGN.md](GENAI_SERVICE_DESIGN.md) — Full architecture design
- [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) — Full ecosystem integration guide
- [docs/CAPTURE_SPINE_INTEGRATION.md](docs/CAPTURE_SPINE_INTEGRATION.md) — Capture Spine specifics
- [prompts/PARALLEL_AGENT_PROMPT.md](prompts/PARALLEL_AGENT_PROMPT.md) — Agent guidance
- [docs/core/PROMPT_MANAGEMENT.md](docs/core/PROMPT_MANAGEMENT.md) — Prompt API details
- [docs/capabilities/](docs/capabilities/) — Capability tier documentation
- Capture Spine productivity features:
  - Message Enrichment — LLM rewrite/cleanup
  - Enrichment Pipelines — Automated multi-step workflows
