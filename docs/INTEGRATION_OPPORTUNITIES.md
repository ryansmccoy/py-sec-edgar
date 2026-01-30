# Integration Opportunities Analysis

**py-sec-edgar + FeedSpine + EntitySpine**

*Analysis Date: January 2026*

---

## Executive Summary

The three packages have **good foundational integration**, but there are several opportunities to make the experience more seamless. This document identifies gaps and proposes improvements.

### Current State

| Integration | Status | Notes |
|-------------|--------|-------|
| py-sec-edgar → EntitySpine | ✅ Good | `Exhibit21Adapter` converts to `FilingFacts` |
| py-sec-edgar → FeedSpine | ✅ Good | `SecRssFeedAdapter`, `SecDailyIndexAdapter` |
| EntitySpine → FeedSpine | ✅ Good | `FeedSpineAdapter` for sighting tracking |
| **Unified CLI** | ❌ Missing | No single command to use all three |
| **Shared Configuration** | ❌ Missing | Each package has separate config |
| **Cross-Package Discovery** | ⚠️ Partial | Optional imports work but not documented |
| **Ready-to-Run Pipelines** | ❌ Missing | Users must wire up manually |

---

## Identified Opportunities

### 1. 🎯 Unified CLI Entry Point (HIGH VALUE)

**Problem**: Users must learn three CLIs (`py_sec_edgar`, `feedspine`, `entityspine`).

**Proposal**: Create a `spine` unified CLI:

```bash
# Instead of:
python -m py_sec_edgar workflows rss --tickers AAPL
python -m entityspine load sec
python -m feedspine collect

# Unified:
spine collect sec --tickers AAPL --resolve-entities --dedupe
spine status                  # Show status across all packages
spine pipeline run sec-to-kg  # Run predefined pipeline
```

**Implementation**: Create `spine/` package at root with Click commands that import from all three.

```
py-sec-edgar/
├── spine/                      # NEW: Unified CLI
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py                 # Click entry point
│   ├── commands/
│   │   ├── collect.py         # Integrates py-sec-edgar + feedspine
│   │   ├── resolve.py         # Integrates entityspine
│   │   ├── pipeline.py        # Pre-built pipelines
│   │   └── status.py          # Cross-package status
│   └── config.py              # Shared config
```

**Effort**: Medium (3-5 days)

---

### 2. 📦 Shared Configuration System (HIGH VALUE)

**Problem**: Each package reads config separately:
- py-sec-edgar: `EDGAR_USER_AGENT`, `EDGAR_STORAGE_PATH`
- EntitySpine: `ENTITYSPINE_DB_URL`, `ENTITYSPINE_STORAGE_TIER`
- FeedSpine: `FEEDSPINE_STORAGE`, `FEEDSPINE_BACKEND`

**Proposal**: Single `.env` / config file:

```ini
# spine.toml or .env

[sec]
user_agent = "Your Name email@example.com"
storage_path = "./data/sec"

[entities]
db_url = "sqlite:///./data/entities.db"
storage_tier = "sqlite"

[feeds]
backend = "duckdb"
db_path = "./data/feeds.db"

[pipeline]
default_output = "./data/output"
dedupe = true
resolve_entities = true
```

**Implementation**:
1. Create shared `spine-config` module
2. Each package reads from shared config if present
3. Falls back to package-specific config

**Effort**: Low (1-2 days)

---

### 3. 🔄 Pre-Built Pipelines (HIGH VALUE)

**Problem**: Users must manually wire up the three packages.

**Proposal**: Pre-built pipeline definitions:

```python
# spine/pipelines/sec_to_knowledge_graph.py
from spine.pipelines import Pipeline

SEC_TO_KG = Pipeline(
    name="sec-to-knowledge-graph",
    description="Full SEC filing to entity knowledge graph",
    steps=[
        CollectStep(
            source="sec-rss",
            form_types=["10-K", "10-Q", "8-K"],
        ),
        DedupeStep(
            backend="feedspine",
            storage="duckdb",
        ),
        ParseStep(
            parser="py-sec-edgar",
            extract=["exhibits", "sections"],
        ),
        ResolveStep(
            resolver="entityspine",
            create_entities=True,
            create_relationships=True,
        ),
        OutputStep(
            format="json",
            destination="./output/",
        ),
    ],
)

# CLI usage:
# spine pipeline run sec-to-knowledge-graph --tickers AAPL,MSFT
```

**Example Pre-Built Pipelines**:

