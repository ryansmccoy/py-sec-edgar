# Phase 2B: EntitySpine Tier 2+ (OPTIONAL)

**STATUS: ⏸️ OPTIONAL**

This phase is optional. Skip if Tier 0-1 (JSON/SQLite) meets your needs.

---

## When You Need Tier 2+

| If You Need... | Use |
|----------------|-----|
| Basic entity resolution | ✅ Tier 1 (SqliteStore) |
| Analytics on entities | 🔄 Tier 2 (DuckDB) |
| Historical `as_of` queries | 🔄 Tier 3 (PostgreSQL) |
| Production deployment | 🔄 Tier 3 (PostgreSQL) |

---

## Current Implementation (Tier 0-1)

EntitySpine v0.3.3 includes:

| Store | Tier | Backend | Status |
|-------|------|---------|--------|
| `JsonEntityStore` | 0 | stdlib json | ✅ Done |
| `SqliteStore` | 1 | stdlib sqlite3 | ✅ Done |
| `SqlModelStore` | 1+ | SQLModel/SQLAlchemy | ✅ Done |

### What Tier 1 Provides

```python
from entityspine import SqliteStore

store = SqliteStore("entities.db")
store.initialize()
store.load_sec_data()  # Auto-download SEC data

# Entity resolution
results = store.search_entities("AAPL")
entities = store.get_entities_by_cik("0000320193")

# Knowledge graph
store.save_asset(asset)
store.save_relationship(relationship)
store.save_event(event)
```

---

## Tier Capability Matrix

| Capability | Tier 0 | Tier 1 | Tier 2 | Tier 3 |
|------------|--------|--------|--------|--------|
| CIK → Entity | ✅ | ✅ | ✅ | ✅ |
| Ticker → Entity (current) | ✅ | ✅ | ✅ | ✅ |
| Ticker → Entity (historical) | ⚠️ | ⚠️ | ⚠️ | ✅ |
| `as_of` honored | ❌ | ❌ | ❌ | ✅ |
| Full-text search | ❌ | LIKE | LIKE | ✅ |
| Analytics queries | ❌ | ❌ | ✅ | ✅ |
| Merge redirect chains | ❌ | ✅ | ✅ | ✅ |

---

## Phase 2B Scope (If Implementing)

### Tier 2: DuckDB Store

```python
# NOT YET IMPLEMENTED
# entityspine/src/entityspine/adapters/duckdb_store.py

class DuckDBStore:
    """Tier 2 store for analytics queries."""

    def __init__(self, path: str):
        import duckdb
        self._conn = duckdb.connect(path)

    # Must return domain dataclasses, not DuckDB types
    def get_entity(self, entity_id: str) -> Entity | None:
        row = self._conn.execute(...).fetchone()
        return row_to_entity(row) if row else None
```

### Tier 3: PostgreSQL Store

```python
# NOT YET IMPLEMENTED
# entityspine/src/entityspine/adapters/postgres_store.py

class PostgresStore:
    """Tier 3 store with temporal queries."""

    def __init__(self, connection_string: str):
        import asyncpg
        ...

    # Supports as_of queries
    async def get_entity(self, entity_id: str, as_of: datetime | None = None) -> Entity | None:
        if as_of:
            # Query temporal table
            ...
        ...
```

---

## Architecture Rules (From Phase 1)

When implementing Tier 2+, follow these rules:

1. **Return domain dataclasses** — Never return ORM models
2. **No tier-specific types leak** — All stores have same interface
3. **Tier honesty** — Lower tiers warn when they can't honor `as_of`

### Example: Tier Honesty

```python
# SqliteStore (Tier 1) warns when as_of is requested
result = store.resolve_cik("0000320193", as_of=datetime(2020, 1, 1))
print(result.warnings)
# ["as_of_ignored: Tier 1 store lacks temporal data"]
```

---

## Pattern Reference

Study these EntitySpine files before implementing Tier 2+:

| File | Pattern |
|------|---------|
| `stores/sqlite_store.py` | Tier 1 implementation |
| `adapters/orm/sqlmodel_store.py` | SQLModel pattern |
| `stores/mappers.py` | Row ↔ domain conversion |
| `domain/protocols.py` | Store protocol interface |

---

## What's Next?

If you implement Tier 2+:
- **Phase 3**: Integration adapters work with any tier
- **Phase 4**: py-sec-edgar can use any tier

---

*Phase 2B of 5 | ⏸️ OPTIONAL | Can parallel with: Phase 2A*
