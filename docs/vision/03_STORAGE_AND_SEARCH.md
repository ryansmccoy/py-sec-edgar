# Storage & Search Architecture

**Purpose**: Define how enriched filings are stored, indexed, and searched.

---

## Storage Philosophy

Every piece of data should be:
1. **Linked** - Connected to its source filing via accession_number
2. **Queryable** - Indexed for fast retrieval
3. **Versioned** - Track enrichment history
4. **Exportable** - Easy to extract for downstream use
5. **Tiered** - Scale from local dev to enterprise with backend choice

---

## Tiered Storage Architecture

> **Design Principle**: Start simple (DuckDB), graduate when needed (PostgreSQL → Elasticsearch)

### Storage by Component

The ecosystem has **three distinct storage systems**, each with different purposes:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        STORAGE COMPONENT OVERVIEW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  py-sec-edgar  │  Section Extraction Storage                        │    │
│  │────────────────┼────────────────────────────────────────────────────│    │
│  │  What:         │  Extracted filing sections, text content, metadata │    │
│  │  Backend:      │  DuckDB (default), SQLite, PostgreSQL, ES          │    │
│  │  File:         │  sec_data/sections.duckdb                          │    │
│  │  Tables:       │  extracted_sections, extraction_jobs               │    │
│  │  Use case:     │  Analytics, search, LLM context retrieval          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  FeedSpine     │  Filing Metadata Storage                           │    │
│  │────────────────┼────────────────────────────────────────────────────│    │
│  │  What:         │  Filing index records from SEC feeds               │    │
│  │  Backend:      │  DuckDB (default), MemoryStorage                   │    │
│  │  File:         │  sec_data/unified_filings.duckdb                   │    │
│  │  Tables:       │  feed_items, sync_state                            │    │
│  │  Use case:     │  Feed sync, filing discovery, download queue       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EntitySpine   │  Entity Reference Storage                          │    │
│  │────────────────┼────────────────────────────────────────────────────│    │
│  │  What:         │  Entities, claims, identifiers, relationships      │    │
│  │  Backend:      │  SQLite (default), JSON file                       │    │
│  │  File:         │  sec_data/entities.db                              │    │
│  │  Tables:       │  entities, claims, identifier_claims               │    │
│  │  Use case:     │  CIK→ticker lookup, entity resolution, symbology   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why Separate Storage?

| Component | Data Characteristics | Why This Backend |
|-----------|---------------------|------------------|
| **py-sec-edgar** (sections) | Large text blobs, analytics-heavy | DuckDB: Columnar compression, fast aggregations |
| **FeedSpine** (filings) | Structured records, frequent inserts | DuckDB: Append-efficient, good for sync |
| **EntitySpine** (entities) | Relational graph, frequent lookups | SQLite: Zero-deps, relational queries, FTS |

### Tier Selection Matrix (py-sec-edgar Extraction Storage)

| Capability | SQLite | DuckDB | PostgreSQL | Elasticsearch |
|------------|--------|--------|------------|---------------|
| **Deployment** | Embedded | Embedded | Server | Server (Docker) |
| **Dependencies** | stdlib | pip | server + driver | server + driver |
| **Max practical size** | ~10GB | ~100GB | Unlimited | Unlimited |
| **Concurrent writes** | ❌ Single | ❌ Single | ✅ MVCC | ✅ Distributed |
| **Basic search (LIKE)** | ⚠️ Slow | ✅ Fast (ILIKE) | ✅ Fast | ✅ |
| **Full-text search** | ⚠️ FTS5 | ❌ | ✅ tsvector | ✅ BM25 |
| **Semantic/vector** | ❌ | ❌ | ⚠️ pgvector | ✅ kNN |
| **Analytics (GROUP BY)** | ⚠️ Slow | ✅ Fast | ✅ Fast | ⚠️ Aggregations |
| **JSON queries** | ⚠️ Limited | ✅ | ✅ JSONB | ✅ Native |
| **Best for** | Prototyping | Local analytics | Production | Text search |

