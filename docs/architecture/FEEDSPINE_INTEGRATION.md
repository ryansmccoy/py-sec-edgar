# FeedSpine Integration in py-sec-edgar

This document describes how py-sec-edgar integrates with FeedSpine to provide a robust, extensible SEC EDGAR data collection system.

## Overview

py-sec-edgar v4 is built on **FeedSpine**, a generic feed capture framework that provides:

- **Storage backends** for structured data
- **Blob storage** for documents
- **Search backends** for full-text search
- **Cache backends** for HTTP response caching
- **Enrichers** for content transformation
- **Progress reporters** for collection status
- **Protocols** for extensibility

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         py-sec-edgar                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    SECFeed (High-level API)              │   │
│  │  - Typed SECFilingContent                                │   │
│  │  - Smart sync strategy (quarterly > daily > RSS)         │   │
│  │  - CIK/ticker resolution                                 │   │
│  │  - Document download                                     │   │
│  │  - Search filings                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                    FeedSpine Components                    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │  DuckDB  │ │Filesystem│ │  Memory  │ │   Memory     │  │  │
│  │  │ Storage  │ │   Blob   │ │  Search  │ │   Cache      │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │  │
│  │       │             │            │              │          │  │
│  │  ┌────┴─────────────┴────────────┴──────────────┴──────┐  │  │
│  │  │                FeedSpine Protocols                   │  │  │
│  │  │  StorageBackend | BlobStorage | SearchBackend |     │  │  │
│  │  │  CacheBackend | Enricher | Notifier | Scheduler     │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## FeedSpine Features Used

### 1. DuckDB Storage (filing metadata)

**Purpose**: Store structured filing metadata with efficient querying.

```python
from feedspine.storage.duckdb import DuckDBStorage

storage = DuckDBStorage(Path("sec_filings.db"))
await storage.initialize()

# Store filing
await storage.upsert(record)

# Query filings
async for record in storage.query(filters={"content.form_type": "10-K"}):
    print(record.content)
```

**Used by**: `SECFeed` for all filing metadata storage.

### 2. Filesystem Blob Storage (documents)

**Purpose**: Store downloaded SEC documents (HTML, XML, XBRL files).

```python
from feedspine.blob.filesystem import FilesystemBlob

blob = FilesystemBlob(Path("sec_documents"))
await blob.initialize()

# Store document
await blob.put("sec/0000320193-24-000081/filing.html", content)

# Retrieve document
doc = await blob.get("sec/0000320193-24-000081/filing.html")
```

**Used by**: `SECFeed.download_document()` for document storage and retrieval.

### 3. Memory Search (full-text search)

**Purpose**: Enable searching across filing metadata.

```python
from feedspine.search.memory import MemorySearch

search = MemorySearch()
await search.initialize()

# Index a filing
await search.index(
    record_id="0000320193-24-000081",
    content={"company_name": "Apple Inc", "form_type": "10-K"},
    metadata={"cik": "0000320193"}
)

# Search filings
response = await search.search("Apple", limit=10)
for result in response.results:
    print(result.record_id)
```

**Used by**: `SECFeed.search()` and `SECFeed.index_filing()`.

### 4. Memory Cache (HTTP caching)

**Purpose**: Cache SEC API responses to reduce duplicate requests.

```python
from feedspine.cache.memory import MemoryCache

cache = MemoryCache()
await cache.initialize()

# Cache with TTL
await cache.set("http:https://sec.gov/...", response_bytes, ttl=3600)

# Get from cache
cached = await cache.get("http:https://sec.gov/...")
```

**Used by**: `SECFeed.download_document()` for HTTP response caching.

### 5. Progress Reporter (collection status)

**Purpose**: Report progress during large collection operations.

```python
from py_sec_edgar.reporters import RichProgressReporter

async with SECFeed(tickers=["AAPL"], forms=["10-K"]) as feed:
    await feed.collect(progress=RichProgressReporter())
```

**Used by**: `SECFeed.collect()` with optional progress parameter.

### 6. Collection Strategy Protocol

**Purpose**: Define how collections are planned and executed.

```python
from feedspine.protocols.strategy import CollectionStrategy, BaseCollectionStrategy

class SmartSyncStrategy(BaseCollectionStrategy):
    """Smart sync uses quarterly indexes for historical data."""

    def plan(self, start_date, end_date) -> SyncPlan:
        # Determine optimal mix of quarterly, daily, and RSS fetches
        ...
```

**Used by**: `SmartSyncStrategy` for intelligent collection planning.

## SECFeed API Reference

The `SECFeed` class wraps all FeedSpine components into a unified API:

```python
from py_sec_edgar.feed import SECFeed, SECFeedConfig

# Configuration
config = SECFeedConfig(
    tickers=["AAPL", "MSFT"],
    forms=["10-K", "10-Q"],
    days=365,
    storage_path=Path("sec_filings.db"),
    blob_path=Path("sec_documents"),
    enable_search=True,
    enable_cache=True,
    cache_ttl_seconds=3600,
)

async with SECFeed(config=config) as feed:
    # Collect filings
    count = await feed.collect(progress=RichProgressReporter())

    # Iterate filings with typed access
    async for filing in feed.filings(form_type="10-K"):
        print(filing.content.company_name)
        print(filing.content.accession_number)

    # Get specific filing
    filing = await feed.get_filing("0000320193-24-000081")

    # Download document to blob storage
    content = await feed.download_document(
        "https://www.sec.gov/Archives/edgar/data/320193/...",
        accession_number="0000320193-24-000081"
    )

    # Search filings
    results = await feed.search("revenue growth", limit=10)

    # Cache operations
    await feed.set_cached("my_key", data)
    cached = await feed.get_cached("my_key")
    await feed.clear_cache()
```

