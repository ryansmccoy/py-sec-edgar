# Integration Implementation Plan

**Phase 1: Shared Configuration + Status + Auto-Discovery**

*Created: January 29, 2026*
*Status: ✅ COMPLETED*

---

## Implementation Summary

All four integration features have been implemented:

| Feature | Status | Location |
|---------|--------|----------|
| Shared Configuration | ✅ Done | `spine/config.py` |
| Status Dashboard | ✅ Done | `py_sec_edgar/src/py_sec_edgar/cli/status.py` |
| Adapter Auto-Discovery | ✅ Done | `feedspine/src/feedspine/discovery.py` |
| EntitySpine Auto-Loading | ✅ Done | `entityspine/src/entityspine/loaders/sec_loader.py` |

### Key Files Created/Modified

1. **`spine/config.py`** - Shared TOML + env var configuration
2. **`spine/__init__.py`** - Package exports
3. **`py_sec_edgar/src/py_sec_edgar/cli/status.py`** - Cross-package status command
4. **`py_sec_edgar/src/py_sec_edgar/cli/app.py`** - Added status command
5. **`feedspine/src/feedspine/discovery.py`** - Entry point adapter discovery
6. **`feedspine/src/feedspine/__init__.py`** - Export discovery functions
7. **`pyproject.toml`** - Added `feedspine.adapters` entry points
8. **`entityspine/src/entityspine/loaders/sec_loader.py`** - SEC auto-loader
9. **`entityspine/src/entityspine/loaders/__init__.py`** - Export SEC loader
10. **`entityspine/src/entityspine/stores/sqlite_store.py`** - Added `auto_load_sec` parameter

---

## Overview

This document details the implementation plan for three integration improvements:

1. **Shared Configuration System** - Single config file for all packages
2. **Status Dashboard** - Cross-package status command
3. **Adapter Auto-Discovery** - FeedSpine auto-discovers py-sec-edgar adapters
4. **EntitySpine Auto-Loading** - Auto-load SEC data on first query

---

## 1. Shared Configuration System

### Goal

Allow users to configure all three packages via a single `.env` file or `spine.toml`.

### Implementation Location

```
py-sec-edgar/                      # Root of monorepo
├── spine/                         # NEW: Shared configuration module
│   ├── __init__.py
│   ├── config.py                  # Shared config loader
│   └── py.typed
```

### Configuration Schema

```python
# spine/config.py

@dataclass
class SpineConfig:
    """Unified configuration for the Spine ecosystem."""

    # SEC settings
    sec_user_agent: str
    sec_data_dir: Path = Path("./data/sec")
    sec_rate_limit: float = 8.0

    # EntitySpine settings
    entity_db_path: Path = Path("./data/entities.db")
    entity_auto_load_sec: bool = True
    entity_storage_tier: str = "sqlite"

    # FeedSpine settings
    feed_backend: str = "duckdb"
    feed_db_path: Path = Path("./data/feeds.db")

    # Integration settings
    enable_deduplication: bool = True
    enable_entity_resolution: bool = True
```

### Environment Variables

| Variable | Package | Description |
|----------|---------|-------------|
| `SPINE_DATA_DIR` | All | Base data directory |
| `SPINE_SEC_USER_AGENT` | py-sec-edgar | SEC API user agent |
| `SPINE_SEC_RATE_LIMIT` | py-sec-edgar | Requests per second |
| `SPINE_ENTITY_DB` | EntitySpine | Entity database path |
| `SPINE_ENTITY_AUTO_LOAD` | EntitySpine | Auto-load SEC data |
| `SPINE_FEED_BACKEND` | FeedSpine | Storage backend |
| `SPINE_FEED_DB` | FeedSpine | Feed database path |

### Loading Priority

1. Environment variables (`SPINE_*`)
2. `spine.toml` in current directory
3. `~/.config/spine/config.toml`
4. Package-specific environment variables
5. Package defaults

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `spine/__init__.py` | CREATE | Package init |
| `spine/config.py` | CREATE | Config loader |
| `py_sec_edgar/core/config.py` | MODIFY | Add spine config fallback |
| `entityspine/core/config.py` | CREATE | Add spine config fallback |

