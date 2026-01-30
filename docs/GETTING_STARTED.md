# Getting Started with the Spine Ecosystem

**The Complete Guide to py-sec-edgar, FeedSpine, and EntitySpine**

*Last Updated: January 2026*

---

## Overview

The **Spine Ecosystem** is a suite of three packages that work together to provide a complete SEC filing and entity resolution pipeline:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SPINE ECOSYSTEM                                 │
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐       │
│   │   py-sec-edgar  │────►│    FeedSpine    │────►│   EntitySpine   │       │
│   │   (SEC Filings) │     │   (Pipelines)   │     │  (Resolution)   │       │
│   │                 │     │                 │     │                 │       │
│   │ • Download      │     │ • Deduplication │     │ • Entity graph  │       │
│   │ • Parse forms   │     │ • Bronze/Silver │     │ • Identifiers   │       │
│   │ • Extract data  │     │ • Change detect │     │ • Relationships │       │
│   └─────────────────┘     └─────────────────┘     └─────────────────┘       │
│                                                                             │
│   Each package works STANDALONE or TOGETHER                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Which Package Do You Need?

| I want to... | Package | Install |
|--------------|---------|---------|
| Download SEC filings | py-sec-edgar | `pip install py-sec-edgar` |
| Monitor SEC RSS feeds | py-sec-edgar | `pip install py-sec-edgar` |
| Build a data pipeline with deduplication | FeedSpine | `pip install feedspine` |
| Resolve company/ticker/CIK relationships | EntitySpine | `pip install entityspine` |
| Build an entity knowledge graph | EntitySpine | `pip install entityspine` |
| Do all of the above | All three | See Quick Start below |

---

## Quick Start (5 Minutes)

### Option A: Full Ecosystem (Recommended)

```bash
# Clone the monorepo
git clone https://github.com/ryansmccoy/py-sec-edgar.git
cd py-sec-edgar

# Create virtual environment and install all packages
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install all three packages in development mode
uv pip install -e ./py_sec_edgar
uv pip install -e ./feedspine
uv pip install -e ./entityspine

# Verify installation
python -c "import py_sec_edgar; import feedspine; import entityspine; print('✓ All packages installed')"
```

### Option B: Individual Package Installation

```bash
# py-sec-edgar only (SEC filings)
pip install py-sec-edgar

# FeedSpine only (data pipelines)
pip install feedspine

# EntitySpine only (entity resolution)
pip install entityspine
# Or with all features:
pip install "entityspine[full]"
```

---

## py-sec-edgar: SEC Filing Processor

### What It Does

- Downloads SEC EDGAR filings (10-K, 10-Q, 8-K, Form 4, etc.)
- Monitors RSS feeds for real-time filings
- Extracts structured data from filings
- Smart sync with 94% fewer API requests

### First Steps

```bash
# See what's available (no download)
uv run python -m py_sec_edgar workflows rss --show-entries --count 10 --list-only

# Download Apple's latest 10-K
uv run python -m py_sec_edgar workflows full-index --tickers AAPL --forms "10-K" --download

# Monitor multiple tickers for 8-K filings
uv run python -m py_sec_edgar workflows daily --tickers AAPL,MSFT,GOOGL --days-back 7 --forms "8-K" --download
```

### Python API

```python
from py_sec_edgar import EdgarClient

# Create client
client = EdgarClient()

# Search for filings
filings = client.search(
    tickers=["AAPL"],
    form_types=["10-K"],
    start_date="2024-01-01",
)

# Download a filing
for filing in filings:
    client.download(filing, output_dir="./sec_data")
```

### Key Documentation

- [README.md](../README.md) - Full CLI reference
- [examples/](../examples/) - Usage examples
- [Workflows Guide](../docs/workflows.md) - Understanding the 4 workflows

---

## EntitySpine: Entity Resolution Engine

### What It Does

- Resolves tickers, CIKs, CUSIPs, LEIs to canonical entities
- Builds a knowledge graph of companies, securities, relationships
- Zero dependencies for core functionality (stdlib-only)
- Tiered storage: Memory → SQLite → DuckDB → PostgreSQL

### First Steps

```python
from entityspine import SqliteStore

# Create and initialize store
store = SqliteStore("entities.db")
store.initialize()

# Load SEC company data (~14,000 companies)
store.load_sec_data()

# Resolve a ticker
results = store.search_entities("AAPL")
entity, score = results[0]
print(f"{entity.primary_name} (CIK: {entity.source_id})")
# Apple Inc. (CIK: 0000320193)

# Get by CIK
entities = store.get_entities_by_cik("0000320193")
apple = entities[0]
```

### CLI

```bash
# Load SEC data
python -m entityspine load sec

# Search for entities
python -m entityspine search "Apple"

# Export to JSON
python -m entityspine export --format json > entities.json
```

### Loading Reference Data