| Pipeline | Description |
|----------|-------------|
| `sec-to-kg` | Full SEC → FeedSpine → EntitySpine |
| `sec-monitor` | RSS monitoring with dedup |
| `bulk-load` | Quarterly index → entities |
| `subsidiary-graph` | Exhibit 21 → relationship graph |

**Effort**: Medium (3-5 days)

---

### 4. 📊 Cross-Package Status Dashboard

**Problem**: No way to see unified status across packages.

**Proposal**: `spine status` command:

```
$ spine status

╭─────────────────────────────────────────────────────────────╮
│                   SPINE ECOSYSTEM STATUS                     │
├─────────────────────────────────────────────────────────────┤
│ py-sec-edgar     v4.2.0    ✅ Ready                         │
│   • Last sync: 2026-01-29 10:30:00                          │
│   • Filings downloaded: 14,523                              │
│   • Storage: ./sec_data (2.3 GB)                            │
├─────────────────────────────────────────────────────────────┤
│ FeedSpine        v1.5.0    ✅ Ready                         │
│   • Backend: DuckDB (feeds.db)                              │
│   • Records: 125,432                                        │
│   • Feeds: sec.rss, sec.daily, sec.quarterly                │
├─────────────────────────────────────────────────────────────┤
│ EntitySpine      v2.3.2    ✅ Ready                         │
│   • Storage: SQLite (entities.db)                           │
│   • Entities: 45,231                                        │
│   • Claims: 234,567                                         │
│   • Relationships: 89,012                                   │
╰─────────────────────────────────────────────────────────────╯
```

**Effort**: Low (1 day)

---

### 5. 🔌 FeedSpine Adapter Registry for py-sec-edgar

**Problem**: SEC feed adapters are in py-sec-edgar but could be auto-discovered.

**Current State**:
```python
# User must explicitly import
from py_sec_edgar.adapters import SecRssFeedAdapter
from feedspine import FeedSpine

spine.register_feed(SecRssFeedAdapter())
```

**Proposal**: Auto-registration via entry points:

```python
# feedspine auto-discovers adapters
spine = FeedSpine(storage=storage)
spine.discover_adapters()  # Auto-discovers py-sec-edgar adapters

# Or explicit:
spine.register_adapter_package("py_sec_edgar.adapters")
```

**Implementation**: Use Python entry points in `pyproject.toml`:

```toml
# py_sec_edgar/pyproject.toml
[project.entry-points."feedspine.adapters"]
sec = "py_sec_edgar.adapters.sec_feeds"
```

**Effort**: Low (1 day)

---

### 6. 🎓 EntitySpine Source Auto-Loading

**Problem**: Users must manually load reference data:

```python
store = SqliteStore("entities.db")
store.initialize()
store.load_sec_data()  # Must remember to call this
```

**Proposal**: Auto-load on first query or via config:

```python
# Auto-load when needed
store = SqliteStore("entities.db", auto_load_sec=True)

# Or lazy loading on first query
results = store.search("AAPL")  # Triggers auto-load if empty
```

**Effort**: Low (0.5 days)

---

### 7. 📄 Exhibit → Entity Relationship Builder

**Problem**: Exhibit 21 adapter creates entities but relationship building is separate.

**Proposal**: Enhanced `Exhibit21Adapter` that:
1. Creates parent entity (registrant)
2. Creates subsidiary entities
3. Creates `SUBSIDIARY_OF` relationships
4. Links jurisdictions to countries via ISO 3166

```python
from py_sec_edgar.exhibits.adapters.entityspine import Exhibit21Adapter
from entityspine import SqliteStore

adapter = Exhibit21Adapter(
    create_relationships=True,
    resolve_jurisdictions=True,  # Use ISO 3166
)

facts = adapter.to_filing_facts(exhibit_data)
result = ingest_filing_facts(store, facts)

print(f"Created {result.relationships_created} subsidiary relationships")
```

**Effort**: Medium (2 days)

---

### 8. 🔍 Cross-Package Search

**Problem**: Can't search across SEC filings AND entities in one query.

**Proposal**: Unified search that spans packages:

```python
from spine import UnifiedSearch

search = UnifiedSearch()

# Search returns results from all packages
results = search.query("Apple")

# Results tagged by source
for r in results:
    if r.source == "entityspine":
        print(f"Entity: {r.entity.primary_name}")
    elif r.source == "py-sec-edgar":
        print(f"Filing: {r.filing.form_type}")
    elif r.source == "feedspine":
        print(f"Record: {r.record.natural_key}")
```

