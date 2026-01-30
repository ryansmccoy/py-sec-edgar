# py-sec-edgar v4 Architecture: Unified Feeds + Direct APIs

## Executive Summary

Your architectural intuition is correct: **the unified feed approach is the right foundation for real-time processing**. But it's not either/or—the best architecture combines both approaches:

| Approach | Best For | When to Use |
|----------|----------|-------------|
| **Unified Feeds** | Real-time monitoring, completeness | "Process everything as it arrives" |
| **Direct APIs** | Targeted lookups, backfill, discovery | "I need this specific company/exhibit/form" |

## Architecture Decision: Push vs Pull

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         py-sec-edgar v4                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      DATA ACQUISITION LAYER                        │ │
│  │                                                                    │ │
│  │  ┌─────────────────────┐      ┌─────────────────────────────────┐ │ │
│  │  │  PUSH (Feeds)       │      │  PULL (APIs)                    │ │ │
│  │  │  ──────────────     │      │  ──────────────                 │ │ │
│  │  │  • RSS (real-time)  │      │  • SecSubmissionsAPI            │ │ │
│  │  │  • Daily Index      │      │  • SecFullTextSearch            │ │ │
│  │  │  • Quarterly Index  │      │  • SecCompanyFactsAPI           │ │ │
│  │  │                     │      │                                 │ │ │
│  │  │  When: Always on    │      │  When: On-demand, backfill      │ │ │
│  │  │  Pattern: FeedSpine │      │  Pattern: Query/Response        │ │ │
│  │  └──────────┬──────────┘      └────────────────┬────────────────┘ │ │
│  │             │                                   │                  │ │
│  │             └───────────────┬───────────────────┘                  │ │
│  │                             ▼                                      │ │
│  └─────────────────────────────┼──────────────────────────────────────┘ │
│                                │                                         │
│  ┌─────────────────────────────┼──────────────────────────────────────┐ │
│  │                     BRONZE LAYER (Raw)                             │ │
│  │                                                                    │ │
│  │  • All sightings stored with source attribution                   │ │
│  │  • Deduplication via content hash                                 │ │
│  │  • Timestamps: seen_at, source_updated_at                         │ │
│  └────────────────────────────┼───────────────────────────────────────┘ │
│                               │                                          │
│  ┌────────────────────────────┼───────────────────────────────────────┐ │
│  │                    RESOLUTION LAYER                                │ │
│  │                                                                    │ │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐ │ │
│  │  │ EntitySpine     │    │ FilingSpine     │    │ ExhibitSpine   │ │ │
│  │  │ (Companies)     │    │ (Filings)       │    │ (Exhibits)     │ │ │
│  │  └─────────────────┘    └─────────────────┘    └────────────────┘ │ │
│  │                                                                    │ │
│  │  Silver Layer: Resolved canonical entities with relationships      │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Why Unified Feeds Are Right for Real-Time

### Advantages of Your Current Approach

1. **Complete Coverage**: You see ALL filings, not just what you're looking for
   - New companies you didn't know about
   - Form types you hadn't considered
   - Emerging patterns across market

2. **No Polling Overhead**: Feed-based approach is efficient
   - RSS updates every 10 minutes
   - Daily index catches everything
   - No need to enumerate all 500K+ CIKs

3. **Event-Driven Processing**: Natural fit for real-time
   ```
   RSS Feed → New Filing Detected → Process → Store → Notify
   ```

4. **Consistency**: Single source of truth for "what filings exist"
   - Dedup across all sources
   - Track first-seen timestamps
   - Build complete history

### When Unified Feeds Aren't Enough

1. **Historical Backfill**: "Give me all 10-Ks from 2010-2020"
   - Feeds are forward-looking
   - Use Direct APIs for backfill

2. **Targeted Lookup**: "What did Apple file last year?"
   - Don't want to process ALL filings
   - Use Submissions API directly

3. **Exhibit Discovery**: "Find all Exhibit 21s filed this month"
   - Exhibits aren't in the RSS feed
   - Use EFTS Search API

4. **XBRL Data**: "Get Apple's revenue history"
   - Company Facts API has structured data
   - More efficient than parsing filings

## Recommended Architecture Improvements

### 1. Add Query Service Layer

Instead of making APIs fit the FeedAdapter protocol, create a separate Query layer:

```python
# Current: FeedSpine handles feeds
feed_spine = FeedSpine()
feed_spine.register_feed(SecRssFeedAdapter())

# NEW: QueryService handles lookups
query_service = QueryService()
query_service.register(SecSubmissionsAPI())
query_service.register(SecFullTextSearch())

# Usage
results = await query_service.submissions.get("320193")  # Direct lookup
exhibits = await query_service.search.find_exhibits("EX-21", year=2024)
```

### 2. Add Backfill Capability

Allow unified feed to backfill from APIs:

```python
class UnifiedFeedMonitor:
    async def backfill(
        self,
        cik: str,
        date_range: tuple[date, date],
        form_types: list[str] | None = None,
    ) -> BackfillResult:
        """Backfill historical filings using submissions API."""
        # Use SecSubmissionsAPI to get historical data
        # Inject into Bronze layer as if from feed
        # Mark source as "backfill:submissions-api"
```

### 3. Lazy Exhibit Resolution

Only fetch exhibits when needed:

```python
class Filing:
    """Filing with lazy exhibit loading."""

    @property
    async def exhibit_21(self) -> Exhibit21 | None:
        """Lazy load Exhibit 21."""
        if self._exhibit_21 is None:
            self._exhibit_21 = await self._load_exhibit("EX-21")
        return self._exhibit_21
```

