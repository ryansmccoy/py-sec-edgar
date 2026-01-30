# LLM Handoff: EntitySpine/FeedSpine/Py-Sec-Edgar Refactoring

**Date:** January 27, 2026
**Last Updated:** January 27, 2026 (session 3)
**Context:** Codebase deduplication and architecture refactoring

---

## Project Context

This workspace contains several related Python packages that have accumulated duplication over time:

```
py-sec-edgar/                    # SEC filing and entity management
├── entityspine/                 # Entity resolution library
├── feedspine/                   # Feed processing pipeline
├── py_sec_edgar/                # SEC-specific domain logic
├── capture-spine-basic/         # Simplified feed reader UI (React + FastAPI)
└── capture-spine/               # Full feature feed reader (reference only)
```

## Current State Summary

### 1. Duplication Analysis Complete ✅

See [DUPLICATION_ANALYSIS.md](DUPLICATION_ANALYSIS.md) for full details.

**Key Findings:**
- Entity models duplicated across py-sec-edgar and entityspine
- Identifier validation overlaps in multiple places
- Record/Filing models need consolidation
- Reference data (SIC, exchanges) is NOT duplicated - stays in py-sec-edgar

### 2. Ownership Matrix Defined ✅

| Package | Owns |
|---------|------|
| **EntitySpine** | Entity, IdentifierClaim, EntityType, EntityStatus, normalization, ULID |
| **FeedSpine** | Record, RecordCandidate, Sighting, Pipeline, deduplication |
| **py-sec-edgar** | SEC taxonomy, reference data, CIK/Accession helpers |
| **capture-spine-basic** | Simplified UI (6 tables), React frontend, FastAPI backend |

### 3. capture-spine-basic UI Complete ✅

Previously implemented:
- **5 view modes**: Condensed, Comfortable, Headlines, Cards, Table
- **Resizable panels**: Drag to adjust sidebar (160-350px) and preview (280-600px)
- **Collapsible panels**: Hide/show sidebar and preview
- **Persisted preferences**: localStorage for view mode, panel sizes, collapse states
- **Custom hooks**: `useLocalStorage`, `useResizable`

### 4. EntitySpine Adapter Pattern Complete ✅ (NEW)

Just implemented the adapter pattern for Entity consolidation:

**Key Changes:**
- `py_sec_edgar/core/identity/adapters.py` - **Updated** with proper scope handling
  - `SECEntity` wrapper class provides convenience API (`.cik`, `.lei`, `.ticker`)
  - `create_sec_entity()` factory handles scope rules automatically
  - Properly routes identifiers to correct scopes (entity/security/listing)

- `py_sec_edgar/core/identity/entity.py` - **Deprecated**
  - Added deprecation warning on import
  - Users should migrate to `SECEntity` from adapters.py

- `py_sec_edgar/core/identity/__init__.py` - **Updated**
  - New exports: `SECEntity`, `create_sec_entity`, `IdentifierClaim`, etc.
  - Legacy exports still work (backward compatible)

**Usage Example:**
```python
# NEW (recommended)
from py_sec_edgar.core.identity import SECEntity, create_sec_entity

apple = create_sec_entity(
    primary_name="Apple Inc",
    cik="0000320193",
    ticker="AAPL",
    lei="HWUPKR0MPOU8FGXBT394",
)
apple.cik  # "0000320193"
apple.ticker  # "AAPL"

# OLD (deprecated, still works)
from py_sec_edgar.core.identity import Entity, EntityType, Identifier
```

---

## Next Steps for Refactoring

### Phase 1: EntitySpine Cleanup ✅ COMPLETE

**What's Done:**
- ✅ Created SECEntity adapter with convenience API
- ✅ Added deprecation warnings to legacy entity.py
- ✅ Updated __init__.py exports for new pattern
- ✅ Migrated `enricher.py` to support both Entity and SECEntity patterns
- ✅ Evaluated registry/store: **DECISION** - Keep using legacy Entity (SEC-specific storage)

**Key Insight:** entityspine uses scope rules for identifiers:
- CIK, LEI → entity_id (ENTITY scope)
- TICKER → listing_id (LISTING scope)
- ISIN, CUSIP, FIGI → security_id (SECURITY scope)

The SECEntity wrapper abstracts this away for py-sec-edgar users.
The registry.py and store.py modules are SEC-specific DuckDB storage - they remain as-is
and use the legacy Entity pattern internally. Conversion happens at boundaries via adapters.py.

### Phase 2: FeedSpine Cleanup ✅ ANALYZED

**Goal:** Make feedspine the single source of truth for Record/Pipeline models.

**Analysis Complete:**
- Current: `_record_to_filing()` extracts data from Record into Filing (discards Record)
- Proposed: SECFeed pattern with typed content (see architecture docs)
- FeedSpine already has `RecordConverter` registry pattern in `feedspine/models/converter.py`

**Architecture Docs:**
- [feed-composition-integration.md](py_sec_edgar/docs/10_architecture/design/feed-composition-integration.md) - Full SECFeed design
- Proposes: `SECFilingContent` (Pydantic), `SECFiling` (wraps Record), `SECFeed` class

**Proposed SECFeed Pattern (not yet implemented):**
```python
# SECFilingContent - typed content schema
class SECFilingContent(BaseModel):
    accession_number: str
    form_type: str
    company_name: str
    cik: str
    filed_date: date

# SECFiling - wraps Record with typed content
@dataclass
class SECFiling:
    id: str
    natural_key: str
    content: SECFilingContent  # Typed, not dict!
    published_at: datetime
    captured_at: datetime
```

