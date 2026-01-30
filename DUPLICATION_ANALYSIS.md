# Code Duplication Analysis & Capture-Spine-Basic Plan

## Executive Summary

There is **significant duplication** across the codebase that needs to be addressed. This document:
1. Identifies all duplication
2. Proposes ownership for each concept
3. Outlines capture-spine-basic architecture

---

## Duplication Analysis

### 1. Entity Models (DESIGN DECISION NEEDED)

| Concept | py-sec-edgar | entityspine | Notes |
|---------|--------------|-------------|-------|
| **Entity** | `core/identity/entity.py` (474 lines) | `domain/entity.py` (114 lines) | py-sec-edgar has richer API |
| **EntityType** | 7 values (COMPANY, FUND, PERSON...) | 11 values (ORGANIZATION, FUND, TRUST...) | Different granularity |
| **EntityStatus** | 4 values | 4 values | Nearly identical |
| **Identifier** | `identifiers.py` (325 lines) | `IdentifierClaim` pattern | Different patterns |
| **IdentifierScheme** | 15 schemes | `IdentifierType` enum | Different scope |

**KEY DIFFERENCE**:
- **entityspine Entity**: Lean, uses `IdentifierClaim` as separate records (normalized DB design)
- **py-sec-edgar Entity**: Rich, embeds identifiers list (convenient API)

**RECOMMENDATION**:
- **Keep both** - they serve different purposes
- py-sec-edgar Entity is for **API convenience** (quick access to `entity.cik`, `entity.ticker`)
- entityspine Entity is for **normalized storage** (IdentifierClaim as separate table)
- Create **adapter** to convert between them when needed

### 2. Identifier Classification (ACCEPTABLE OVERLAP)

| Concept | py-sec-edgar | entityspine | Notes |
|---------|--------------|-------------|-------|
| CIK validation | `core/identity/cik.py` | `core/identifier.py` | py-sec-edgar is more complete |
| Ticker detection | `identifiers.py` | `looks_like_ticker()` | Similar but different needs |
| ULID generation | Not present | `core/ulid.py` | entityspine only |
| Normalization | `core/identity/` | `core/normalize.py` | Some overlap |

**RECOMMENDATION**:
- **Keep both** - py-sec-edgar needs SEC-specific validation (accession format, CIK format)
- entityspine has general-purpose utilities
- Create **thin wrappers** where py-sec-edgar needs entityspine features

### 3. Reference Data (py-sec-edgar only - NO DUPLICATION ✓)

| Module | Description | Keep In |
|--------|-------------|---------|
| `reference/sic.py` | SIC codes | py-sec-edgar (SEC-specific) |
| `reference/exchanges.py` | Exchange codes | py-sec-edgar (SEC-specific) |
| `reference/jurisdictions.py` | State/country codes | py-sec-edgar (SEC-specific) |
| `reference/periods.py` | Fiscal period helpers | py-sec-edgar (SEC-specific) |

**CONCLUSION**: Reference data is NOT duplicated - stays in py-sec-edgar ✓

### 4. Taxonomy (py-sec-edgar only - NO DUPLICATION ✓)

| Module | Description | Keep In |
|--------|-------------|---------|
| `taxonomy/forms.py` | SEC form types | py-sec-edgar (SEC-specific) |
| `taxonomy/exhibits.py` | Exhibit types | py-sec-edgar (SEC-specific) |
| `taxonomy/sections.py` | Filing sections | py-sec-edgar (SEC-specific) |

**CONCLUSION**: Taxonomy is NOT duplicated - stays in py-sec-edgar ✓

### 5. Record/Filing Models (POTENTIAL DUPLICATION)

| Concept | py-sec-edgar | feedspine | capture-spine |
|---------|--------------|-----------|---------------|
| **Filing** | `core/identity/filing.py` | N/A | `records` table |
| **Record** | N/A | `models/record.py` | `records` table |
| **RecordCandidate** | N/A | `models/record.py` | `items` table |

**RECOMMENDATION**:
- **feedspine owns**: Generic Record, RecordCandidate, Sighting
- **py-sec-edgar owns**: SEC Filing (extends/wraps feedspine Record)
- **capture-spine**: Uses feedspine models for storage

---

