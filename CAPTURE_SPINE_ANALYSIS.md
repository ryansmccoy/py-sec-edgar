# Capture-Spine Deep Dive Analysis

## Executive Summary

**capture-spine** is a production-quality, full-featured feed capture application originally built to capture SEC data. It's currently working flawlessly and represents the mature implementation from which **FeedSpine** was extracted as a library.

This analysis examines the architecture to determine:
1. What components overlap with FeedSpine
2. What's unique to capture-spine's full-app context
3. Recommended integration strategy

**Key Finding**: FeedSpine was built FROM capture-spine. The refactoring direction should be:
- **capture-spine** → Full application (keeps DB, React UI, API, knowledge management)
- **FeedSpine** → Embeddable library (keeps core pipeline logic)
- Integration: capture-spine can optionally USE FeedSpine adapters

---

## Architecture Comparison

### Pipeline Stages

| Stage | capture-spine | FeedSpine | Overlap |
|-------|--------------|-----------|---------|
| **Fetch** | `IngestPipeline` (426 lines) | `HttpClient` (416 lines) | Different approaches - capture-spine has enumerators |
| **Parse** | `ParsePipeline` (664 lines) + `ParserRegistry` | `Pipeline.process()` + adapters | Both have registry patterns |
| **Enrich** | `BaseEnricher` + domain handlers | `enricher/` module | Similar concepts |
| **Index** | `IndexPipeline` + Elasticsearch | Optional `search/` module | capture-spine has full ES integration |
| **Resolve** | `ResolvePipeline` + EntitySpine | Not in FeedSpine | Unique to capture-spine |

### Storage Architecture

| Layer | capture-spine | FeedSpine |
|-------|--------------|-----------|
| **Bronze** | `items` table + `BodyStore` filesystem | `StorageBackend` protocol |
| **Silver** | `records` table + `sightings` | `Record` + `Sighting` models |
| **Gold** | `knowledge_*` tables | Not implemented |

### Key Insight
capture-spine implements all three medallion layers in a concrete PostgreSQL + filesystem setup, while FeedSpine provides abstract protocols that can use different backends (Memory, SQLite, PostgreSQL).

---

## capture-spine Component Inventory

### 1. Backend (`app/`)

#### Repositories (`db/repos/`) - 20+ Classes
```
feeds.py          - FeedStatus, visibility, polling management
records.py        - Upsert, batch operations, dedup by (region, record_type, unique_id)
items.py          - Raw captured content
sightings.py      - When/where records were seen
checkpoints.py    - Feed position tracking
content_blobs.py  - Large content storage
feed_runs.py      - Run metadata and statistics
knowledge_items.py    - Gold layer entities
knowledge_relations.py - Entity relationships
entity_mappings.py    - EntitySpine integration
```

**Assessment**: Repository layer is mature, battle-tested. FeedSpine's storage protocols could be implemented as adapters to these repos.

#### Domains (`domains/`) - Plugin Architecture
```python
# base.py - Abstract handlers
class BaseEnricher(ABC):
    @abstractmethod
    async def enrich(self, record: RecordContext) -> dict: ...

class BaseDisplayer(ABC):
    @abstractmethod
    async def display(self, record: RecordContext) -> RenderOutput: ...

# registry.py - Lazy-loaded domain handlers
class DomainRegistry:
    _domains = {"sec": ("app.domains.sec", "SECDomain"), ...}
```

**Assessment**: Excellent plugin pattern. Could be shared with py-sec-edgar's `@register_parser` pattern.

#### Pipelines (`pipelines/`) - 5 Stages
```
fetch/      - IngestPipeline + BodyStore + Enumerators
parse/      - ParsePipeline + ParserRegistry
enrich/     - EnrichPipeline + domain handlers
index/      - IndexPipeline + Elasticsearch
resolve/    - ResolvePipeline + EntitySpine
lakehouse/  - Unified processing
```

**Assessment**: Pipeline stages are well-separated. FeedSpine extracted the core `fetch→parse` flow but not the full `enrich→index→resolve` chain.

### 2. Frontend (`frontend/`)

#### Pages - 40+ Routes
Notable: `NewsfeedPage.tsx` (main reader interface)

#### Components
```
newsfeed/       - 30+ components for feed reading
├── ArticleList.tsx
├── ArticleDetail.tsx
├── FeedSidebar.tsx
├── HeaderBar.tsx
├── useNewsfeedState.ts  (1111 lines - central state)
reader/         - RecordList, RecordDetail
knowledge/      - Knowledge graph UI
```

**Assessment**: NewsfeedPage is a sophisticated, feature-rich component. Could be extracted as a standalone React component for py-sec-edgar.

### 3. Configuration (`feeds.yaml`)

1469-line feed configuration supporting:
- SEC feeds (RSS, daily-index, full-index, monthly XBRL)
- Hacker News API
- Generic RSS/Atom feeds
- Custom headers, storage modes, polling intervals

