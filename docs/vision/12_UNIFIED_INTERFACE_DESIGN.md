# Unified Interface Design

**Purpose**: Lock down the exact functionality and user flows for EntitySpine, FeedSpine, and py-sec-edgar — both standalone and integrated.

> **Updated 2026-01-27**: See [14_V4_MASTER_ROADMAP.md](14_V4_MASTER_ROADMAP.md) for implementation status and [15_DATA_MODEL_REFERENCE.md](15_DATA_MODEL_REFERENCE.md) for canonical data models.

---

## Executive Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE THREE PILLARS                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────────┐   │
│  │   EntitySpine   │   │    FeedSpine    │   │      py-sec-edgar           │   │
│  │                 │   │                 │   │                             │   │
│  │  WHO is it?     │   │  WHAT happened? │   │  Download + Extract + Enrich│   │
│  │                 │   │                 │   │                             │   │
│  │  Entity         │   │  Feed capture   │   │  SEC domain logic           │   │
│  │  resolution     │   │  with history   │   │  on top of FeedSpine        │   │
│  └────────┬────────┘   └────────┬────────┘   └──────────────┬──────────────┘   │
│           │                     │                           │                   │
│           │                     │                           │                   │
│           └─────────────────────┴───────────────────────────┘                   │
│                                 │                                               │
│                                 ▼                                               │
│                    ┌─────────────────────────┐                                  │
│                    │    INTEGRATION LAYER    │                                  │
│                    │                         │                                  │
│                    │  py-sec-edgar.SEC()     │                                  │
│                    │  unifies all three      │                                  │
│                    └─────────────────────────┘                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

| Package | Core Question | Standalone Value | Integration Value |
|---------|--------------|------------------|-------------------|
| **EntitySpine** | "Who is this entity?" | Resolve any identifier to a canonical entity | Link filings to entities across time |
| **FeedSpine** | "What records exist?" | Capture any feed with deduplication | Track filing discovery across SEC feeds |
| **py-sec-edgar** | "What does this filing say?" | Download, parse, extract SEC filings | Build knowledge graph, LLM analysis |

---

## 1. EntitySpine: Identity Resolution

### 1.1 Standalone Functionality

EntitySpine is a **zero-dependency entity resolution library**. It works completely independently of SEC data.

```python
# =============================================================================
# STANDALONE ENTITYSPINE
# =============================================================================

from entityspine import SqliteStore

# Create store (works with :memory: or file path)
store = SqliteStore("./entities.db")
store.initialize()

# -----------------------------------------------------------------------------
# CORE CAPABILITY 1: SEC Company Resolution
# -----------------------------------------------------------------------------

# Load SEC's company_tickers.json (~14,000 companies)
store.load_sec_data()  # Auto-downloads from SEC

# Resolve by ticker
results = store.search_entities("AAPL")
entity, score = results[0]
print(f"{entity.primary_name}")  # Apple Inc.
print(f"CIK: {entity.source_id}")  # 0000320193

# Resolve by CIK
entities = store.get_entities_by_cik("0000320193")

# Resolve by name (fuzzy matching)
results = store.search_entities("Apple Computer")  # Historical name
entity, score = results[0]
print(f"{entity.primary_name}")  # Apple Inc. (score: 0.85)

# -----------------------------------------------------------------------------
# CORE CAPABILITY 2: Identifier Management (Claims Model)
# -----------------------------------------------------------------------------

from entityspine import Entity, IdentifierClaim, IdentifierScheme, ClaimStatus

# Create an entity with multiple identifiers
entity = Entity(
    primary_name="Apple Inc.",
    source_system="sec",
    source_id="0000320193",
)

# Add identifier claims (point-in-time correctness)
ticker_claim = IdentifierClaim(
    scheme=IdentifierScheme.TICKER,
    value="AAPL",
    source="nasdaq",
    status=ClaimStatus.ACTIVE,
    valid_from=date(1980, 12, 12),  # IPO date
)

cusip_claim = IdentifierClaim(
    scheme=IdentifierScheme.CUSIP,
    value="037833100",
    source="cusip_global",
    status=ClaimStatus.ACTIVE,
)

lei_claim = IdentifierClaim(
    scheme=IdentifierScheme.LEI,
    value="HWUPKR0MPOU8FGXBT394",
    source="gleif",
    status=ClaimStatus.ACTIVE,
)

# Save with claims
store.save_entity(entity, claims=[ticker_claim, cusip_claim, lei_claim])

# -----------------------------------------------------------------------------
# CORE CAPABILITY 3: Entity ↔ Security ↔ Listing Hierarchy
# -----------------------------------------------------------------------------

from entityspine import Entity, Security, Listing

# Entity (legal identity)
apple = Entity(primary_name="Apple Inc.", source_system="sec", source_id="0000320193")

# Security (tradeable instrument, belongs to entity)
common_stock = Security(
    entity_id=apple.entity_id,
    name="Apple Inc. Common Stock",
    security_type=SecurityType.COMMON_STOCK,
)

# Listing (exchange-specific, belongs to security)
nasdaq_listing = Listing(
    security_id=common_stock.security_id,
    ticker="AAPL",
    exchange_mic="XNAS",
    status=ListingStatus.ACTIVE,
)

# Why this matters: TICKER BELONGS ON LISTING, NOT ENTITY
# - Google has GOOGL (Class A) and GOOG (Class C) - same entity, different securities
# - FB became META - same entity, different ticker over time
# - Apple has AAPL on NASDAQ and APC on Frankfurt - same security, different listings

# -----------------------------------------------------------------------------
# CORE CAPABILITY 4: Identifier Validation
# -----------------------------------------------------------------------------

from entityspine import (
    validate_cik, validate_cusip, validate_isin, validate_lei,
    normalize_cik, normalize_ticker,
)

# Validate identifiers (returns True/False)
assert validate_cik("0000320193") == True
assert validate_cusip("037833100") == True  # Check digit validated
assert validate_isin("US0378331005") == True

# Normalize (pad CIK, uppercase ticker, etc.)
assert normalize_cik("320193") == "0000320193"  # Pad to 10 digits
assert normalize_ticker("aapl") == "AAPL"
```

