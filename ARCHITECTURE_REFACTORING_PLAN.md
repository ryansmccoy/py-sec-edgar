# Architecture Refactoring Plan

## Overview

This document outlines the plan to refactor the py-sec-edgar ecosystem into a clean, modular architecture with proper separation of concerns across four packages plus a unified application:

| Package | Purpose | Scope |
|---------|---------|-------|
| **py-sec-edgar** | SEC-specific data acquisition & parsing | SEC APIs, forms, exhibits, company data, taxonomy |
| **EntitySpine** | Entity resolution & knowledge graph | Entities, relationships, storage, graph, claims |
| **FeedSpine** | Data pipelines & collection | Feeds, change detection, medallion layers |
| **capture-spine** | Content acquisition (full app) | Web capture, rate limiting, provenance, full UI |
| **capture-spine-basic** | Simplified unified reader | 6 tables, no auth, optional spine integration |

---

## Code Duplication Analysis

**See:** [DUPLICATION_ANALYSIS.md](DUPLICATION_ANALYSIS.md) for detailed analysis.

### Key Findings

| Concept | Owner | Notes |
|---------|-------|-------|
| **Entity models** | EntitySpine | py-sec-edgar has convenience wrappers, NOT duplication |
| **Identifier utilities** | EntitySpine (core), py-sec-edgar (SEC-specific) | CIK/Accession stay in py-sec-edgar |
| **Taxonomy** | py-sec-edgar | Forms, exhibits, sections - SEC-specific |
| **Reference data** | py-sec-edgar | SIC codes, exchanges, jurisdictions - SEC-specific |
| **Records/Pipeline** | FeedSpine | Record, Sighting, Pipeline models |
| **UI/Reader** | capture-spine-basic | Simplified NewsfeedPage from capture-spine |

### Ownership Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONCEPT OWNERSHIP                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  EntitySpine         │  FeedSpine           │  py-sec-edgar                │
│  ════════════════    │  ════════════════    │  ════════════════            │
│  • Entity            │  • Record            │  • SEC Filing (wraps Record) │
│  • IdentifierClaim   │  • RecordCandidate   │  • Form taxonomy             │
│  • EntityType        │  • Sighting          │  • Exhibit taxonomy          │
│  • EntityStatus      │  • Pipeline          │  • CIK/Accession helpers     │
│  • Normalization     │  • Storage backends  │  • Reference data (SIC, etc) │
│  • ULID generation   │  • Deduplication     │  • Section extraction        │
│  • Entity resolution │  • Change detection  │  • SEC API adapters          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current Pain Points

1. **Mixed concerns** - SEC parsing logic mixed with entity resolution
2. **No extension points** - Adding new parsers requires copying code
3. **Duplicate models** - Same concepts defined in multiple places
4. **Tight coupling** - Hard to use packages independently
5. **No plugin system** - Everything hardcoded

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      UNIFIED APPLICATION LAYER                              │
│  ┌──────────────────────────────┐    ┌──────────────────────────────┐      │
│  │   capture-spine (FULL)       │    │   capture-spine-basic        │      │
│  │   40+ tables, auth, ES, KG   │    │   6 tables, no auth          │      │
│  └──────────────────────────────┘    └──────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           py-sec-edgar                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Exhibits   │  │   Forms     │  │  Companies  │  │  Taxonomy   │        │
│  │  (plugin)   │  │  (plugin)   │  │  (service)  │  │  Reference  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                         │
│                          FilingFacts Contract                               │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
         ┌──────────▼──────────┐      ┌──────────▼──────────┐
         │     FeedSpine       │      │    EntitySpine      │
         │  ┌───────────────┐  │      │  ┌───────────────┐  │
         │  │ Feed Registry │  │      │  │Entity Registry│  │
         │  │ Change Detect │  │◄────►│  │ Graph Service │  │
         │  │ Medallion Arch│  │      │  │ Resolution    │  │
         │  │ Sightings     │  │      │  │ Storage       │  │
         │  └───────────────┘  │      │  └───────────────┘  │
         └─────────────────────┘      └─────────────────────┘