EntitySpine includes bulk data sources for market reference data:

```python
from entityspine.sources import (
    ISO10383Source,    # MIC codes (exchanges)
    ISO3166Source,     # Country codes
    ISO4217Source,     # Currency codes
    GLEIFSource,       # LEI (Legal Entity Identifiers)
)

# Fetch MIC data
mic_source = ISO10383Source()
mics = await mic_source.fetch()
print(f"Loaded {len(mics)} MIC codes")

# Create registry for lookups
from entityspine.sources import MICRegistry
registry = MICRegistry()
await registry.load_from_source()
nyse = registry.lookup("XNYS")
```

### Key Documentation

- [entityspine/README.md](../entityspine/README.md) - Full API reference
- [entityspine/docs/](../entityspine/docs/) - Architecture guides
- [ARCHITECTURE_AND_TIERS.md](../entityspine/ARCHITECTURE_AND_TIERS.md) - Tiered storage design

---

## FeedSpine: Data Pipeline Framework

### What It Does

- Storage-agnostic feed collection framework
- Automatic deduplication via natural keys
- Sighting history ("when did we first see this?")
- Bronze → Silver → Gold data quality tiers
- Pluggable storage backends (Memory, DuckDB, PostgreSQL)

### First Steps

```python
import asyncio
from feedspine import FeedSpine, MemoryStorage

async def main():
    storage = MemoryStorage()

    async with FeedSpine(storage=storage) as spine:
        # Register a feed adapter
        from feedspine.adapters import RSSFeedAdapter
        spine.register_feed(RSSFeedAdapter(
            name="sec-rss",
            url="https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=&company=&dateb=&owner=include&count=40&output=atom",
        ))

        # Collect with automatic deduplication
        result = await spine.collect()

        print(f"New records: {result.total_new}")
        print(f"Duplicates skipped: {result.total_duplicates}")

asyncio.run(main())
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Record** | A piece of captured data with metadata |
| **Natural Key** | Unique business identifier (e.g., `SEC-AAPL-10K-2024`) |
| **Layer** | Data quality tier: Bronze → Silver → Gold |
| **Sighting** | A record of when we "saw" a natural key |

### Key Documentation

- [feedspine/README.md](../feedspine/README.md) - Full API reference
- [feedspine/docs/getting-started/](../feedspine/docs/getting-started/) - Tutorials
- [feedspine/docs/concepts/](../feedspine/docs/concepts/) - Core concepts

---

## Integration Patterns

### Pattern 1: py-sec-edgar → EntitySpine (Filing to Entity)

Link SEC filings to resolved entities:

```python
from py_sec_edgar import EdgarClient
from entityspine import SqliteStore

# Initialize
client = EdgarClient()
store = SqliteStore("entities.db")
store.initialize()
store.load_sec_data()

# Get filing
filing = client.get_filing(cik="0000320193", accession="0000320193-23-000106")

# Resolve entity
entities = store.get_entities_by_cik(filing.cik)
entity = entities[0]

print(f"Filing: {filing.form_type} for {entity.primary_name}")
# Filing: 10-K for Apple Inc.
```

### Pattern 2: py-sec-edgar → FeedSpine (Deduplicated Collection)

Use FeedSpine to deduplicate SEC feed collection:

```python
from feedspine import FeedSpine, DuckDBStorage
from feedspine.adapters.sec import SECFilingAdapter

async def collect_sec_filings():
    storage = DuckDBStorage("sec_filings.db")

    async with FeedSpine(storage=storage) as spine:
        # SEC RSS adapter with natural key = accession number
        spine.register_feed(SECFilingAdapter(
            name="sec-rss",
            form_types=["10-K", "10-Q", "8-K"],
        ))

        # Collect - duplicates automatically skipped
        result = await spine.collect()

        # Get new filings only
        new_filings = result.new_records
        return new_filings
```

### Pattern 3: Full Pipeline (All Three Packages)

Complete workflow from RSS to knowledge graph:

```python
from py_sec_edgar import EdgarClient
from feedspine import FeedSpine, DuckDBStorage
from entityspine import SqliteStore

async def full_pipeline():
    # 1. Collect with FeedSpine (deduplication)
    feed_storage = DuckDBStorage("feeds.db")
    async with FeedSpine(storage=feed_storage) as spine:
        result = await spine.collect()
        new_filings = result.new_records

    # 2. Download with py-sec-edgar
    client = EdgarClient()
    for filing in new_filings:
        client.download(filing.content, output_dir="./sec_data")

    # 3. Resolve with EntitySpine
    entity_store = SqliteStore("entities.db")
    entity_store.initialize()

    for filing in new_filings:
        # Resolve CIK to entity
        entities = entity_store.get_entities_by_cik(filing.content["cik"])
        if entities:
            entity = entities[0]
            # Create filing-entity relationship
            entity_store.link_filing_to_entity(
                filing_accession=filing.natural_key,
                entity_id=entity.entity_id,
            )