**Assessment**: This configuration model is production-proven. FeedSpine should use the same YAML format.

---

## FeedSpine Architecture

### Core Modules
```
feedspine/
├── adapter/       - Feed adapter protocol
├── http/          - HttpClient with rate limiting
├── models/        - Record, Sighting, RecordCandidate
├── storage/       - Storage backends (Memory, SQLite)
├── pipeline.py    - Core Pipeline orchestrator
├── protocols/     - Abstract interfaces
├── enricher/      - Content enrichment
├── search/        - Optional search integration
└── scheduler/     - Feed scheduling
```

### Key Differences from capture-spine

| Aspect | FeedSpine | capture-spine |
|--------|-----------|---------------|
| Deployment | Library (pip install) | Full application |
| Storage | Pluggable backends | PostgreSQL + filesystem |
| UI | None | Full React app |
| Knowledge | None | Knowledge graph |
| Entity Resolution | None | EntitySpine integration |
| Configuration | Python/CLI | YAML + database |

---

## Recommended Integration Strategy

### Option A: capture-spine Uses FeedSpine Adapters (Recommended)

```
┌──────────────────────────────────────────────────────────┐
│                   capture-spine                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              FeedSpine Adapters                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────────────┐  │   │
│  │  │SEC Feed │  │HN Feed  │  │Generic RSS Feed │  │   │
│  │  │Adapter  │  │Adapter  │  │Adapter          │  │   │
│  │  └────┬────┘  └────┬────┘  └────────┬────────┘  │   │
│  └───────┼────────────┼────────────────┼───────────┘   │
│          │            │                │               │
│          ▼            ▼                ▼               │
│  ┌──────────────────────────────────────────────────┐  │
│  │           capture-spine Storage Backend          │  │
│  │  (Implements FeedSpine StorageBackend protocol)  │  │
│  └──────────────────────────────────────────────────┘  │
│                          │                              │
│           ┌──────────────┼──────────────┐              │
│           ▼              ▼              ▼              │
│     ┌─────────┐   ┌─────────┐   ┌───────────────┐     │
│     │PostgreSQL│  │BodyStore│   │ Elasticsearch │     │
│     │(records)│   │(files)  │   │(search index) │     │
│     └─────────┘   └─────────┘   └───────────────┘     │
└──────────────────────────────────────────────────────────┘
```

**Benefits**:
- capture-spine stays stable (working flawlessly)
- FeedSpine gets battle-tested adapters
- Gradual migration possible
- Both projects benefit from shared code

**Implementation Steps**:
1. Create `CaptureSpineStorageBackend` implementing FeedSpine's `StorageBackend` protocol
2. Wrap capture-spine's repositories as FeedSpine-compatible storage
3. Optionally use FeedSpine's `HttpClient` instead of capture-spine's `Fetcher`
4. Keep capture-spine's `ParsePipeline`, `EnrichPipeline`, `IndexPipeline`, `ResolvePipeline` as-is

### Option B: Extract Tables/Polling to FeedSpine (Higher Risk)

Would require:
- Moving `FeedsRepository`, `RecordsRepository`, `SightingsRepository` patterns to FeedSpine
- Adding PostgreSQL storage backend to FeedSpine
- Adding feed scheduling to FeedSpine

**Risk**: Breaking working capture-spine functionality

### Recommendation: Option A

Keep capture-spine as the reference implementation and gradually adopt FeedSpine adapters where they provide value.

---

## React Component Extraction Analysis

### Target: NewsfeedPage for py-sec-edgar

#### Current Structure
```
frontend/src/pages/NewsfeedPage.tsx (orchestration)
frontend/src/components/newsfeed/
├── useNewsfeedState.ts     (1111 lines - all state management)
├── ArticleList.tsx         (virtualized list)
├── ArticleDetail.tsx       (article viewer)
├── FeedSidebar.tsx         (feed navigation)
├── HeaderBar.tsx           (toolbar)
├── MarkdownRenderer.tsx    (content display)
└── 25+ more components
```

#### Extraction Requirements

**Must Extract**:
1. `useNewsfeedState.ts` - Core state management (TanStack Query)
2. `ArticleList.tsx` - Virtual scrolling list
3. `ArticleDetail.tsx` - Content viewer
4. `FeedSidebar.tsx` - Feed navigation

**Can Simplify**:
1. Remove knowledge graph features
2. Remove multi-user features
3. Remove tagging/folders
4. Remove Elasticsearch faceted search

**New for py-sec-edgar**:
1. Filing-specific metadata display (CIK, form type, accession)
2. Document link handling (primary/exhibit documents)
3. XBRL data integration
4. Company search integration

#### Proposed Simplified Component