## Proposed Ownership Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONCEPT OWNERSHIP                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐                    ┌─────────────────────┐        │
│  │    EntitySpine      │                    │    FeedSpine        │        │
│  │    (owns)           │                    │    (owns)           │        │
│  ├─────────────────────┤                    ├─────────────────────┤        │
│  │ • Entity            │                    │ • Record            │        │
│  │ • EntityType        │                    │ • RecordCandidate   │        │
│  │ • EntityStatus      │                    │ • Sighting          │        │
│  │ • IdentifierClaim   │                    │ • Pipeline          │        │
│  │ • Normalization     │                    │ • Storage           │        │
│  │ • ULID generation   │                    │ • Deduplication     │        │
│  │ • Entity resolution │                    │ • Change detection  │        │
│  └─────────────────────┘                    └─────────────────────┘        │
│             │                                        │                      │
│             └──────────────┬─────────────────────────┘                      │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       py-sec-edgar                                   │   │
│  │                       (SEC domain)                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ • SEC Filing (wraps feedspine Record)                               │   │
│  │ • Form taxonomy (10-K, 8-K, etc.)                                   │   │
│  │ • Exhibit taxonomy (Ex 21, Ex 23, etc.)                             │   │
│  │ • Section extraction (Item 1, Item 7, etc.)                         │   │
│  │ • Reference data (SIC, exchanges, jurisdictions)                    │   │
│  │ • SEC-specific CIK/accession helpers (thin wrappers)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    capture-spine-basic                               │   │
│  │                    (unified app)                                     │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ • React UI (NewsfeedPage)                                           │   │
│  │ • Core tables (feeds, records, sightings)                           │   │
│  │ • Simple API (no auth, no multi-user)                               │   │
│  │ • Configuration dashboard (simplified)                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Capture-Spine-Basic Architecture

### Philosophy