**Status:** Pattern designed but NOT implemented. Current `_record_to_filing()` works fine.
Implement SECFeed when typed content and IDE autocomplete become priorities.

### Phase 3: Integration

**Goal:** Wire packages together properly.

1. **py-sec-edgar depends on:**
   - entityspine (for Entity, IdentifierClaim)
   - feedspine (for Record, Pipeline)

2. **capture-spine-basic depends on:**
   - entityspine, feedspine (via py-sec-edgar or directly)

---

## Key Files to Review

### EntitySpine
```
entityspine/
├── domain/
│   ├── entity.py          # Entity model (114 lines)
│   └── identifier.py      # IdentifierClaim
├── core/
│   ├── normalize.py       # Normalization
│   └── ulid.py            # ULID generation
└── services/
    └── resolver.py        # Entity resolution
```

### FeedSpine
```
feedspine/
├── models/
│   ├── record.py          # Record, RecordCandidate
│   └── sighting.py        # Sighting
├── pipeline/
│   ├── processor.py       # Pipeline processing
│   └── dedup.py           # Deduplication
└── storage/
    └── backend.py         # Storage interface
```

### Py-Sec-Edgar (to refactor)
```
py_sec_edgar/
├── core/
│   └── identity/
│       ├── entity.py      # DUPLICATE - consolidate with entityspine
│       ├── identifiers.py # DUPLICATE - consolidate with entityspine
│       ├── filing.py      # KEEP - SEC-specific
│       └── cik.py         # KEEP - SEC-specific validation
├── reference/             # KEEP - SEC reference data
│   ├── sic.py
│   ├── exchanges.py
│   └── jurisdictions.py
└── taxonomy/              # KEEP - SEC form/exhibit taxonomy
    ├── forms.py
    └── exhibits.py
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONCEPT OWNERSHIP                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────┐                    ┌─────────────────────┐    │
│  │    EntitySpine      │                    │    FeedSpine        │    │
│  │    (owns)           │                    │    (owns)           │    │
│  ├─────────────────────┤                    ├─────────────────────┤    │
│  │ • Entity            │                    │ • Record            │    │
│  │ • EntityType        │                    │ • RecordCandidate   │    │
│  │ • EntityStatus      │                    │ • Sighting          │    │
│  │ • IdentifierClaim   │                    │ • Pipeline          │    │
│  │ • Normalization     │                    │ • Storage           │    │
│  │ • ULID generation   │                    │ • Deduplication     │    │
│  │ • Entity resolution │                    │ • Change detection  │    │
│  └─────────────────────┘                    └─────────────────────┘    │
│             │                                        │                  │
│             └──────────────┬─────────────────────────┘                  │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       py-sec-edgar                               │   │
│  │                       (SEC domain)                               │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ • SEC Filing (wraps feedspine Record)                           │   │
│  │ • Form taxonomy (10-K, 8-K, etc.)                               │   │
│  │ • Exhibit taxonomy (Ex 21, Ex 23, etc.)                         │   │
│  │ • Section extraction (Item 1, Item 7, etc.)                     │   │
│  │ • Reference data (SIC, exchanges, jurisdictions)                │   │
│  │ • SEC-specific CIK/accession helpers                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                            │                                            │
│                            ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    capture-spine-basic                           │   │
│  │                    (unified app)                                 │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ • React UI (5 view modes, resizable panels)                     │   │
│  │ • Core tables (feeds, records, sightings)                       │   │
│  │ • Simple API (no auth, no multi-user)                           │   │
│  │ • FastAPI backend                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Relevant Documentation

| File | Description |
|------|-------------|
| [DUPLICATION_ANALYSIS.md](DUPLICATION_ANALYSIS.md) | Full duplication analysis with recommendations |
| [ARCHITECTURE_REFACTORING_PLAN.md](ARCHITECTURE_REFACTORING_PLAN.md) | 5-phase refactoring plan |
| [capture-spine-basic/OVERVIEW.md](capture-spine-basic/OVERVIEW.md) | Architecture overview |
| [capture-spine-basic/ROADMAP.md](capture-spine-basic/ROADMAP.md) | Feature roadmap |
| [capture-spine-basic/STATUS.md](capture-spine-basic/STATUS.md) | Current implementation status |

---

## Commands to Start

```bash
# Explore entityspine
ls entityspine/
cat entityspine/domain/entity.py

# Explore feedspine
ls feedspine/
cat feedspine/models/record.py

# Compare with py-sec-edgar duplicates
cat py_sec_edgar/core/identity/entity.py
cat py_sec_edgar/core/identity/identifiers.py

# Run capture-spine-basic frontend
cd capture-spine-basic/frontend
npm install
npm run dev
```

---

## Questions for Next LLM

1. **Entity consolidation strategy:** ✅ DECIDED - Use adapter pattern (SECEntity wraps entityspine Entity)
2. **Record/Filing relationship:** ✅ ANALYZED - SECFeed pattern designed but not implemented (current works fine)
3. **Import direction:** ✅ DECIDED - py-sec-edgar imports entityspine/feedspine
4. **Breaking changes:** ✅ HANDLED - Legacy Entity still works with deprecation warning

## Remaining Work

1. **SECFeed Implementation (optional):** Implement the typed SECFeed pattern when IDE autocomplete becomes a priority
2. **Documentation:** Update user-facing docs to reflect new patterns
3. **Testing:** Add tests for SECEntity adapter pattern