### Tier Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     STORAGE TIER SELECTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIER 0: ZERO DEPENDENCIES                                                   │
│  ┌─────────────────────────────────────────────────┐                        │
│  │  SQLite (stdlib)                                │                        │
│  │  • No pip install needed                        │                        │
│  │  • Basic storage only                           │                        │
│  │  • Slow on large text                           │                        │
│  │  • Use when: Cannot install any packages        │                        │
│  └─────────────────────────────────────────────────┘                        │
│                           │                                                  │
│                           ▼                                                  │
│  TIER 1: LOCAL ANALYTICS (Default)                                          │
│  ┌─────────────────────────────────────────────────┐                        │
│  │  DuckDB                                         │                        │
│  │  • Zero server setup                            │                        │
│  │  • Single file, portable                        │                        │
│  │  • Fast analytics (columnar)                    │                        │
│  │  • ILIKE search                                 │                        │
│  │  • Use when: Local dev, single user, analytics │                        │
│  └─────────────────────────────────────────────────┘                        │
│                           │                                                  │
│                           ▼                                                  │
│  TIER 2: PRODUCTION MULTI-USER                                              │
│  ┌─────────────────────────────────────────────────┐                        │
│  │  PostgreSQL                                     │                        │
│  │  • Full-text search (tsvector + GIN)           │                        │
│  │  • Concurrent users (MVCC)                      │                        │
│  │  • ACID transactions                            │                        │
│  │  • Optional: pgvector for embeddings           │                        │
│  │  • Use when: Team access, production           │                        │
│  └─────────────────────────────────────────────────┘                        │
│                           │                                                  │
│                           ▼                                                  │
│  TIER 3: ENTERPRISE SEARCH                                                  │
│  ┌─────────────────────────────────────────────────┐                        │
│  │  Elasticsearch (+ PostgreSQL for metadata)     │                        │
│  │  • BM25 relevance ranking                       │                        │
│  │  • Semantic search (dense vectors)             │                        │
│  │  • Faceted search & aggregations               │                        │
│  │  • Horizontal scaling                           │                        │
│  │  • Use when: Search-heavy, semantic, scale-out │                        │
│  └─────────────────────────────────────────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Feature Availability by Tier (py-sec-edgar Extraction Storage)

> **Note**: This tiered architecture applies to **py-sec-edgar's section extraction storage**.
> FeedSpine and EntitySpine have their own storage backends (see "Storage by Component" above).

```python
# py_sec_edgar/storage/capabilities.py

TIER_CAPABILITIES = {
    "sqlite": {
        "tier": 0,
        "name": "SQLite (Zero Deps)",
        "features": {
            "store_sections": True,
            "basic_search": True,        # LIKE (slow on large text)
            "full_text_search": False,
            "semantic_search": False,
            "concurrent_writes": False,
            "analytics_fast": False,
            "entity_resolution": True,   # Via EntityResolverPort
        },
        "limits": {
            "max_sections": 100_000,
            "max_db_size_gb": 10,
            "concurrent_users": 1,
        },
        "use_when": "Prototyping, zero dependencies required",
    },

    "duckdb": {
        "tier": 1,
        "name": "DuckDB (Local Analytics)",
        "features": {
            "store_sections": True,
            "basic_search": True,        # ILIKE (fast)
            "full_text_search": False,
            "semantic_search": False,
            "concurrent_writes": False,
            "analytics_fast": True,      # Columnar storage
            "entity_resolution": True,
        },
        "limits": {
            "max_sections": 10_000_000,
            "max_db_size_gb": 100,
            "concurrent_users": 1,
        },
        "use_when": "Local development, analytics workloads, single user",
    },

    "postgresql": {
        "tier": 2,
        "name": "PostgreSQL (Production)",
        "features": {
            "store_sections": True,
            "basic_search": True,
            "full_text_search": True,    # tsvector + GIN index
            "semantic_search": "pgvector",  # Optional extension
            "concurrent_writes": True,
            "analytics_fast": True,
            "entity_resolution": True,
        },
        "limits": {
            "max_sections": 100_000_000,
            "max_db_size_gb": 1000,
            "concurrent_users": 100,
        },
        "use_when": "Team access, production, full-text search needed",
    },

    "elasticsearch": {
        "tier": 3,
        "name": "Elasticsearch (Enterprise Search)",
        "features": {
            "store_sections": True,
            "basic_search": True,
            "full_text_search": True,    # BM25 ranking
            "semantic_search": True,     # Dense vector kNN
            "concurrent_writes": True,
            "analytics_fast": True,      # Aggregations
            "entity_resolution": True,
            "faceted_search": True,      # Unique to ES
            "highlighting": True,        # Search result highlighting
        },
        "limits": {
            "max_sections": "unlimited",
            "max_db_size_gb": "unlimited",
            "concurrent_users": "unlimited",
        },
        "use_when": "Search-heavy workloads, semantic search, scale-out",
    },
}
```

