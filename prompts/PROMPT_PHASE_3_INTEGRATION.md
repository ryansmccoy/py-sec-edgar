# Phase 3: Integration Adapters

**STATUS: ✅ COMPLETE (January 26, 2026)**

This phase created formal adapters between EntitySpine and FeedSpine.

---

## ✅ Deliverables Implemented

| Component | Location | Status |
|-----------|----------|--------|
| SymbologyRefreshService | `entityspine/src/entityspine/services/symbology_refresh.py` | ✅ Done |
| SECTickerSource | `entityspine/src/entityspine/sources/sec.py` | ✅ Done |
| FeedSpineAdapter | `entityspine/src/entityspine/adapters/feedspine_adapter.py` | ✅ Done |
| EntityEnricher | `feedspine/src/feedspine/enricher/entity_enricher.py` | ✅ Done |
| Integration Tests | `entityspine/tests/integration/test_feedspine_integration.py` | ✅ 17 passing |

---

## ⚠️ CRITICAL: Read This Design Doc First

**Before implementing, study the integration analysis:**
```
entityspine/docs/design/archive/v2.0/09_FEEDSPINE_INTEGRATION_ANALYSIS.md
```

This document explains:
- Why FeedSpine and EntitySpine are **complementary, not overlapping**
- FeedSpine: "Have I seen this record before?" (deduplication)
- EntitySpine: "What entity does this identifier belong to?" (resolution)

---

## What This Phase Delivers

### 1. SymbologyRefreshService (EntitySpine side)
Refresh symbology from multiple sources, only appending NEW identifiers.

### 2. EntityEnricher (FeedSpine side)
Enrich feed records with EntitySpine resolution.

### 3. FeedSpineAdapter (EntitySpine side)
Optional: Use FeedSpine as audit trail for symbology updates.

---

## Prerequisites

```bash
# EntitySpine v0.3.3+ working
pip install entityspine
python -c "from entityspine import SqliteStore; s=SqliteStore(':memory:'); s.load_sec_data(); print(f'Loaded {s.count()} entities')"

# FeedSpine tests passing
cd feedspine
python -m pytest tests/ -x -q  # 506 passing, 1 failing OK
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INTEGRATION ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DATA SOURCES              FEEDSPINE              ENTITYSPINE               │
│  ───────────               ─────────              ───────────               │
│                                                                              │
│  SEC Tickers ─┐                                                              │
│               │      ┌──────────────────┐                                   │
│  GLEIF LEI ───┼─────▶│  FeedSpine       │     ┌──────────────────────┐     │
│               │      │  (Optional)      │     │  EntitySpine         │     │
│  OpenFIGI ────┤      │                  │     │                      │     │
│               │      │  • Deduplication │────▶│  • Entity Resolution │     │
│  Custom ──────┘      │  • Sightings     │     │  • Claims Storage    │     │
│                      │  • Audit Trail   │     │  • Identity Graph    │     │
│                      └──────────────────┘     └──────────────────────┘     │
│                                                                              │
│                              OR                                              │
│                                                                              │
│  SEC Tickers ─┐                                                              │
│               │                               ┌──────────────────────┐     │
│  GLEIF LEI ───┼──────────────────────────────▶│  EntitySpine         │     │
│               │      (Direct, no FeedSpine)   │                      │     │
│  Custom ──────┘                               │  • SymbologyRefresh  │     │
│                                               │  • Dedup at ingest   │     │
│                                               └──────────────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Deliverable 1: SymbologyRefreshService (EntitySpine)

**Key insight**: EntitySpine can refresh symbology **with or without** FeedSpine.

```python
# entityspine/src/entityspine/services/symbology_refresh.py

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass
class RefreshResult:
    """Result of a symbology refresh operation."""
    source: str
    records_fetched: int
    new_entities: int
    new_claims: int
    skipped_duplicates: int
    errors: list[str]