### 1.2 EntitySpine Storage Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ENTITYSPINE STORAGE TIERS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 0: JSON File                           TIER 1: SQLite                 │
│  ┌─────────────────────────────────┐         ┌─────────────────────────────┐│
│  │  • Zero dependencies            │         │  • Zero dependencies        ││
│  │  • Human-readable               │         │  • FTS5 full-text search    ││
│  │  • Git-friendly                 │         │  • Relational queries       ││
│  │  • <10K entities                │         │  • <100K entities           ││
│  │                                 │         │                             ││
│  │  from entityspine import        │         │  from entityspine import    ││
│  │      JsonStore                  │         │      SqliteStore            ││
│  │  store = JsonStore("ents.json") │         │  store = SqliteStore("e.db")││
│  └─────────────────────────────────┘         └─────────────────────────────┘│
│                                                                              │
│  TIER 2: DuckDB                              TIER 3: PostgreSQL             │
│  ┌─────────────────────────────────┐         ┌─────────────────────────────┐│
│  │  • pip install entityspine[duck]│         │  • pip install [postgres]   ││
│  │  • Columnar analytics           │         │  • Full ACID                ││
│  │  • Fast aggregations            │         │  • Concurrent writes        ││
│  │  • <10M entities                │         │  • Unlimited scale          ││
│  │                                 │         │                             ││
│  │  from entityspine.stores import │         │  from entityspine.stores    ││
│  │      DuckDBStore                │         │      import PostgresStore   ││
│  │  store = DuckDBStore("e.duckdb")│         │  store = PostgresStore(url) ││
│  └─────────────────────────────────┘         └─────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 EntitySpine API Summary

```python
# =============================================================================
# ENTITYSPINE PUBLIC API
# =============================================================================

class SqliteStore:  # (or JsonStore, DuckDBStore, PostgresStore)
    """Storage backend for entities."""

    # Lifecycle
    def initialize(self) -> None: ...
    def close(self) -> None: ...

    # Entity CRUD
    def save_entity(self, entity: Entity, claims: List[IdentifierClaim] = None) -> str: ...
    def get_entity(self, entity_id: str) -> Entity | None: ...
    def delete_entity(self, entity_id: str) -> bool: ...

    # Resolution (the core value)
    def search_entities(self, query: str, limit: int = 10) -> List[Tuple[Entity, float]]: ...
    def get_entities_by_cik(self, cik: str) -> List[Entity]: ...
    def get_entities_by_ticker(self, ticker: str, as_of: date = None) -> List[Entity]: ...
    def get_entities_by_cusip(self, cusip: str) -> List[Entity]: ...
    def get_entities_by_isin(self, isin: str) -> List[Entity]: ...
    def get_entities_by_lei(self, lei: str) -> List[Entity]: ...

    # Bulk operations
    def load_sec_data(self) -> int: ...  # Returns count loaded
    def export_to_json(self, path: str) -> None: ...
    def import_from_json(self, path: str) -> int: ...

    # Claims
    def get_claims(self, entity_id: str) -> List[IdentifierClaim]: ...
    def add_claim(self, entity_id: str, claim: IdentifierClaim) -> None: ...


class EntityResolutionService:
    """High-level resolution with confidence scoring."""

    def __init__(self, store: SqliteStore): ...

    def resolve(self, query: str) -> ResolutionResult: ...
    def resolve_cik(self, cik: str) -> Entity | None: ...
    def resolve_ticker(self, ticker: str, as_of: date = None) -> Entity | None: ...
    def batch_resolve(self, queries: List[str]) -> List[ResolutionResult]: ...
```

---

## 2. FeedSpine: Feed Capture Framework

### 2.1 Standalone Functionality

FeedSpine is a **storage-agnostic feed capture framework**. It works with ANY feed, not just SEC.

