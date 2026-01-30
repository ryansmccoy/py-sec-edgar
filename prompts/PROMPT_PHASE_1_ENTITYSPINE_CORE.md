# Phase 1: EntitySpine Core Implementation

**STATUS: ✅ COMPLETE (January 2026)**

EntitySpine v0.3.3 is fully implemented and published to PyPI.

**GitHub:** https://github.com/ryansmccoy/entity-spine
**PyPI:** https://pypi.org/project/entityspine/

---

## What EntitySpine Does

EntitySpine solves the **entity resolution problem** for SEC EDGAR data:

> *"Is CIK 0000320193 the same company as ticker AAPL on NASDAQ?"*

It provides:
- **Entity Resolution** — Resolve tickers, CIKs, CUSIPs to canonical entities
- **Knowledge Graph** — Model companies, people, relationships, events
- **Zero Dependencies** — stdlib-only for Tier 0-1 (no pip install needed)

---

## Quick Start (30 seconds)

```python
from entityspine import SqliteStore

# Create store and load ~8,000 SEC companies (auto-downloads from SEC)
store = SqliteStore(":memory:")
store.initialize()
store.load_sec_data()  # Fetches from https://www.sec.gov/files/company_tickers.json

# Resolve by ticker
results = store.search_entities("AAPL")
entity, score = results[0]
print(f"{entity.primary_name} (CIK: {entity.source_id})")
# Apple Inc. (CIK: 0000320193)

# Resolve by CIK
entities = store.get_entities_by_cik("0000320193")
print(entities[0].primary_name)
# Apple Inc.
```

---

## Implementation Summary

| Component | Status | Location |
|-----------|--------|----------|
| Domain models | ✅ Done | `domain/*.py` - Entity, Security, Listing, Claim |
| KG models | ✅ Done | `domain/graph.py` - Asset, Contract, Product, Brand, Event |
| Stores | ✅ Done | `stores/sqlite_store.py`, `stores/json_store.py` |
| Integration | ✅ Done | `integration/` - FilingFacts, ingest_filing_facts() |
| Pydantic adapters | ✅ Done | `adapters/pydantic/` (optional) |
| ORM adapters | ✅ Done | `adapters/orm/` (optional) |
| Tests | ✅ 315 passing | Full unit + integration tests |
| PyPI | ✅ Published | `pip install entityspine` |

---

## Architecture (INVIOLABLE)

### Domain Model Hierarchy

```
Entity (Apple Inc.)
  └── Security (Apple Common Stock)
        └── Listing (AAPL on NASDAQ)
              └── IdentifierClaim (ticker=AAPL, scheme=TICKER)
```

**CRITICAL RULE:** Ticker belongs on **Listing**, NOT Entity.

### Zero-Dependency Core

```python
# Works with ZERO pip dependencies
from entityspine import SqliteStore, Entity, Security, Listing

# Optional extras
pip install "entityspine[pydantic]"  # Validation wrappers
pip install "entityspine[orm]"       # SQLModel/SQLAlchemy
```

---

## Examples (MUST READ)

The `examples/` directory contains working code that demonstrates all patterns:

| Example | What It Shows |
|---------|---------------|
| `01_end_to_end_sec_filing_to_kg.py` | **Complete integration proof** - SEC → KG |
| `02_load_sec_company_tickers.py` | Load SEC data, search entities |
| `03_entity_identifier_claims.py` | Multi-scheme identifiers (CIK, LEI, CUSIP) |
| `04_knowledge_graph_relationships.py` | Build KG with suppliers, customers |
| `05_filing_facts_ingestion.py` | Use FilingFacts contract for bulk ingestion |

### Run Examples

```bash
cd entityspine
python examples/01_end_to_end_sec_filing_to_kg.py
python examples/05_filing_facts_ingestion.py
```

---

## Integration Contract (For FeedSpine/py-sec-edgar)

EntitySpine defines contracts in `entityspine.integration` that external systems use:

### FilingFacts Contract