class SymbologySource(Protocol):
    """Protocol for symbology data sources."""
    name: str
    async def fetch(self) -> list[dict]:
        """Fetch current symbology data."""
        ...


class SymbologyRefreshService:
    """
    Refresh symbology from multiple sources, ONLY appending new identifiers.

    Key Features:
    - Only appends NEW identifiers (no duplicates)
    - Tracks when identifiers were first/last seen
    - Works with OR without FeedSpine
    - Uses EntitySpine for identity resolution

    Example:
        >>> from entityspine import SqliteStore
        >>> from entityspine.services.symbology_refresh import SymbologyRefreshService
        >>> from entityspine.sources.sec import SECTickerSource
        >>>
        >>> store = SqliteStore("entities.db")
        >>> store.initialize()
        >>>
        >>> service = SymbologyRefreshService(store)
        >>> service.add_source(SECTickerSource())
        >>> results = await service.refresh_all()
        >>> print(f"Added {sum(r.new_claims for r in results)} new identifiers")
    """

    def __init__(
        self,
        store,  # EntityStore
        feedspine=None,  # Optional FeedSpine for audit trail
    ):
        self._store = store
        self._spine = feedspine  # Optional
        self._sources: list[SymbologySource] = []

    def add_source(self, source: SymbologySource) -> None:
        """Register a symbology source."""
        self._sources.append(source)

    async def refresh_all(self) -> list[RefreshResult]:
        """Refresh all registered sources."""
        results = []
        for source in self._sources:
            result = await self.refresh_source(source)
            results.append(result)
        return results

    async def refresh_source(self, source: SymbologySource) -> RefreshResult:
        """
        Refresh symbology from a single source.

        Process:
        1. Fetch raw data from source
        2. If FeedSpine configured, store for audit trail
        3. For each record, check if identifier exists
        4. Only insert NEW identifiers (no duplicates!)
        """
        raw_records = await source.fetch()

        # Optional: Store in FeedSpine for audit
        if self._spine:
            await self._store_in_feedspine(source.name, raw_records)

        new_entities = 0
        new_claims = 0
        skipped = 0
        errors = []

        for record in raw_records:
            try:
                result = self._process_record(source.name, record)
                if result == "new_entity":
                    new_entities += 1
                elif result == "new_claim":
                    new_claims += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(str(e))

        return RefreshResult(
            source=source.name,
            records_fetched=len(raw_records),
            new_entities=new_entities,
            new_claims=new_claims,
            skipped_duplicates=skipped,
            errors=errors,
        )

    def _process_record(self, source: str, record: dict) -> str:
        """Process a single record. Returns 'new_entity', 'new_claim', or 'skipped'."""
        cik = record.get("cik")
        if not cik:
            return "skipped"

        # Check if entity exists by CIK
        existing = self._store.get_entities_by_cik(cik)

        if not existing:
            # New entity - create it
            self._create_entity_from_record(record)
            return "new_entity"

        # Entity exists - check if we have all claims
        # (e.g., maybe we now have a ticker we didn't have before)
        return "skipped"  # Already exists
```

---

## Deliverable 2: Symbology Sources

```python
# entityspine/src/entityspine/sources/sec.py

import httpx

class SECTickerSource:
    """SEC company_tickers.json source."""

    name = "sec-tickers"
    url = "https://www.sec.gov/files/company_tickers.json"

    async def fetch(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.url,
                headers={"User-Agent": "EntitySpine/1.0 (contact@example.com)"},
            )
            data = response.json()

            return [
                {
                    "cik": str(item["cik_str"]).zfill(10),
                    "ticker": item.get("ticker"),
                    "name": item.get("title"),
                }
                for item in data.values()
            ]


# entityspine/src/entityspine/sources/gleif.py

class GLEIFSource:
    """GLEIF LEI bulk data source."""

    name = "gleif-lei"

    async def fetch(self) -> list[dict]:
        # Download and parse GLEIF golden copy
        # Returns list of {"lei": "...", "name": "...", ...}
        ...