### Configuration

```python
# pyproject.toml / settings
[tool.py-sec-edgar]
storage_backend = "duckdb"  # or "sqlite", "postgresql", "elasticsearch"
database_path = "./sec_data/sections.duckdb"

# PostgreSQL (Tier 2)
# storage_backend = "postgresql"
# database_url = "postgresql://user:pass@localhost/sec_data"

# Elasticsearch (Tier 3)
# storage_backend = "elasticsearch"
# elasticsearch_url = "http://localhost:9200"
# elasticsearch_index = "sec_sections"
```

### CLI Tier Selection

```bash
# Default: DuckDB
py-sec-edgar extract filing.htm --store

# Explicit tier selection
py-sec-edgar extract filing.htm --store --backend duckdb
py-sec-edgar extract filing.htm --store --backend postgresql
py-sec-edgar extract filing.htm --store --backend elasticsearch

# Check available features
py-sec-edgar storage capabilities
# Backend: duckdb (Tier 1 - Local Analytics)
# ✅ store_sections
# ✅ basic_search (ILIKE)
# ❌ full_text_search (upgrade to PostgreSQL)
# ❌ semantic_search (upgrade to Elasticsearch)
# ✅ analytics_fast
```

### Graduation Path

```python
from py_sec_edgar.storage import get_extraction_storage

# Start local
storage = get_extraction_storage("duckdb", "./sections.duckdb")

# Later: migrate to PostgreSQL
# 1. Export from DuckDB
storage.export_to("postgresql://localhost/sec_data")

# 2. Switch config
storage = get_extraction_storage("postgresql", "postgresql://localhost/sec_data")

# API remains identical
job = storage.start_job("batch_extract")
storage.store_section(section, job.job_id)
results = storage.search_sections("cybersecurity risk")
```

### EntitySpine Storage (SQLite)

EntitySpine uses SQLite by design for zero-dependency entity resolution:

```python
from entityspine import SqliteStore, EntityResolutionService

# Default: SQLite with FTS5 for entity search
store = SqliteStore("./sec_data/entities.db")

# In-memory for testing
store = SqliteStore(":memory:")

# Resolve CIK → entity
resolver = EntityResolutionService(store)
entity = resolver.resolve_cik("0000320193")  # Apple Inc.
```

**Why SQLite for EntitySpine?**
- Zero dependencies (Python stdlib)
- FTS5 full-text search built-in
- Small dataset (thousands of entities, not millions of sections)
- Relational queries for entity graph traversal

### FeedSpine Storage (DuckDB)

FeedSpine uses DuckDB for efficient feed sync and filing discovery:

```python
from feedspine import FeedSpine, DuckDBStorage, MemoryStorage

# Persistent: DuckDB for production
storage = DuckDBStorage("./sec_data/unified_filings.duckdb")

# In-memory: for testing
storage = MemoryStorage()

async with FeedSpine(storage=storage) as spine:
    await spine.sync()  # Sync SEC feeds
    filings = await spine.query(ticker="AAPL", form="10-K")
```

**Why DuckDB for FeedSpine?**
- Fast append-only writes for feed sync
- Columnar storage for efficient date-range queries
- Single-file portable database
- Analytics queries (filings by form type, date trends)

---