**Effort**: High (5+ days)

---

### 9. 📝 Filing → Entity Event Linking

**Problem**: 8-K filings aren't linked to EntitySpine Events.

**Proposal**: Adapter that creates Events from 8-K filings:

```python
from py_sec_edgar.forms.adapters.entityspine import Form8KEventAdapter

adapter = Form8KEventAdapter()
events = adapter.extract_events(form_8k_data)

# Events like:
# - EventType.EARNINGS_RELEASE
# - EventType.EXECUTIVE_CHANGE
# - EventType.ACQUISITION
# - EventType.DIVIDEND_DECLARATION

for event in events:
    store.create_event(event)
```

**Effort**: Medium (3 days)

---

### 10. 📈 Observation Pipeline from Filings

**Problem**: Financial data in 10-K/10-Q isn't captured as EntitySpine Observations.

**Proposal**: Adapter that extracts financial observations:

```python
from py_sec_edgar.forms.adapters.entityspine import Form10KObservationAdapter

adapter = Form10KObservationAdapter()
observations = adapter.extract_observations(form_10k_data)

# Observations like:
# - revenue, total_assets, net_income (from XBRL)
# - employee_count, risk_factors_count (from text)

for obs in observations:
    store.create_observation(obs)
```

**Effort**: High (5+ days, XBRL parsing needed)

---

## Priority Matrix

| Opportunity | Value | Effort | Priority |
|-------------|-------|--------|----------|
| 1. Unified CLI | High | Medium | ⭐⭐⭐ P1 |
| 2. Shared Config | High | Low | ⭐⭐⭐ P1 |
| 3. Pre-Built Pipelines | High | Medium | ⭐⭐⭐ P1 |
| 4. Status Dashboard | Medium | Low | ⭐⭐ P2 |
| 5. Adapter Registry | Medium | Low | ⭐⭐ P2 |
| 6. Auto-Load Sources | Low | Low | ⭐⭐ P2 |
| 7. Enhanced Exhibit Adapter | Medium | Medium | ⭐⭐ P2 |
| 8. Cross-Package Search | High | High | ⭐ P3 |
| 9. 8-K Event Adapter | Medium | Medium | ⭐ P3 |
| 10. Financial Observations | High | High | ⭐ P3 |

---

## Recommended Implementation Order

### Phase 1: Foundation (Week 1)
1. ✅ Shared configuration system
2. ✅ `spine` unified CLI scaffold
3. ✅ `spine status` command

### Phase 2: Pipelines (Week 2)
4. Pre-built pipeline framework
5. `sec-to-kg` pipeline
6. `sec-monitor` pipeline

### Phase 3: Enhancements (Week 3)
7. Adapter auto-discovery
8. Enhanced Exhibit 21 adapter
9. EntitySpine auto-loading

### Phase 4: Advanced (Future)
10. Cross-package search
11. 8-K event extraction
12. Financial observations from XBRL

---

## Quick Wins (Can Do Today)

### 1. Add `spine` alias to existing CLIs

```bash
# In py-sec-edgar/pyproject.toml
[project.scripts]
spine-sec = "py_sec_edgar:cli.main"

# In entityspine/pyproject.toml
[project.scripts]
spine-entity = "entityspine:cli.main"

# In feedspine/pyproject.toml
[project.scripts]
spine-feed = "feedspine:cli.main"
```

### 2. Document Integration in READMEs

Add "Integration" sections to each package README linking to `GETTING_STARTED.md`.

### 3. Add `ENTITYSPINE_AVAILABLE` Pattern Everywhere

```python
# Standard pattern for optional integration
try:
    from entityspine import SqliteStore
    ENTITYSPINE_AVAILABLE = True
except ImportError:
    ENTITYSPINE_AVAILABLE = False

def resolve_entity(cik: str):
    if not ENTITYSPINE_AVAILABLE:
        return None
    # ... resolution logic
```

---

## Conclusion

The three packages have solid integration foundations. The highest-value improvements are:

1. **Unified CLI** - Single entry point for all operations
2. **Shared Config** - One config file for all packages
3. **Pre-Built Pipelines** - Ready-to-run workflows

These would significantly reduce the learning curve and make the ecosystem feel like a cohesive product rather than three separate tools.

---

*See also: [INTEGRATION_MANIFESTO.md](INTEGRATION_MANIFESTO.md) for detailed contract specifications.*
