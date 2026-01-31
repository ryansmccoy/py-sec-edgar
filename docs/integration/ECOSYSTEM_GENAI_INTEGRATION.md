# Spine Ecosystem - Integration Opportunities

**Last Updated:** 2026-01-31
**Status:** Active Planning

This document maps the integration opportunities between GenAI Spine and other applications in the Spine ecosystem.

---

## 🗺️ Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  SPINE ECOSYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        GENAI-SPINE (Central AI)                          │   │
│  │                                                                          │   │
│  │  Endpoints: /v1/summarize, /v1/extract, /v1/classify, /v1/rewrite       │   │
│  │             /v1/infer-title, /v1/generate-commit, /v1/execute-prompt    │   │
│  │                                                                          │   │
│  │  Providers: Ollama (local) | OpenAI (cloud) | Anthropic (cloud)         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                          │
│       ┌───────────────────────────────┼───────────────────────────────┐         │
│       │                               │                               │         │
│       ▼                               ▼                               ▼         │
│  ┌──────────────┐            ┌──────────────┐            ┌──────────────┐       │
│  │  FEEDSPINE   │            │ CAPTURE-SPINE │           │  ENTITYSPINE │       │
│  │  (Ingestion) │            │  (Full Stack) │           │  (Domains)   │       │
│  ├──────────────┤            ├──────────────┤            ├──────────────┤       │
│  │ RSS feeds    │            │ Chat sessions │           │ Entity models│       │
│  │ SEC filings  │            │ Work sessions │           │ Result[T]    │       │
│  │ News articles│            │ Message enrich│           │ ExecutionCtx │       │
│  └──────────────┘            └──────────────┘            └──────────────┘       │
│       │                               │                               │         │
│       └───────────────────────────────┼───────────────────────────────┘         │
│                                       │                                          │
│                                       ▼                                          │
│                            ┌──────────────────┐                                  │
│                            │   SPINE-CORE     │                                  │
│                            │ (Orchestration)  │                                  │
│                            ├──────────────────┤                                  │
│                            │ Pipeline runner  │                                  │
│                            │ Quality checks   │                                  │
│                            │ Work manifests   │                                  │
│                            └──────────────────┘                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Integration Status Matrix

### By Application

| Application | Status | Priority | GenAI Endpoints Used |
|-------------|--------|----------|---------------------|
| **Capture Spine** | ✅ Ready | P0 | `/v1/rewrite`, `/v1/infer-title`, `/v1/generate-commit` |
| **FeedSpine** | 🟡 Planned | P1 | `/v1/summarize`, `/v1/classify`, `/v1/extract` |
| **EntitySpine** | 🟡 Planned | P2 | Type sharing (`Result[T]`, `ExecutionContext`) |
| **Spine-Core** | 🟡 Planned | P2 | Pipeline patterns, QualityRunner |
| **Market Spine** | 🔴 Future | P3 | Market analysis, sentiment |
| **py-sec-edgar** | 🔴 Future | P3 | Filing summarization, NER |

---

## 🔗 Detailed Integration Points

### 1. Capture Spine (Ready ✅)

| Feature | GenAI Endpoint | Status | Description |
|---------|---------------|--------|-------------|
| Message Enrichment | `/v1/rewrite` | ✅ | Clean, format, organize chat messages |
| Title Generation | `/v1/infer-title` | ✅ | Generate titles from conversation content |
| Work Session Commits | `/v1/generate-commit` | ✅ | Generate commit messages from session activity |
| Todo Extraction | `/v1/extract` | ✅ | Extract action items from messages |
| Conversation Summary | `/v1/summarize` | ✅ | Summarize long conversation threads |

**Example Integration:**
```python
# capture-spine/services/enrichment.py
from httpx import AsyncClient

genai = AsyncClient(base_url="http://genai-spine:8100")

async def enrich_message(content: str, mode: str = "clean") -> dict:
    response = await genai.post("/v1/rewrite", json={
        "content": content,
        "mode": mode
    })
    return response.json()
```

---

### 2. FeedSpine (Planned 🟡)

| Feature | GenAI Endpoint | Status | Description |
|---------|---------------|--------|-------------|
| Article Summarization | `/v1/summarize` | 🟡 | Summarize ingested articles |
| Content Classification | `/v1/classify` | 🟡 | Classify by topic, sentiment |
| Entity Extraction | `/v1/extract` | 🟡 | Extract companies, people, tickers |
| Story Clustering | `/v1/cluster` | 🔴 | Group related articles (new endpoint) |
| Deduplication | `/v1/dedupe` | 🔴 | Detect duplicate content (new endpoint) |

**Proposed Architecture:**
```python
# feedspine/enrichers/llm_enricher.py
class LLMEnricher(BaseEnricher):
    """Enrich feed items using GenAI Spine."""

    async def enrich(self, item: FeedItem) -> EnrichedItem:
        # Summarize
        summary = await self.genai.post("/v1/summarize", json={
            "content": item.content,
            "max_sentences": 3
        })

        # Classify
        classification = await self.genai.post("/v1/classify", json={
            "content": item.content,
            "categories": ["market", "earnings", "regulatory", "general"]
        })

        return EnrichedItem(
            **item.dict(),
            summary=summary["summary"],
            category=classification["classification"]
        )
```