## Storage Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Filing Store   │  │   Entity Store   │  │    Graph Store   │
│    (DuckDB)      │  │   (EntitySpine)  │  │    (DuckDB)      │
│                  │  │                  │  │                  │
│ • Raw filings    │  │ • Companies      │  │ • Relationships  │
│ • Sections       │  │ • Securities     │  │ • Edges          │
│ • Metadata       │  │ • Identifiers    │  │ • Paths          │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         └──────────────┬──────┴──────────────┬──────┘
                        │                     │
                        ▼                     ▼
              ┌──────────────────┐  ┌──────────────────┐
              │   Search Index   │  │   Vector Store   │
              │  (Full-Text)     │  │  (Embeddings)    │
              │                  │  │                  │
              │ • Risk factors   │  │ • Semantic search│
              │ • Guidance text  │  │ • Similar filings│
              │ • Entity names   │  │ • Clustering     │
              └──────────────────┘  └──────────────────┘
```

---

## 1. Filing Store (DuckDB)

### Schema

```sql
-- Core filing table
CREATE TABLE filings (
    -- Identity
    accession_number VARCHAR PRIMARY KEY,
    cik VARCHAR NOT NULL,
    form_type VARCHAR NOT NULL,
    filed_date DATE NOT NULL,
    period_of_report DATE,
    fiscal_year_end VARCHAR,

    -- Company info
    company_name VARCHAR,
    ticker VARCHAR,
    sic_code VARCHAR,
    state_of_incorporation VARCHAR,

    -- URLs
    filing_url VARCHAR,
    index_url VARCHAR,
    primary_document VARCHAR,

    -- Status
    download_status VARCHAR DEFAULT 'pending',
    enrichment_status VARCHAR DEFAULT 'pending',
    enrichment_version VARCHAR,
    enriched_at TIMESTAMP,

    -- Full enriched data (JSON)
    enriched_data JSON,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_cik (cik),
    INDEX idx_ticker (ticker),
    INDEX idx_form_type (form_type),
    INDEX idx_filed_date (filed_date),
);

-- Sections extracted from filings
CREATE TABLE filing_sections (
    id INTEGER PRIMARY KEY,
    accession_number VARCHAR NOT NULL REFERENCES filings(accession_number),
    section_id VARCHAR NOT NULL,  -- 'item_1a', 'item_7', etc.
    title VARCHAR,
    text TEXT,
    html TEXT,
    word_count INTEGER,
    start_offset INTEGER,
    end_offset INTEGER,
    extraction_confidence FLOAT,

    UNIQUE(accession_number, section_id),
    INDEX idx_section (accession_number, section_id),
);

-- Entity mentions
CREATE TABLE entity_mentions (
    id INTEGER PRIMARY KEY,
    accession_number VARCHAR NOT NULL REFERENCES filings(accession_number),

    -- Entity info
    entity_name VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,  -- 'supplier', 'customer', etc.

    -- Context
    section_id VARCHAR,
    surrounding_text TEXT,
    start_offset INTEGER,
    end_offset INTEGER,

    -- Confidence
    confidence FLOAT,
    extraction_method VARCHAR,

    -- Resolution
    resolved_entity_id VARCHAR,  -- Link to EntitySpine
    resolved_cik VARCHAR,

    INDEX idx_entity (entity_name),
    INDEX idx_type (entity_type),
    INDEX idx_filing (accession_number),
);

-- Risk factors
CREATE TABLE risk_factors (
    id INTEGER PRIMARY KEY,
    accession_number VARCHAR NOT NULL REFERENCES filings(accession_number),

    title VARCHAR,
    text TEXT NOT NULL,
    category VARCHAR,  -- 'operational', 'financial', etc.
    severity VARCHAR,  -- 'high', 'medium', 'low'

    -- Change tracking
    is_new BOOLEAN DEFAULT FALSE,
    is_modified BOOLEAN DEFAULT FALSE,
    prior_accession VARCHAR,  -- Link to previous filing

    INDEX idx_category (category),
    INDEX idx_severity (severity),
);

