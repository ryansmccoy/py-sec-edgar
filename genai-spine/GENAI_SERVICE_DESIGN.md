# GenAI Spine - Unified AI Service Design Document

**Date**: January 30, 2026
**Version**: 1.0.0
**Status**: Planning

---

## Executive Summary

**GenAI Spine** is a standalone, Dockerized generative AI service that provides a unified API for all LLM/AI capabilities across the Spine ecosystem. It consolidates all GenAI logic from Capture Spine into a reusable microservice that can be consumed by:

- **Capture Spine** - News/feed capture, article enrichment, chat
- **EntitySpine** - Entity resolution, relationship extraction, knowledge graph enrichment
- **FeedSpine** - Feed categorization, content summarization, deduplication
- **Market Spine** - Financial analysis, sentiment scoring, report generation

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Architecture Tiers](#architecture-tiers)
3. [Capabilities Matrix](#capabilities-matrix)
4. [Project Structure](#project-structure)
5. [API Design](#api-design)
6. [Implementation Roadmap](#implementation-roadmap)

---

## Current State Analysis

### Existing LLM Infrastructure in Capture Spine

```
capture-spine/app/llm/
├── providers/
│   ├── base.py         # Abstract LLM provider interface
│   ├── openai.py       # GPT-4o, GPT-4o-mini
│   ├── anthropic.py    # Claude Sonnet, Haiku
│   ├── bedrock.py      # AWS Bedrock (Claude, Nova)
│   └── ollama.py       # Local models (Llama, Qwen, Mistral)
├── prompts.py          # Prompt templates
├── cost.py             # Token counting & cost tracking
└── types.py            # Request/response models
```

### What Exists Today

| Capability | Status | Location |
|------------|--------|----------|
| Multi-provider support (OpenAI, Anthropic, Bedrock, Ollama) | ✅ Complete | `app/llm/providers/` |
| Cost tracking per token/model | ✅ Complete | `app/llm/cost.py` |
| Prompt template CRUD | ✅ Complete | `prompts` table + API |
| Prompt versioning | ✅ Complete | `prompt_versions` table |
| Transform API | ✅ Complete | `/api/llm/transform` |
| Chat conversations | ✅ Complete | `/api/v2/chat/` |
| Feed categorization | ✅ Complete | `/api/semantic/` |
| Entity extraction (basic) | 🟡 Partial | `app/features/intelligence/` |
| Significance scoring | 🟡 Partial | `app/features/intelligence/` |
| SSE Streaming | 🔴 Planned | Documented in specs |

### What Other Spines Need

| Spine | AI Needs |
|-------|----------|
| **EntitySpine** | Entity disambiguation, relationship extraction, person-company linking |
| **FeedSpine** | Content summarization, duplicate detection, topic classification |
| **Market Spine** | Sentiment analysis, earnings call parsing, financial metrics extraction |
| **Capture Spine** | All of above + chat, search, alerts |

---

## Architecture Tiers

### 🟢 Tier 1: Basic (Ollama-Only, Self-Hosted)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │   GenAI Spine    │────▶│           Ollama                 │  │
│  │   (FastAPI)      │     │   llama3.2 / qwen2.5 / mistral  │  │
│  │   Port: 8100     │     │   Port: 11434                    │  │
│  └──────────────────┘     └──────────────────────────────────┘  │
│           │                                                      │
│           ▼                                                      │
│  ┌──────────────────┐                                           │
│  │    SQLite        │  (prompts, history, costs)                │
│  │    ./data/       │                                           │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘

Features:
- Zero external API costs
- ~8GB GPU VRAM for small models
- Good for development & testing
- 50-100 tokens/sec on modern GPU
```

**Best For**: Development, testing, privacy-sensitive deployments

---

### 🟡 Tier 2: Intermediate (Multi-Provider)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Docker Compose Stack                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │   GenAI Spine    │                                                   │
│  │   (FastAPI)      │                                                   │
│  │   Port: 8100     │                                                   │
│  └────────┬─────────┘                                                   │
│           │                                                              │
│     ┌─────┴─────┬─────────────┬─────────────┐                          │
│     ▼           ▼             ▼             ▼                          │
│  ┌──────┐  ┌────────┐  ┌──────────┐  ┌───────────┐                    │
│  │Ollama│  │OpenAI  │  │Anthropic │  │ Bedrock   │                    │
│  │Local │  │API     │  │API       │  │ (AWS)     │                    │
│  └──────┘  └────────┘  └──────────┘  └───────────┘                    │
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐                         │
│  │   PostgreSQL     │     │      Redis       │                         │
│  │   (state/prompts)│     │   (cache/queue)  │                         │
│  └──────────────────┘     └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘

Features:
- Intelligent routing (cost vs speed vs quality)
- Fallback chains (Ollama → OpenAI → Anthropic)
- Caching layer (Redis)
- Rate limiting per provider
- Cost tracking & budgets
```

**Best For**: Production deployments, cost-conscious usage

---

### 🔴 Tier 3: Advanced (Full Platform)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Kubernetes / ECS Cluster                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         API Gateway / Load Balancer                     │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                    │                                │                        │
│            ┌───────┴───────┐              ┌────────┴────────┐               │
│            ▼               ▼              ▼                 ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  GenAI API   │  │  GenAI API   │  │  SSE Worker  │  │  Batch Worker│    │
│  │  Instance 1  │  │  Instance 2  │  │  (streaming) │  │  (bulk ops)  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│            │               │                  │                │            │
│            └───────────────┼──────────────────┼────────────────┘            │
│                            ▼                  ▼                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Provider Router                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────────┐ │  │
│  │  │ Ollama  │  │ OpenAI  │  │Anthropic│  │ Bedrock │  │ Groq/Gemini│ │  │
│  │  │ (GPU)   │  │ (fast)  │  │ (smart) │  │ (AWS)   │  │ (fallback) │ │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────────┐│
│  │  PostgreSQL    │  │  Redis Cluster │  │  S3 / MinIO (artifacts)       ││
│  │  (RDS/Aurora)  │  │  (ElastiCache) │  │  (embeddings, exports)        ││
│  └────────────────┘  └────────────────┘  └────────────────────────────────┘│
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Vector Store (pgvector / Pinecone)                 │  │
│  │                    For RAG & Semantic Search                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘

Features:
- Horizontal scaling
- SSE streaming workers
- Batch processing queue
- Vector store for RAG
- Multi-region failover
- Audit logging
- A/B testing prompts
```

**Best For**: Enterprise, high-volume, mission-critical

---

### 🚀 Tier 4: Mind-Blowing (Agentic + Knowledge Graph)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS AGENT PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Agent Orchestrator                                │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │ │
│  │  │ Research    │  │ Analysis    │  │ Report      │  │ Trade Signal    │   │ │
│  │  │ Agent       │  │ Agent       │  │ Generator   │  │ Agent           │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘   │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                          Tool Registry                                      │ │
│  │  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌─────────────────────┐    │ │
│  │  │ SEC EDGAR │  │ Entity    │  │ Market     │  │ External APIs       │    │ │
│  │  │ Tools     │  │ Resolver  │  │ Data Tools │  │ (News, Filings...)  │    │ │
│  │  └───────────┘  └───────────┘  └────────────┘  └─────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │                     Knowledge Graph (Neo4j)                                 │ │
│  │  Companies ←→ People ←→ Filings ←→ Events ←→ Prices ←→ Sentiment          │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐ │
│  │              Real-Time Event Stream (Kafka / NATS)                          │ │
│  │  [filing_detected] → [entity_resolved] → [sentiment_scored] → [alert_sent] │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│  Mind-Blowing Features:                                                         │
│  • Autonomous research agents that monitor SEC filings 24/7                    │
│  • Cross-entity relationship discovery ("Who's connected to this insider?")    │
│  • Predictive alerts ("Similar filings preceded 10%+ moves")                   │
│  • Natural language queries ("What did Apple executives say about AI?")        │
│  • Auto-generated investment memos with citations                               │
│  • Multi-step reasoning chains with full audit trail                           │
│  • Real-time knowledge graph updates as new filings arrive                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Capabilities Matrix

### By Complexity Level

#### 🟢 BASIC (5 Capabilities)

| # | Capability | Description | Use Case |
|---|------------|-------------|----------|
| 1 | **Text Completion** | Basic prompt → response | Freeform questions, simple tasks |
| 2 | **Text Summarization** | Long text → concise summary | Article digests, filing summaries |
| 3 | **Text Classification** | Content → category | Topic assignment, sentiment (pos/neg/neutral) |
| 4 | **Key Point Extraction** | Document → bullet points | Meeting notes, report highlights |
| 5 | **Template Fill** | Template + variables → formatted output | Email drafts, report sections |

#### 🟡 INTERMEDIATE (5 Capabilities)

| # | Capability | Description | Use Case |
|---|------------|-------------|----------|
| 6 | **Entity Extraction (NER)** | Text → structured entities | Company names, people, dates, amounts |
| 7 | **Sentiment Analysis** | Content → scored sentiment | News sentiment, earnings call tone |
| 8 | **Question Answering** | Context + question → answer | Research queries over documents |
| 9 | **Semantic Search** | Query → similar documents | Find related filings, articles |
| 10 | **Content Tagging** | Document → relevant tags | Auto-categorization, topic discovery |

#### 🔴 ADVANCED (5 Capabilities)

| # | Capability | Description | Use Case |
|---|------------|-------------|----------|
| 11 | **Document Comparison** | Doc A + Doc B → diff analysis | 10-K year-over-year changes |
| 12 | **Relationship Extraction** | Text → entity relationships | Build knowledge graphs |
| 13 | **Multi-Document Synthesis** | Multiple docs → unified analysis | Research compilation |
| 14 | **Structured Data Extraction** | Unstructured → JSON/tables | Parse tables from PDFs, extract financials |
| 15 | **Chain-of-Thought Reasoning** | Complex query → reasoned answer | Investment thesis analysis |

#### 🚀 MIND-BLOWING (5 Capabilities)

| # | Capability | Description | Use Case |
|---|------------|-------------|----------|
| 16 | **Autonomous Agents** | Goal → multi-step execution | "Research NVDA's AI exposure" |
| 17 | **Knowledge Graph Queries** | Natural language → graph traversal | "Who are the common board members between X and Y?" |
| 18 | **Predictive Insights** | Historical patterns → forward-looking | "Similar filings preceded major moves" |
| 19 | **Real-Time Event Processing** | Stream → instant enrichment | Live filing alerts with entity resolution |
| 20 | **Report Generation** | Data + template → full document | Auto-generate investment memos |

---

## Project Structure

```
genai-spine/
├── docker-compose.yml           # Full stack (API + Ollama + DB)
├── docker-compose.dev.yml       # Development overrides
├── Dockerfile                   # API container
├── pyproject.toml              # Python dependencies
├── README.md                   # Quick start guide
├── Makefile                    # Common commands
│
├── src/
│   └── genai_spine/
│       ├── __init__.py
│       ├── main.py             # FastAPI app entry
│       ├── settings.py         # Pydantic settings
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py          # FastAPI app factory
│       │   ├── deps.py         # Dependency injection
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── health.py           # /health, /ready
│       │       ├── completions.py      # /v1/completions
│       │       ├── chat.py             # /v1/chat/completions (OpenAI-compatible)
│       │       ├── summarize.py        # /v1/summarize
│       │       ├── extract.py          # /v1/extract (entities, key points)
│       │       ├── classify.py         # /v1/classify
│       │       ├── embeddings.py       # /v1/embeddings
│       │       ├── prompts.py          # /v1/prompts (CRUD)
│       │       ├── models.py           # /v1/models (list available)
│       │       └── agents.py           # /v1/agents (advanced)
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py       # Configuration management
│       │   ├── logging.py      # Structured logging
│       │   └── exceptions.py   # Custom exceptions
│       │
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract provider interface
│       │   ├── registry.py     # Provider registration
│       │   ├── router.py       # Intelligent routing logic
│       │   ├── ollama.py       # Ollama client
│       │   ├── openai.py       # OpenAI client
│       │   ├── anthropic.py    # Anthropic client
│       │   ├── bedrock.py      # AWS Bedrock client
│       │   └── groq.py         # Groq client (fast inference)
│       │
│       ├── capabilities/
│       │   ├── __init__.py
│       │   ├── base.py         # Base capability interface
│       │   │
│       │   ├── basic/
│       │   │   ├── __init__.py
│       │   │   ├── completion.py       # Text completion
│       │   │   ├── summarization.py    # Summarize text
│       │   │   ├── classification.py   # Classify content
│       │   │   ├── extraction.py       # Extract key points
│       │   │   └── template.py         # Template fill
│       │   │
│       │   ├── intermediate/
│       │   │   ├── __init__.py
│       │   │   ├── ner.py              # Named entity recognition
│       │   │   ├── sentiment.py        # Sentiment analysis
│       │   │   ├── qa.py               # Question answering
│       │   │   ├── semantic_search.py  # Semantic search
│       │   │   └── tagging.py          # Auto-tagging
│       │   │
│       │   ├── advanced/
│       │   │   ├── __init__.py
│       │   │   ├── comparison.py       # Document comparison
│       │   │   ├── relationships.py    # Relationship extraction
│       │   │   ├── synthesis.py        # Multi-doc synthesis
│       │   │   ├── structured.py       # Structured extraction
│       │   │   └── reasoning.py        # Chain-of-thought
│       │   │
│       │   └── agents/
│       │       ├── __init__.py
│       │       ├── base.py             # Agent base class
│       │       ├── research.py         # Research agent
│       │       ├── analysis.py         # Analysis agent
│       │       └── tools/              # Agent tools
│       │           ├── __init__.py
│       │           ├── sec_edgar.py    # SEC filing tools
│       │           ├── entity.py       # EntitySpine integration
│       │           └── market.py       # Market data tools
│       │
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── manager.py      # Prompt template manager
│       │   ├── versioning.py   # Version control for prompts
│       │   ├── renderer.py     # Template rendering (Jinja2)
│       │   └── library/
│       │       ├── summarization.yaml
│       │       ├── extraction.yaml
│       │       ├── classification.yaml
│       │       └── sec_filings.yaml
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py         # Abstract storage interface
│       │   ├── sqlite.py       # SQLite (Tier 1)
│       │   ├── postgres.py     # PostgreSQL (Tier 2+)
│       │   └── models.py       # SQLAlchemy models
│       │
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── memory.py       # In-memory cache
│       │   └── redis.py        # Redis cache
│       │
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── metrics.py      # Prometheus metrics
│       │   ├── tracing.py      # OpenTelemetry
│       │   └── cost.py         # Cost tracking
│       │
│       └── integrations/
│           ├── __init__.py
│           ├── capture_spine.py    # Capture Spine hooks
│           ├── entity_spine.py     # EntitySpine hooks
│           ├── feed_spine.py       # FeedSpine hooks
│           └── market_spine.py     # Market Spine hooks
│
├── tests/
│   ├── conftest.py
│   ├── test_providers/
│   ├── test_capabilities/
│   ├── test_api/
│   └── test_integration/
│
├── scripts/
│   ├── seed_prompts.py         # Load default prompt library
│   ├── benchmark.py            # Performance benchmarking
│   └── migrate.py              # Database migrations
│
├── docs/
│   ├── API.md                  # API reference
│   ├── PROVIDERS.md            # Provider configuration
│   ├── PROMPTS.md              # Prompt authoring guide
│   ├── DEPLOYMENT.md           # Deployment guide
│   └── INTEGRATION.md          # Integration examples
│
└── examples/
    ├── basic_completion.py
    ├── summarize_article.py
    ├── extract_entities.py
    ├── research_agent.py
    └── capture_spine_integration.py
```

---

## API Design

### OpenAI-Compatible Endpoints

For drop-in compatibility with existing tools:

```
POST /v1/chat/completions      # OpenAI-compatible chat
POST /v1/completions           # OpenAI-compatible completion
POST /v1/embeddings            # OpenAI-compatible embeddings
GET  /v1/models                # List available models
```

### GenAI Spine Native Endpoints

```
# Health & Status
GET  /health                   # Health check
GET  /ready                    # Readiness check
GET  /metrics                  # Prometheus metrics

# Core Capabilities
POST /v1/summarize             # Summarize text
POST /v1/extract               # Extract entities/key points
POST /v1/classify              # Classify content
POST /v1/compare               # Compare documents
POST /v1/synthesize            # Multi-doc synthesis

# Prompt Management
GET  /v1/prompts               # List prompts
POST /v1/prompts               # Create prompt
GET  /v1/prompts/{id}          # Get prompt
PUT  /v1/prompts/{id}          # Update prompt
DELETE /v1/prompts/{id}        # Delete prompt
GET  /v1/prompts/{id}/versions # List versions
POST /v1/prompts/{id}/render   # Preview rendered prompt

# Agent Operations (Advanced)
POST /v1/agents/research       # Start research agent
POST /v1/agents/analyze        # Start analysis agent
GET  /v1/agents/{id}/status    # Check agent status
GET  /v1/agents/{id}/result    # Get agent result

# Provider Management
GET  /v1/providers             # List providers
GET  /v1/providers/{name}/models # List models for provider
POST /v1/providers/test        # Test provider connection

# Usage & Costs
GET  /v1/usage                 # Usage statistics
GET  /v1/costs                 # Cost breakdown
```

### Request/Response Examples

#### Summarization

```bash
POST /v1/summarize
{
  "content": "Apple Inc. reported Q4 2025 revenue of $94.9B...",
  "max_sentences": 3,
  "focus": "financial_metrics",
  "output_format": "bullet_points"
}

Response:
{
  "summary": "• Apple Q4 revenue: $94.9B (↑8% YoY)\n• iPhone: $46.2B\n• Services: $25.0B",
  "key_metrics": {
    "revenue": 94900000000,
    "growth_yoy": 0.08
  },
  "usage": {
    "input_tokens": 1250,
    "output_tokens": 85,
    "cost_usd": 0.0042
  }
}
```

#### Entity Extraction

```bash
POST /v1/extract
{
  "content": "Tim Cook, CEO of Apple Inc., announced...",
  "entity_types": ["PERSON", "ORG", "ROLE"],
  "link_entities": true  # Cross-reference with EntitySpine
}

Response:
{
  "entities": [
    {
      "text": "Tim Cook",
      "type": "PERSON",
      "start": 0,
      "end": 8,
      "resolved": {
        "entityspine_id": "person:tim-cook",
        "roles": ["CEO:Apple Inc."]
      }
    },
    {
      "text": "Apple Inc.",
      "type": "ORG",
      "start": 17,
      "end": 27,
      "resolved": {
        "entityspine_id": "entity:0000320193",
        "ticker": "AAPL",
        "cik": "0000320193"
      }
    }
  ]
}
```

---

## Integration Examples

### Capture Spine Integration

```python
# In capture-spine, replace direct LLM calls with GenAI Spine

from httpx import AsyncClient

class GenAIClient:
    def __init__(self, base_url: str = "http://genai-spine:8100"):
        self.client = AsyncClient(base_url=base_url)

    async def summarize_article(self, content: str) -> dict:
        response = await self.client.post("/v1/summarize", json={
            "content": content,
            "max_sentences": 3,
            "focus": "news"
        })
        return response.json()

    async def categorize_feed(self, feed_metadata: dict) -> dict:
        response = await self.client.post("/v1/classify", json={
            "content": feed_metadata["description"],
            "categories": ["technology", "finance", "healthcare", ...],
            "multi_label": True
        })
        return response.json()
```

### EntitySpine Integration

```python
# Entity resolution with GenAI disambiguation

async def resolve_with_ai(text: str, candidates: list[Entity]) -> Entity:
    """Use GenAI to disambiguate entity matches."""
    response = await genai_client.post("/v1/completions", json={
        "messages": [
            {"role": "system", "content": "You are an entity disambiguation expert..."},
            {"role": "user", "content": f"Given '{text}', which entity is correct?\n{candidates}"}
        ],
        "output_schema": {"type": "object", "properties": {"entity_id": {"type": "string"}}}
    })
    return response.json()["parsed"]["entity_id"]
```

### FeedSpine Integration

```python
# Content enrichment during feed processing

class GenAIEnricher(Enricher):
    async def enrich(self, record: Record) -> Record:
        # Summarize content
        summary = await self.genai.summarize(record.content)

        # Extract entities
        entities = await self.genai.extract(record.content, ["ORG", "PERSON"])

        # Score sentiment
        sentiment = await self.genai.classify(
            record.content,
            categories=["positive", "negative", "neutral"]
        )

        return record.with_enrichments(
            summary=summary,
            entities=entities,
            sentiment=sentiment
        )
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Project scaffolding with UV/pyproject.toml
- [ ] Docker Compose with Ollama
- [ ] Basic FastAPI app with health endpoints
- [ ] Provider abstraction (Ollama first)
- [ ] SQLite storage for prompts
- [ ] Basic completion endpoint

### Phase 2: Core Capabilities (Week 3-4)

- [ ] Summarization capability
- [ ] Entity extraction capability
- [ ] Classification capability
- [ ] Prompt management CRUD
- [ ] OpenAI-compatible endpoints
- [ ] Cost tracking

### Phase 3: Multi-Provider (Week 5-6)

- [ ] OpenAI provider
- [ ] Anthropic provider
- [ ] Bedrock provider
- [ ] Intelligent routing
- [ ] Redis caching
- [ ] PostgreSQL storage option

### Phase 4: Advanced (Week 7-8)

- [ ] SSE streaming
- [ ] Document comparison
- [ ] Multi-document synthesis
- [ ] Embeddings endpoint
- [ ] Semantic search

### Phase 5: Agents (Week 9-10)

- [ ] Agent framework
- [ ] Research agent
- [ ] Tool registry
- [ ] Integration hooks for all Spines
- [ ] Knowledge graph queries

---

## Docker Compose Example (Tier 1)

```yaml
# docker-compose.yml
version: '3.8'

services:
  genai-api:
    build: .
    ports:
      - "8100:8100"
    environment:
      - GENAI_PROVIDER=ollama
      - OLLAMA_URL=http://ollama:11434
      - DATABASE_URL=sqlite:///data/genai.db
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

---

## Next Steps

1. **Review this design** with stakeholders
2. **Choose initial tier** (recommend Tier 1 for MVP)
3. **Create repository** at `genai-spine/`
4. **Migrate providers** from capture-spine
5. **Build core capabilities** incrementally
6. **Integrate with capture-spine** first, then others

---

*Document generated: January 30, 2026*