```

---

## Phase 1: py-sec-edgar Plugin System

### 1.1 Exhibits (✅ COMPLETE)

```
py_sec_edgar/exhibits/
├── __init__.py          # Public API
├── models.py            # Domain models (ExhibitData, Subsidiary, etc.)
├── registry.py          # @register_parser decorator
├── base.py              # BaseExhibitParser, strategies
├── service.py           # ExhibitService (HTTP, discovery)
├── parsers/
│   ├── __init__.py      # Auto-import for registration
│   ├── exhibit21.py     # @register_parser("21") - Subsidiaries
│   ├── exhibit23.py     # @register_parser("23") - Auditor consent
│   ├── exhibit31.py     # @register_parser("31") - Certifications
│   └── exhibit99.py     # @register_parser("99") - Press releases
└── adapters/
    ├── __init__.py
    └── entityspine.py   # Exhibit21Adapter, Exhibit23Adapter
```

**Status**: ✅ COMPLETE - Models, registry, base, service, Exhibit21Parser, and EntitySpine adapters all implemented and tested.

### 1.2 Forms (Sections) - ✅ COMPLETE

```
py_sec_edgar/forms/
├── __init__.py          # Public API
├── models.py            # FormData, Section, Item, Form10KData, Form8KData
├── registry.py          # @register_parser decorator
├── base.py              # BaseFormParser, section strategies (Anchor, Heading, Div)
├── service.py           # FormService, SECFormClient, FormComparator
└── parsers/
    ├── __init__.py
    ├── form10k.py       # @register_parser("10-K") - Annual report
    ├── form8k.py        # @register_parser("8-K") - Current events
    └── ...              # Add more as needed
```

**Status**: ✅ COMPLETE - Models, registry, base with strategies, service, 10-K and 8-K parsers implemented and tested.

### 1.3 Companies - ✅ COMPLETE

```
py_sec_edgar/companies/
├── __init__.py          # Public API
├── models.py            # Company, CompanySnapshot, CompanyChange, ChangeReport
├── service.py           # CompanyService with loaders and comparator
└── adapters/            # (Future: version control, adapters)
    ├── __init__.py
    ├── company_tickers.py    # company_tickers.json parser
    └── company_exchange.py   # company_tickers_exchange.json parser
```

**Status**: ✅ COMPLETE - Models and service implemented with download, load, and compare functionality.

---

## Phase 2: EntitySpine Enhancements

### 2.1 Move Entity Models

**From py-sec-edgar → EntitySpine**:
- `ExtractedEntity`, `ExtractedRelationship`, `ExtractedEvent` → Already in contracts
- Add: `CompanyEntity`, `PersonEntity`, `SubsidiaryEntity` specializations

### 2.2 Entity Resolution Registry

```
entityspine/resolution/
├── __init__.py
├── registry.py          # @register_resolver decorator
├── base.py              # BaseResolver interface
└── resolvers/
    ├── __init__.py
    ├── cik_resolver.py      # Resolve by CIK
    ├── ticker_resolver.py   # Resolve by ticker
    ├── name_resolver.py     # Fuzzy name matching
    └── lei_resolver.py      # Resolve by LEI
```

### 2.3 Enrichment Pipeline

```
entityspine/enrichment/
├── __init__.py
├── registry.py          # @register_enricher decorator
├── base.py              # BaseEnricher interface
├── pipeline.py          # EnrichmentPipeline orchestrator
└── enrichers/
    ├── __init__.py
    ├── sec_enricher.py      # Enrich from SEC data
    ├── openfigi_enricher.py # Enrich with FIGI
    └── llm_enricher.py      # LLM-based enrichment (tiered)
```

### 2.4 Graph Adapters

```
entityspine/adapters/
├── __init__.py
├── base.py              # BaseGraphAdapter
├── filing_facts.py      # FilingFacts → Graph (exists)
├── exhibit21.py         # Exhibit21Data → Subsidiaries
└── form_def14a.py       # DEF14A → Officers/Directors
```

---

## Phase 3: FeedSpine Data Pipeline

### 3.1 Feed Registry

```
feedspine/feeds/
├── __init__.py
├── registry.py          # @register_feed decorator
├── base.py              # BaseFeed interface
├── models.py            # FeedRecord, Sighting, FeedConfig
└── sources/
    ├── __init__.py
    ├── sec_company_feed.py  # SEC company_tickers.json
    ├── sec_filing_feed.py   # SEC filing stream
    ├── sec_exhibit_feed.py  # Exhibit extraction feed
    └── openfigi_feed.py     # OpenFIGI reference data
