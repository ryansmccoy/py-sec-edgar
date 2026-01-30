# Financial Data Ecosystem

> **Recurring Prompt Document**
> Integration architecture across all projects in the py-sec-edgar workspace.

---

## Ecosystem Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            FINANCIAL DATA ECOSYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              DATA SOURCES                                        │    │
│  │   SEC EDGAR │ Finnhub │ Yahoo │ FactSet │ Bloomberg │ News │ VS Code Chat       │    │
│  └─────────────────────────────────────────────┬───────────────────────────────────┘    │
│                                                │                                         │
│                                                ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                       DOMAIN LAYER - ENTITYSPINE                                 │    │
│  │   • stdlib-only dataclasses (zero dependencies)                                  │    │
│  │   • Entity → Security → Listing (financial hierarchy)                            │    │
│  │   • Observation, Event (point-in-time facts)                                     │    │
│  │   • ChatWorkspace → ChatSession → ChatMessage (productivity)                     │    │
│  │   • Exchange, BrokerDealer (market infrastructure)                               │    │
│  │   • Extraction models: StoryCluster, SignificanceScore (v2.3.2)                  │    │
│  │   • Workflow/Execution: ExecutionContext, Result[T], QualityStatus (v2.3.3)      │    │
│  │   • Error domain: ErrorCategory, ErrorContext, ErrorRecord (v2.3.3)              │    │
│  │   • Multi-vendor identifier resolution (CIK, CUSIP, ISIN, LEI)                   │    │
│  │   Status: ✅ Public on PyPI                                                       │    │
│  └─────────────────────────────────────────────┬───────────────────────────────────┘    │
│                                                │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                       INGESTION LAYER - FEEDSPINE                                │    │
│  │   • Storage-agnostic feed capture                                                │    │
│  │   • Natural key deduplication (same record = 1 entry + sightings)                │    │
│  │   • Bronze → Silver → Gold medallion architecture                                │    │
│  │   • Adapters: RSS, JSON, SEC EDGAR, Copilot Chat (new!)                          │    │
│  │   • Checkpointing for incremental sync                                           │    │
│  │   Status: 🔄 Private → Plan 1.0.0 release                                         │    │
│  └─────────────────────────────────────────────┬───────────────────────────────────┘    │
│                                                │                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐    │
│  │                   ORCHESTRATION LAYER - SPINE-CORE                               │    │
│  │   • Pipeline infrastructure (WorkManifest, DB adapters, SQL schema)              │    │
│  │   • Quality gates with QualityRunner (uses entityspine.QualityResult)            │    │
│  │   • Idempotency helpers (skip/force checks, delete+insert)                       │    │
│  │   • Reject sinks for validation failures                                         │    │
│  │   • Temporal utilities (WeekEnding, rolling windows)                             │    │
│  │   • NOTE: Domain types moved to entityspine v2.3.3 (spine-core imports them)     │    │
│  │   Status: ✅ Public on GitHub                                                     │    │
│  └─────────────────────────────────────────────┬───────────────────────────────────┘    │
│                                                │                                         │
│          ┌─────────────────────────────────────┴────────────────────────────┐           │
│          ▼                                                                  ▼           │
│  ┌──────────────────────────────────┐        ┌──────────────────────────────────────┐  │
│  │         CAPTURE-SPINE            │        │     TRADING-DESKTOP (MarketSpine)    │  │
│  │   • FastAPI + React UI           │        │   • Bloomberg-style React SPA        │  │
│  │   • PostgreSQL + Elasticsearch   │  ◄───► │   • Portfolio/Trading/Research       │  │
│  │   • Celery workers               │        │   • Real-time market data            │  │
│  │   • LLM enrichment (Bedrock)     │        │   • Vite + TailwindCSS               │  │
│  │   • Productivity features (new!) │        │   • Zustand + React Query            │  │
│  │   Status: 🔒 Private             │        │   Status: 🔒 Private                 │  │
│  └──────────────────────────────────┘        └──────────────────────────────────────┘  │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Why It Works

> "Why is it now that it feels like it's so easy to implement features with this entity model system?"
> — User, Jan 29, 2026

| Design Choice | Benefit |
|---------------|---------|
| **stdlib-only domain** | No Pydantic/ORM complexity in entityspine core |
| **Composable hierarchy** | Workspace→Session→Message mirrors Entity→Security→Listing |
| **Hash-based deduplication** | feedspine handles any content type the same way |
| **Factory functions** | `create_entity()`, `create_chat_session()` - consistent patterns |
| **Tiered storage** | JSON → SQLite → DuckDB → PostgreSQL progression |