```python
from entityspine.integration import FilingFacts, FilingEvidence, ingest_filing_facts
from entityspine import SqliteStore

# External system (py-sec-edgar) provides this:
facts = FilingFacts(
    evidence=FilingEvidence(
        accession_number="0001045810-24-000029",
        form_type="10-K",
        filed_date=date(2024, 2, 21),
        cik="0001045810",
    ),
    registrant_name="NVIDIA Corporation",
    registrant_cik="0001045810",
    registrant_ticker="NVDA",
    # ... extracted entities, relationships, events
)

# EntitySpine ingests it:
store = SqliteStore("entities.db")
store.initialize()
result = ingest_filing_facts(store, facts)
print(f"Created: {result.entities_created} entities, {result.relationships_created} relationships")
```

### Contract Dataclasses

All contracts are stdlib `@dataclass` (no pydantic required):

```python
@dataclass
class FilingEvidence:
    accession_number: str
    form_type: str
    filed_date: date
    cik: str

@dataclass
class ExtractedEntity:
    name: str
    entity_type: str  # "organization", "person"

@dataclass
class ExtractedRelationship:
    source_name: str
    target_name: str
    relationship_type: str  # "SUPPLIER", "CUSTOMER", "COMPETITOR"
```

---

## Key Files

```
entityspine/
├── src/entityspine/
│   ├── __init__.py          # Exports: SqliteStore, JsonEntityStore, domain models
│   ├── domain/              # Canonical stdlib dataclasses
│   │   ├── entity.py        # Entity (NO identifiers on Entity)
│   │   ├── security.py      # Security
│   │   ├── listing.py       # Listing (TICKER lives here)
│   │   ├── claim.py         # IdentifierClaim
│   │   ├── graph.py         # KG: Asset, Contract, Product, Brand, Event
│   │   ├── enums.py         # All enumerations
│   │   └── validators.py    # normalize_cik(), normalize_ticker(), etc.
│   ├── stores/
│   │   ├── sqlite_store.py  # SqliteStore with load_sec_data()
│   │   └── json_store.py    # JsonEntityStore with load_sec_data()
│   ├── integration/         # Contracts for external systems
│   │   ├── contracts.py     # FilingFacts, FilingEvidence, ExtractedEntity
│   │   └── ingest.py        # ingest_filing_facts()
│   └── adapters/
│       ├── pydantic/        # Optional Pydantic wrappers
│       └── orm/             # Optional SQLModel layer
└── examples/
    ├── 01_end_to_end_sec_filing_to_kg.py  # MUST READ
    └── 05_filing_facts_ingestion.py       # MUST READ
```

---

## Verification Commands

```bash
# Install and test
pip install entityspine
python -c "from entityspine import SqliteStore; s = SqliteStore(':memory:'); s.initialize(); print(s.load_sec_data())"
# Expected: ~8000

# Run examples
cd entityspine
python examples/01_end_to_end_sec_filing_to_kg.py
python examples/05_filing_facts_ingestion.py

# Run tests
pytest tests/ -v
# Expected: 315 passed
```

---

## What External Systems Provide

### py-sec-edgar Provides:

```python
# py-sec-edgar parses SEC filings and creates FilingFacts:
from entityspine.integration import FilingFacts, FilingEvidence

facts = FilingFacts(
    evidence=FilingEvidence(...),
    registrant_name="...",
    registrant_cik="...",
    entities=[...],        # Extracted company names, people
    relationships=[...],   # Supplier/customer relationships
    events=[...],          # Earnings, acquisitions
)
```

### FeedSpine Provides:

```python
# FeedSpine detects new filings and triggers EntitySpine:
# When a new filing appears in SEC RSS feed:
filing_cik = "0000320193"

# Look up entity in EntitySpine
from entityspine import SqliteStore
store = SqliteStore("entities.db")
results = store.get_entities_by_cik(filing_cik)
entity = results[0] if results else None
```

---

## What's Next?

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 2A** | FeedSpine Enhancement | 🔄 Ready |
| **Phase 2B** | EntitySpine Tier 2+ (DuckDB/PostgreSQL) | ⏸️ Optional |
| **Phase 3** | Integration Adapters | ❌ Not started |
| **Phase 4** | py-sec-edgar Services | ❌ Not started |

---

*Phase 1 of 5 | ✅ COMPLETED*