```

---

## Common Use Cases

### 1. Research: Download All 10-Ks for Analysis

```bash
# Download 2024 10-K filings for S&P 500 companies
uv run python -m py_sec_edgar workflows full-index \
    --tickers-file sp500_tickers.txt \
    --forms "10-K" \
    --start-date 2024-01-01 \
    --download \
    --extract
```

### 2. Monitoring: Real-Time 8-K Alerts

```bash
# Monitor 8-K filings for your watchlist
uv run python -m py_sec_edgar workflows rss \
    --tickers AAPL,MSFT,GOOGL \
    --forms "8-K" \
    --interval 300 \
    --notify
```

### 3. Entity Resolution: Map Tickers to CIKs

```python
from entityspine import SqliteStore

store = SqliteStore("entities.db")
store.initialize()
store.load_sec_data()

# Map tickers to CIKs
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
for ticker in tickers:
    results = store.search_entities(ticker)
    if results:
        entity, _ = results[0]
        claims = store.get_claims(entity.entity_id)
        cik = next((c.value for c in claims if c.scheme == "cik"), None)
        print(f"{ticker} → CIK {cik}")
```

### 4. Data Pipeline: Deduplicated Feed Collection

```python
# Collect from multiple feeds without duplicates
from feedspine import FeedSpine, DuckDBStorage

storage = DuckDBStorage("feeds.db")
async with FeedSpine(storage=storage) as spine:
    # Same filing in RSS and daily index = stored once
    spine.register_feed(sec_rss_adapter)
    spine.register_feed(sec_daily_adapter)

    result = await spine.collect()
    print(f"New: {result.total_new}, Dups skipped: {result.total_duplicates}")
```

---

## Project Structure

```
py-sec-edgar/                    # Monorepo root
├── py_sec_edgar/               # SEC filing processor
│   ├── src/py_sec_edgar/       # Source code
│   ├── examples/               # Usage examples
│   └── tests/                  # Unit tests
│
├── entityspine/                # Entity resolution engine
│   ├── src/entityspine/        # Source code
│   │   ├── domain/             # Domain models (stdlib-only)
│   │   ├── sources/            # Bulk data sources (ISO, GLEIF, etc.)
│   │   ├── stores/             # Storage backends
│   │   └── loaders/            # Data loaders
│   ├── examples/               # Usage examples
│   └── tests/                  # Unit tests
│
├── feedspine/                  # Data pipeline framework
│   ├── src/feedspine/          # Source code
│   ├── examples/               # Usage examples
│   └── tests/                  # Unit tests
│
├── docs/                       # Shared documentation
├── scripts/                    # Utility scripts
└── INTEGRATION_MANIFESTO.md    # Integration patterns
```

---

## Troubleshooting

### "Module not found" Errors

```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate

# Reinstall in development mode
uv pip install -e ./py_sec_edgar
uv pip install -e ./entityspine
uv pip install -e ./feedspine
```

### SEC Rate Limiting

py-sec-edgar automatically handles SEC rate limiting (10 requests/second). If you see 403 errors:

```python
# Set your user agent (required by SEC)
export SEC_USER_AGENT="Your Name your.email@example.com"
# or in Python:
from py_sec_edgar.config import configure
configure(user_agent="Your Name your.email@example.com")
```

### EntitySpine: "No entities found"

```python
# Ensure you've loaded reference data
store = SqliteStore("entities.db")
store.initialize()

# Load SEC company data (required for ticker/CIK resolution)
store.load_sec_data()

# Now search works
results = store.search_entities("AAPL")
```

### FeedSpine: Duplicates Not Being Detected

Ensure your natural key is consistent:

```python
from feedspine.models.record import RecordCandidate

# Natural key must be unique and consistent
candidate = RecordCandidate(
    natural_key=f"SEC-{cik}-{accession}",  # Consistent format
    content={"cik": cik, ...},
    ...
)
```

---

## Next Steps

1. **Explore Examples**: Each package has an `examples/` directory
2. **Read the Integration Manifesto**: [INTEGRATION_MANIFESTO.md](INTEGRATION_MANIFESTO.md)
3. **Join Discussions**: GitHub Issues for questions
4. **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## FAQ

### Can I use just one package?

Yes! Each package is designed to work standalone. Install only what you need.

### What Python version is required?

- py-sec-edgar: Python 3.10+
- FeedSpine: Python 3.11+
- EntitySpine: Python 3.10+ (3.11+ for some features)

### Is there a web UI?

The `capture-spine` package (not covered in this guide) provides a web UI with Elasticsearch search. See [capture-spine/README.md](../capture-spine/README.md).

### How do I report bugs?

Open an issue at https://github.com/ryansmccoy/py-sec-edgar/issues

---

*For detailed API documentation, see each package's README and docs/ folder.*