-- Product lines
CREATE TABLE product_lines (
    id INTEGER PRIMARY KEY,
    accession_number VARCHAR NOT NULL REFERENCES filings(accession_number),

    name VARCHAR NOT NULL,
    description TEXT,

    -- Financials
    revenue DECIMAL,
    revenue_pct FLOAT,
    growth_rate FLOAT,

    -- Commentary
    management_commentary TEXT,
    outlook VARCHAR,  -- 'positive', 'neutral', 'negative'
);

-- Management guidance
CREATE TABLE management_guidance (
    accession_number VARCHAR PRIMARY KEY REFERENCES filings(accession_number),

    outlook_summary TEXT,
    sentiment VARCHAR,

    revenue_guidance TEXT,
    margin_guidance TEXT,
    capex_guidance TEXT,

    growth_drivers JSON,  -- Array of strings
    headwinds JSON,
    strategic_priorities JSON,
);

-- Exhibits
CREATE TABLE exhibits (
    id INTEGER PRIMARY KEY,
    accession_number VARCHAR NOT NULL REFERENCES filings(accession_number),

    exhibit_number VARCHAR NOT NULL,
    filename VARCHAR,
    description VARCHAR,

    exhibit_type VARCHAR,
    classified_type VARCHAR,

    parties JSON,  -- Array of party names
    effective_date DATE,
    key_terms JSON,

    is_new BOOLEAN DEFAULT FALSE,
    is_incorporated BOOLEAN DEFAULT FALSE,
);
```

### Python Interface

```python
from py_sec_edgar.storage import FilingStore

store = FilingStore("./sec_data/filings.duckdb")

# Save enriched filing
store.save(enriched_filing)

# Query filings
filings = store.query(
    ticker="AAPL",
    form_types=["10-K"],
    filed_after=date(2020, 1, 1),
)

# Get specific filing with all data
filing = store.get("0000320193-24-000081", include_sections=True)

# Query by entity mentioned
filings = store.query_by_entity(
    entity_name="TSMC",
    entity_type="supplier",
)

# Query by risk category
filings = store.query_by_risk(
    category="cyber",
    severity="high",
)
```

---

## 2. Entity Store (EntitySpine Integration)

### How It Links

```python
from py_sec_edgar.storage import FilingStore
from entityspine import SqliteStore

# Stores
filing_store = FilingStore("./filings.duckdb")
entity_store = SqliteStore("./entities.db")

# When we find a mention like "TSMC" in Apple's filing:
# 1. Check if TSMC exists in EntitySpine
results = entity_store.search_entities("TSMC", limit=1)
if results:
    entity, score = results[0]
    resolved_entity_id = entity.entity_id
else:
    # Create new entity (or mark for review)
    entity = create_entity(primary_name="TSMC", ...)
    entity_store.save_entity(entity)
    resolved_entity_id = entity.entity_id

# 2. Store mention with resolution
store.save_entity_mention(
    accession_number="0000320193-24-000081",
    entity_name="TSMC",
    entity_type="supplier",
    resolved_entity_id=resolved_entity_id,
    ...
)
```

### Entity Resolution Service

```python
class EntityResolutionService:
    """Resolve entity mentions to canonical entities."""

    def __init__(self, entity_store: SqliteStore):
        self.store = entity_store
        self.cache = {}  # name -> entity_id

    def resolve(self, name: str, context: dict = None) -> str | None:
        """Resolve name to entity_id."""

        # Check cache
        if name in self.cache:
            return self.cache[name]

        # Exact match by name
        results = self.store.search_entities(name, limit=5)

        if results:
            best_match, score = results[0]
            if score > 0.9:  # High confidence
                self.cache[name] = best_match.entity_id
                return best_match.entity_id

        # Try with context (CIK, ticker, etc.)
        if context and context.get("cik"):
            entities = self.store.get_entities_by_cik(context["cik"])
            if entities:
                self.cache[name] = entities[0].entity_id
                return entities[0].entity_id

        return None  # Unresolved

    def batch_resolve(self, mentions: List[EntityMention]) -> List[EntityMention]:
        """Resolve a batch of mentions."""
        for mention in mentions:
            mention.resolved_entity_id = self.resolve(
                mention.name,
                {"section": mention.section}
            )
        return mentions
