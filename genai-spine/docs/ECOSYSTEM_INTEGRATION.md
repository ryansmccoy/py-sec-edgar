# GenAI Spine - Full Ecosystem Integration Guide

**Last Updated**: 2026-01-31
**Status**: Active Development

This document tracks GenAI Spine's integration opportunities across the **entire Spine ecosystem**, not just Capture Spine. Use this as your reference for building features that serve multiple projects.

---

## 🗺️ Ecosystem Map

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           GENAI SPINE - CENTRAL AI SERVICE                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  Capabilities: /v1/summarize, /v1/extract, /v1/classify, /v1/rewrite, /v1/generate-commit│
│                                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐                  │
│  │    ENTITYSPINE    │   │     FEEDSPINE     │   │    SPINE-CORE     │                  │
│  │   Domain Models   │   │  Feed Ingestion   │   │   Orchestration   │                  │
│  ├───────────────────┤   ├───────────────────┤   ├───────────────────┤                  │
│  │ • ExtractionType  │   │ • LLMEnricher     │   │ • QualityRunner   │                  │
│  │ • StoryCluster    │   │ • StoryClusterer  │   │ • LLM Validation  │                  │
│  │ • SignificanceScore│  │ • DedupIntelligence│  │ • Explanation Gen │                  │
│  │ • ChatMessage     │   │ • ContentClassify │   │ • Error Analysis  │                  │
│  └─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘                  │
│            │                       │                       │                             │
│            └───────────────────────┼───────────────────────┘                             │
│                                    │                                                     │
│                                    ▼                                                     │
│                        ┌───────────────────────────┐                                     │
│                        │      CAPTURE-SPINE        │                                     │
│                        │    Full Stack App         │                                     │
│                        ├───────────────────────────┤                                     │
│                        │ • Message Enrichment      │                                     │
│                        │ • Work Sessions           │                                     │
│                        │ • Pipelines               │                                     │
│                        │ • Knowledge Base          │                                     │
│                        └───────────────────────────┘                                     │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Integration Matrix by Project

### Required GenAI Capabilities

| Project | Capability | GenAI Endpoint | Status | Priority |
|---------|-----------|----------------|--------|----------|
| **ENTITYSPINE** | | | | |
| | Entity disambiguation | `/v1/disambiguate` | 🔴 New | P2 |
| | Identifier suggestion | `/v1/suggest-identifier` | 🔴 New | P3 |
| **FEEDSPINE** | | | | |
| | Content enrichment | `/v1/enrich` | 🔴 New | P1 |
| | Story clustering | `/v1/cluster-stories` | 🔴 New | P1 |
| | Dedup intelligence | `/v1/check-duplicate` | 🔴 New | P2 |
| | Content classification | `/v1/classify` | ✅ Exists | - |
| | Entity extraction | `/v1/extract` | ✅ Exists | - |
| **SPINE-CORE** | | | | |
| | Quality explanation | `/v1/explain-failure` | 🔴 New | P2 |
| | Data validation | `/v1/validate` | 🔴 New | P2 |
| | Error diagnosis | `/v1/diagnose-error` | 🔴 New | P3 |
| **CAPTURE-SPINE** | | | | |
| | Message rewrite | `/v1/rewrite` | ✅ Complete | - |
| | Title inference | `/v1/infer-title` | ✅ Complete | - |
| | Commit generation | `/v1/generate-commit` | ✅ Complete | - |
| | Todo extraction | `/v1/extract` | ✅ Exists | - |
| | Summarization | `/v1/summarize` | ✅ Exists | - |

---

## 🧱 Foundation Types (Reuse, Don't Reinvent)

### From entityspine (stdlib-only, always safe)

```python
# Import these instead of creating custom types
from entityspine.domain.workflow import (
    ExecutionContext,      # Track LLM execution lineage
    new_execution_context, # Factory for root contexts
    Result, Ok, Err,       # Explicit success/failure
    TaskStatus,            # PENDING, RUNNING, COMPLETED, FAILED
    WorkflowStatus,        # Pipeline-level status
    QualityStatus,         # PASS, WARN, FAIL
)
from entityspine.domain.errors import (
    ErrorCategory,         # NETWORK, DATABASE, PARSE, VALIDATION, etc.
    ErrorContext,          # Rich error metadata
)
```