---

## Project Details

### 1. py-sec-edgar

| Attribute | Value |
|-----------|-------|
| **Purpose** | SEC EDGAR filing downloads and XBRL parsing |
| **Language** | Python |
| **Status** | ✅ Public on GitHub, PyPI |
| **Location** | `b:\github\py-sec-edgar\` (root) |
| **Dependencies** | Standalone |
| **Consumers** | feedspine, capture-spine |

**Key modules:**
- `py_sec_edgar/` — Core SEC EDGAR client
- Download SEC filings by CIK, ticker, date range
- Parse XBRL financial statements
- Full-text search over filings

---

### 2. entityspine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Domain models and entity resolution |
| **Language** | Python (stdlib-only core) |
| **Status** | ✅ Public on PyPI |
| **Location** | `b:\github\py-sec-edgar\entityspine\` |
| **Dependencies** | None (stdlib-only for Tier 0-1) |
| **Consumers** | feedspine, capture-spine, trading-desktop |

**Key modules (`src/entityspine/domain/`):**
- `entity.py`, `security.py`, `listing.py` — Financial hierarchy
- `observation.py` — Point-in-time facts with provenance
- `graph.py` — Events, relationships, knowledge graph
- `chat.py` — ChatWorkspace, ChatSession, ChatMessage (v2.3.1)
- `extraction.py` — ExtractionType, StoryCluster, SignificanceScore (v2.3.2)
- `workflow.py` — ExecutionContext, Result[T], WorkflowDefinition (v2.3.3)
- `errors.py` — ErrorCategory, ErrorContext, ErrorRecord (v2.3.3)
- `markets.py` — Exchange, BrokerDealer, Clearinghouse
- `enums/` — Comprehensive enums (EntityType, SecurityType, etc.)
- `validators.py` — Identifier normalization (CIK, CUSIP, ISIN, LEI)

**Architecture:**
```
Entity ≠ Security ≠ Listing
  │         │         │
  └── CIK   └── CUSIP └── Ticker (TICKER belongs on Listing!)
