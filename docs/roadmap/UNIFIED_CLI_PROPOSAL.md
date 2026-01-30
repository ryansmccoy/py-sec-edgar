# Unified CLI Design Document

**py-sec-edgar + FeedSpine + EntitySpine**

*Status: PROPOSAL - Needs Discussion*
*Created: January 29, 2026*

---

## Executive Summary

This document outlines a proposal for a unified command-line interface that provides a cohesive experience across the py-sec-edgar, FeedSpine, and EntitySpine packages. The goal is to **hide complexity while exposing power** - users shouldn't need to know they're using three separate packages unless they want to.

---

## Design Philosophy

### Option A: Hidden Integration (Recommended for v1)

The CLI is `py-sec-edgar` but internally uses FeedSpine and EntitySpine:

```bash
# User just sees py-sec-edgar
sec-edgar download --tickers AAPL --forms 10-K

# Internally:
# 1. Uses FeedSpine for deduplication/sighting tracking
# 2. Uses EntitySpine for CIK resolution
# 3. User doesn't know/care about these details
```

**Pros:**
- Simple user experience
- No learning curve
- Single package to install
- Natural progression - features appear as "intelligent" py-sec-edgar

**Cons:**
- Hidden complexity might confuse power users
- Harder to debug integration issues
- FeedSpine/EntitySpine features not directly accessible

### Option B: Exposed Sub-Commands

The CLI has explicit sub-commands for each package:

```bash
# Main commands
sec-edgar download --tickers AAPL

# Entity management (optional, explicit)
sec-edgar entity resolve AAPL
sec-edgar entity search "Apple"
sec-edgar entity load sec

# Feed management (optional, explicit)
sec-edgar feed status
sec-edgar feed collect
sec-edgar feed dedupe
```

**Pros:**
- Power users can access advanced features
- Clear separation of concerns
- Debugging is easier
- Teaches users about the ecosystem

**Cons:**
- More complex CLI surface
- Users might be confused by sub-commands
- Need to maintain more documentation

### Option C: Progressive Disclosure (Recommended for v2)

Start hidden, expose as needed:

```bash
# Simple commands work without any knowledge of underlying packages
sec-edgar download AAPL

# Advanced flag exposes entity features
sec-edgar download AAPL --with-entities
sec-edgar entity search "Apple"  # Available but not advertised

# Admin/power user commands
sec-edgar admin entity status
sec-edgar admin feed collect
```

**Pros:**
- Best of both worlds
- Simple for beginners
- Powerful for experts
- Can evolve over time

**Cons:**
- More complex implementation
- Need careful UX design

---

## Proposed Architecture

### Directory Structure

```
py_sec_edgar/
└── src/py_sec_edgar/
    └── cli/
        ├── __init__.py          # Export main app
        ├── app.py               # Main Typer app, top-level commands
        ├── workflows.py         # Workflow commands (existing)
        ├── feeds.py             # Feed/sync commands (existing)
        │
        ├── entity/              # NEW: Entity sub-commands
        │   ├── __init__.py
        │   ├── commands.py      # resolve, search, load, etc.
        │   └── formatters.py    # Output formatting
        │
        ├── admin/               # NEW: Admin/power user commands
        │   ├── __init__.py
        │   ├── entity.py        # EntitySpine management
        │   ├── feed.py          # FeedSpine management
        │   └── status.py        # Cross-package status
        │
        └── integration/         # NEW: Integration utilities
            ├── __init__.py
            ├── entityspine.py   # EntitySpine integration
            └── feedspine.py     # FeedSpine integration
```

### Command Groups

```python
# py_sec_edgar/cli/app.py

app = typer.Typer(name="sec-edgar")

# Primary commands (simple, hidden integration)
@app.command()
def download(tickers: list[str], forms: list[str]):
    """Download filings - uses EntitySpine for resolution, FeedSpine for dedup."""
    # Internally uses both packages but user doesn't see this
    pass

# Optional: Entity sub-commands (for power users)
entity_app = typer.Typer(name="entity", help="Entity resolution commands")
app.add_typer(entity_app, hidden=False)  # Can be hidden=True initially

@entity_app.command("resolve")
def entity_resolve(query: str):
    """Resolve a ticker/CIK/name to entity."""
    pass

# Optional: Admin sub-commands (for debugging/management)
admin_app = typer.Typer(name="admin", help="Admin commands", hidden=True)
app.add_typer(admin_app)
```