```python
# =============================================================================
# STANDALONE FEEDSPINE
# =============================================================================

from feedspine import FeedSpine, MemoryStorage, DuckDBStorage
from feedspine import RSSFeedAdapter, JSONFeedAdapter
from feedspine.models import Layer, RecordCandidate
from datetime import datetime, UTC

# -----------------------------------------------------------------------------
# CORE CAPABILITY 1: Feed Collection with Deduplication
# -----------------------------------------------------------------------------

async def collect_news():
    storage = DuckDBStorage("feeds.duckdb")

    async with FeedSpine(storage=storage) as spine:
        # Register any RSS/Atom feed
        spine.register_feed(RSSFeedAdapter(
            name="hacker-news",
            url="https://news.ycombinator.com/rss",
        ))
        spine.register_feed(RSSFeedAdapter(
            name="techcrunch",
            url="https://techcrunch.com/feed/",
        ))

        # Collect - automatic deduplication by natural_key
        result = await spine.collect()

        print(f"Processed: {result.total_processed}")
        print(f"New records: {result.total_new}")
        print(f"Duplicates skipped: {result.total_duplicates}")

# -----------------------------------------------------------------------------
# CORE CAPABILITY 2: Sighting History
# -----------------------------------------------------------------------------

# Same record can appear in multiple feeds at different times
# FeedSpine tracks ALL sightings

# Example: An SEC filing appears in:
# 1. RSS feed (5 minutes after filing)
# 2. Daily index (next business day)
# 3. Quarterly index (end of quarter)

# FeedSpine stores it ONCE but tracks 3 sightings:
record = await storage.get_record("sec-edgar:0000320193-24-000081")
print(record.sightings)
# [
#   Sighting(feed="rss", captured_at="2024-11-01T09:05:00"),
#   Sighting(feed="daily", captured_at="2024-11-02T06:00:00"),
#   Sighting(feed="quarterly", captured_at="2024-12-31T12:00:00"),
# ]

# Key insight: captured_at vs published_at
print(record.published_at)  # 2024-11-01T09:00:00 (when SEC published)
print(record.captured_at)   # 2024-11-01T09:05:00 (when we first saw it)

# -----------------------------------------------------------------------------
# CORE CAPABILITY 3: Medallion Architecture (Bronze → Silver → Gold)
# -----------------------------------------------------------------------------

from feedspine.models import Layer

# Bronze: Raw data as captured
candidate = RecordCandidate(
    natural_key="my-feed:item-123",
    published_at=datetime.now(UTC),
    content={"raw_html": "<p>...</p>", "title": "Breaking News"},
)
record = await spine.store(candidate)  # Stored as Layer.BRONZE

# Silver: Validated and normalized
silver_record = record.promote(Layer.SILVER, enrichments={
    "validated": True,
    "normalized_title": "Breaking News - Stock Market Update",
    "entities_mentioned": ["AAPL", "TSLA"],
})

# Gold: Fully enriched (ML, aggregations, etc.)
gold_record = silver_record.promote(Layer.GOLD, enrichments={
    "sentiment_score": 0.75,
    "topic_classification": "markets",
    "impact_prediction": "high",
})

# -----------------------------------------------------------------------------
# CORE CAPABILITY 4: Checkpoints and Incremental Sync
# -----------------------------------------------------------------------------

from feedspine.core.checkpoint import FileCheckpointStore

checkpoint_store = FileCheckpointStore("./checkpoints")

async with FeedSpine(
    storage=storage,
    checkpoint_store=checkpoint_store,
) as spine:
    # First run: fetches everything
    await spine.collect()

    # Subsequent runs: only fetch new items since last checkpoint
    await spine.collect()  # Much faster - only delta

# -----------------------------------------------------------------------------
# CORE CAPABILITY 5: Custom Feed Adapters
# -----------------------------------------------------------------------------

from feedspine import BaseFeedAdapter
from typing import AsyncIterator

class MyCustomFeedAdapter(BaseFeedAdapter):
    """Adapter for any data source."""

    name = "my-custom-feed"

    async def fetch(self) -> AsyncIterator[RecordCandidate]:
        # Fetch from your API, database, file, etc.
        async for item in my_api.get_items():
            yield RecordCandidate(
                natural_key=f"my-feed:{item['id']}",
                published_at=item['timestamp'],
                content=item['data'],
            )
```