**capture-spine-basic** is a **NEW project** that:
1. Uses py-sec-edgar, entityspine, feedspine as dependencies
2. Has minimal tables (only what's needed for local feed reading)
3. Keeps the NewsfeedPage UI (simplified)
4. Has simple configuration (no complex dashboards)
5. Single-user (no auth)

### What to Keep vs Remove

#### Keep (Core Newsfeed Experience)
- [ ] NewsfeedPage layout and UX
- [ ] ArticleList with virtual scrolling
- [ ] ArticleDetail with preview
- [ ] FeedSidebar with feed selection
- [ ] Keyboard shortcuts (j/k navigation)
- [ ] Read/unread tracking
- [ ] Text size/spacing preferences
- [ ] Basic filtering (by feed, by date)
- [ ] Search within feeds

#### Remove (Advanced Features)
- [ ] User authentication/multi-user
- [ ] Groups/folders hierarchy
- [ ] Knowledge items (notes, prompts)
- [ ] Time machine
- [ ] Semantic topics
- [ ] Story clustering
- [ ] Elasticsearch integration
- [ ] Complex settings dashboards
- [ ] Tagging system
- [ ] Alert rules
- [ ] Saved items per user
- [ ] User quotas

### Database Schema (Minimal)

```sql
-- capture-spine-basic minimal schema
-- Only 6 tables instead of 40+

-- 1. Feeds (from feeds.yaml)
CREATE TABLE feeds (
    feed_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    feed_type TEXT NOT NULL,  -- rss, api, index
    base_url TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    poll_interval_seconds INTEGER DEFAULT 3600,
    enabled BOOLEAN DEFAULT true,
    last_polled_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Feed checkpoints (for resumable polling)
CREATE TABLE feed_checkpoints (
    feed_id UUID REFERENCES feeds(feed_id),
    checkpoint_key TEXT NOT NULL,
    checkpoint_value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (feed_id, checkpoint_key)
);

-- 3. Records (normalized from feedspine)
CREATE TABLE records (
    record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    natural_key TEXT NOT NULL,
    region TEXT NOT NULL DEFAULT 'US',
    record_type TEXT NOT NULL,  -- sec_filing, rss_article, etc.
    title TEXT,
    url TEXT,
    content JSONB NOT NULL DEFAULT '{}',
    published_at TIMESTAMPTZ,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(region, record_type, natural_key)
);

-- 4. Sightings (when/where we saw records)
CREATE TABLE sightings (
    sighting_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id UUID REFERENCES records(record_id),
    feed_id UUID REFERENCES feeds(feed_id),
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(record_id, feed_id)
);

-- 5. User read state (single user)
CREATE TABLE read_state (
    record_id UUID REFERENCES records(record_id) PRIMARY KEY,
    read_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Settings (key-value)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_records_published ON records(published_at DESC);
CREATE INDEX idx_records_natural_key ON records(natural_key);
CREATE INDEX idx_sightings_feed ON sightings(feed_id);
```

### Backend API (Simplified)

```python
# capture_spine_basic/api/routes.py
from fastapi import FastAPI
from feedspine import Pipeline, StorageBackend
from py_sec_edgar.exhibits import ExhibitService

app = FastAPI(title="capture-spine-basic")

# Only essential endpoints
@app.get("/api/feeds")
async def list_feeds(): ...

@app.get("/api/records")
async def list_records(
    feed_ids: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
): ...

@app.get("/api/records/{record_id}")
async def get_record(record_id: str): ...

@app.post("/api/records/{record_id}/read")
async def mark_read(record_id: str): ...

@app.get("/api/settings")
async def get_settings(): ...

@app.put("/api/settings")
async def update_settings(settings: dict): ...

# NO: /api/users, /api/groups, /api/knowledge, /api/alerts, etc.
```

### Frontend Structure

```
capture-spine-basic/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # ~200 lines
│   ├── db/
│   │   ├── schema.sql          # ~60 lines (vs 4800+ in full)
│   │   └── repos.py            # ~150 lines
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   └── ReaderPage.tsx  # Simplified NewsfeedPage
│   │   ├── components/
│   │   │   ├── ArticleList.tsx     # Keep
│   │   │   ├── ArticleDetail.tsx   # Keep (simplified)
│   │   │   ├── FeedSidebar.tsx     # Keep (simplified)
│   │   │   └── SettingsModal.tsx   # Simplified (no dashboards)
│   │   └── hooks/
│   │       └── useReaderState.ts   # Simplified from 1111 lines to ~300
│   └── package.json
├── feeds.yaml                   # Feed configuration
├── pyproject.toml
└── README.md
```

### Integration with Spine Packages

```python
# capture_spine_basic/backend/main.py
"""capture-spine-basic - simplified feed reader with full spine integration."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from feedspine import Pipeline
from feedspine.storage.postgres import PostgresStorage

# Optional imports with graceful degradation
try:
    from entityspine import EntityResolver
    ENTITYSPINE_AVAILABLE = True
except ImportError:
    ENTITYSPINE_AVAILABLE = False

try:
    from py_sec_edgar.exhibits import ExhibitService
    from py_sec_edgar.forms import FormService
    PYSECEDGAR_AVAILABLE = True
except ImportError:
    PYSECEDGAR_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize storage
    storage = PostgresStorage(DATABASE_URL)
    await storage.initialize()

    # Create pipeline
    app.state.pipeline = Pipeline(storage=storage)

    # Optional: entity resolution
    if ENTITYSPINE_AVAILABLE:
        app.state.resolver = EntityResolver()

    # Optional: SEC parsing
    if PYSECEDGAR_AVAILABLE:
        app.state.exhibit_service = ExhibitService()
        app.state.form_service = FormService()

    yield

    await storage.close()


app = FastAPI(title="capture-spine-basic", lifespan=lifespan)
```

---

## Migration Path

### Phase 1: Clean Up Duplication (1-2 days)

1. **py-sec-edgar**:
   - Remove `core/identity/entity.py` (use entityspine)
   - Keep `core/identity/cik.py`, `accession.py` (SEC-specific)
   - Keep all of `core/taxonomy/` (SEC-specific)
   - Keep all of `core/reference/` (SEC-specific)
   - Update imports to use entityspine where appropriate

2. **entityspine**:
   - Ensure clean Entity, IdentifierClaim exports
   - Ensure normalize functions are exported
   - No changes needed if already clean

3. **feedspine**:
   - No changes needed

### Phase 2: Create capture-spine-basic (2-3 days)

1. Create new project structure
2. Copy simplified UI components from capture-spine
3. Implement minimal backend with 6 tables
4. Wire up feedspine Pipeline
5. Add optional entityspine/py-sec-edgar integration

### Phase 3: Test Integration (1 day)

1. Test standalone mode (no entityspine/py-sec-edgar)
2. Test with py-sec-edgar only
3. Test full integration
4. Document all three modes

---

## File Changes Required

### py-sec-edgar Changes

```
REMOVE:
- core/identity/entity.py           # Use entityspine.Entity
- core/identity/matching.py         # Use entityspine matching

KEEP (SEC-specific):
- core/identity/cik.py              # CIK validation
- core/identity/accession.py        # Accession number
- core/identity/filing.py           # SEC Filing model
- core/identity/store.py            # Local caching
- core/taxonomy/*                   # All taxonomy
- core/reference/*                  # All reference data
- core/extraction/*                 # All extraction

UPDATE:
- core/identity/__init__.py         # Update imports
- exhibits/adapters/entityspine.py  # Use entityspine types
```

### New capture-spine-basic Files

```
CREATE:
capture-spine-basic/
├── backend/
│   ├── api/routes.py               # ~200 lines
│   ├── db/schema.sql               # ~60 lines
│   ├── db/repos.py                 # ~150 lines
│   └── main.py                     # ~100 lines
├── frontend/
│   ├── src/App.tsx                 # ~50 lines
│   ├── src/pages/ReaderPage.tsx    # ~150 lines
│   ├── src/components/             # ~1000 lines total
│   └── src/hooks/useReaderState.ts # ~300 lines
├── feeds.yaml                      # Copy from capture-spine
├── pyproject.toml
└── README.md
```

---

## Summary

| Aspect | py-sec-edgar | entityspine | feedspine | capture-spine-basic |
|--------|--------------|-------------|-----------|---------------------|
| **Entity models** | Remove | **OWNS** | N/A | Uses entityspine |
| **Identifiers** | CIK/Accession only | **OWNS** | N/A | Uses entityspine |
| **SEC taxonomy** | **OWNS** | N/A | N/A | Uses py-sec-edgar |
| **Records** | Filing wraps | N/A | **OWNS** | Uses feedspine |
| **Pipeline** | N/A | N/A | **OWNS** | Uses feedspine |
| **UI** | N/A | N/A | N/A | **OWNS** (simplified) |
| **Tables** | N/A | N/A | N/A | 6 tables |
| **Lines of code** | -500 (remove dups) | +0 | +0 | ~2000 (new) |
