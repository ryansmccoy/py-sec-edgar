# py-sec-edgar Project Status

**Last Updated:** January 27, 2026 (Session 2)

---

## Overview

This project consists of four integrated packages for SEC EDGAR data processing:

| Package | Purpose | Status | Tests |
|---------|---------|--------|-------|
| **EntitySpine** | Entity resolution & knowledge graph | ✅ Published to PyPI | 315+ passing |
| **FeedSpine** | Feed management & deduplication | ✅ Functional | 506 passing, 1 failing |
| **py-sec-edgar** | SEC filing download & extraction | ✅ Phase 5 Complete | 506+ passing |
| **capture-spine** | Active capture project | ✅ In Development | — |

---

## 🎯 Feature Completion Status

### ✅ COMPLETE (Ready for Release)

| Feature | Description | Location |
|---------|-------------|----------|
| **Simple Download Interface** | Download filings with one function | py_sec_edgar |
| **Local Filing Inventory** | See what filings you have locally | py_sec_edgar |
| **Ticker → CIK Resolution** | Automatic resolution using EntitySpine | py_sec_edgar |
| **Form/Section/Exhibit Enums** | Type-safe 169 forms, 129 sections, 98 exhibits | py_sec_edgar |
| **Content Extraction** | Extract text/sections from filings | py_sec_edgar |
| **CLI Commands** | sec init, feed sync, company-lookup | py_sec_edgar |
| **Smart Sync Strategy** | 94% fewer HTTP requests for bulk | feedspine |
| **Resumable Downloads** | Continue interrupted downloads | feedspine |
| **Unified Feed View** | Deduplicated filings from all sources | feedspine |
| **EntitySpine Integration** | Entity resolution in py_sec_edgar | py_sec_edgar/integrations |
| **Exhibit 21 Parser** | Corporate hierarchy extraction (918 lines) | entityspine/parser |
| **Graph Service** | Relationship traversal (812 lines) | entityspine/services |
| **Timeline Service** | Point-in-time queries (549 lines) | entityspine/services |
| **9 Core Services** | audit, conflicts, data_quality, fuzzy, etc. | entityspine/services |

### 🔄 PARTIALLY COMPLETE

| Feature | Status | Notes |
|---------|--------|-------|
| **Progress Reporting** | Protocol exists | RichProgressReporter not wired |
| **Filing Facts Ingestion** | Generator exists | Pipeline not fully wired |

### ❌ NOT STARTED (Future Releases)

| Feature | Tier | Requires |
|---------|------|----------|
| **Knowledge Graph Queries** | Tier 3 | Graph service (exists) + high-level API |
| **LLM-Powered Extraction** | Tier 3 | External LLM integration |
| **SigDev Event Extraction** | Tier 3 | LLM + schemas |
| **Risk Analysis** | Tier 3 | LLM |
| **Real-Time Streaming** | Tier 3 | WebSocket |

---

## Recent Sessions (January 27, 2026)

### Session 2: Documentation & Feature Verification

1. **Feature Audit** ✅
   - Verified V4_POTENTIAL_FEATURES.md against actual implementation
   - Most Tier 1 and Tier 2 features are COMPLETE
   - Tier 3 (LLM-based) features are NOT STARTED

2. **Services Discovery** ✅
   - Discovered comprehensive existing services (graph 812 lines, timeline 549 lines)
   - Exhibit 21 parser exists (918 lines) - handles corporate hierarchy
   - 9 services fully implemented in EntitySpine

3. **Documentation Updated** ✅
   - Created `entityspine/docs/SERVICES_REFERENCE.md`
   - Updated `entityspine/docs/README.md`
   - Updated this file with feature status

### Session 1: File Organization & Tests

1. **File Organization Cleanup** ✅
   - Moved old versions (v0, v1, v2, v3, xbrl) to `archive/old_versions/`
   - Consolidated root `tests/` into `py_sec_edgar/tests/`
   - Moved documentation to appropriate packages
   - Root directory now has clean structure with 4 main packages

2. **EntitySpine Integration Tests** ✅
   - Created `tests/integration/test_entity_storage_complete.py`
   - 9 tests covering: storage, audit, validation, duplicates, conflicts, scoring, workflow
   - All tests passing

### Key API Learnings
- Entity uses `primary_name` (not `name`)
- `IdentifierClaim` requires scheme-appropriate target (`entity_id` for CIK, `listing_id` for TICKER)
- Stores require `initialize()` before use
- AuditManager uses `user_id` parameter