```

### 3.2 Change Detection

```
feedspine/changes/
├── __init__.py
├── detector.py          # ChangeDetector
├── models.py            # ChangeEvent, ChangeSet
└── strategies/
    ├── __init__.py
    ├── hash_strategy.py     # Content hash comparison
    ├── field_strategy.py    # Field-by-field comparison
    └── fuzzy_strategy.py    # Fuzzy matching for renames
```

### 3.3 Medallion Architecture

```
feedspine/layers/
├── __init__.py
├── base.py              # BaseLayer interface
├── bronze.py            # Raw data ingestion
├── silver.py            # Validation, normalization
└── gold.py              # Aggregation, enrichment
```

---

## Phase 4: Integration Contracts

### 4.1 Shared Contracts (in EntitySpine)

```python
# entityspine/integration/contracts.py

@dataclass
class FilingFacts:
    """Contract for py-sec-edgar → EntitySpine"""
    evidence: FilingEvidence
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]
    events: list[ExtractedEvent]

@dataclass
class FeedRecord:
    """Contract for FeedSpine → EntitySpine"""
    natural_key: str
    content: dict
    source_feed: str
    captured_at: datetime
```

### 4.2 Adapters in Each Package

| Source | Adapter Location | Converts |
|--------|------------------|----------|
| Exhibit21Data | py-sec-edgar/exhibits/adapters/entityspine.py | → FilingFacts |
| FormData | py-sec-edgar/forms/adapters/entityspine.py | → FilingFacts |
| CompanySnapshot | py-sec-edgar/companies/adapters/feedspine.py | → FeedRecord |
| FeedRecord | feedspine/adapters/entityspine.py | → Entity ingestion |

---

## Task Tracker

### Phase 1: py-sec-edgar Plugin System

| Task | Status | File(s) |
|------|--------|---------|
| Exhibits: models.py | ✅ DONE | exhibits/models.py |
| Exhibits: registry.py | ✅ DONE | exhibits/registry.py |
| Exhibits: base.py | ✅ DONE | exhibits/base.py |
| Exhibits: service.py | ✅ DONE | exhibits/service.py |
| Exhibits: exhibit21 parser | ✅ DONE | exhibits/parsers/exhibit21.py |
| Exhibits: exhibit23 parser | ⬜ TODO | exhibits/parsers/exhibit23.py |
| Exhibits: __init__.py | ✅ DONE | exhibits/__init__.py |
| Exhibits: EntitySpine adapters | ✅ DONE | exhibits/adapters/entityspine.py |
| Forms: models.py | ✅ DONE | forms/models.py |
| Forms: registry.py | ✅ DONE | forms/registry.py |
| Forms: base.py | ✅ DONE | forms/base.py |
| Forms: 10-K parser | ✅ DONE | forms/parsers/form10k.py |
| Forms: 8-K parser | ✅ DONE | forms/parsers/form8k.py |
| Forms: service.py | ✅ DONE | forms/service.py |
| Forms: __init__.py | ✅ DONE | forms/__init__.py |
| Companies: models.py | ✅ DONE | companies/models.py |
| Companies: service.py | ✅ DONE | companies/service.py |
| Companies: __init__.py | ✅ DONE | companies/__init__.py |
| Cleanup: old exhibit21_service | ✅ DONE | Renamed to _deprecated |

### Phase 2: EntitySpine Enhancements

| Task | Status | File(s) |
|------|--------|---------|
| Resolution: registry.py | ⬜ TODO | resolution/registry.py |
| Resolution: cik_resolver | ⬜ TODO | resolution/resolvers/cik.py |
| Enrichment: pipeline.py | ⬜ TODO | enrichment/pipeline.py |
| Enrichment: llm_enricher | ⬜ TODO | enrichment/enrichers/llm.py |
| Adapters: exhibit21.py | ⬜ TODO | adapters/exhibit21.py |

### Phase 3: FeedSpine Data Pipeline

| Task | Status | File(s) |
|------|--------|---------|
| Feeds: registry.py | ⬜ TODO | feeds/registry.py |
| Feeds: sec_company_feed | ⬜ TODO | feeds/sources/sec_company.py |
| Changes: detector.py | ⬜ TODO | changes/detector.py |
| Layers: medallion impl | ⬜ TODO | layers/*.py |

### Phase 4: Integration

| Task | Status | File(s) |
|------|--------|---------|
| Delete old exhibit21_service.py | ✅ DONE | Renamed to _deprecated |
| Update examples | ⬜ TODO | entityspine/examples/*.py |
| Integration tests | ✅ DONE | tests/integration/ (42 passing) |

### Phase 5: capture-spine-basic (NEW)

| Task | Status | File(s) |
|------|--------|---------|
| Project scaffold | ✅ DONE | capture-spine-basic/ |
| Database schema (6 tables) | ✅ DONE | backend/db/schema.sql |
| FastAPI backend | ✅ DONE | src/capture_spine_basic/api/main.py |
| CLI commands | ✅ DONE | src/capture_spine_basic/cli.py |
| feeds.yaml config | ✅ DONE | feeds.yaml |
| Docker setup | ✅ DONE | docker-compose.yml, Dockerfile |
| React UI components | ⬜ TODO | Copy from capture-spine |
| Feed polling logic | ⬜ TODO | Integrate feedspine Pipeline |

---

## Design Principles

### 1. Plugin Architecture
```python
# All plugin systems follow this pattern:
@register_parser("21")  # or @register_feed, @register_resolver, etc.
class MyParser(BaseParser):
    def parse(self, content, ref) -> Data:
        ...