```

---

### 3. feedspine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Feed ingestion and deduplication |
| **Language** | Python |
| **Status** | 🔄 Private → Plan 1.0.0 PyPI release |
| **Location** | `b:\github\py-sec-edgar\feedspine\` |
| **Dependencies** | entityspine (optional), pydantic |
| **Consumers** | capture-spine, trading-desktop |

**Key modules (`src/feedspine/`):**
- `core/feedspine.py` — Main orchestration (`FeedSpine`, `CollectionResult`)
- `adapter/` — Feed adapters (`RSSFeedAdapter`, `JSONFeedAdapter`)
- `storage/` — Storage backends (`MemoryStorage`, `DuckDBStorage`)
- `models/` — `Record`, `Sighting`, `FeedRun`, `Task`
- `pipeline.py` — `Pipeline`, `PipelineStats`
- `cache/`, `queue/`, `scheduler/` — Backend abstractions
- `earnings/` — Earnings-specific providers (planned)

**Key concepts:**
- **Natural key deduplication** — Same record = 1 entry + multiple sightings
- **Bronze → Silver → Gold** — Medallion data quality tiers
- **Protocol-based design** — Swap backends without code changes

---

### 4. spine-core

| Attribute | Value |
|-----------|-------|
| **Purpose** | Pipeline framework and orchestration primitives |
| **Language** | Python |
| **Status** | ✅ Public on GitHub |
| **Location** | `b:\github\py-sec-edgar\spine-core\` |
| **Dependencies** | structlog, ulid |
| **Consumers** | feedspine, capture-spine |

**Key modules (`packages/spine-core/src/spine/core/`):**
- `execution.py` — `ExecutionContext`, `new_batch_id`
- `manifest.py` — `WorkManifest` for multi-stage workflows
- `result.py` — `Result[T]`, `Ok`, `Err` for error handling
- `errors.py` — Structured error types (`SpineError`, `TransientError`)
- `idempotency.py` — Skip/force checks, delete+insert helpers
- `quality.py` — Quality gates and `QualityRunner`
- `rejects.py` — Reject sink for validation failures
- `temporal.py` — `WeekEnding`, date range utilities
- `schema.py` — Core infrastructure DDL

**Key modules (`packages/spine-domains/src/spine/domains/`):**
- `finra/` — FINRA domain pipelines
- `market_data/` — Market data domain
- `reference/` — Reference data domain

---

### 5. capture-spine

| Attribute | Value |
|-----------|-------|
| **Purpose** | Content capture, storage, and productivity |
| **Language** | Python (FastAPI), TypeScript (React) |
| **Status** | 🔒 Private repo (keep private) |
| **Location** | `b:\github\py-sec-edgar\capture-spine\` |
| **Dependencies** | spine-core, entityspine, PostgreSQL, Redis |
| **Consumers** | trading-desktop (planned) |

**Backend (`app/`):**
- `api/routers/` — 50+ FastAPI routers (feeds, items, records, search, etc.)
- `features/` — Feature modules (auth, feeds, search, ingest, llm, etc.)
- `domains/` — Domain logic
- `tasks/` — Celery background tasks
- `llm/` — LLM integration (Bedrock)

**Frontend (`frontend/`):**
- React 18 + TypeScript + Vite
- Newsfeed reader UI
- Knowledge management

**Key capabilities:**
- Point-in-time content capture
- LLM enrichment (summarization, entity extraction)
- Full-text search (PostgreSQL tsvector + optional Elasticsearch)
- Real-time updates (WebSocket)
- Productivity features: VS Code chat ingestion, TODO tracking, file upload

---

### 6. trading-desktop (MarketSpine)

| Attribute | Value |
|-----------|-------|
| **Purpose** | Institutional investment management UI |
| **Language** | TypeScript, React 18, Vite |
| **Status** | 🔒 Private (not for GitHub/PyPI) |
| **Location** | `b:\github\py-sec-edgar\spine-core\trading-desktop\trading-desktop\` |
| **Dependencies** | API backends (capture-spine, feedspine) |
| **Consumers** | End users |

**Structure (`src/`):**
- `pages/` — 18 route pages (Dashboard, Portfolio, Trading, Research, etc.)
- `components/` — Reusable UI components
- `layouts/` — AdminLayout with navigation
- `store/` — Zustand state management
- `api/` — API clients
- `widgets/` — Dashboard widgets

**Key pages:**
| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | Key metrics and alerts |
| Portfolio | `/portfolio` | Portfolio overview |
| Holdings | `/holdings` | Position detail |
| Trading | `/trading` | Order execution |
| Analytics | `/analytics` | Performance analytics |
| Risk | `/risk` | Risk management |
| Companies | `/companies` | Entity profiles (entityspine) |
| News | `/news` | News feed (capture-spine) |

---

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ SEC EDGAR   │     │  Finnhub    │     │ News APIs   │
│ (8-K, 10-Q) │     │ (Estimates) │     │ (RSS, Web)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │    py-sec-edgar   │                   │
       │    downloads      │                   │
       ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────┐
│                    FEEDSPINE                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │ Estimates │  │  Actuals  │  │  Calendar │       │
│  │ Storage   │  │  Storage  │  │  Events   │       │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│        │              │              │              │
│        └──────────────┼──────────────┘              │
│                       ▼                             │
│              ┌───────────────┐                      │
│              │  Comparison   │                      │
│              │    Engine     │                      │
│              │ (Beat/Miss)   │                      │
│              └───────────────┘                      │
└─────────────────────────┬───────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ ENTITYSPINE│  │CAPTURE-SPINE│ │SPINE-CORE │
   │            │  │            │  │           │
   │ Entity     │  │ Store as   │  │ Run as    │
   │ Resolution │  │ Records    │  │ Pipeline  │
   └────────────┘  └─────┬──────┘  └───────────┘
                         │
                         ▼
              ┌────────────────────┐
              │  TRADING-DESKTOP   │
              │  (MarketSpine)     │
              │                    │
              │  • Earnings Widget │
              │  • Alert Dashboard │
              │  • Research Hub    │
              └────────────────────┘
```

---

## Integration Points

### feedspine ↔ entityspine

```python
# feedspine uses entityspine for entity resolution
from entityspine import EntityResolver

resolver = EntityResolver()
entity = resolver.resolve(ticker="MSFT", source="finnhub")
# Returns canonical entity_id for cross-source linking
```

### feedspine ↔ capture-spine

```python
# feedspine stores records in capture-spine
from feedspine.adapters import CaptureSpineAdapter

adapter = CaptureSpineAdapter(base_url="http://capture-spine:8000")
adapter.store_earnings(earnings_result)  # POST /api/records
```

### spine-core ↔ capture-spine

