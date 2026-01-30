# V4 Master Roadmap: Unified SEC Data Platform

**Status**: Active Development
**Last Updated**: 2026-01-27
**Version**: 4.0.0-alpha

---

## Executive Summary

py-sec-edgar v4 evolves from a filing downloader into a **comprehensive SEC data platform** built on three pillars:

| Pillar | Package | Core Question | Primary Value |
|--------|---------|---------------|---------------|
| **Identity** | EntitySpine | "Who is this?" | Resolve any identifier to canonical entity |
| **Collection** | FeedSpine | "What exists?" | Capture all filings with deduplication |
| **Intelligence** | py-sec-edgar | "What does it mean?" | Extract, enrich, analyze SEC data |

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            V4 ARCHITECTURE OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────────┐   │
│  │   EntitySpine   │   │    FeedSpine    │   │      py-sec-edgar           │   │
│  │                 │   │                 │   │                             │   │
│  │  • Entity       │   │  • Unified      │   │  • SEC domain logic         │   │
│  │    resolution   │   │    feeds        │   │  • QueryService (APIs)      │   │
│  │  • Identifiers  │   │  • Real-time    │   │  • Section extraction       │   │
│  │  • Relationships│   │  • Dedup        │   │  • SigDev detection         │   │
│  │  • Versioning   │   │  • Bronze layer │   │  • Company-centric API      │   │
│  └────────┬────────┘   └────────┬────────┘   └──────────────┬──────────────┘   │
│           │                     │                           │                   │
│           └─────────────────────┴───────────────────────────┘                   │
│                                 │                                               │
│                    ┌────────────┴────────────┐                                  │
│                    │    Integration Layer    │                                  │
│                    │                         │                                  │
│                    │  SEC() unified interface│                                  │
│                    │  Bronze → Silver → Gold │                                  │
│                    └─────────────────────────┘                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Decisions (Finalized)

### Decision 1: Push vs Pull Data Acquisition

**Decision**: Use BOTH approaches for different use cases.

| Approach | Implementation | When to Use |
|----------|---------------|-------------|
| **Push (Feeds)** | FeedSpine + FeedAdapter | Real-time monitoring, completeness |
| **Pull (APIs)** | QueryService + SEC APIs | Targeted lookups, backfill, discovery |

**Rationale**: Unified feeds provide completeness without needing to enumerate 500K+ CIKs. Direct APIs provide surgical precision for specific queries.

```python
# Push: Real-time monitoring (FeedSpine)
async with UnifiedFeedMonitor(form_types=["10-K"]) as monitor:
    async for filing in monitor.watch():
        await process(filing)

# Pull: On-demand lookup (QueryService)
async with QueryService() as qs:
    apple = await qs.submissions.get("320193")
```

### Decision 2: Data Layer Architecture

**Decision**: Bronze/Silver/Gold tiered storage with source attribution.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  BRONZE (Raw)              SILVER (Resolved)           GOLD (Enriched)          │
│  ─────────────             ────────────────            ─────────────            │
│                                                                                  │
│  • All sightings           • Canonical entities        • Knowledge graph        │
│  • Source tracking         • Deduplicated              • Relationships          │
│  • Content hashes          • CIK/ticker linked         • SigDev events          │
│  • seen_at timestamps      • Validated                 • Analytics-ready        │
│                                                                                  │
│  Storage: append-only      Storage: upsert             Storage: materialized    │
│  TTL: indefinite           TTL: indefinite             TTL: refresh on demand   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Decision 3: Entity Versioning Model

**Decision**: Point-in-time versioning with sighting-based change detection.

```python
@dataclass
class EntityVersion:
    entity_id: str           # Stable across versions
    version_id: str          # Unique per version
    valid_from: datetime     # When this became current
    valid_to: datetime       # When superseded (None = current)

    # Data at this point in time
    name: str
    identifiers: List[IdentifierClaim]
    relationships: List[EntityRelationship]

    # Lineage
    source_sightings: List[str]  # What informed this version
```

### Decision 4: SEC API Integration

**Decision**: SEC APIs are Query layer, NOT FeedAdapters.

| API | Purpose | Integration |
|-----|---------|-------------|
| **Submissions** | Company filing history | `QueryService.submissions` |
| **EFTS Search** | Cross-company discovery | `QueryService.search` |
| **Company Facts** | XBRL metrics | `QueryService.facts` |