```tsx
// py-sec-edgar-ui/src/UnifiedFilingFeed.tsx
interface UnifiedFilingFeedProps {
  apiEndpoint: string;  // FeedSpine or capture-spine API
  initialFilters?: {
    formTypes?: string[];
    companies?: string[];
    dateRange?: [Date, Date];
  };
}

function UnifiedFilingFeed({ apiEndpoint, initialFilters }: UnifiedFilingFeedProps) {
  // Simplified state from useNewsfeedState
  const { filings, selectedFiling, filters } = useFilingFeed(apiEndpoint);

  return (
    <div className="filing-feed">
      <FilingSidebar filters={filters} />
      <FilingList filings={filings} />
      <FilingDetail filing={selectedFiling} />
    </div>
  );
}
```

---

## What Should Stay Where

### Keep in capture-spine (Full App Features)
- PostgreSQL repositories and migrations
- React frontend (NewsfeedPage, knowledge UI)
- Multi-user authentication
- Feed management API
- Elasticsearch integration
- Knowledge graph features
- WebSocket real-time updates

### Keep in FeedSpine (Library Core)
- `StorageBackend` protocol
- `FeedAdapter` protocol
- `Pipeline` orchestrator
- `HttpClient` with rate limiting
- `Record`, `Sighting`, `RecordCandidate` models
- CLI tools (`feed` command)

### Share Between Both
- Feed adapter implementations (SEC, HN, RSS)
- Parser registry pattern
- Configuration YAML schema
- Domain enricher pattern

### Move to py-sec-edgar
- SEC-specific exhibit parsing
- Form parsing (10-K, 8-K, etc.)
- XBRL extraction
- EntitySpine company matching

---

## Integration Points

### 1. FeedSpine → py-sec-edgar
```python
# py-sec-edgar can use FeedSpine for feed collection
from feedspine import Pipeline, MemoryStorage
from feedspine.adapter.sec import SECRSSAdapter

async def collect_filings():
    storage = MemoryStorage()
    adapter = SECRSSAdapter()
    pipeline = Pipeline(storage=storage)

    stats = await pipeline.process(adapter)

    # Now parse with py-sec-edgar
    for record in storage.list_records():
        filing = parse_filing(record.content_url)
```

### 2. capture-spine → FeedSpine
```python
# capture-spine uses FeedSpine storage backend
from feedspine.protocols.storage import StorageBackend

class CaptureSpineStorage(StorageBackend):
    """Adapter wrapping capture-spine repos."""

    def __init__(self, container: Container):
        self.records_repo = container.records
        self.sightings_repo = container.sightings

    async def store_record(self, record: Record) -> UUID:
        return await self.records_repo.upsert(record.to_dict())
```

### 3. capture-spine → py-sec-edgar
```python
# capture-spine enriches SEC records with py-sec-edgar
from py_sec_edgar import parse_filing

class SECEnricher(BaseEnricher):
    async def enrich(self, context: RecordContext) -> dict:
        if context.record_type == "sec_filing":
            filing_data = parse_filing(context.content_url)
            return {"facts": filing_data.facts, "exhibits": filing_data.exhibits}
        return {}
```

---

## Migration Roadmap

### Phase 1: Shared Models (Low Risk)
- Create shared `feedspine.models` that both projects use
- Ensure `Record`, `Sighting`, `RecordCandidate` are identical

### Phase 2: Adapter Extraction (Medium Risk)
- Extract SEC feed adapter from capture-spine to FeedSpine
- Test in FeedSpine, then optionally use in capture-spine

### Phase 3: Storage Backend (Medium Risk)
- Create `CaptureSpineStorageBackend` implementing FeedSpine protocol
- capture-spine can use FeedSpine pipeline with its own storage

### Phase 4: UI Component Library (Low Risk)
- Extract simplified NewsfeedPage as `@py-sec-edgar/feed-ui`
- Create py-sec-edgar specific variant with filing metadata

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|------------|------------|
| Shared models | Low | Backward-compatible additions |
| FeedSpine adapters | Low | New code, doesn't touch capture-spine |
| Storage backend wrapper | Medium | Comprehensive testing |
| UI extraction | Low | Copy, don't modify original |
| Replace capture-spine fetch | High | Don't do until FeedSpine proven |
| Replace capture-spine parse | High | Don't do until FeedSpine proven |

**Recommendation**: Start with low-risk changes, prove value, then gradually adopt.

---

## Conclusion

capture-spine is a mature, working system that should NOT be refactored aggressively. Instead:

1. **FeedSpine** should continue as the embeddable library
2. **capture-spine** should optionally adopt FeedSpine components
3. **py-sec-edgar** should use FeedSpine for feed collection
4. **React components** can be extracted for py-sec-edgar UI

The key principle: **FeedSpine was extracted FROM capture-spine**, not the other way around. Any "refactoring" should be capture-spine adopting FeedSpine components, not replacing capture-spine with FeedSpine.