## Component Initialization

When `SECFeed.initialize()` is called:

1. **DuckDB Storage**: Created at `config.storage_path`
2. **Blob Storage**: Created at `config.blob_path` (if set)
3. **Search Backend**: Initialized if `config.enable_search=True`
4. **Cache Backend**: Initialized if `config.enable_cache=True`
5. **Smart Sync Strategy**: Plans optimal collection approach
6. **Feed Adapters**: Created based on sync plan

## Data Flow

```
SEC EDGAR APIs
     │
     ▼
┌─────────────────────┐
│   Feed Adapters     │  (Quarterly, Daily, RSS)
│   - SecQuarterly    │
│   - SecDaily        │
│   - SecRss          │
└─────────────────────┘
     │
     ▼
┌─────────────────────┐
│   Record Creation   │  Convert to TypedRecord[SECFilingContent]
└─────────────────────┘
     │
     ├──────────────────► DuckDB Storage (metadata)
     │
     ├──────────────────► Memory Search (indexing)
     │
     ▼
┌─────────────────────┐
│  Document Download  │  On-demand via download_document()
│  - HTTP Request     │
│  - HTTP Cache       │
│  - Blob Storage     │
└─────────────────────┘
```

## Extension Points

### Adding New Storage Backends

FeedSpine protocols allow custom implementations:

```python
from feedspine.protocols.storage import StorageBackend

class PostgresStorage(StorageBackend):
    async def upsert(self, record: Record) -> UpsertResult: ...
    async def query(self, filters) -> AsyncIterator[Record]: ...
```

### Adding Custom Enrichers

Add document parsing or content extraction:

```python
from feedspine.protocols.enricher import Enricher

class XBRLEnricher(Enricher):
    async def enrich(self, record: Record) -> EnrichmentResult:
        # Parse XBRL and add structured financial data
        ...
```

### Adding Custom Notifiers

Send notifications on collection events:

```python
from feedspine.protocols.notification import Notifier

class SlackNotifier(Notifier):
    async def send(self, notification: Notification) -> bool:
        # Send to Slack webhook
        ...
```

## Shared Components (moved to FeedSpine)

The following components were originally in py-sec-edgar but have been **moved to FeedSpine** as they are domain-agnostic. py-sec-edgar re-exports them for backward compatibility:

### Progress Reporters
```python
# Use from either location
from feedspine.reporter import RichProgressReporter, SimpleProgressReporter
# Or backward-compatible:
from py_sec_edgar.reporters import RichProgressReporter, SimpleProgressReporter
```

### Metrics Collection
```python
# FeedSpine location (canonical)
from feedspine.metrics import CollectionMetrics, MetricsSummary

# py-sec-edgar re-export (SyncMetrics is alias for CollectionMetrics)
from py_sec_edgar.utils.metrics import SyncMetrics, CollectionMetrics
```

### HTTP Rate Limiting
```python
# FeedSpine provides generic rate limiter
from feedspine.http import RateLimiter, HttpClient

# py-sec-edgar's SecClient uses FeedSpine's RateLimiter internally
from py_sec_edgar.client.http import SecClient  # Uses feedspine.http.RateLimiter
```

## Best Practices

1. **Always use async context manager**:
   ```python
   async with SECFeed(...) as feed:
       await feed.collect()
   ```

2. **Enable search for large collections**:
   ```python
   config = SECFeedConfig(enable_search=True, ...)
   ```

3. **Use progress reporter for visibility**:
   ```python
   await feed.collect(progress=RichProgressReporter())
   ```

4. **Leverage blob storage for documents**:
   ```python
   content = await feed.download_document(url)
   # Documents are cached in blob storage for future access
   ```

5. **Configure cache TTL appropriately**:
   ```python
   config = SECFeedConfig(
       enable_cache=True,
       cache_ttl_seconds=3600,  # 1 hour for active collection
   )
   ```

## Summary

py-sec-edgar v4 fully leverages FeedSpine's capabilities:

| FeedSpine Feature | py-sec-edgar Integration | Status |
|-------------------|-------------------------|--------|
| DuckDBStorage | Filing metadata storage | ✅ Active |
| FilesystemBlob | Document storage | ✅ Active |
| MemorySearch | Filing search | ✅ Active |
| MemoryCache | HTTP response caching | ✅ Active |
| ProgressReporter | Collection progress | ✅ Active |
| CollectionStrategy | Smart sync planning | ✅ Active |
| RateLimiter | HTTP rate limiting | ✅ Active |
| CollectionMetrics | Sync metrics/observability | ✅ Active |
| HttpClient | HTTP downloads | ✅ Active |