---

## Specific Command Proposals

### Top-Level Commands (Hidden Integration)

These work "magically" without users knowing about FeedSpine/EntitySpine:

| Command | Integration | Description |
|---------|-------------|-------------|
| `sec-edgar download` | EntitySpine | Resolves tickers to CIKs automatically |
| `sec-edgar search` | EntitySpine | Fuzzy search with entity resolution |
| `sec-edgar monitor` | FeedSpine | RSS with automatic deduplication |
| `sec-edgar sync` | FeedSpine | Smart sync with sighting tracking |
| `sec-edgar status` | Both | Shows filing count + entity count |

### Entity Sub-Commands (Exposed but Optional)

```bash
sec-edgar entity resolve AAPL
# Resolves "AAPL" to entity, shows CIK, name, aliases, etc.

sec-edgar entity search "Apple"
# Fuzzy search across all known entities

sec-edgar entity load sec
# Explicitly load/refresh SEC company_tickers.json

sec-edgar entity claims 0000320193
# Show all identifier claims for entity

sec-edgar entity graph AAPL --depth 2
# Show entity relationship graph
```

### Admin Sub-Commands (Hidden by Default)

```bash
sec-edgar admin status
# Full status across all integrated packages

sec-edgar admin feed collect
# Manually trigger FeedSpine collection

sec-edgar admin feed dedupe
# Show deduplication statistics

sec-edgar admin entity rebuild
# Rebuild entity index

sec-edgar admin config
# Show all configuration (py-sec-edgar + EntitySpine + FeedSpine)
```

---

## Configuration Integration

### Single Config File (Optional)

Users CAN use a single config file, but individual package configs still work:

```toml
# sec-edgar.toml (optional unified config)

[sec]
user_agent = "MyApp user@example.com"
data_dir = "./data/sec"

[entities]
db_path = "./data/entities.db"
auto_load_sec = true

[feeds]
backend = "duckdb"
db_path = "./data/feeds.db"
```

### Config Loading Priority

1. Environment variables (highest priority)
2. `sec-edgar.toml` in current directory
3. `~/.config/sec-edgar/config.toml`
4. Package-specific defaults

---

## Graceful Degradation

The CLI should work even if optional packages aren't installed:

```python
# py_sec_edgar/cli/integration/entityspine.py

try:
    from entityspine import SqliteStore
    from entityspine.services.resolver import EntityResolver
    ENTITYSPINE_AVAILABLE = True
except ImportError:
    ENTITYSPINE_AVAILABLE = False


def resolve_ticker(ticker: str) -> dict | None:
    """Resolve ticker to entity info.

    Returns None if EntitySpine not available.
    Falls back to company_tickers.json lookup.
    """
    if ENTITYSPINE_AVAILABLE:
        resolver = get_resolver()
        result = resolver.resolve(ticker)
        return result.to_dict() if result else None
    else:
        # Fallback to basic company_tickers.json
        from py_sec_edgar.services import CompanyService
        return CompanyService().lookup(ticker)
```

### User Feedback

When a feature requires an optional package:

```python
@app.command()
def entity_graph(query: str):
    """Show entity relationship graph."""
    if not ENTITYSPINE_AVAILABLE:
        console.print(
            "[yellow]Entity graph requires EntitySpine.[/yellow]\n"
            "Install with: pip install entityspine\n"
            "Or: pip install py-sec-edgar[entities]"
        )
        raise typer.Exit(1)
    # ... actual implementation
```

---

## Implementation Phases

### Phase 1: Hidden Integration (Current Sprint)

1. Add EntitySpine resolution to `sec-edgar download`
2. Add FeedSpine deduplication to `sec-edgar monitor`
3. Add `sec-edgar status` with entity/feed counts
4. No new visible commands

### Phase 2: Entity Commands (v4.1)