---

## 2. Cross-Package Status Dashboard

### Goal

Single command to see status across all integrated packages.

### Implementation Location

Add to py-sec-edgar CLI:

```
py_sec_edgar/src/py_sec_edgar/cli/
├── app.py              # Add status command
└── status.py           # NEW: Status implementation
```

### Command Interface

```bash
$ sec-edgar status

╭─────────────────────────────────────────────────────────────╮
│                   SPINE ECOSYSTEM STATUS                     │
├─────────────────────────────────────────────────────────────┤
│ py-sec-edgar     v4.0.0    ✅ Ready                         │
│   • Data directory: ./sec_data                              │
│   • Filings cached: 1,234                                   │
│   • Storage used: 156 MB                                    │
│   • Last sync: 2026-01-29 10:30:00                          │
├─────────────────────────────────────────────────────────────┤
│ EntitySpine      v0.3.3    ✅ Available                     │
│   • Database: ./data/entities.db                            │
│   • Entities: 14,523                                        │
│   • Claims: 45,231                                          │
│   • SEC data loaded: ✅                                     │
├─────────────────────────────────────────────────────────────┤
│ FeedSpine        v0.1.0    ✅ Available                     │
│   • Backend: DuckDB                                         │
│   • Records: 2,341                                          │
│   • Feeds registered: 3                                     │
╰─────────────────────────────────────────────────────────────╯
```

### Implementation

```python
# py_sec_edgar/cli/status.py

def get_pysecedgar_status() -> dict:
    """Get py-sec-edgar status."""
    from py_sec_edgar import __version__
    from py_sec_edgar.core.config import get_settings

    settings = get_settings()
    data_dir = settings.data_dir

    # Count filings
    filing_count = 0
    storage_bytes = 0
    if data_dir.exists():
        for f in data_dir.rglob("*"):
            if f.is_file():
                filing_count += 1
                storage_bytes += f.stat().st_size

    return {
        "version": __version__,
        "ready": True,
        "data_dir": str(data_dir),
        "filing_count": filing_count,
        "storage_mb": storage_bytes / (1024 * 1024),
    }


def get_entityspine_status() -> dict | None:
    """Get EntitySpine status if available."""
    try:
        from entityspine import __version__
        from entityspine.stores import SqliteStore

        # Try to get entity count from default DB
        # ...
        return {"version": __version__, "available": True, ...}
    except ImportError:
        return None


def get_feedspine_status() -> dict | None:
    """Get FeedSpine status if available."""
    try:
        from feedspine import __version__
        return {"version": __version__, "available": True, ...}
    except ImportError:
        return None
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `py_sec_edgar/cli/status.py` | CREATE | Status implementation |
| `py_sec_edgar/cli/app.py` | MODIFY | Add status command |

---

## 3. Adapter Auto-Discovery

### Goal

FeedSpine automatically discovers py-sec-edgar adapters via entry points.

### Implementation

Add entry points to py-sec-edgar:

```toml
# py_sec_edgar/pyproject.toml

[project.entry-points."feedspine.adapters"]
sec-rss = "py_sec_edgar.adapters.sec_feeds:SecRssFeedAdapter"
sec-daily = "py_sec_edgar.adapters.sec_feeds:SecDailyIndexAdapter"
sec-quarterly = "py_sec_edgar.adapters.sec_feeds:SecQuarterlyIndexAdapter"
```

Add discovery to FeedSpine:

```python
# feedspine/src/feedspine/discovery.py

def discover_adapters() -> dict[str, type]:
    """Discover adapters from installed packages."""
    import importlib.metadata

    adapters = {}
    for ep in importlib.metadata.entry_points(group="feedspine.adapters"):
        try:
            adapter_class = ep.load()
            adapters[ep.name] = adapter_class
        except Exception:
            pass
    return adapters