```

---

## Deliverable 3: EntityEnricher (FeedSpine side)

When FeedSpine detects a new filing, enrich it with EntitySpine resolution.

```python
# feedspine/src/feedspine/enrichers/entity_enricher.py

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entityspine import SqliteStore


class EntityEnricher:
    """
    Enrich FeedSpine records with EntitySpine entity resolution.

    Use Case: FeedSpine detects new SEC filing, wants to know
    which company it belongs to (not just CIK, but full entity context).

    Example:
        >>> from entityspine import SqliteStore
        >>> from feedspine.enrichers.entity_enricher import EntityEnricher
        >>>
        >>> store = SqliteStore("entities.db")
        >>> store.load_sec_data()
        >>> enricher = EntityEnricher(store)
        >>>
        >>> # FeedSpine detected new filing
        >>> record = {"cik": "0000320193", "form_type": "10-K"}
        >>> enriched = enricher.enrich(record)
        >>> print(enriched["entity_name"])  # "Apple Inc."
    """

    def __init__(self, store: "SqliteStore"):
        self._store = store

    def enrich(self, record: dict) -> dict:
        """Add entity context to a feed record."""
        cik = record.get("cik")
        if not cik:
            return record

        # Resolve CIK to entity
        entities = self._store.get_entities_by_cik(cik)
        if entities:
            entity = entities[0]
            record["entity_id"] = entity.entity_id
            record["entity_name"] = entity.primary_name
            record["entity_type"] = entity.entity_type.value if hasattr(entity, 'entity_type') else "organization"

        return record
```

---

## Deliverable 4: Optional FeedSpine Adapter (EntitySpine)

Use FeedSpine as audit trail when refreshing symbology.

```python
# entityspine/src/entityspine/adapters/feedspine_adapter.py