```

### 2. Contract-Based Integration
```python
# Packages communicate via contracts, not implementations
from entityspine.integration import FilingFacts, ingest_filing_facts

facts = my_parser.to_filing_facts(data)  # Contract
result = ingest_filing_facts(store, facts)  # Standard ingestion
```

### 3. Adapter Pattern for Cross-Package
```python
# Each package has adapters/ for converting to other packages
from py_sec_edgar.exhibits.adapters.entityspine import Exhibit21Adapter

adapter = Exhibit21Adapter()
filing_facts = adapter.adapt(exhibit21_data)
```

### 4. Strategy Pattern for Parsing
```python
# Composable parsing strategies
parser = Exhibit21Parser(strategies=[
    TableParsingStrategy(),
    DivParsingStrategy(),
    PlainTextParsingStrategy(),
])
```

### 5. Registry Auto-Discovery
```python
# Parsers auto-register on import
from py_sec_edgar.exhibits import get_parser

parser = get_parser("21")  # Automatically discovered
```

### 6. Graceful Degradation
```python
# py-sec-edgar works standalone, integrates when dependencies available
from py_sec_edgar.exhibits import ExhibitService

# Level 1: Always works
data = ExhibitService().get_exhibit(cik, "21")

# Level 2: With EntitySpine (optional)
try:
    from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
    from entityspine.integration import ingest_filing_facts
    facts = exhibit_to_filing_facts(data)
    result = ingest_filing_facts(store, facts)
except ImportError:
    pass  # Continue without entity resolution
```

---

## Integration Testing Strategy

### Test Categories

| Category | Purpose | Frequency | Sample Size |
|----------|---------|-----------|-------------|
| **Unit Tests** | Component logic | Every commit | N/A |
| **Fixed Filing Tests** | Regression on known filings | Every commit | 10-20 filings |
| **Random Filing Tests** | Edge case discovery | Daily/Nightly | 50-100 filings |
| **Contract Tests** | Cross-package compliance | Every commit | All contracts |
| **Stress Tests** | Performance validation | Weekly | 1000+ filings |

### Random Filing Test Framework

```python
# tests/integration/test_random_filings.py
from py_sec_edgar.testing import get_random_filings, EdgeCaseReport