```

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `py_sec_edgar/pyproject.toml` | MODIFY | Add entry points |
| `feedspine/discovery.py` | CREATE | Adapter discovery |
| `feedspine/__init__.py` | MODIFY | Export discover_adapters |

---

## 4. EntitySpine Auto-Loading

### Goal

EntitySpine automatically loads SEC data on first query if database is empty.

### Implementation

```python
# entityspine/stores/sqlite_store.py

class SqliteStore:
    def __init__(
        self,
        db_path: str | Path = ":memory:",
        auto_load_sec: bool = True,  # NEW
    ):
        self._auto_load_sec = auto_load_sec
        self._sec_loaded = False

    def _ensure_sec_data(self):
        """Load SEC data if empty and auto_load enabled."""
        if not self._auto_load_sec or self._sec_loaded:
            return

        # Check if entities exist
        count = self.count_entities()
        if count == 0:
            logger.info("Auto-loading SEC company data...")
            self.load_sec_data()

        self._sec_loaded = True

    def search_entities(self, query: str, limit: int = 10):
        """Search entities - auto-loads SEC data if needed."""
        self._ensure_sec_data()  # NEW
        return self._search_entities_impl(query, limit)

    def get_entities_by_cik(self, cik: str):
        """Get by CIK - auto-loads SEC data if needed."""
        self._ensure_sec_data()  # NEW
        return self._get_entities_by_cik_impl(cik)
```

### Files to Modify

| File | Action | Description |
|------|--------|-------------|
| `entityspine/stores/sqlite_store.py` | MODIFY | Add auto-load |
| `entityspine/stores/memory_store.py` | MODIFY | Add auto-load |

---

## Implementation Order

### Step 1: Shared Config (spine/)

1. Create `spine/` package at monorepo root
2. Implement config loader with environment + TOML support
3. Add fallback to py-sec-edgar config
4. Add fallback to entityspine config (if it has one)

### Step 2: Status Command

1. Create `py_sec_edgar/cli/status.py`
2. Implement status collectors for each package
3. Add command to main CLI app
4. Test with/without optional packages

### Step 3: Adapter Discovery

1. Add entry points to py-sec-edgar pyproject.toml
2. Create discovery module in feedspine
3. Add `discover_adapters()` to feedspine exports
4. Test discovery works

### Step 4: EntitySpine Auto-Load

1. Add `auto_load_sec` parameter to SqliteStore
2. Implement lazy loading logic
3. Add to MemoryStore as well
4. Test auto-load behavior

---

## Testing Plan

### Shared Config Tests

```python
def test_config_loads_from_env():
    """Config loads from SPINE_* environment variables."""

def test_config_loads_from_toml():
    """Config loads from spine.toml file."""

def test_config_priority():
    """Environment variables override TOML."""

def test_package_fallback():
    """Falls back to package-specific config if no spine config."""
```

### Status Tests

```python
def test_status_without_optional_packages():
    """Status works without EntitySpine/FeedSpine."""

def test_status_with_all_packages():
    """Status shows all packages when available."""

def test_status_shows_correct_counts():
    """Status shows accurate entity/filing counts."""
```

### Auto-Load Tests

```python
def test_auto_load_on_first_search():
    """SEC data loaded on first search if empty."""

def test_auto_load_disabled():
    """Auto-load can be disabled."""

def test_auto_load_only_once():
    """Auto-load only happens once per instance."""
```

---

## Rollout Plan

1. **PR 1**: Shared config module (`spine/`)
2. **PR 2**: Status command
3. **PR 3**: Adapter discovery
4. **PR 4**: EntitySpine auto-load

Each PR should:
- Include tests
- Update relevant documentation
- Be independently deployable

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Config loading time | < 100ms |
| Status command time | < 2s |
| Auto-load time (cold) | < 5s |
| Adapter discovery time | < 500ms |

---

*Ready for implementation. Proceeding with Step 1: Shared Config.*