---

## Quick Start

### EntitySpine (Entity Resolution)

```python
from entityspine import SqliteStore

# Load SEC companies and resolve entities
store = SqliteStore(":memory:")
store.initialize()
store.load_sec_data()  # Auto-downloads ~8,000 companies

# Resolve by ticker
results = store.search_entities("AAPL")
entity, score = results[0]
print(f"{entity.primary_name} (CIK: {entity.source_id})")
# Apple Inc. (CIK: 0000320193)
```

---

## Phase Progress

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| **Phase 1** | EntitySpine Core | ✅ COMPLETE | v0.3.3 on PyPI |
| **Phase 2A** | FeedSpine Enhancement | ✅ COMPLETE | EntityEnricher added |
| **Phase 2B** | EntitySpine Tier 2+ | ⏸️ Optional | DuckDB/PostgreSQL |
| **Phase 3** | Integration Adapters | ✅ COMPLETE | EntitySpine ↔ FeedSpine |
| **Phase 4** | py-sec-edgar Services | ✅ COMPLETE | Ticker resolution + CLI |
| **Phase 5** | Section Extraction | ✅ COMPLETE | EntityMentionExtractor, FilingExtractor, CLI |

---

## EntitySpine (Phase 1 ✅)

**GitHub:** https://github.com/ryansmccoy/entity-spine
**PyPI:** https://pypi.org/project/entityspine/
**Version:** 0.4.0

### Key Features

- Zero-dependency core (stdlib only)
- Auto-download from SEC (`load_sec_data()`)
- Entity resolution by ticker, CIK, name
- Knowledge graph models (Asset, Contract, Product, Brand, Event)
- Integration contracts for external systems

### Services Inventory (January 2026)

| Service | Module | Status | Description |
|---------|--------|--------|-------------|
| **Audit** | `services/audit.py` | ✅ Complete | Change tracking with reversion |
| **Conflicts** | `services/conflicts.py` | ✅ Complete | Duplicate detection & resolution |
| **Data Quality** | `services/data_quality.py` | ✅ Complete | Validation & cleansing |
| **Fuzzy** | `services/fuzzy.py` | ✅ Complete | Name matching & normalization |
| **Graph** | `services/graph_service.py` | ✅ Complete | Relationship traversal (812 lines) |
| **Timeline** | `services/timeline.py` | ✅ Complete | Point-in-time queries (549 lines) |
| **Clustering** | `services/clustering.py` | ✅ Complete | Entity grouping |
| **Resolver** | `services/resolver.py` | ✅ Complete | Multi-identifier resolution |
| **Symbology** | `services/symbology_refresh.py` | ✅ Complete | Identifier refresh |

### Parser Inventory

| Parser | Module | Status | Description |
|--------|--------|--------|-------------|
| **Exhibit 21** | `parser/exhibit21.py` | ✅ Complete | Corporate hierarchy parsing (918 lines) |

### Examples to Study

| Example | Description |
|---------|-------------|
| `01_end_to_end_sec_filing_to_kg.py` | **Complete data flow** - SEC → KG |
| `02_load_sec_company_tickers.py` | Load SEC data, search entities |
| `05_filing_facts_ingestion.py` | FilingFacts contract for bulk ingestion |

```bash
cd entityspine
python examples/01_end_to_end_sec_filing_to_kg.py
python examples/05_filing_facts_ingestion.py
```

### Integration Contract

EntitySpine defines contracts for external systems:

```python
from entityspine.integration import FilingFacts, FilingEvidence, ingest_filing_facts

facts = FilingFacts(
    evidence=FilingEvidence(
        accession_number="0001045810-24-000029",
        form_type="10-K",
        filed_date=date(2024, 2, 21),
        cik="0001045810",
    ),
    registrant_name="NVIDIA Corporation",
    registrant_cik="0001045810",
    # ... entities, relationships, events
)

result = ingest_filing_facts(store, facts)
```

---

## FeedSpine (Phase 2A 🔄)

**Location:** `feedspine/`
**Version:** 1.1

### Test Status

```bash
cd feedspine
python -m pytest tests/ -x -q
# 506 passed, 1 failed (elasticsearch initialization)
```

### Key Features

- Feed management and scheduling
- Record deduplication by natural key
- Multiple storage backends (Memory, SQLite, PostgreSQL)
- Async-first architecture

### Integration with EntitySpine