---

### 3. EntitySpine (Planned 🟡)

**Type Sharing (No API calls):**
```python
# genai-spine uses entityspine's domain types
from entityspine.domain.workflow import Result, Ok, Err, ExecutionContext
from entityspine.domain.errors import ErrorCategory

# All GenAI capabilities return Result[T]
async def summarize(content: str) -> Result[Summary]:
    try:
        summary = await _call_llm(content)
        return Ok(summary)
    except LLMError as e:
        return Err(ErrorCategory.NETWORK, str(e))
```

| Type | Usage in GenAI Spine |
|------|---------------------|
| `Result[T]` | Explicit success/failure handling |
| `ExecutionContext` | Track LLM execution lineage |
| `ErrorCategory` | Smart retry logic (NETWORK=retry, CONFIG=don't) |

---

### 4. Spine-Core (Planned 🟡)

| Pattern | Usage in GenAI Spine |
|---------|---------------------|
| `Pipeline` | LLM calls as pipeline steps |
| `QualityRunner` | Validate LLM outputs |
| `IdempotencyHelper` | Cache by content hash |
| `WorkManifest` | Track batch LLM execution |

**Example:**
```python
# genai-spine/pipelines/enrichment_pipeline.py
from spine.framework import Pipeline, PipelineStep

class EnrichmentPipeline(Pipeline):
    steps = [
        SummarizeStep(),      # /v1/summarize
        ExtractEntitiesStep(), # /v1/extract
        ClassifyStep(),        # /v1/classify
    ]
```

---

## 🚀 Future Endpoints (Ecosystem-Driven)

Based on integration needs, these endpoints are planned:

| Endpoint | Priority | Requester | Description |
|----------|----------|-----------|-------------|
| `/v1/cluster-stories` | P1 | FeedSpine | Group related articles |
| `/v1/dedupe` | P1 | FeedSpine | Detect duplicate content |
| `/v1/compare` | P2 | Capture Spine | Compare document versions |
| `/v1/disambiguate` | P2 | EntitySpine | Entity disambiguation |
| `/v1/explain-failure` | P2 | Spine-Core | Explain pipeline failures |
| `/v1/validate` | P2 | Spine-Core | Validate data with LLM |

---

## 📋 Implementation Roadmap

### Phase 1: Core Integration (Current)
- ✅ GenAI Spine v0.1.0 released
- ✅ Capture Spine endpoints ready
- 🟡 FeedSpine adapters in progress

### Phase 2: Type Sharing (Next 2 weeks)
- [ ] Add entityspine as optional dependency
- [ ] Implement Result[T] pattern in capabilities
- [ ] Add ExecutionContext tracking

### Phase 3: Pipeline Integration (Next month)
- [ ] Integrate with spine-core Pipeline
- [ ] Add batch processing support
- [ ] Implement QualityRunner for LLM validation

### Phase 4: Advanced Features (Q2 2026)
- [ ] Story clustering for FeedSpine
- [ ] Document comparison
- [ ] Streaming support
- [ ] RAG integration

---

## 🔧 Configuration

### Environment Variables
```bash
# GenAI Spine configuration
GENAI_API_HOST=0.0.0.0
GENAI_API_PORT=8100
GENAI_DEFAULT_PROVIDER=ollama
GENAI_DEFAULT_MODEL=llama3.2:latest
GENAI_OLLAMA_URL=http://localhost:11434
GENAI_OPENAI_API_KEY=sk-...
GENAI_ANTHROPIC_API_KEY=sk-ant-...

# For other apps to connect
GENAI_SPINE_URL=http://localhost:8100
```

### Docker Compose (Multi-Service)
```yaml
services:
  genai-spine:
    build: ./genai-spine
    ports:
      - "8100:8100"
    environment:
      - GENAI_OLLAMA_URL=http://ollama:11434

  capture-spine:
    build: ./capture-spine
    environment:
      - GENAI_SPINE_URL=http://genai-spine:8100
    depends_on:
      - genai-spine
```

---

## 📚 Related Documents

| Document | Description |
|----------|-------------|
| [genai-spine/STATUS.md](../genai-spine/STATUS.md) | Current GenAI Spine status |
| [genai-spine/CHANGELOG.md](../genai-spine/CHANGELOG.md) | Version history |
| [genai-spine/docs/ECOSYSTEM_INTEGRATION.md](../genai-spine/docs/ECOSYSTEM_INTEGRATION.md) | Detailed integration guide |
| [genai-spine/docs/CAPTURE_SPINE_INTEGRATION.md](../genai-spine/docs/CAPTURE_SPINE_INTEGRATION.md) | Capture Spine mapping |