```python
# spine-core posts execution results to capture-spine
from spine.adapters.capture_spine import CaptureSpineAdapter

adapter = CaptureSpineAdapter(base_url="http://capture-spine:8000")
adapter.store_execution(workflow_result)  # record_type='pipeline_run'
```

### capture-spine ↔ trading-desktop

- **API**: capture-spine provides REST API consumed by trading-desktop
- **WebSocket**: Real-time updates for earnings alerts
- **Migration plan**: Move capture-spine React components into trading-desktop

---

## Publication Status

| Project | GitHub | PyPI | Action Needed |
|---------|--------|------|---------------|
| py-sec-edgar | ✅ Public | ✅ Published | None |
| entityspine | ✅ Public | ✅ Published | None |
| feedspine | 🔒 Private | ❌ Not published | Create 1.0.0, publish |
| spine-core | ✅ Public | ❌ Not published | Consider PyPI or keep as git dep |
| capture-spine | 🔒 Private | ❌ N/A | Keep private |
| trading-desktop | 🔒 Private | ❌ N/A | Keep private |

---

## 📊 Documentation Readiness Assessment

Use this table when auditing documentation across the ecosystem.

### Project Checklist Status

| Project | README | pyproject.toml | ARCHITECTURE.md | CHANGELOG | CI/CD | Docker | project_meta.yaml |
|---------|--------|----------------|-----------------|-----------|-------|--------|-------------------|
| **py-sec-edgar** | ✅ | ✅ | ❌ Needs creation | ❌ Needs creation | ❌ | ❌ | ❌ |
| **entityspine** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **feedspine** | ⚠️ Needs update | ✅ | ❌ Needs creation | ❌ Needs creation | ❌ | ❌ | ❌ |
| **spine-core** | ✅ | ✅ | ⚠️ Needs update | ❌ Needs creation | ❌ | ⚠️ Exists | ❌ |
| **capture-spine** | ⚠️ Needs update | ✅ | ❌ Needs creation | ❌ Needs creation | ❌ | ✅ | ❌ |
| **trading-desktop** | ✅ Updated | ✅ package.json | ❌ Needs creation | ❌ Needs creation | ❌ | ❌ | ❌ |

### Priority Order for Alignment

1. **entityspine** — Gold standard, verify patterns are documented
2. **feedspine** — Secondary reference, align with entityspine
3. **spine-core** — Core primitives, document ExecutionContext, Result[T]
4. **py-sec-edgar** — Root project, needs ARCHITECTURE.md
5. **capture-spine** — Full stack, complex docs needed
6. **trading-desktop** — Frontend only, TypeDoc setup

---

## 🔧 Key File Paths for Automation

### Files to Extract Features From (Git Commits)

```
entityspine/src/entityspine/domain/**/*.py
feedspine/src/feedspine/**/*.py
spine-core/packages/spine-core/src/spine/core/*.py
capture-spine/app/**/*.py
spine-core/trading-desktop/trading-desktop/src/**/*.tsx
py_sec_edgar/**/*.py
```

### Files to Extract TODOs From

```
**/*.py — Python TODOs
**/*.ts — TypeScript TODOs
**/*.tsx — React TODOs
**/TODO.md — Existing TODO files
**/ROADMAP.md — Existing roadmaps
```

### Config Files to Standardize

| File | Python Projects | TypeScript Projects |
|------|-----------------|---------------------|
| CI/CD | `.github/workflows/ci.yml` | `.github/workflows/ci.yml` |
| Release | `.github/workflows/release.yml` | N/A |
| Docker | `docker/Dockerfile`, `docker-compose.yml` | `docker/Dockerfile` |
| Make | `Makefile` | `Makefile` |
| Meta | `project_meta.yaml` | `project_meta.yaml` |

---

## 🏗️ Architecture Patterns to Document

### entityspine Patterns (Gold Standard)

1. **Dataclass Hierarchies**
   ```python
   Entity → Security → Listing
   ChatWorkspace → ChatSession → ChatMessage
   ```

2. **Factory Functions**
   ```python
   create_entity(), create_security(), create_chat_session()
   ```

3. **Natural Key Hashing**
   ```python
   @property
   def content_hash(self) -> str:
       return hashlib.sha256(canonical_repr).hexdigest()[:16]
   ```

4. **Enum-based Classification**
   ```python
   EntityType, SecurityType, ListingStatus, ChatRole
   ```

### feedspine Patterns

1. **Protocol-based Adapters**
   ```python
   class FeedAdapter(Protocol):
       def fetch(self) -> Iterator[Record]: ...
   ```