**Implementation**: [py_sec_edgar/services/query_service.py](../py_sec_edgar/src/py_sec_edgar/services/query_service.py)

### Decision 5: Exhibit 21 Strategy

**Research Finding**: 92.4% of Exhibit 21s are in 10-K filings.

| Form | % of Exhibit 21s | Strategy |
|------|------------------|----------|
| 10-K | 92.4% | Primary source - monitor via feeds |
| S-1 | 2.3% | IPO filings - important for new companies |
| 10-Q | 1.9% | Rare - amendments/updates |
| Other | 3.4% | Edge cases - EFTS search for discovery |

---

## Package Integration Points

### EntitySpine ↔ FeedSpine

```python
# FeedSpine ingests, EntitySpine resolves
class SECFilingAdapter(FeedAdapter):
    async def fetch(self) -> AsyncIterator[RecordCandidate]:
        async for filing in self._fetch_rss():
            # FeedSpine captures the sighting
            yield RecordCandidate(
                natural_key=filing.accession_number,
                payload=filing.to_dict(),
            )

# EntitySpine resolves the CIK to canonical entity
entity = await entity_spine.resolve_by_cik(filing.cik)
```

### EntitySpine ↔ py-sec-edgar

```python
# py-sec-edgar uses EntitySpine for company resolution
async with SEC() as sec:
    # Under the hood: EntitySpine resolves ticker → CIK → Entity
    company = await sec.company("AAPL")

    # Company object has resolved entity
    print(company.cik)          # From EntitySpine
    print(company.entity_id)    # Canonical entity ID
```

### FeedSpine ↔ py-sec-edgar

```python
# py-sec-edgar uses FeedSpine for filing collection
class SECFeedCollector:
    def __init__(self, feed_spine: FeedSpine):
        self.feed_spine = feed_spine

        # Register SEC-specific feeds
        feed_spine.register_feed(SecRssFeedAdapter())
        feed_spine.register_feed(SecDailyIndexAdapter())

# Real-time monitoring via FeedSpine
async with UnifiedFeedMonitor() as monitor:
    async for filing in monitor.watch(form_types=["10-K"]):
        await sec.process(filing)
```

### Full Integration: SEC() Unified Interface

```python
from py_sec_edgar import SEC

async with SEC() as sec:
    # Company-centric access (EntitySpine + FeedSpine + QueryService)
    apple = await sec.company("AAPL")

    # Get filings (from Bronze layer, populated by FeedSpine)
    filings = await apple.filings(form_types=["10-K"], years=5)

    # Get Exhibit 21 (QueryService for discovery)
    for filing in filings:
        exhibit_21 = await filing.exhibit("EX-21")
        if exhibit_21:
            subsidiaries = await sec.parse_exhibit_21(exhibit_21)

            # Store to Silver layer (EntitySpine)
            for sub in subsidiaries:
                await sec.entity_spine.ingest_subsidiary(
                    parent=apple.entity_id,
                    subsidiary=sub,
                    source=filing.reference,
                )
```

---

## Feature Roadmap

### Phase 1: Foundation (Current)

| Feature | Status | Package | Notes |
|---------|--------|---------|-------|
| SEC RSS Feed Adapter | ✅ Done | FeedSpine | Real-time filing capture |
| SEC Daily Index Adapter | ✅ Done | FeedSpine | Daily catchup |
| Entity Resolution | ✅ Done | EntitySpine | Ticker/CIK/name resolution |
| Identifier Claims | ✅ Done | EntitySpine | Point-in-time identifiers |
| SEC Submissions API | ✅ Done | py-sec-edgar | Company filing history |
| SEC EFTS Search API | ✅ Done | py-sec-edgar | Full-text search |
| SEC Company Facts API | ✅ Done | py-sec-edgar | XBRL data |
| QueryService | ✅ Done | py-sec-edgar | Cached API access |
| Section Extraction | ✅ Done | py-sec-edgar | 10-K/10-Q sections |

### Phase 2: Data Model (Next)

| Feature | Status | Package | Priority |
|---------|--------|---------|----------|
| Bronze Layer Storage | 🔲 Todo | FeedSpine | P0 |
| Silver Layer (Resolved) | 🔲 Todo | EntitySpine | P0 |
| Entity Versioning | 🔲 Todo | EntitySpine | P0 |
| Subsidiary Relationships | 🔲 Todo | EntitySpine | P1 |
| Exhibit 21 Parser | 🔲 Todo | py-sec-edgar | P1 |
| Corporate Hierarchy | 🔲 Todo | EntitySpine | P1 |
| Change Detection | 🔲 Todo | EntitySpine | P2 |