**Key Benefits:**
- `ExecutionContext.child()` creates linked sub-contexts for tracing
- `Result[T]` forces explicit error handling (no silent exceptions)
- `ErrorCategory` enables smart retry logic (NETWORK=retry, CONFIG=don't)

### From spine-core (pipeline infrastructure)

```python
# Import when building LLM pipelines
from spine.framework import Pipeline, PipelineResult, PipelineStatus
from spine.core import (
    QualityRunner,         # Validate LLM outputs
    WorkManifest,          # Track batch execution state
    IdempotencyHelper,     # Cache by input hash
    compute_hash,          # Deterministic content hashing
)
```

**Why spine-core for LLM Pipelines:**
- LLM calls ARE pipelines: input → transform → output
- `QualityRunner` can validate LLM responses (format, hallucination)
- `IdempotencyHelper` caches responses (same prompt = same response)

### Optional Dependency Pattern

```toml
# genai-spine/pyproject.toml
[project.optional-dependencies]
ecosystem = ["entityspine>=0.3.0", "spine-core>=0.1.0"]
```

```python
# genai_spine/compat.py
try:
    from entityspine.domain.workflow import Result, Ok, Err, ExecutionContext
    from entityspine.domain.errors import ErrorCategory, ErrorContext
    HAS_ECOSYSTEM = True
except ImportError:
    # Fallback: compatible local types
    from genai_spine._types import Result, Ok, Err, ExecutionContext
    from genai_spine._types import ErrorCategory, ErrorContext
    HAS_ECOSYSTEM = False
```

---

## 1️⃣ ENTITYSPINE Integration

### Current State
EntitySpine provides stdlib-only domain models used across the ecosystem:
- `ExtractionType`, `ExtractedEntity` - NER types
- `StoryCluster`, `SignificanceScore` - Content intelligence
- `ChatWorkspace`, `ChatSession`, `ChatMessage` - Chat models
- **NEW**: `ExecutionContext`, `Result[T]`, `ErrorCategory` - Workflow types

### Opportunity: Entity Disambiguation

When resolving entities from text, sometimes the same name refers to different things:
- "Apple" → Apple Inc. (AAPL) vs Apple Records
- "Amazon" → Amazon.com (AMZN) vs Amazon River

**Proposed Endpoint:**
```
POST /v1/disambiguate
{
  "text": "Apple reported strong iPhone sales",
  "candidates": [
    {"entity_id": "aapl", "name": "Apple Inc.", "type": "COMPANY"},
    {"entity_id": "apple_records", "name": "Apple Records", "type": "COMPANY"}
  ],
  "context": "financial news"
}

Response:
{
  "selected_entity_id": "aapl",
  "confidence": 0.98,
  "reasoning": "Context mentions iPhone sales, a product of Apple Inc."
}
```

**EntitySpine Integration Point:**
```python
# entityspine/domain/resolution.py could use this
from genai_spine import GenAIClient

client = GenAIClient()
result = client.disambiguate(
    text=mention.text,
    candidates=entity_candidates,
    context=document_context
)
```

### Opportunity: Identifier Suggestion

When an entity lacks standard identifiers (CUSIP, LEI, etc.), suggest likely matches:

```
POST /v1/suggest-identifier
{
  "entity_name": "Berkshire Hathaway",
  "entity_type": "COMPANY",
  "known_identifiers": {"CIK": "0001067983"}
}

Response:
{
  "suggestions": [
    {"type": "CUSIP", "value": "084670702", "confidence": 0.95},
    {"type": "LEI", "value": "5493002QMJ4FVQKRFU59", "confidence": 0.90}
  ]
}
```

---

## 2️⃣ FEEDSPINE Integration

### Current State
FeedSpine has an enricher system with Bronze → Silver → Gold medallion architecture:
- `PassthroughEnricher` - Basic promotion
- `MetadataEnricher` - Add metadata fields
- `EntityEnricher` - Link to entityspine entities

### 🎯 HIGH PRIORITY: LLMEnricher

**New enricher that calls GenAI Spine for content intelligence:**

```python
# feedspine/enricher/llm_enricher.py

from feedspine.protocols.enricher import EnrichmentResult, EnrichmentStatus
from feedspine.models.record import Record

class LLMEnricher:
    """
    Enricher that uses GenAI Spine for content intelligence.

    Supports multiple enrichment modes:
    - extract: Pull entities from content
    - classify: Categorize content
    - summarize: Create summary
    - cluster: Assign to story cluster
    """

    def __init__(
        self,
        genai_url: str = "http://localhost:8100",
        modes: list[str] = ["extract", "classify"],
    ):
        self.genai_url = genai_url
        self.modes = modes

    async def enrich(self, record: Record) -> EnrichmentResult:
        """Enrich record using GenAI Spine."""
        import httpx

        async with httpx.AsyncClient() as client:
            enrichments = {}

            if "extract" in self.modes:
                resp = await client.post(
                    f"{self.genai_url}/v1/extract",
                    json={"text": record.content, "types": ["COMPANY", "PERSON"]}
                )
                enrichments["entities"] = resp.json()["entities"]

            if "classify" in self.modes:
                resp = await client.post(
                    f"{self.genai_url}/v1/classify",
                    json={"text": record.content}
                )
                enrichments["category"] = resp.json()["category"]

            if "summarize" in self.modes:
                resp = await client.post(
                    f"{self.genai_url}/v1/summarize",
                    json={"text": record.content, "max_sentences": 2}
                )
                enrichments["summary"] = resp.json()["summary"]

            # Store enrichments in record metadata
            record.metadata.extra["llm_enrichment"] = enrichments

            return EnrichmentResult(
                record_id=record.id,
                status=EnrichmentStatus.SUCCESS,
                enricher_name="LLMEnricher",
                source_layer=record.layer,
                target_layer=record.layer,
                fields_added=list(enrichments.keys()),
            )
```

### Opportunity: Story Clustering

Group related articles into story clusters using LLM understanding:

```
POST /v1/cluster-stories
{
  "articles": [
    {"id": "a1", "title": "Apple announces iPhone 16", "content": "..."},
    {"id": "a2", "title": "iPhone pre-orders break records", "content": "..."},
    {"id": "a3", "title": "Tesla Q3 earnings miss", "content": "..."}
  ],
  "existing_clusters": [
    {"id": "c1", "name": "Apple Product Launch", "article_ids": ["a0"]}
  ]
}

Response:
{
  "assignments": [
    {"article_id": "a1", "cluster_id": "c1", "confidence": 0.95},
    {"article_id": "a2", "cluster_id": "c1", "confidence": 0.92},
    {"article_id": "a3", "cluster_id": "new", "suggested_name": "Tesla Q3 Earnings"}
  ]
}
```

**FeedSpine Integration:**
```python
# feedspine/enricher/story_clusterer.py

class StoryClusterer:
    """Assign articles to story clusters using GenAI."""

    async def cluster(self, records: list[Record], existing_clusters: list[dict]):
        resp = await self.client.post(
            f"{self.genai_url}/v1/cluster-stories",
            json={
                "articles": [{"id": r.id, "title": r.title, "content": r.content} for r in records],
                "existing_clusters": existing_clusters
            }
        )
        return resp.json()["assignments"]
```

### Opportunity: Intelligent Deduplication

FeedSpine already does content-hash deduplication, but LLM can catch semantic duplicates:

```
POST /v1/check-duplicate
{
  "new_article": {
    "title": "Apple's new iPhone breaks sales records",
    "content": "Apple Inc. announced today..."
  },
  "candidates": [
    {"id": "existing1", "title": "iPhone sales exceed expectations", "content": "..."}
  ]
}

Response:
{
  "is_duplicate": true,
  "duplicate_of": "existing1",
  "confidence": 0.87,
  "relationship": "same_event",  // or "follow_up", "angle_shift"
  "reasoning": "Both articles report iPhone sales success from same announcement"
}
```

---

## 3️⃣ SPINE-CORE Integration

### Current State
Spine-core provides pipeline infrastructure:
- `QualityRunner` - Execute quality checks
- `ExecutionContext` - Track pipeline lineage
- `Result[T]` - Explicit error handling

### Opportunity: LLM Quality Explanations

When a quality check fails, explain WHY in human terms:

```
POST /v1/explain-failure
{
  "check_name": "market_share_sum",
  "expected": 100.0,
  "actual": 87.3,
  "context": {
    "entity": "FINRA ATS",
    "period": "2026-W04",
    "records": [
      {"venue": "IEX", "share": 45.2},
      {"venue": "NASDAQ", "share": 42.1}
    ]
  }
}

Response:
{
  "explanation": "Market share total of 87.3% indicates missing venue data. Only 2 venues reported (IEX, NASDAQ) when typically 5-8 venues are expected for FINRA ATS data.",
  "likely_causes": [
    "Missing BATS/EDGX venue data",
    "Incomplete data ingestion for week 2026-W04",
    "Source API may have had outage"
  ],
  "suggested_actions": [
    "Check source API status for 2026-W04",
    "Verify all expected venues are configured",
    "Review ingestion logs for errors"
  ]
}
```

**Spine-Core Integration:**
```python
# spine/core/quality.py

class QualityRunner:
    def __init__(self, conn, genai_url: str | None = None):
        self.conn = conn
        self.genai_url = genai_url

    def run_check(self, check: QualityCheck, ctx: dict) -> QualityResult:
        result = check.check_fn(ctx)

        # If failed and GenAI available, get explanation
        if result.status == QualityStatus.FAIL and self.genai_url:
            explanation = self._get_explanation(check, result, ctx)
            result.llm_explanation = explanation

        return result
```

### Opportunity: Error Diagnosis

When pipelines fail, diagnose the error:

```
POST /v1/diagnose-error
{
  "error_type": "ConnectionError",
  "error_message": "Connection refused: localhost:5432",
  "stack_trace": "...",
  "context": {
    "pipeline": "finra_ats_ingest",
    "step": "load_to_postgres",
    "environment": "development"
  }
}

Response:
{
  "diagnosis": "PostgreSQL database is not running or not accessible",
  "root_cause": "Database service unavailable",
  "fix_steps": [
    "1. Check if PostgreSQL is running: `pg_isready -h localhost -p 5432`",
    "2. If not running: `docker-compose up -d postgres`",
    "3. Verify connection string in config"
  ],
  "related_errors": ["similar errors seen in 15% of pipeline runs this week"]
}
```

---

## 4️⃣ CAPTURE-SPINE Integration

See: [CAPTURE_SPINE_INTEGRATION.md](./CAPTURE_SPINE_INTEGRATION.md) for detailed specs.

**Summary of capabilities (✅ = implemented in GenAI):**
| Capability | Endpoint | Status |
|------------|----------|--------|
| Message Rewrite | `/v1/rewrite` | ✅ |
| Title Inference | `/v1/infer-title` | ✅ |
| Commit Generation | `/v1/generate-commit` | ✅ |
| Entity Extraction | `/v1/extract` | ✅ |
| Classification | `/v1/classify` | ✅ |
| Summarization | `/v1/summarize` | ✅ |
| Pipeline Execution | `/v1/execute-prompt` | 🔴 Needed |

---

## 🔧 Implementation Priority

### Phase 1: Wire Up Existing (This Week)
All capabilities are coded, just need API endpoints:

1. **`/v1/rewrite`** - Wire `capabilities/rewrite.py`
2. **`/v1/infer-title`** - Wire `capabilities/rewrite.py`
3. **`/v1/generate-commit`** - Wire `capabilities/commit.py`

### Phase 2: FeedSpine Integration (Week 2)
High value for content pipelines:

4. **`LLMEnricher`** - New feedspine enricher
5. **`/v1/cluster-stories`** - Story clustering endpoint
6. **`/v1/check-duplicate`** - Semantic dedup endpoint

### Phase 3: Spine-Core Integration (Week 3)
Pipeline intelligence:

7. **`/v1/explain-failure`** - Quality check explanation
8. **`/v1/diagnose-error`** - Error diagnosis

### Phase 4: EntitySpine Integration (Week 4)
Entity resolution enhancement:

9. **`/v1/disambiguate`** - Entity disambiguation
10. **`/v1/suggest-identifier`** - Identifier suggestions

---

## 📦 Shared Prompts

Create prompts in `genai-spine/prompts/` that serve multiple projects:

### `prompts/entity-extraction.yaml`
```yaml
slug: entity-extraction
name: Entity Extraction
system_prompt: |
  You are an entity extraction system for financial content.
  Extract entities of the specified types from the text.
  Return structured JSON with entity text, type, and confidence.
variables:
  - text
  - types
used_by:
  - feedspine.LLMEnricher
  - capture-spine.enrichment
```

### `prompts/story-clustering.yaml`
```yaml
slug: story-clustering
name: Story Clustering
system_prompt: |
  You analyze news articles and group them into story clusters.
  A story cluster represents a developing news event or topic.
  Articles about the same event should be in the same cluster.
variables:
  - articles
  - existing_clusters
used_by:
  - feedspine.StoryClusterer
```

### `prompts/quality-explanation.yaml`
```yaml
slug: quality-explanation
name: Quality Check Explanation
system_prompt: |
  You are a data quality expert. Explain why a data quality check failed
  and suggest likely causes and remediation steps.
variables:
  - check_name
  - expected
  - actual
  - context
used_by:
  - spine-core.QualityRunner
```

---

## 🔗 Cross-Project Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        GENAI-POWERED DATA FLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. INGESTION (FeedSpine)                                                   │
│     │                                                                       │
│     │  RSS Feed → Record (Bronze)                                          │
│     │      │                                                               │
│     │      ├── /v1/extract → entities                                      │
│     │      ├── /v1/classify → category                                     │
│     │      └── /v1/cluster-stories → story_id                              │
│     │                                                                       │
│     └── Record (Silver) with enrichments                                    │
│                                                                             │
│  2. STORAGE (Capture-Spine)                                                 │
│     │                                                                       │
│     │  Record (Silver) → PostgreSQL                                         │
│     │      │                                                               │
│     │      ├── /v1/summarize → display summary                             │
│     │      └── Entity linking via EntitySpine                              │
│     │                                                                       │
│     └── Record (Gold) ready for display                                     │
│                                                                             │
│  3. QUALITY (Spine-Core)                                                    │
│     │                                                                       │
│     │  QualityRunner checks data                                            │
│     │      │                                                               │
│     │      └── /v1/explain-failure → human-readable explanation            │
│     │                                                                       │
│     └── Quality report with explanations                                    │
│                                                                             │
│  4. DISPLAY (Trading-Desktop)                                               │
│     │                                                                       │
│     │  News widget shows enriched records                                   │
│     │  Alerts show quality failures with explanations                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 TODO for GenAI Agent

### Immediate (Wire up existing code)
- [ ] Create `/v1/rewrite` endpoint in `api/routers/`
- [ ] Create `/v1/infer-title` endpoint
- [ ] Create `/v1/generate-commit` endpoint
- [ ] Add lifespan handler to main.py for storage

### Next Sprint (FeedSpine support)
- [ ] Design `/v1/enrich` unified enrichment endpoint
- [ ] Design `/v1/cluster-stories` endpoint
- [ ] Design `/v1/check-duplicate` endpoint
- [ ] Create `prompts/story-clustering.yaml`

### Future (Spine-Core, EntitySpine)
- [ ] Design `/v1/explain-failure` endpoint
- [ ] Design `/v1/diagnose-error` endpoint
- [ ] Design `/v1/disambiguate` endpoint
- [ ] Create prompts for each capability

---

## References

- [CAPTURE_SPINE_INTEGRATION.md](./CAPTURE_SPINE_INTEGRATION.md) - Detailed Capture Spine specs
- [capture-spine/docs/features/productivity/](../../capture-spine/docs/features/productivity/) - Feature requirements
- [feedspine/src/feedspine/enricher/](../../feedspine/src/feedspine/enricher/) - Enricher implementations
- [spine-core/packages/spine-core/src/spine/core/quality.py](../../spine-core/packages/spine-core/src/spine/core/quality.py) - Quality framework
- [entityspine/src/entityspine/domain/extraction.py](../../entityspine/src/entityspine/domain/extraction.py) - Extraction models
- [docs/architecture/ECOSYSTEM.md](../../docs/architecture/ECOSYSTEM.md) - Ecosystem overview