```

---

## 3. Search Capabilities

### Full-Text Search (DuckDB FTS)

```sql
-- Create full-text search index
CREATE TABLE fts_index AS
SELECT
    accession_number,
    company_name,
    text
FROM filing_sections
WHERE section_id IN ('item_1a', 'item_7');

-- Full-text search
SELECT accession_number, company_name
FROM fts_index
WHERE text MATCH 'cybersecurity AND incident'
ORDER BY score DESC
LIMIT 20;
```

### Python Search API

```python
from py_sec_edgar.search import FilingSearch

search = FilingSearch(store)

# Full-text search
results = search.text_search(
    query="supply chain disruption",
    form_types=["10-K", "10-Q"],
    filed_after=date(2023, 1, 1),
    limit=50,
)

# Entity search
results = search.entity_search(
    entity_name="NVIDIA",
    relationship="supplier",
)

# Risk search
results = search.risk_search(
    category="cyber",
    keywords=["ransomware", "data breach"],
)

# Semantic search (requires embeddings)
results = search.semantic_search(
    query="companies discussing AI chip supply constraints",
    limit=20,
)
```

### Vector Search (Optional)

```python
from py_sec_edgar.search import VectorSearch

# Initialize with embedding model
vector_search = VectorSearch(
    store=store,
    embedding_model="text-embedding-3-small",  # OpenAI
    # Or local: embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)

# Index sections
await vector_search.index_sections(
    sections=["item_1a", "item_7"],
    batch_size=100,
)

# Semantic search
results = await vector_search.search(
    query="companies facing semiconductor shortage risks",
    n_results=20,
)

# Find similar filings
similar = await vector_search.find_similar(
    accession_number="0000320193-24-000081",
    section="item_1a",
    n_results=10,
)
```

---

## 4. Export Capabilities

### Export to Pandas

```python
import pandas as pd
from py_sec_edgar.storage import FilingStore

store = FilingStore("./filings.duckdb")

# Export entity mentions to DataFrame
df = store.to_dataframe(
    table="entity_mentions",
    filters={
        "entity_type": "supplier",
        "ticker": "AAPL",
    }
)

# Export risk factors
df_risks = store.to_dataframe(
    table="risk_factors",
    filters={
        "category": "cyber",
        "filed_after": date(2023, 1, 1),
    }
)

# Custom SQL to DataFrame
df = store.query_to_dataframe("""
    SELECT
        f.ticker,
        f.filed_date,
        COUNT(DISTINCT em.entity_name) as supplier_count
    FROM filings f
    JOIN entity_mentions em ON f.accession_number = em.accession_number
    WHERE em.entity_type = 'supplier'
    GROUP BY f.ticker, f.filed_date
    ORDER BY supplier_count DESC
""")
```

### Export to JSON

```python
# Export enriched filing to JSON
with open("aapl_10k_2024.json", "w") as f:
    json.dump(enriched_filing.to_dict(), f, indent=2)

# Export batch
filings = store.query(ticker="AAPL", form_types=["10-K"])
for filing in filings:
    filename = f"{filing.ticker}_{filing.form_type}_{filing.filed_date}.json"
    with open(f"./export/{filename}", "w") as f:
        json.dump(filing.to_dict(), f)
```

### Export to Parquet (Analytics)

```python
# Export to Parquet for big data tools
store.export_to_parquet(
    table="entity_mentions",
    path="./export/entity_mentions.parquet",
    partition_by=["entity_type"],
)

# Export all tables
store.export_all_to_parquet("./export/")
```

---

## 5. Unified Query Interface

```python
from py_sec_edgar import SEC

async with SEC(data_dir="./sec_data") as sec:
    # Download and enrich
    await sec.download(
        tickers=["AAPL", "MSFT", "GOOGL"],
        forms=["10-K"],
        days=365,
        enrich=True,
    )

    # Query local data
    # ----------------

    # What filings do I have?
    inventory = sec.inventory()
    print(inventory)
    # Ticker  | Form  | Count | Date Range
    # AAPL    | 10-K  | 3     | 2022-2024
    # MSFT    | 10-K  | 3     | 2022-2024
    # GOOGL   | 10-K  | 3     | 2022-2024

    # Search for specific content
    filings = sec.search(
        text="artificial intelligence",
        form_types=["10-K"],
    )

    # Find by entity relationship
    filings = sec.search(
        mentions="NVIDIA",
        relationship="supplier",
    )

    # Find by risk category
    filings = sec.search(
        risk_category="cyber",
        risk_severity="high",
    )

    # Get enriched filing
    filing = sec.get("AAPL", "10-K", year=2024)

    # Access extracted data
    print(filing.suppliers)
    print(filing.competitors)
    print(filing.risk_factors)
```

---

## 6. Data Freshness & Sync

```python
from py_sec_edgar.storage import FilingStore

store = FilingStore("./filings.duckdb")

# Check what needs updating
stale = store.get_stale_filings(
    enrichment_version="1.0.0",  # Re-enrich if version < this
    max_age_days=30,            # Re-enrich if older than this
)

# Get download status
status = store.get_download_status()
# {
#     "total": 150,
#     "downloaded": 145,
#     "pending": 3,
#     "failed": 2,
# }

# Get enrichment status
status = store.get_enrichment_status()
# {
#     "total": 145,
#     "enriched": 120,
#     "pending": 20,
#     "failed": 5,
# }

# Sync with SEC (download new, re-enrich stale)
await sec.sync(
    tickers=["AAPL", "MSFT"],
    forms=["10-K", "10-Q"],
    enrich=True,
    re_enrich_stale=True,
)
```

---

## 7. When to Upgrade Storage Tiers

### Decision Tree

```
START: "What's your use case?"
           │
           ▼
    ┌──────────────────┐
    │ Local dev only?  │─── Yes ──▶ DuckDB (Tier 1) ✅
    │ Single user?     │
    └──────┬───────────┘
           │ No
           ▼
    ┌──────────────────┐
    │ Need concurrent  │─── Yes ──▶ PostgreSQL (Tier 2) ✅
    │ users/writes?    │
    └──────┬───────────┘
           │ No
           ▼
    ┌──────────────────┐
    │ Need full-text   │─── Yes ──▶ PostgreSQL (Tier 2) ✅
    │ search?          │
    └──────┬───────────┘
           │ No
           ▼
    ┌──────────────────┐
    │ Need semantic    │─── Yes ──▶ Elasticsearch (Tier 3)
    │ search / AI?     │           or PostgreSQL + pgvector
    └──────┬───────────┘
           │ No
           ▼
       DuckDB (Tier 1) ✅
       (Start here!)
```

### Upgrade Signals

| Signal | From | To | Reason |
|--------|------|----|--------|
| DB file > 50GB | DuckDB | PostgreSQL | Better storage efficiency, streaming |
| Multiple users need access | DuckDB | PostgreSQL | MVCC concurrency |
| "Search all filings for X" | DuckDB | PostgreSQL | Full-text search with tsvector |
| Faceted search needed | PostgreSQL | Elasticsearch | Aggregation buckets |
| "Find similar risk factors" | Any | Elasticsearch | Vector similarity |
| Query latency > 1s | Any | Higher tier | Better indexing |

### Migration Commands

```bash
# DuckDB → PostgreSQL
py-sec-edgar storage migrate \
    --from duckdb:./sections.duckdb \
    --to postgresql://localhost/sec_data \
    --verify

# PostgreSQL → Elasticsearch (sync, keep both)
py-sec-edgar storage sync \
    --source postgresql://localhost/sec_data \
    --target elasticsearch://localhost:9200/sec_sections \
    --incremental
```

---

## Next Steps

- [04_KNOWLEDGE_GRAPH.md](04_KNOWLEDGE_GRAPH.md) - Build cross-filing relationships
- [05_LLM_INTEGRATION.md](05_LLM_INTEGRATION.md) - AI-powered enrichment
- [06_FRONTEND_VISUALIZATION.md](06_FRONTEND_VISUALIZATION.md) - React visualization