### Phase 3: Company-Centric API

| Feature | Status | Package | Priority |
|---------|--------|---------|----------|
| `Company` model class | 🔲 Todo | py-sec-edgar | P0 |
| `sec.company()` method | 🔲 Todo | py-sec-edgar | P0 |
| Filing navigation | 🔲 Todo | py-sec-edgar | P0 |
| Auto-enrichment | 🔲 Todo | py-sec-edgar | P1 |
| Version-controlled ingestion | 🔲 Todo | EntitySpine | P1 |
| Coverage verification | 🔲 Todo | py-sec-edgar | P2 |

### Phase 4: Intelligence Layer

| Feature | Status | Package | Priority |
|---------|--------|---------|----------|
| SigDev Event Detection | 🔲 Todo | py-sec-edgar | P1 |
| Knowledge Graph | 🔲 Todo | EntitySpine | P2 |
| Risk Classification | 🔲 Todo | py-sec-edgar | P2 |
| Executive Extraction | 🔲 Todo | py-sec-edgar | P3 |
| EventSpine Integration | 🔲 Todo | Future | P3 |

---

## Detailed Implementation Tasks

### Task 1: Bronze Layer Storage (P0)

**Goal**: Store all filing sightings with source attribution.

```python
# Bronze layer schema
@dataclass
class FilingSighting:
    sighting_id: str
    accession_number: str
    cik: str
    form_type: str

    # Source tracking
    source: str  # "feed:rss", "feed:daily-index", "api:submissions"
    source_url: str
    source_updated_at: datetime
    seen_at: datetime

    # Dedup
    content_hash: str

    # Processing state
    processed: bool = False
    entity_id: Optional[str] = None
```

**Files to create**:
- `feedspine/src/feedspine/storage/bronze.py`
- `feedspine/src/feedspine/storage/backends/sqlite.py`
- `feedspine/src/feedspine/storage/backends/duckdb.py`

### Task 2: Entity Versioning (P0)

**Goal**: Track entity changes over time with full lineage.

```python
# Entity version tracking
class EntityVersionStore:
    async def get_current(self, entity_id: str) -> EntityVersion:
        """Get current version of entity."""

    async def get_as_of(self, entity_id: str, as_of: datetime) -> EntityVersion:
        """Get entity as it existed at a point in time."""

    async def create_version(
        self,
        entity_id: str,
        changes: Dict[str, Any],
        source_sightings: List[str],
    ) -> EntityVersion:
        """Create new version from changes."""
```

**Files to create**:
- `entityspine/src/entityspine/versioning/version_store.py`
- `entityspine/src/entityspine/versioning/change_detector.py`

### Task 3: Company Model (P0)

**Goal**: Rich company object for company-centric workflows.

```python
@dataclass
class Company:
    """Rich company object with filing access."""
    cik: str
    ticker: Optional[str]
    name: str
    entity_id: str  # EntitySpine canonical ID

    # Lazy-loaded
    _sec: "SEC"
    _filings: Optional[List[Filing]] = None
    _subsidiaries: Optional[List[Subsidiary]] = None

    async def filings(
        self,
        form_types: List[str] = None,
        years: int = 5,
    ) -> List[Filing]:
        """Get company's filings."""

    async def subsidiaries(self, as_of: date = None) -> List[Subsidiary]:
        """Get corporate hierarchy from Exhibit 21."""
```

**Files to create**:
- `py_sec_edgar/src/py_sec_edgar/models/company.py`
- `py_sec_edgar/src/py_sec_edgar/models/filing.py`
- `py_sec_edgar/src/py_sec_edgar/models/subsidiary.py`

### Task 4: Exhibit 21 Parser (P1)

**Goal**: Robust parser for subsidiary extraction.

```python
class Exhibit21Parser:
    """Parse Exhibit 21 to extract subsidiaries."""

    def parse(self, html_content: str) -> List[SubsidiaryInfo]:
        """Extract subsidiaries from Exhibit 21 HTML."""

    def compare_years(
        self,
        year1: List[SubsidiaryInfo],
        year2: List[SubsidiaryInfo],
    ) -> SubsidiaryChanges:
        """Detect changes between years."""
```

**Files to create**:
- `py_sec_edgar/src/py_sec_edgar/parsers/exhibit_21.py`
- `py_sec_edgar/src/py_sec_edgar/models/subsidiary.py`