2. **Storage Abstraction**
   ```python
   class Storage(Protocol):
       def store(self, record: Record) -> str: ...
   ```

3. **Medallion Architecture**
   ```
   Bronze (raw) → Silver (cleaned) → Gold (enriched)
   ```

### spine-core Patterns

1. **Result Monad**
   ```python
   Result[T] = Ok(value) | Err(error)
   ```

2. **Execution Context**
   ```python
   with ExecutionContext(name="job") as ctx:
       ctx.log.info("Starting")
   ```

3. **Work Manifests**
   ```python
   manifest = WorkManifest(items=[...])
   for item in manifest:
       process(item)
   ```

---

## Active Feature Development

| Feature | Projects | Status | Location |
|---------|----------|--------|----------|
| **Copilot Chat Ingestion** | entityspine → feedspine → capture-spine | 🟡 In Progress | [docs/integration/copilot-chat-ingestion.md](docs/integration/copilot-chat-ingestion.md) |
| **VS Code Chat Parser** | capture-spine | ✅ Working | [capture-spine/scripts/copilot_chat_parser.py](capture-spine/scripts/copilot_chat_parser.py) |
| **Chat Domain Models** | entityspine | ✅ Complete | [entityspine/src/entityspine/domain/chat.py](entityspine/src/entityspine/domain/chat.py) |
| **Extraction Models** | entityspine (migrated from capture-spine) | ✅ Complete | [entityspine/src/entityspine/domain/extraction.py](entityspine/src/entityspine/domain/extraction.py) |
| **TODO Management** | capture-spine | 🔴 Planning | [capture-spine/docs/features/productivity/](capture-spine/docs/features/productivity/) |
| **File Upload** | capture-spine | 🔴 Planning | [capture-spine/docs/features/file-upload/](capture-spine/docs/features/file-upload/) |
| **Modern Earnings** | feedspine → entityspine | 🟡 Planning | [feedspine/docs/features/modern-earnings-intelligence/](feedspine/docs/features/modern-earnings-intelligence/) |

---

## Recent Model Migrations

### v2.3.3 — Workflow/Error Models (Jan 29, 2026)

Moved workflow and error domain models from spine-core to entityspine. **spine-core now imports from entityspine** for these types, adding only infrastructure (DB adapters, SQL schema).

| Model | Purpose | Migration Pattern |
|-------|---------|-------------------|
| `ExecutionContext` | Pipeline lineage tracking | `from entityspine.domain import ExecutionContext` |
| `Ok`, `Err`, `Result` | Explicit success/failure handling | spine-core adds exception hierarchy |
| `WorkflowStatus`, `TaskStatus` | Workflow state machines | Used by WorkManifest |
| `QualityStatus`, `QualityCategory` | Quality check classification | QualityRunner uses these |
| `QualityResult` | Quality check outcome | spine-core adds QualityRunner |
| `WorkflowDefinition`, `WorkflowStep` | Declarative workflow modeling | New capability |
| `ErrorCategory`, `ErrorSeverity` | Error classification | spine-core adds SpineError hierarchy |
| `ErrorContext`, `ErrorRecord` | Structured error metadata | For logging/alerting |

**Why the migration?**
- **Domain vs Infrastructure separation**: Domain types (enums, dataclasses) belong in entityspine; infrastructure (DB, retry logic) stays in spine-core
- **stdlib-only guarantee**: entityspine's zero-dependency promise extends to workflow concepts
- **Reusability**: capture-spine can use `WorkflowDefinition` without spine-core dependency

### v2.3.2 — Extraction Models (Jan 29, 2026)

Moved NLP/extraction domain models from capture-spine to entityspine for ecosystem-wide reuse.

| Model | Purpose | Migration Guide |
|-------|---------|-----------------|
| `ExtractionType` | Entity types for NER extraction | [extraction-model-migration.md](docs/integration/extraction-model-migration.md) |
| `ExtractedEntity` | Individual entity mention | - |
| `StoryCluster` | Story/topic clustering | - |
| `SignificanceScore` | Content prioritization scoring | - |
| `ContentLink` | Article relationship tracking | - |

---

## User Feedback Log

### Jan 29, 2026 Session

**Observation: Why entityspine feels easy**
> "Why is it now that it feels like it's so easy to implement features with this entity model system? entityspine I guess can manage this type of stuff too?"

**Answer:** entityspine's stdlib-only approach + composable patterns (Workspace→Session→Message mirrors Entity→Security→Listing) + factory functions make domain modeling fast.