1. Add `sec-edgar entity` sub-command group
2. Expose: resolve, search, claims
3. Add `--with-entities` flag to relevant commands
4. Document entity features

### Phase 3: Admin Commands (v4.2)

1. Add `sec-edgar admin` sub-command group (hidden)
2. Cross-package status command
3. FeedSpine management commands
4. Configuration management

### Phase 4: Unified Config (v5.0)

1. Add `sec-edgar.toml` support
2. Migrate to shared config module
3. Full documentation

---

## Open Questions

### 1. Should entity commands be hidden initially?

**Option A**: Hidden (`hidden=True`), discoverable via docs
**Option B**: Visible but grouped separately
**Option C**: Always visible

*Recommendation*: Start hidden (Option A), move to visible (Option B) in v4.1

### 2. How to handle conflicting configs?

If user has both `SEC_EDGAR_DATA_DIR` and `ENTITYSPINE_DB_PATH`, which wins?

*Recommendation*: SEC_EDGAR_ prefix always wins; EntitySpine uses SEC path unless explicitly overridden

### 3. Should we create a `spine` meta-CLI?

A separate `spine` command that wraps all three packages?

```bash
spine sec download AAPL
spine entity resolve AAPL
spine feed collect
```

*Recommendation*: No, keep `sec-edgar` as the primary interface. Users who want direct access can use package CLIs.

---

## Alternative: Package-Specific CLIs

If we don't want a unified CLI, document using packages separately:

```bash
# SEC filings
sec-edgar download --tickers AAPL

# Entity resolution (separate)
entityspine resolve AAPL
entityspine search "Apple"

# Feed management (separate)
feedspine collect
feedspine status
```

This is simpler but requires users to learn three CLIs.

---

## Next Steps

1. **Discuss**: Review this document, decide on Option A/B/C
2. **Prototype**: Implement Phase 1 (hidden integration)
3. **Test**: Get user feedback on hidden vs exposed
4. **Iterate**: Adjust based on feedback

---

## Appendix: Example Session

### Hidden Integration (User Experience)

```bash
$ sec-edgar download AAPL --forms 10-K
✓ Resolved AAPL → Apple Inc. (CIK: 0000320193)
✓ Found 5 10-K filings (2020-2024)
✓ Downloading...
  [████████████████████████████] 5/5 complete
✓ Saved to ./sec_data/Archives/edgar/data/320193/

$ sec-edgar monitor --tickers AAPL,MSFT --forms 8-K
✓ Monitoring RSS feed for 8-K filings...
  Checking every 5 minutes
  Press Ctrl+C to stop

  10:32:15 - New filing: AAPL 8-K (Item 8.01)
  10:47:23 - New filing: MSFT 8-K (Item 5.02)
  (duplicate skipped: AAPL 8-K - already seen at 10:32:15)

$ sec-edgar status
SEC Edgar Status
─────────────────────────────────────────
  Filings downloaded:     1,234
  Storage location:       ./sec_data (156 MB)
  Entities resolved:      456
  Feed sightings:         2,341
  Last sync:              10 minutes ago
```

### With Entity Commands Exposed

```bash
$ sec-edgar entity resolve AAPL
╭─ Entity: Apple Inc. ─────────────────────────────────────╮
│ CIK:        0000320193                                   │
│ Ticker:     AAPL (XNAS)                                  │
│ LEI:        HWUPKR0MPOU8FGXBT394                         │
│ Type:       Corporation                                  │
│ Status:     Active                                       │
│ SIC:        3571 - Electronic Computers                  │
│                                                          │
│ Aliases:                                                 │
│   • Apple Inc                                            │
│   • Apple Computer Inc                                   │
│   • Apple Computer, Inc.                                 │
╰──────────────────────────────────────────────────────────╯

$ sec-edgar entity search "nvidia"
  Score  Entity                    CIK
  ─────  ────────────────────────  ──────────
  0.98   NVIDIA CORP               0001045810
  0.72   NVIDIA Corporation        0001045810
  0.45   nVidia                    0001045810
```

---

*This document is a proposal for discussion. Implementation details may change based on feedback.*