### Task 5: Coverage Verification (P2)

**Goal**: Verify feed coverage against SEC API ground truth.

```python
async def verify_coverage(
    bronze: BronzeLayer,
    query_service: QueryService,
    cik: str,
    date_range: tuple[date, date],
) -> CoverageReport:
    """Compare what we've seen vs what SEC has."""

    # What we have (from feeds)
    seen = await bronze.query(cik=cik, date_range=date_range)

    # What SEC has (ground truth)
    subs = await query_service.submissions.get(cik)
    expected = [f for f in subs.filings if in_range(f, date_range)]

    # Find gaps
    missing = find_missing(seen, expected)

    return CoverageReport(
        total_expected=len(expected),
        total_seen=len(seen),
        missing=missing,
        coverage_pct=len(seen) / len(expected) * 100,
    )
```

---

## File Organization

```
py-sec-edgar/
├── docs/
│   └── vision/
│       ├── 10_ENTITYSPINE_UNIVERSAL_FABRIC.md
│       ├── 11_EVENTSPINE_AND_FUTURE_ROADMAP.md
│       ├── 12_UNIFIED_INTERFACE_DESIGN.md
│       ├── 13_COMPANY_CENTRIC_API.md
│       ├── 14_V4_MASTER_ROADMAP.md          ← THIS FILE
│       └── 15_DATA_MODEL_REFERENCE.md       ← Create next
│
├── entityspine/
│   └── src/entityspine/
│       ├── core/
│       │   ├── entity.py          # Entity model
│       │   └── claims.py          # Identifier claims
│       ├── stores/
│       │   ├── sqlite.py          # SQLite backend
│       │   └── duckdb.py          # DuckDB backend
│       └── versioning/
│           ├── version_store.py   # Version management
│           └── change_detector.py # Change detection
│
├── feedspine/
│   └── src/feedspine/
│       ├── protocols/
│       │   └── feed.py            # FeedAdapter protocol
│       ├── core/
│       │   └── feedspine.py       # Main orchestrator
│       └── storage/
│           ├── bronze.py          # Bronze layer
│           └── backends/
│               ├── sqlite.py
│               └── duckdb.py
│
└── py_sec_edgar/
    └── src/py_sec_edgar/
        ├── adapters/
        │   ├── sec_feeds.py       # SEC feed adapters
        │   └── sec_api.py         # SEC API clients
        ├── services/
        │   ├── query_service.py   # QueryService
        │   └── collector.py       # Filing collector
        ├── models/
        │   ├── company.py         # Company model
        │   ├── filing.py          # Filing model
        │   └── subsidiary.py      # Subsidiary model
        ├── parsers/
        │   └── exhibit_21.py      # Exhibit 21 parser
        └── sec.py                 # Main SEC() interface
```

---

## Success Metrics

### Phase 1 Complete When:
- [ ] Can monitor SEC filings in real-time via FeedSpine
- [ ] Can lookup any company via QueryService
- [ ] Can search for exhibits across all filers

### Phase 2 Complete When:
- [ ] All sightings stored in Bronze layer with lineage
- [ ] Entities have version history
- [ ] Can query "entity as of date X"

### Phase 3 Complete When:
- [ ] `sec.company("AAPL")` returns rich Company object
- [ ] Can navigate company → filings → exhibits
- [ ] Corporate hierarchy available from Exhibit 21

### Phase 4 Complete When:
- [ ] SigDev events detected from filings
- [ ] Knowledge graph links entities/events/filings
- [ ] Can answer "What changed for AAPL this quarter?"

---

## Related Documents

- [10_ENTITYSPINE_UNIVERSAL_FABRIC.md](10_ENTITYSPINE_UNIVERSAL_FABRIC.md) - Entity resolution architecture
- [11_EVENTSPINE_AND_FUTURE_ROADMAP.md](11_EVENTSPINE_AND_FUTURE_ROADMAP.md) - Event detection (future)
- [12_UNIFIED_INTERFACE_DESIGN.md](12_UNIFIED_INTERFACE_DESIGN.md) - API design patterns
- [13_COMPANY_CENTRIC_API.md](13_COMPANY_CENTRIC_API.md) - Company-centric workflows
- [ARCHITECTURE_UNIFIED_FEEDS_VS_APIS.md](../../ARCHITECTURE_UNIFIED_FEEDS_VS_APIS.md) - Push vs Pull decisions