### 4. Hybrid Processing Pipeline

```python
# Real-time: Process all filings as they come in
async with UnifiedFeedMonitor() as monitor:
    async for filing in monitor.watch():
        await bronze_layer.store(filing)  # Store sighting

        # Enrich with API data (async, non-blocking)
        asyncio.create_task(
            enrich_with_exhibits(filing)
        )

# Batch: Targeted processing
async def enrich_company(cik: str):
    """Enrich company data using APIs."""
    async with SecSubmissionsAPI() as api:
        subs = await api.get_submissions(cik)
        # Store/update company info

    async with SecCompanyFactsAPI() as facts_api:
        facts = await facts_api.get_company_facts(cik)
        # Store XBRL metrics
```

## Specific Recommendations

### 1. Don't Force APIs into FeedAdapter

The FeedAdapter protocol is for streaming data sources. APIs are request/response. Keep them separate:

| Protocol | Usage |
|----------|-------|
| `FeedAdapter` | RSS, daily index, file watchers |
| `QueryAPI` | Submissions, EFTS, Company Facts |

### 2. Add Cache Layer for API Responses

SEC APIs are rate-limited (10/sec). Cache aggressively:

```python
class CachedSubmissionsAPI(SecSubmissionsAPI):
    def __init__(self, cache_ttl: int = 3600):  # 1 hour
        self._cache = TTLCache(ttl=cache_ttl)

    async def get_submissions(self, cik: str) -> CompanySubmissions:
        if cik in self._cache:
            return self._cache[cik]

        result = await super().get_submissions(cik)
        self._cache[cik] = result
        return result
```

### 3. Add Source Tracking

Know where data came from:

```python
@dataclass
class FilingSighting:
    accession_number: str
    source: str  # "feed:rss", "feed:daily-index", "api:submissions", "api:efts"
    source_updated_at: datetime
    seen_at: datetime
```

### 4. Implement Filing Completeness Check

Use APIs to verify feed coverage:

```python
async def verify_coverage(cik: str, date_range: tuple) -> CoverageReport:
    """Compare feed coverage against submissions API."""
    # Get filings from Bronze layer (what we've seen)
    seen_filings = await bronze.query(cik=cik, date_range=date_range)

    # Get filings from API (ground truth)
    api_filings = await submissions_api.get_submissions(cik)
    api_filings_filtered = [
        f for f in api_filings
        if date_range[0] <= f.filing_date <= date_range[1]
    ]

    # Find gaps
    seen_accessions = {f.accession_number for f in seen_filings}
    missing = [
        f for f in api_filings_filtered
        if f.accession_number not in seen_accessions
    ]

    return CoverageReport(
        total_expected=len(api_filings_filtered),
        total_seen=len(seen_filings),
        missing=missing,
    )
```

## Usage Patterns

### Pattern 1: Real-Time Monitoring (Unified Feed)

```python
# Your current pattern - CORRECT
async with UnifiedFeedMonitor(form_types=["10-K"]) as monitor:
    async for filing in monitor.watch():
        # Process immediately
        await process_10k(filing)
```

### Pattern 2: Historical Research (API)

```python
# NEW pattern for research
async def research_company_history(ticker: str):
    cik = await entity_spine.resolve_ticker(ticker)

    async with SecSubmissionsAPI() as api:
        subs = await api.get_submissions(cik)

        for ten_k in subs.get_recent_10k(count=5):
            exhibit_21 = await api.find_exhibit(
                cik, ten_k["accession_number"], "EX-21"
            )
            if exhibit_21:
                content = await api.get_filing_document(
                    cik, ten_k["accession_number"], exhibit_21
                )
                yield parse_exhibit_21(content)
```

### Pattern 3: Discovery (Search API)

```python
# NEW pattern for discovery
async def find_recent_subsidiary_changes():
    async with SecFullTextSearch() as search:
        results = await search.search(
            query='"subsidiary" AND "acquisition"',
            forms=["10-K", "8-K"],
            date_range=("2024-01-01", "2024-12-31"),
        )
        return results.hits
```

### Pattern 4: Backfill (Hybrid)

```python
# Fill gaps in unified feed
async def backfill_missing():
    # Check what we're missing
    coverage = await verify_coverage("320193", (date(2020, 1, 1), date(2024, 1, 1)))

    # Backfill from API
    for filing in coverage.missing:
        async with SecSubmissionsAPI() as api:
            # Get filing details
            index = await api.get_filing_index("320193", filing.accession_number)

            # Store to Bronze layer
            await bronze.store(
                filing=filing,
                source="backfill:submissions-api",
            )
```

## Summary

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **SecRssFeedAdapter** | Real-time filings | FeedSpine (existing) |
| **SecDailyIndexAdapter** | Daily catchup | FeedSpine (existing) |
| **SecSubmissionsAPI** | Company lookups | NEW - Query Service |
| **SecFullTextSearch** | Discovery, cross-company | NEW - Query Service |
| **SecCompanyFactsAPI** | XBRL metrics | NEW - Query Service |

Your unified feed is the **backbone** for completeness and real-time.
The APIs are **surgical tools** for specific queries and backfill.

Both working together = comprehensive SEC data platform.

## Next Steps

1. ✅ Created `sec_api.py` with direct API adapters
2. 📋 Create QueryService wrapper for clean API access
3. 📋 Add caching layer for API responses
4. 📋 Implement backfill capability in UnifiedFeedMonitor
5. 📋 Add coverage verification tool