### 2.2 FeedSpine Storage Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FEEDSPINE STORAGE TIERS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  In-Memory (Testing)                         DuckDB (Production)            │
│  ┌─────────────────────────────────┐         ┌─────────────────────────────┐│
│  │  from feedspine import          │         │  pip install feedspine[duck]││
│  │      MemoryStorage              │         │                             ││
│  │  storage = MemoryStorage()      │         │  from feedspine import      ││
│  │                                 │         │      DuckDBStorage          ││
│  │  • Fast for tests               │         │  storage = DuckDBStorage(   ││
│  │  • No persistence               │         │      "feeds.duckdb"         ││
│  │  • Resets on restart            │         │  )                          ││
│  └─────────────────────────────────┘         │                             ││
│                                              │  • Single file, portable    ││
│  PostgreSQL (Scale)                          │  • Columnar analytics       ││
│  ┌─────────────────────────────────┐         │  • Fast date-range queries  ││
│  │  pip install feedspine[postgres]│         └─────────────────────────────┘│
│  │                                 │                                        │
│  │  from feedspine import          │         Redis (Real-time)              │
│  │      PostgresStorage            │         ┌─────────────────────────────┐│
│  │  storage = PostgresStorage(url) │         │  pip install feedspine[redis││
│  │                                 │         │                             ││
│  │  • Concurrent writes            │         │  from feedspine import      ││
│  │  • Full ACID                    │         │      RedisStorage           ││
│  │  • Production scale             │         │                             ││
│  └─────────────────────────────────┘         │  • Sub-ms access            ││
│                                              │  • Pub/sub notifications    ││
│                                              └─────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 FeedSpine API Summary

```python
# =============================================================================
# FEEDSPINE PUBLIC API
# =============================================================================

class FeedSpine:
    """Main orchestrator for feed collection."""

    def __init__(
        self,
        storage: StorageProtocol,
        checkpoint_store: CheckpointStore = None,
    ): ...

    # Lifecycle
    async def __aenter__(self) -> "FeedSpine": ...
    async def __aexit__(self, *args) -> None: ...

    # Feed registration
    def register_feed(self, adapter: FeedAdapter) -> None: ...
    def unregister_feed(self, name: str) -> None: ...

    # Collection
    async def collect(self, feeds: List[str] = None) -> CollectionResult: ...
    async def collect_one(self, feed_name: str) -> CollectionResult: ...

    # Direct storage
    async def store(self, candidate: RecordCandidate) -> Record: ...
    async def get(self, natural_key: str) -> Record | None: ...

    # Query
    async def query(self, spec: QuerySpec) -> List[Record]: ...
    async def count(self, spec: QuerySpec = None) -> int: ...


@dataclass
class CollectionResult:
    """Result of a collection run."""
    total_processed: int
    total_new: int
    total_duplicates: int
    total_errors: int
    duration_seconds: float
    feeds_collected: List[str]


@dataclass
class Record:
    """A captured record with full history."""
    record_id: str
    natural_key: str
    published_at: datetime
    captured_at: datetime
    content: dict
    layer: Layer  # BRONZE, SILVER, GOLD
    sightings: List[Sighting]
    enrichments: dict

    def promote(self, layer: Layer, enrichments: dict) -> "Record": ...


@dataclass
class Sighting:
    """When/where a record was observed."""
    feed_name: str
    captured_at: datetime
    metadata: dict = field(default_factory=dict)
```

---

## 3. py-sec-edgar: SEC Domain Layer

### 3.1 Standalone Functionality

py-sec-edgar provides **SEC-specific functionality** built on FeedSpine.

```python
# =============================================================================
# STANDALONE PY-SEC-EDGAR
# =============================================================================

from py_sec_edgar import SEC, Forms, Sections, Exhibits
from datetime import date

async with SEC(data_dir="./sec_data") as sec:

    # -------------------------------------------------------------------------
    # CORE CAPABILITY 1: Download Filings
    # -------------------------------------------------------------------------

    result = await sec.download(
        tickers=["AAPL", "MSFT", "NVDA"],
        forms=[Forms.FORM_10K, Forms.FORM_10Q],
        days=365,  # Last year
    )
    print(f"Downloaded {result.file_count} files")
    print(f"Companies: {result.company_count}")
    print(f"Total size: {result.total_size_mb:.1f} MB")

    # By date range
    result = await sec.download(
        tickers=["AAPL"],
        forms=[Forms.FORM_8K],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
    )

    # -------------------------------------------------------------------------
    # CORE CAPABILITY 2: List and Search Downloaded Filings
    # -------------------------------------------------------------------------

    # List all downloaded filings for a company
    filings = await sec.list_filings(ticker="AAPL", form="10-K")
    for f in filings:
        print(f"{f.filed_date}: {f.form_type} - {f.accession_number}")

    # Search across all downloaded filings
    refs = await sec.filings.search(
        tickers=["AAPL", "MSFT"],
        forms=[Forms.FORM_10K],
        filed_after="2024-01-01",
    )

    # -------------------------------------------------------------------------
    # CORE CAPABILITY 3: Section Extraction
    # -------------------------------------------------------------------------

    # Extract specific sections from a filing
    content = await sec.extract(
        filings[0],
        sections=[
            Sections.ITEM_1_BUSINESS,
            Sections.ITEM_1A_RISK_FACTORS,
            Sections.ITEM_7_MDA,
        ],
    )

    print(f"Total words: {content.word_count}")
    for section in content.sections:
        print(f"  {section.title}: {section.word_count} words")
        print(f"  Preview: {section.text[:200]}...")

    # Extract all sections (default)
    full_content = await sec.extract(filings[0])

    # -------------------------------------------------------------------------
    # CORE CAPABILITY 4: Exhibit Handling
    # -------------------------------------------------------------------------

    # List exhibits in a filing
    exhibits = await sec.list_exhibits(filings[0])
    for ex in exhibits:
        print(f"{ex.exhibit_type}: {ex.description}")

    # Download specific exhibit types
    contracts = await sec.download_exhibits(
        filings[0],
        types=[Exhibits.EX_10, Exhibits.EX_10_1],  # Material contracts
    )

    # -------------------------------------------------------------------------
    # CORE CAPABILITY 5: Typed Enums (Discovery)
    # -------------------------------------------------------------------------

    # 169 SEC form types
    print(Forms.FORM_10K)      # "10-K"
    print(Forms.FORM_8K)       # "8-K"
    print(Forms.FORM_DEF_14A)  # "DEF 14A"

    # Section enums for extraction
    print(Sections.ITEM_1A_RISK_FACTORS)  # "item_1a"
    print(Sections.ITEM_7_MDA)            # "item_7"

    # Exhibit types
    print(Exhibits.EX_21)     # "EX-21" (Subsidiaries)
    print(Exhibits.EX_10_1)   # "EX-10.1" (Material contract)
```

### 3.2 py-sec-edgar Built on FeedSpine

Under the hood, py-sec-edgar uses FeedSpine for filing discovery:

```python
# =============================================================================
# HOW PY-SEC-EDGAR USES FEEDSPINE (internal architecture)
# =============================================================================

# py_sec_edgar/services/collector.py (simplified)

from feedspine import FeedSpine, DuckDBStorage
from feedspine import RSSFeedAdapter, JSONFeedAdapter

class SECFeedCollector:
    """Collects filings from SEC feeds using FeedSpine."""

    def __init__(self, data_dir: Path):
        self.storage = DuckDBStorage(data_dir / "filings.duckdb")
        self.spine = FeedSpine(storage=self.storage)

        # Register SEC-specific feed adapters
        self.spine.register_feed(SECRSSAdapter())      # Real-time RSS
        self.spine.register_feed(SECDailyAdapter())    # Daily index
        self.spine.register_feed(SECQuarterlyAdapter())# Full index

    async def sync(self, days: int = 7) -> SyncResult:
        """Sync filings from SEC feeds."""
        result = await self.spine.collect()
        return SyncResult(
            new_filings=result.total_new,
            duplicates=result.total_duplicates,
        )


# The key insight: FeedSpine handles deduplication
# Filing appears in RSS (immediate) → Daily index (next day) → Quarterly (end of Q)
# FeedSpine stores it ONCE, tracks 3 sightings
```

### 3.3 py-sec-edgar API Summary

```python
# =============================================================================
# PY-SEC-EDGAR PUBLIC API
# =============================================================================

class SEC:
    """Simple interface to SEC filings."""

    # Sub-interfaces
    filings: FilingsInterface
    graph: GraphInterface
    intelligence: IntelligenceInterface

    # Lifecycle
    async def __aenter__(self) -> "SEC": ...
    async def __aexit__(self, *args) -> None: ...

    # High-level operations
    async def download(
        self,
        tickers: List[str] = None,
        ciks: List[str] = None,
        forms: List[Forms | str] = None,
        days: int = None,
        start_date: date = None,
        end_date: date = None,
    ) -> DownloadResult: ...

    async def list_filings(
        self,
        ticker: str = None,
        cik: str = None,
        form: str = None,
        limit: int = 100,
    ) -> List[Filing]: ...

    async def extract(
        self,
        filing: Filing,
        sections: List[Sections] = None,
    ) -> ExtractedContent: ...

    async def sync(self, days: int = 7) -> SyncResult: ...


class FilingsInterface:
    """Discovery and search operations."""

    async def search(
        self,
        tickers: List[str] = None,
        forms: List[Forms] = None,
        filed_after: date | str = None,
        filed_before: date | str = None,
        limit: int = 100,
    ) -> List[FilingRef]: ...

    async def latest(
        self,
        forms: List[Forms] = None,
        days: int = 7,
        limit: int = 100,
    ) -> List[FilingRef]: ...

    async def get(self, accession: str) -> FilingRef | None: ...
    async def count(self, forms: List[Forms] = None) -> int: ...


class GraphInterface:
    """Knowledge graph queries (requires enrichment)."""

    async def find_suppliers(self, company: str) -> List[RelatedEntity]: ...
    async def find_customers(self, company: str) -> List[RelatedEntity]: ...
    async def find_competitors(self, company: str) -> List[RelatedEntity]: ...
    async def find_path(self, from_: str, to: str) -> PathResult: ...


class IntelligenceInterface:
    """LLM-powered analysis (requires configure_llm())."""

    async def extract_entities(self, text: str) -> List[ExtractedEntity]: ...
    async def extract_contracts(self, text: str) -> List[ExtractedContract]: ...
    async def ask(self, filing: Filing, question: str) -> str: ...
```

---

## 4. Integration: How They Work Together

### 4.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INTEGRATION ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                              USER CODE                                   │   │
│   │                                                                          │   │
│   │  async with SEC() as sec:                                               │   │
│   │      # Downloads, resolves tickers, extracts, enriches                  │   │
│   │      result = await sec.download(tickers=["AAPL"], forms=["10-K"])     │   │
│   │                                                                          │   │
│   └───────────────────────────────────┬─────────────────────────────────────┘   │
│                                       │                                          │
│   ┌───────────────────────────────────▼─────────────────────────────────────┐   │
│   │                            py-sec-edgar                                  │   │
│   │                                                                          │   │
│   │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │   │
│   │  │ SEC Class    │   │ Extraction   │   │ Graph        │                │   │
│   │  │ (facade)     │   │ Engine       │   │ Storage      │                │   │
│   │  └──────┬───────┘   └──────────────┘   └──────────────┘                │   │
│   │         │                                                               │   │
│   └─────────┼───────────────────────────────────────────────────────────────┘   │
│             │                                                                    │
│   ┌─────────▼───────────────────────────────────────────────────────────────┐   │
│   │                             FeedSpine                                    │   │
│   │                                                                          │   │
│   │  SEC Feeds → Dedup → Sighting History → Filing Records                  │   │
│   │                                                                          │   │
│   │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐                │   │
│   │  │ RSS Adapter  │   │ Daily Adapter│   │ Full Adapter │                │   │
│   │  │ (real-time)  │   │ (next day)   │   │ (quarterly)  │                │   │
│   │  └──────────────┘   └──────────────┘   └──────────────┘                │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                       │                                          │
│   ┌───────────────────────────────────▼─────────────────────────────────────┐   │
│   │                            EntitySpine                                   │   │
│   │                                                                          │   │
│   │  Ticker → CIK → Entity                                                  │   │
│   │  AAPL → 0000320193 → "Apple Inc." (with LEI, CUSIP, history)           │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Integration Flow: Download Filings

```python
# =============================================================================
# FLOW: User calls sec.download(tickers=["AAPL"], forms=["10-K"])
# =============================================================================

# STEP 1: py-sec-edgar receives request
async with SEC() as sec:
    result = await sec.download(tickers=["AAPL"], forms=["10-K"])

# STEP 2: EntitySpine resolves ticker → CIK
# Inside py-sec-edgar:
from entityspine import EntityResolutionService

resolver = EntityResolutionService(store)
result = resolver.resolve_ticker("AAPL")
cik = result.entity.source_id  # "0000320193"

# STEP 3: FeedSpine queries for filings by CIK
# Inside py-sec-edgar:
filings = await self.spine.query(QuerySpec(
    filters={"cik": cik, "form_type": "10-K"},
    order_by="filed_date",
    descending=True,
))

# STEP 4: Download actual filing content
for filing in filings:
    content = await self.http_client.get(filing.filing_url)
    await self.save_to_disk(filing, content)

# STEP 5: Return result to user
return DownloadResult(
    filings=filings,
    file_count=len(filings),
    total_size_mb=total_size / 1024 / 1024,
)
```

### 4.3 Integration Flow: Entity Extraction and Graph

```python
# =============================================================================
# FLOW: Extract entities and build knowledge graph
# =============================================================================

async with SEC() as sec:
    # Download and extract Apple's 10-K
    filings = await sec.list_filings(ticker="AAPL", form="10-K", limit=1)
    content = await sec.extract(filings[0], sections=[Sections.ITEM_1_BUSINESS])

    # STEP 1: Extract raw entity mentions from text
    # (Uses LLM or NER model)
    mentions = await sec.intelligence.extract_entities(content.text)
    # [
    #   EntityMention(name="TSMC", context="Item 1", type="supplier"),
    #   EntityMention(name="Samsung", context="Item 1", type="supplier"),
    #   EntityMention(name="Foxconn", context="Item 1", type="supplier"),
    # ]

    # STEP 2: Resolve mentions to canonical entities via EntitySpine
    for mention in mentions:
        resolved = resolver.resolve(mention.name)
        if resolved.status == ResolutionStatus.FOUND:
            mention.resolved_entity_id = resolved.entity.entity_id
            mention.resolved_cik = resolved.entity.source_id

    # STEP 3: Store in knowledge graph with evidence
    await sec.graph.add_relationship(
        source_cik="0000320193",  # Apple
        target_entity_id=mention.resolved_entity_id,  # TSMC
        relationship="SUPPLIES_TO",
        evidence={
            "accession_number": filings[0].accession_number,
            "section": "Item 1",
            "excerpt": "...manufactured primarily by TSMC...",
            "confidence": 0.95,
        }
    )

    # STEP 4: Query the graph
    suppliers = await sec.graph.find_suppliers("AAPL")
    # [
    #   RelatedEntity(name="TSMC", relationship="supplier", evidence_count=15),
    #   RelatedEntity(name="Samsung", relationship="supplier", evidence_count=8),
    # ]
```

### 4.4 Dependency Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DEPENDENCY MATRIX                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                          EntitySpine    FeedSpine    py-sec-edgar               │
│                          ──────────     ─────────    ────────────               │
│                                                                                  │
│  EntitySpine              -             ❌            ❌                         │
│  (identity resolution)    standalone    not needed   not needed                 │
│                                                                                  │
│  FeedSpine                ❌            -             ❌                         │
│  (feed capture)           not needed    standalone   not needed                 │
│                                                                                  │
│  py-sec-edgar             ✅ optional   ✅ required  -                          │
│  (SEC domain)             enhances      core dep     standalone                 │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  INSTALLATION COMBOS:                                                           │
│                                                                                  │
│  1. EntitySpine only:     pip install entityspine                               │
│     Use case: Ticker/CIK lookup for your own app                               │
│                                                                                  │
│  2. FeedSpine only:       pip install feedspine                                 │
│     Use case: Capture any feed (RSS, API) with dedup                           │
│                                                                                  │
│  3. py-sec-edgar only:    pip install py-sec-edgar                              │
│     Use case: Download SEC filings (includes FeedSpine)                        │
│     Note: EntitySpine optional but enhances resolution                         │
│                                                                                  │
│  4. Full stack:           pip install py-sec-edgar[full]                        │
│     Use case: Complete SEC analysis with entity resolution                     │
│     Installs: py-sec-edgar + entityspine[sqlite] + feedspine[duckdb]          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. User Flows

### 5.1 Flow: New User Just Wants Apple's 10-K

```python
# Simplest possible usage - no configuration needed

from py_sec_edgar import SEC, Forms

async with SEC() as sec:
    # Download Apple's last 5 years of 10-Ks
    result = await sec.download(
        tickers=["AAPL"],
        forms=[Forms.FORM_10K],
        years=5
    )
    print(f"Downloaded {result.file_count} filings")

# That's it! Files are in ./sec_data/
```

### 5.2 Flow: Researcher Wants Risk Factor Analysis

```python
from py_sec_edgar import SEC, Forms, Sections

async with SEC() as sec:
    # Get recent 10-Ks for tech companies
    result = await sec.download(
        tickers=["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
        forms=[Forms.FORM_10K],
        years=3
    )

    # Extract risk factors from each
    for filing in await sec.list_filings(form="10-K"):
        content = await sec.extract(filing, sections=[Sections.ITEM_1A_RISK_FACTORS])

        # Analyze risks
        print(f"\n{filing.company_name} ({filing.filed_date}):")
        print(f"  Risk section: {content.sections[0].word_count} words")

        # With LLM analysis (optional)
        if sec.intelligence.is_configured:
            risks = await sec.intelligence.extract_risks(content.text)
            for risk in risks[:5]:
                print(f"  - {risk.category}: {risk.title}")
```

### 5.3 Flow: Quant Building Supply Chain Model

```python
from py_sec_edgar import SEC, Forms
from entityspine import SqliteStore, EntityResolutionService

# Initialize EntitySpine for entity resolution
store = SqliteStore("./entities.db")
store.initialize()
store.load_sec_data()
resolver = EntityResolutionService(store)

async with SEC(entity_resolver=resolver) as sec:
    # Download all tech sector 10-Ks
    result = await sec.download(
        sic_codes=["7370", "7371", "7372"],  # Software/services
        forms=[Forms.FORM_10K],
        years=5
    )

    # Build supply chain graph
    await sec.graph.enrich(
        tickers=["NVDA", "AMD", "INTC", "TSMC"],
        sections=[Sections.ITEM_1_BUSINESS, Sections.ITEM_7_MDA],
    )

    # Query relationships
    nvda_suppliers = await sec.graph.find_suppliers("NVDA")
    for s in nvda_suppliers:
        print(f"{s.name}: {s.mention_count} mentions, confidence {s.confidence:.2f}")

    # Find common suppliers
    common = await sec.graph.find_common_suppliers(["NVDA", "AMD"])
    print(f"\nCommon suppliers: {[s.name for s in common]}")
```

### 5.4 Flow: Using EntitySpine Standalone

```python
from entityspine import SqliteStore

# No SEC downloads needed - just entity resolution
store = SqliteStore("./entities.db")
store.initialize()
store.load_sec_data()

# Your internal system has company names from various sources
company_names = [
    "Apple",
    "MSFT",
    "Alphabet Inc",
    "Meta Platforms",
    "Taiwan Semiconductor",
]

# Resolve each to canonical entity
for name in company_names:
    results = store.search_entities(name)
    if results:
        entity, score = results[0]
        print(f"{name} → {entity.primary_name} (CIK: {entity.source_id}, score: {score:.2f})")
    else:
        print(f"{name} → NOT FOUND")

# Output:
# Apple → Apple Inc. (CIK: 0000320193, score: 0.95)
# MSFT → Microsoft Corporation (CIK: 0000789019, score: 1.00)
# Alphabet Inc → Alphabet Inc. (CIK: 0001652044, score: 0.98)
# Meta Platforms → Meta Platforms, Inc. (CIK: 0001326801, score: 0.97)
# Taiwan Semiconductor → Taiwan Semiconductor Manufacturing Company Limited (CIK: 0001046179, score: 0.85)
```

### 5.5 Flow: Using FeedSpine Standalone

```python
from feedspine import FeedSpine, DuckDBStorage, RSSFeedAdapter

# Generic feed collection - nothing SEC-specific
storage = DuckDBStorage("./feeds.duckdb")

async with FeedSpine(storage=storage) as spine:
    # Register ANY RSS feeds
    spine.register_feed(RSSFeedAdapter(
        name="techcrunch",
        url="https://techcrunch.com/feed/",
    ))
    spine.register_feed(RSSFeedAdapter(
        name="ars-technica",
        url="https://feeds.arstechnica.com/arstechnica/index",
    ))

    # Collect with deduplication
    result = await spine.collect()
    print(f"New articles: {result.total_new}")
    print(f"Duplicates: {result.total_duplicates}")

    # Query collected records
    recent = await spine.query(QuerySpec(
        filters={"feed": "techcrunch"},
        order_by="published_at",
        descending=True,
        limit=10,
    ))

    for record in recent:
        print(f"{record.published_at}: {record.content['title']}")
```

---

## 6. CLI Interface

### 6.1 Unified CLI Design

```bash
# =============================================================================
# PY-SEC-EDGAR CLI
# =============================================================================

# Download filings
sec download --tickers AAPL MSFT --forms 10-K 10-Q --days 365
sec download --ciks 0000320193 --forms 10-K --years 5
sec download --sic 7370 --forms 10-K --start 2023-01-01 --end 2024-12-31

# List downloaded filings
sec list --ticker AAPL --form 10-K
sec list --recent 30  # Last 30 days

# Extract sections
sec extract 0000320193-24-000081 --sections item_1a item_7
sec extract AAPL --form 10-K --year 2024 --sections all

# Graph operations
sec graph enrich --tickers NVDA AAPL --forms 10-K
sec graph suppliers NVDA
sec graph customers TSLA
sec graph path NVDA AAPL

# Sync feeds
sec sync --days 7
sec sync --full  # Full historical sync

# =============================================================================
# ENTITYSPINE CLI
# =============================================================================

# Resolve identifiers
entityspine resolve AAPL
entityspine resolve 0000320193
entityspine resolve "Apple Inc"

# Search entities
entityspine search "semiconductor"
entityspine search --cik 0000320193

# Load data
entityspine load-sec  # Download SEC company_tickers.json
entityspine import companies.csv --mapping config.yaml

# =============================================================================
# FEEDSPINE CLI
# =============================================================================

# Feed management
feedspine add-feed hacker-news https://news.ycombinator.com/rss
feedspine list-feeds
feedspine remove-feed hacker-news

# Collection
feedspine collect
feedspine collect --feed hacker-news

# Query
feedspine query --feed hacker-news --limit 10
feedspine stats
```

### 6.2 CLI Output Examples

```bash
$ sec download --tickers AAPL --forms 10-K --years 3

📥 Downloading SEC Filings
  Tickers: AAPL
  Forms: 10-K
  Years: 3

🔍 Resolving tickers...
  AAPL → Apple Inc. (CIK: 0000320193) ✓

📡 Syncing SEC feeds...
  RSS feed: 0 new
  Daily index: 3 new

⬇️ Downloading files...
  [████████████████████] 3/3 filings

✅ Complete!
  Files: 3
  Size: 45.2 MB
  Location: ./sec_data/filings/

$ sec graph suppliers NVDA

🔗 Suppliers of NVIDIA Corporation

┌─────────────────────────────────────┬──────────┬────────────┬─────────────┐
│ Supplier                            │ Mentions │ Confidence │ Last Seen   │
├─────────────────────────────────────┼──────────┼────────────┼─────────────┤
│ Taiwan Semiconductor (TSMC)         │ 47       │ 0.98       │ 2024-11-15  │
│ Samsung Electronics                 │ 23       │ 0.95       │ 2024-11-15  │
│ SK Hynix                            │ 18       │ 0.92       │ 2024-11-15  │
│ Micron Technology                   │ 12       │ 0.89       │ 2024-11-15  │
│ ASML Holding                        │ 8        │ 0.85       │ 2024-11-15  │
└─────────────────────────────────────┴──────────┴────────────┴─────────────┘

Source: 15 filings analyzed (2019-2024)
```

---

## 7. Storage Summary

### 7.1 What Stores What

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STORAGE SUMMARY                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  COMPONENT        │ DEFAULT BACKEND │ STORES                                    │
│  ────────────────────────────────────────────────────────────────────────────── │
│  EntitySpine      │ SQLite          │ • Entities (companies, people)            │
│                   │ entities.db     │ • Securities (stocks, bonds)              │
│                   │                 │ • Listings (exchange tickers)             │
│                   │                 │ • Identifier claims (CIK, CUSIP, LEI)     │
│                   │                 │ • Resolution history                      │
│                                                                                  │
│  FeedSpine        │ DuckDB          │ • Feed items (natural_key deduped)        │
│                   │ filings.duckdb  │ • Sighting history (when/where seen)      │
│                   │                 │ • Checkpoints (incremental sync)          │
│                   │                 │ • Layer metadata (bronze/silver/gold)     │
│                                                                                  │
│  py-sec-edgar     │ DuckDB          │ • Extracted sections (text, metadata)     │
│  (sections)       │ sections.duckdb │ • Extraction jobs (batch tracking)        │
│                   │                 │ • Section search index                    │
│                                                                                  │
│  py-sec-edgar     │ DuckDB          │ • Graph nodes (entities)                  │
│  (graph)          │ graph.duckdb    │ • Graph edges (relationships)             │
│                   │                 │ • Evidence (supporting text)              │
│                   │                 │ • Temporal history                        │
│                                                                                  │
│  py-sec-edgar     │ Filesystem      │ • Raw filing HTML/SGML                    │
│  (downloads)      │ ./sec_data/     │ • Exhibits (PDFs, contracts)              │
│                   │                 │ • XBRL data                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Directory Structure

```
./sec_data/                          # Default data directory
├── entities.db                      # EntitySpine SQLite
├── filings.duckdb                   # FeedSpine DuckDB
├── sections.duckdb                  # py-sec-edgar extractions
├── graph.duckdb                     # py-sec-edgar knowledge graph
├── filings/                         # Downloaded filing files
│   ├── 0000320193/                  # By CIK
│   │   ├── 000032019324000081/      # By accession
│   │   │   ├── aapl-20240928.htm    # Primary document
│   │   │   ├── aapl-20240928_g1.jpg # Graphics
│   │   │   └── Financial_Report.xlsx# Exhibits
│   │   └── ...
│   └── ...
├── checkpoints/                     # FeedSpine sync checkpoints
│   ├── rss.json
│   ├── daily.json
│   └── quarterly.json
└── cache/                           # HTTP response cache
    └── company_tickers.json         # SEC company list
```

---

## 8. Model Summary

### 8.1 Core Models by Package

```python
# =============================================================================
# ENTITYSPINE MODELS
# =============================================================================

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

class EntityType(Enum):
    COMPANY = "company"
    PERSON = "person"
    FUND = "fund"
    GOVERNMENT = "government"

class IdentifierScheme(Enum):
    CIK = "cik"
    TICKER = "ticker"
    CUSIP = "cusip"
    ISIN = "isin"
    LEI = "lei"
    FIGI = "figi"
    EIN = "ein"

@dataclass
class Entity:
    entity_id: str
    primary_name: str
    entity_type: EntityType
    source_system: str  # "sec", "gleif", etc.
    source_id: str      # CIK for SEC entities
    created_at: datetime
    updated_at: datetime

@dataclass
class IdentifierClaim:
    claim_id: str
    entity_id: str
    scheme: IdentifierScheme
    value: str
    source: str
    status: ClaimStatus
    valid_from: date | None
    valid_to: date | None

@dataclass
class Security:
    security_id: str
    entity_id: str
    name: str
    security_type: SecurityType

@dataclass
class Listing:
    listing_id: str
    security_id: str
    ticker: str
    exchange_mic: str
    status: ListingStatus


# =============================================================================
# FEEDSPINE MODELS
# =============================================================================

class Layer(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"

@dataclass
class Record:
    record_id: str
    natural_key: str      # Unique business ID
    published_at: datetime
    captured_at: datetime
    layer: Layer
    content: dict
    sightings: list[Sighting]
    enrichments: dict

@dataclass
class Sighting:
    feed_name: str
    captured_at: datetime
    metadata: dict

@dataclass
class RecordCandidate:
    natural_key: str
    published_at: datetime
    content: dict


# =============================================================================
# PY-SEC-EDGAR MODELS
# =============================================================================

@dataclass
class Filing:
    accession_number: AccessionNumber
    cik: CIK
    company_name: str
    form_type: str
    filed_date: date
    period_of_report: date | None
    filing_url: str

@dataclass
class ExtractedSection:
    section_key: str
    title: str
    text: str
    word_count: int
    start_offset: int
    end_offset: int

@dataclass
class ExtractedContent:
    filing: Filing
    sections: list[ExtractedSection]
    word_count: int
    extracted_at: datetime

@dataclass
class GraphNode:
    node_id: str
    node_type: NodeType  # COMPANY, PERSON, PRODUCT
    name: str
    properties: dict

@dataclass
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    relationship: RelationshipType  # SUPPLIES_TO, COMPETES_WITH
    evidence: list[EdgeEvidence]
    confidence: float
```

---

## 9. Error Handling

### 9.1 Exception Hierarchy

```python
# =============================================================================
# ENTITYSPINE EXCEPTIONS
# =============================================================================

class EntitySpineError(Exception):
    """Base exception for EntitySpine."""
    pass

class EntityNotFoundError(EntitySpineError):
    """Entity not found in store."""
    pass

class ResolutionError(EntitySpineError):
    """Failed to resolve identifier."""
    pass

class StorageError(EntitySpineError):
    """Storage backend error."""
    pass


# =============================================================================
# FEEDSPINE EXCEPTIONS
# =============================================================================

class FeedSpineError(Exception):
    """Base exception for FeedSpine."""
    pass

class FeedError(FeedSpineError):
    """Error fetching from a feed."""
    pass

class StorageError(FeedSpineError):
    """Storage backend error."""
    pass


# =============================================================================
# PY-SEC-EDGAR EXCEPTIONS
# =============================================================================

class SECEdgarError(Exception):
    """Base exception for py-sec-edgar."""
    pass

class RateLimitError(SECEdgarError):
    """SEC rate limit exceeded (10 req/sec)."""
    pass

class FilingNotFoundError(SECEdgarError):
    """Filing not found at SEC."""
    pass

class ExtractionError(SECEdgarError):
    """Failed to extract sections from filing."""
    pass
```

---

## 10. Configuration

### 10.1 Configuration Options

```python
# =============================================================================
# PY-SEC-EDGAR CONFIGURATION
# =============================================================================

from py_sec_edgar import configure

# Required: SEC requires user agent
configure(user_agent="MyApp admin@example.com")

# Optional: Custom data directory
configure(data_dir="./my_data")

# Optional: Rate limiting (default: 10 req/sec per SEC rules)
configure(requests_per_second=5)  # Be extra polite

# Optional: LLM for intelligence features
configure_llm(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o",
)

# Optional: EntitySpine integration
from entityspine import SqliteStore
store = SqliteStore("./entities.db")
configure(entity_store=store)


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

# SEC_EDGAR_USER_AGENT="MyApp admin@example.com"
# SEC_EDGAR_DATA_DIR="./sec_data"
# SEC_EDGAR_REQUESTS_PER_SECOND="10"
# OPENAI_API_KEY="sk-..."


# =============================================================================
# PYPROJECT.TOML CONFIGURATION
# =============================================================================

# [tool.py-sec-edgar]
# user_agent = "MyApp admin@example.com"
# data_dir = "./sec_data"
# storage_backend = "duckdb"
#
# [tool.entityspine]
# store_path = "./entities.db"
# auto_load_sec = true
#
# [tool.feedspine]
# storage = "duckdb"
# storage_path = "./feeds.duckdb"
```

---

## Summary

| Package | Standalone | Integrated | User Gets |
|---------|-----------|------------|-----------|
| **EntitySpine** | Resolve any identifier to canonical entity | Link extracted entities to graph | "AAPL" → Apple Inc. with CIK, LEI, CUSIP |
| **FeedSpine** | Capture any feed with dedup + history | Track when filings first appeared | Same filing from 3 feeds → stored once |
| **py-sec-edgar** | Download + extract SEC filings | Complete analysis platform | Risk factors, suppliers, LLM Q&A |

The key insight: **Each package is independently useful, but together they create a complete SEC analysis platform.**