**Requests captured:**
1. ✅ VS Code Copilot chat ingestion (parser exists, models created)
2. ⏳ feedspine CopilotChatProvider (next step)
3. 🔴 TODO tracking with conversation origin
4. 🔴 Drag-drop file upload with LLM enrichment
5. ✅ Integration docs folder created
6. ✅ Extraction models migrated from capture-spine → entityspine (ExtractionType, StoryCluster, SignificanceScore)
7. ✅ Workflow/Error models migrated from spine-core → entityspine (ExecutionContext, Result[T], ErrorCategory)

**Model migration request:**
> "If we have opportunity to move stuff out of capture spine into feed spine or entity spine go for it, we can make it a dependency for the project then import both"

**Quote for history:**
> "Make sure you are keeping track of the features and updating it with my responses so I can keep this history"

---

## Related Documentation

### Integration Docs

- [docs/integration/README.md](docs/integration/README.md) — Cross-project integration patterns
- [docs/integration/copilot-chat-ingestion.md](docs/integration/copilot-chat-ingestion.md) — Chat → feedspine → capture-spine
- [docs/integration/extraction-model-migration.md](docs/integration/extraction-model-migration.md) — NLP models migration guide

### By Project

| Project | Docs Location | Key Files |
|---------|---------------|-----------|
| **entityspine** | [entityspine/docs/](entityspine/docs/) | ARCHITECTURE.md, DEVELOPMENT_HISTORY.md |
| **feedspine** | [feedspine/docs/](feedspine/docs/) | features/, architecture/ |
| **spine-core** | [spine-core/docs/](spine-core/docs/) | architecture/ |
| **capture-spine** | [capture-spine/docs/](capture-spine/docs/) | features/, architecture/ |
| **trading-desktop** | [spine-core/trading-desktop/trading-desktop/README.md](spine-core/trading-desktop/trading-desktop/README.md) | Modules, integration |

### Feature Docs

| Feature | Location |
|---------|----------|
| Productivity Suite | [capture-spine/docs/features/productivity/](capture-spine/docs/features/productivity/) |
| File Upload | [capture-spine/docs/features/file-upload/](capture-spine/docs/features/file-upload/) |
| Chat Ingestion | [feedspine/docs/features/copilot-chat-ingestion/](feedspine/docs/features/copilot-chat-ingestion/) |
| Modern Earnings | [feedspine/docs/features/modern-earnings-intelligence/](feedspine/docs/features/modern-earnings-intelligence/) |
| 8-K Release Capture | [feedspine/docs/features/8k-release-capture/](feedspine/docs/features/8k-release-capture/) |

---

*This is a living document. Update as integrations evolve.*
---

## 📝 Current TODO Tracking

### High Priority

| Task | Project | Location | Notes |
|------|---------|----------|-------|
| Add ARCHITECTURE.md | py-sec-edgar | `docs/ARCHITECTURE.md` | Document filing download flow |
| Add CHANGELOG.md | py-sec-edgar | `docs/CHANGELOG.md` | Backfill from git history |
| Create project_meta.yaml | ALL | Root of each project | Ecosystem metadata |
| Add CI/CD workflows | ALL | `.github/workflows/` | Tests, lint, coverage |
| feedspine 1.0.0 release | feedspine | — | Prep for PyPI publication |

### Medium Priority

| Task | Project | Location | Notes |
|------|---------|----------|-------|
| CopilotChatProvider | feedspine | `src/feedspine/adapter/` | Use entityspine chat models |
| TypeDoc setup | trading-desktop | `typedoc.json` | API documentation |
| Docker standardization | ALL | `docker/` | Consistent Dockerfiles |
| Makefile standardization | ALL | `Makefile` | Common commands |

### Low Priority

| Task | Project | Location | Notes |
|------|---------|----------|-------|
| TODO extraction script | spine-core | `scripts/` | Scan code for TODOs |
| Feature auto-gen from git | spine-core | `scripts/` | Parse commit messages |
| Directory reorganization | feedspine | — | By feature using file dates |

---

## 🔒 Safety Constraints

**NEVER DO WITHOUT EXPLICIT PERMISSION:**
- Push to GitHub (any repository)
- Publish to PyPI (any package)
- Delete production data
- Modify `.git/` directory
- Run `git push`, `twine upload`, or similar

**ALWAYS ASK BEFORE:**
- Moving files to archive
- Renaming modules
- Changing pyproject.toml metadata
- Creating GitHub releases

---