def test_exhibit21_random():
    filings = get_random_filings(form_type="10-K", count=50)
    results = []

    for filing in filings:
        result = parse_exhibit21_with_diagnostics(filing)
        results.append(result)

    report = EdgeCaseReport.from_results(results)

    # Minimum 80% success rate
    assert report.success_rate >= 0.8

    # Save edge cases for parser improvement
    report.save("test_outputs/edge_cases.json")
```

### Edge Case Detection & Reporting

Every parser reports:
1. **Confidence score** (0.0-1.0)
2. **Strategy used** (which parsing approach worked)
3. **Warnings** (unusual patterns detected)
4. **Parse time** (performance)

```python
result = service.get_exhibit_with_diagnostics(cik, "21")
print(f"Confidence: {result.confidence}")
print(f"Warnings: {result.warnings}")
print(f"Strategy: {result.strategy}")
```

### CI/CD Integration

```yaml
# .github/workflows/integration-tests.yml
jobs:
  random-filing-tests:
    runs-on: ubuntu-latest
    schedule:
      - cron: '0 6 * * *'  # Daily at 6 AM
    steps:
      - run: pytest tests/integration/ --random-count=50
      - uses: actions/upload-artifact@v4
        with:
          name: edge-case-report
          path: test_outputs/
```

---

## Next Steps (Updated)

### Completed ✅
1. ~~Complete exhibits module~~ ✅
2. ~~Create companies module~~ ✅
3. ~~Create forms module~~ ✅
4. ~~Wire to EntitySpine (exhibits adapter)~~ ✅
5. ~~Delete old exhibit21_service.py~~ ✅ (renamed to _deprecated)

### Phase 2: Integration (In Progress)
1. [ ] Create integration test framework with random filings
2. [ ] Add diagnostics to all parsers (confidence, warnings)
3. [ ] Create contract tests for FilingFacts
4. [ ] Add graceful degradation checks to all adapters

### Phase 3: EntitySpine Enhancements
1. [ ] Resolution registry with @register_resolver
2. [ ] Enrichment pipeline with @register_enricher
3. [ ] Graph adapters for forms/exhibits

### Phase 4: FeedSpine Pipeline
1. [ ] Feed registry with @register_feed
2. [ ] Change detection strategies
3. [ ] Medallion layer implementations

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| py-sec-edgar Manifesto | [py_sec_edgar/docs/MANIFESTO.md](py_sec_edgar/docs/MANIFESTO.md) | Package philosophy |
| EntitySpine Manifesto | [entityspine/docs/MANIFESTO.md](entityspine/docs/MANIFESTO.md) | Entity resolution design |
| FeedSpine Manifesto | [py_sec_edgar/docs/20_framework_feedspine/MANIFESTO.md](py_sec_edgar/docs/20_framework_feedspine/MANIFESTO.md) | Pipeline design |
| capture-spine Manifesto | [capture-spine/docs/MANIFESTO.md](capture-spine/docs/MANIFESTO.md) | Acquisition design |
| **Integration Manifesto** | [INTEGRATION_MANIFESTO.md](INTEGRATION_MANIFESTO.md) | Cross-package integration |
| **Duplication Analysis** | [DUPLICATION_ANALYSIS.md](DUPLICATION_ANALYSIS.md) | Cross-package code ownership |
| **capture-spine-basic README** | [capture-spine-basic/README.md](capture-spine-basic/README.md) | Simplified app docs |

---

## File Mapping: Archive → New Location

| Archive File | New Location | Notes |
|--------------|--------------|-------|
| exhibit21_downloader_test.py | py_sec_edgar/exhibits/parsers/exhibit21.py | ✅ Done |
| entity_ingestion_test.py | feedspine/feeds/sources/sec_company.py | Feed collection |
| corporate_hierarchy_test.py | entityspine/examples/08_corporate_hierarchy.py | Already exists, update |
| company_version_control.py | py_sec_edgar/companies/service.py | ✅ Done |
| analyze_changes.py | py_sec_edgar/companies/service.py | ✅ Done |

---

## Success Criteria

1. **Extensibility**: Add new exhibit parser in <50 lines
2. **Independence**: Each package usable standalone
3. **Testability**: All parsers unit-testable without network
4. **Discoverability**: `list_parsers()` shows all available
5. **Traceability**: Every entity links back to source filing