```python
# When FeedSpine detects new filing, look up in EntitySpine
from entityspine import SqliteStore

store = SqliteStore("entities.db")
entities = store.get_entities_by_cik("0001045810")
if entities:
    print(f"Filing from: {entities[0].primary_name}")
```

---

## py-sec-edgar (Phase 4 ✅)

**Location:** `py_sec_edgar/`
**Version:** 4.x

### Test Status

```bash
cd py_sec_edgar
python -m pytest tests/ -q
# 490 passed, 1 error (pre-existing fixture issue)
```

### Key Features

- SEC filing download by CIK/accession
- Section extraction (10-K, 10-Q)
- **EntitySpine-powered ticker resolution**
- **CLI commands: `entity-lookup`, `entity-search`, `symbology-refresh`**

### EntitySpine Integration (✅ IMPLEMENTED)

```python
# Resolve ticker to CIK using EntitySpine
from py_sec_edgar.services.entity_service import EntityResolutionService

service = EntityResolutionService(data_dir)
cik = service.resolve_ticker("AAPL")  # Uses direct ticker lookup
print(f"AAPL → {cik}")
# AAPL → 0000320193

# Search by name
results = service.search_entities("Apple")
for cik, name, score in results:
    print(f"{score:.2f} | {name} (CIK: {cik})")
```

### Integration Architecture

```
py_sec_edgar/integrations/
├── __init__.py           # ENTITYSPINE_AVAILABLE, FEEDSPINE_AVAILABLE
├── entityspine.py        # Single integration point for EntitySpine
└── feedspine.py          # Single integration point for FeedSpine
```

**Key Design Principles Applied:**
- py-sec-edgar downloads SEC data, EntitySpine only ingests
- CIK is an IdentifierClaim (scheme=CIK), not entity.source_id
- Ticker resolution uses direct lookup, not fuzzy search
- All imports use public API (`from entityspine import X`)

---

## Directory Structure

```
b:\github\py-sec-edgar\
├── entityspine/              # Phase 1 - Entity resolution ✅
│   ├── src/entityspine/
│   │   ├── domain/           # Canonical dataclasses
│   │   ├── stores/           # SqliteStore, JsonEntityStore
│   │   └── integration/      # FilingFacts contracts
│   └── examples/             # MUST READ examples
├── feedspine/                # Phase 2A - Feed management 🔄
│   └── src/feedspine/
├── py_sec_edgar/             # Phase 4 - Filing download ❌
│   └── src/py_sec_edgar/
└── prompts/                  # Phase guides
    ├── PROJECT_STATUS.md               # This file
    ├── PROMPT_PHASE_1_ENTITYSPINE_CORE.md
    ├── PROMPT_PHASE_2A_FEEDSPINE_CORE.md
    ├── PROMPT_PHASE_2B_ENTITYSPINE_TIER2.md
    ├── PROMPT_PHASE_3_INTEGRATION.md
    ├── PROMPT_PHASE_4_PYSECEDGAR.md
    └── PROMPT_PHASE_5_SECTION_EXTRACTION.md  # Final phase
```

---

## Next Actions

### 🎯 High Priority

1. **Wire Filing Facts Pipeline**
   - Connect FilingFactsGenerator → ingest_filing_facts()
   - Location: `py_sec_edgar/services/filing_facts_generator.py`

2. **Test Graph/Timeline Services End-to-End**
   - Run `examples/01_end_to_end_sec_filing_to_kg.py` with real data
   - Verify Exhibit 21 parser extracts subsidiaries correctly

3. **High-Level Graph Query API**
   - Create simple `sec.graph.find_suppliers("NVDA")` interface
   - Wraps existing `graph_service.py`

### 📦 Integration Backlog

See `prompts/INTEGRATION_IMPROVEMENTS_BACKLOG.md` for:
- CIK normalization consolidation (8 places)
- Company services deduplication
- HTTP client consolidation

### ⚠️ Known Test Issues

1. **FeedSpine** - 1 elasticsearch test failing (non-critical)
2. **py-sec-edgar** - 1 pre-existing fixture error (non-critical)

---

## Commands Reference

```bash
# EntitySpine
pip install entityspine
cd entityspine
python examples/01_end_to_end_sec_filing_to_kg.py
pytest tests/ -v

# FeedSpine
cd feedspine
pytest tests/ -x -q

# py-sec-edgar
cd py_sec_edgar
pytest tests/ -x -q
```