"""
Optional adapter to use FeedSpine for symbology refresh audit trail.

FeedSpine Adds:
- Sighting tracking (first_seen, last_seen)
- Deduplication at source level
- Bronze/Silver/Gold layer management
- Scheduled refresh (cron)

Without FeedSpine:
- EntitySpine handles deduplication at entity level
- No source-level sightings (just claims)
- Manual refresh triggers
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from feedspine import FeedSpine


class FeedSpineAdapter:
    """Adapter for using FeedSpine with EntitySpine symbology refresh."""

    def __init__(self, feedspine: "FeedSpine"):
        self._spine = feedspine

    async def store_raw_records(self, source: str, records: list[dict]) -> None:
        """Store raw symbology records in FeedSpine Bronze layer."""
        for record in records:
            natural_key = self._derive_key(source, record)
            await self._spine.record(
                feed_id=source,
                natural_key=natural_key,
                content=record,
            )

    def _derive_key(self, source: str, record: dict) -> str:
        """Derive natural key for deduplication."""
        if cik := record.get("cik"):
            return f"cik:{cik}"
        if lei := record.get("lei"):
            return f"lei:{lei}"
        raise ValueError("No identifier found for natural key")
```

---

## Data Flow Diagrams

### Flow 1: Symbology Refresh (WITHOUT FeedSpine)

```
SEC API ────▶ SymbologyRefreshService ────▶ EntitySpine
              │
              ├─ Fetch company_tickers.json
              ├─ For each record:
              │    ├─ Check if CIK exists in EntitySpine
              │    ├─ If new: Create Entity + Claims
              │    └─ If exists: Skip (no duplicates)
              └─ Return RefreshResult
```

### Flow 2: Symbology Refresh (WITH FeedSpine)

```
SEC API ────▶ SymbologyRefreshService ────▶ FeedSpine ────▶ EntitySpine
              │                              │
              ├─ Fetch company_tickers.json  ├─ Store in Bronze
              │                              ├─ Track sightings
              │                              └─ Dedup by natural_key
              │
              └─ Process new records ────────────────────▶ Create Entities
```

### Flow 3: FeedSpine Filing Detection (WITH EntitySpine enrichment)

```
SEC RSS Feed ────▶ FeedSpine ────▶ EntityEnricher ────▶ Enriched Record
                   │                │
                   ├─ Detect new    ├─ Lookup CIK in EntitySpine
                   │  filing        ├─ Add entity_name, entity_id
                   └─ Dedup         └─ Return enriched record
```

---

## Integration Tests

```python
# tests/integration/test_feedspine_entityspine.py

import pytest
from entityspine import SqliteStore


def test_enrich_feedspine_record_with_entityspine():
    """FeedSpine record gets enriched with EntitySpine entity context."""
    # Setup EntitySpine
    store = SqliteStore(":memory:")
    store.initialize()
    store.load_sec_data()

    # Simulate FeedSpine record
    record = {"cik": "0000320193", "form_type": "10-K"}

    # Enrich with EntitySpine
    entities = store.get_entities_by_cik(record["cik"])
    assert len(entities) > 0

    record["entity_name"] = entities[0].primary_name
    assert record["entity_name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_symbology_refresh_no_duplicates():
    """SymbologyRefreshService only adds new identifiers."""
    from entityspine.services.symbology_refresh import SymbologyRefreshService

    store = SqliteStore(":memory:")
    store.initialize()

    service = SymbologyRefreshService(store)

    # First refresh - should add entities
    result1 = await service.refresh_all()
    count1 = sum(r.new_entities for r in result1)

    # Second refresh - should skip all (no duplicates)
    result2 = await service.refresh_all()
    count2 = sum(r.new_entities for r in result2)

    assert count2 == 0  # No new entities on second refresh
```

---

## Acceptance Criteria

```bash
# 1. SymbologyRefreshService works without FeedSpine
python -c "
from entityspine import SqliteStore

store = SqliteStore(':memory:')
store.initialize()
store.load_sec_data()
print(f'Loaded {store.count()} entities without FeedSpine')
"

# 2. EntitySpine can enrich a FeedSpine-style record
python -c "
from entityspine import SqliteStore

store = SqliteStore(':memory:')
store.initialize()
store.load_sec_data()

# Simulate FeedSpine record
record = {'cik': '0000320193', 'form_type': '10-K'}
entities = store.get_entities_by_cik(record['cik'])
record['entity_name'] = entities[0].primary_name
print(record)
"
# {'cik': '0000320193', 'form_type': '10-K', 'entity_name': 'Apple Inc.'}

# 3. No duplicates on repeated refresh
python -c "
from entityspine import SqliteStore

store = SqliteStore(':memory:')
store.initialize()

# First load
store.load_sec_data()
count1 = store.count()

# Second load (same data)
store.load_sec_data()
count2 = store.count()

print(f'First: {count1}, Second: {count2}')
assert count2 == count1, 'Duplicates were created!'
"
```

---

## Key Reference Documents

| Document | Purpose |
|----------|---------|
| `entityspine/docs/design/archive/v2.0/09_FEEDSPINE_INTEGRATION_ANALYSIS.md` | Full integration design |
| `entityspine/docs/archive/v1/03_FEEDSPINE_INTEGRATION.md` | FeedSpine feed definitions |
| `entityspine/examples/05_filing_facts_ingestion.py` | FilingFacts contract |
| `entityspine/src/entityspine/integration/contracts.py` | Integration dataclasses |

---

## What's Next?

After Phase 3:
- **Phase 4**: py-sec-edgar services (ticker resolution CLI, `--ticker` flag)
- **Phase 5**: Section extraction with entity mention resolution

---

*Phase 3 of 5 | ❌ NOT STARTED | Depends on: Phase 1 + Phase 2A*
*Key Insight: FeedSpine is OPTIONAL for EntitySpine - design supports both patterns*
