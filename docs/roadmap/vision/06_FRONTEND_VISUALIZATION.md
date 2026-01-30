# Frontend Visualization Architecture

**Purpose**: Define the React-based frontend for exploring SEC filings and knowledge graph.

---

## Vision

A **mind-blowing** interactive visualization where users can:
1. **Explore filings** with a real-time feed of latest SEC filings
2. **Search everything** - by ticker, company name, supplier name, customer name, keywords
3. **Dive deep** into any filing's enriched data across multiple views/tabs
4. **Click-through provenance** - every extracted fact links back to original sentence
5. **Navigate the knowledge graph** of company relationships
6. **Filter by sector** to see industry trends and competitors
7. **Ask questions** and get AI-powered answers with source citations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND STACK                                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   React + Vite   │────▶│   FastAPI        │────▶│   py-sec-edgar   │
│                  │     │   Backend        │     │   + DuckDB       │
│ • Dashboard      │◀────│                  │◀────│                  │
│ • Graph Viz      │     │ • REST API       │     │ • Filings        │
│ • Filing View    │     │ • WebSocket      │     │ • Graph          │
│ • Search         │     │ • SSE Stream     │     │ • LLM            │
└──────────────────┘     └──────────────────┘     └──────────────────┘
        │
        ▼
┌──────────────────┐
│   Visualization  │
│                  │
│ • D3.js graphs   │
│ • Cytoscape.js   │
│ • React Flow     │
│ • Recharts       │
└──────────────────┘
```

---

## 1. API Backend (FastAPI)

### Routes

```python
from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="py-sec-edgar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# INVENTORY & FILINGS
# =============================================================================

@app.get("/api/inventory")
async def get_inventory() -> InventoryResponse:
    """Get summary of downloaded filings."""
    return {
        "total_filings": 450,
        "companies": 25,
        "by_form": {"10-K": 75, "10-Q": 225, "8-K": 150},
        "date_range": {"start": "2020-01-01", "end": "2024-12-31"},
        "enriched": 400,
        "pending": 50,
    }


# =============================================================================
# REAL-TIME FILING FEED
# =============================================================================

@app.get("/api/feed/latest")
async def get_latest_filings(
    limit: int = Query(default=50, le=200),
    form_types: List[str] | None = None,
    since: datetime | None = None,
) -> LatestFilingsResponse:
    """
    Get real-time feed of latest filings.

    Like a Twitter feed but for SEC filings.
    """
    return {
        "filings": [...],
        "last_updated": datetime.now().isoformat(),
    }


@app.websocket("/api/feed/stream")
async def filing_feed_stream(websocket: WebSocket):
    """
    WebSocket stream for real-time filing updates.

    Client receives new filings as they're collected.
    """
    await websocket.accept()
    async for filing in get_new_filings_stream():
        await websocket.send_json(filing)


@app.get("/api/filings")
async def list_filings(
    ticker: str | None = None,
    form_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    enriched_only: bool = False,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
) -> FilingsListResponse:
    """List filings with filters."""
    # Query from DuckDB
    ...


@app.get("/api/filings/{accession_number}")
async def get_filing(accession_number: str) -> EnrichedFilingResponse:
    """Get single enriched filing with all data."""
    filing = store.get(accession_number)
    return filing.to_dict()


@app.get("/api/filings/{accession_number}/entities")
async def get_filing_entities(accession_number: str) -> EntitiesResponse:
    """Get entities extracted from filing."""
    ...


@app.get("/api/filings/{accession_number}/risks")
async def get_filing_risks(accession_number: str) -> RisksResponse:
    """Get risk factors from filing."""
    ...


# =============================================================================
# SEARCH
# =============================================================================

@app.get("/api/search")
async def search(
    q: str,
    form_types: List[str] | None = None,
    tickers: List[str] | None = None,
    entity_type: str | None = None,
    risk_category: str | None = None,
) -> SearchResponse:
    """Full-text and structured search."""
    ...


@app.get("/api/search/entities")
async def search_entities(
    name: str,
    entity_type: str | None = None,
) -> EntitySearchResponse:
    """Search for entity mentions across filings."""
    ...


@app.get("/api/search/advanced")
async def advanced_search(
    # Basic filters
    q: str | None = None,
    ticker: str | None = None,
    cik: str | None = None,
    company_name: str | None = None,

    # Form filters
    form_types: List[str] | None = None,
    start_date: date | None = None,
    end_date: date | None = None,

    # Entity/relationship filters (THE ADVANCED STUFF)
    supplier_name: str | None = None,      # Find filings mentioning this supplier
    customer_name: str | None = None,      # Find filings mentioning this customer
    competitor_name: str | None = None,    # Find filings mentioning this competitor
    any_entity: str | None = None,         # Find any mention of this entity

    # Sector/industry filters
    sic_code: str | None = None,
    sector: str | None = None,

    # Risk filters
    risk_category: str | None = None,
    min_risk_severity: str | None = None,

    # Enrichment status
    enriched_only: bool = False,
    has_guidance: bool | None = None,

    # Pagination
    limit: int = Query(default=50, le=500),
    offset: int = 0,
) -> AdvancedSearchResponse:
    """
    Advanced search with relationship and entity filters.

    Examples:
    - "Find all filings that mention TSMC as a supplier"
    - "Find 10-K filings in semiconductor sector with cyber risks"
    - "Find filings where Microsoft is mentioned as competitor"
    """
    ...


@app.get("/api/search/by-supplier/{supplier_name}")
async def search_by_supplier(
    supplier_name: str,
    limit: int = 50,
) -> FilingsListResponse:
    """
    Find all filings that mention a specific supplier.

    Returns filings with context of how the supplier was mentioned.
    """
    ...


@app.get("/api/search/by-customer/{customer_name}")
async def search_by_customer(
    customer_name: str,
    limit: int = 50,
) -> FilingsListResponse:
    """Find all filings that mention a specific customer."""
    ...


# =============================================================================
# EVIDENCE & PROVENANCE (Click-through to source)
# =============================================================================

@app.get("/api/evidence/{mention_id}")
async def get_mention_evidence(mention_id: str) -> EvidenceResponse:
    """
    Get full evidence trail for an extracted fact.

    Returns:
    - The exact sentence where entity was found
    - Surrounding context (~500 chars)
    - Link to SEC document
    - All sightings across filings
    - When we first/last saw this
    """
    return {
        "mention": {...},
        "source": {
            "filing": "Apple Inc. 10-K (2024-11-01)",
            "section": "Risk Factors",
            "sentence": "We rely on TSMC for substantially all of our...",
            "sentence_highlighted": "We rely on <mark>TSMC</mark> for substantially all of our...",
            "surrounding_context": "...",
            "char_start": 45023,
            "char_end": 45027,
            "sec_url": "https://sec.gov/...",
        },
        "temporal": {
            "first_seen": "2020-11-06T...",
            "first_seen_filing": "0000320193-20-000096",
            "last_seen": "2024-11-01T...",
            "occurrence_count": 5,
        },
        "all_sightings": [...]
    }


@app.get("/api/filings/{accession}/section/{section_id}/context")
async def get_section_context(
    accession: str,
    section_id: str,
    char_start: int,
    char_end: int,
    context_chars: int = Query(default=500, le=2000),
) -> ContextResponse:
    """
    Get text context around a specific location in a filing.

    Used when user clicks on an extracted fact to see original context.
    """
    ...


# =============================================================================
# KNOWLEDGE GRAPH
# =============================================================================

@app.get("/api/graph/company/{identifier}")
async def get_company_graph(
    identifier: str,  # ticker, CIK, or name
    depth: int = Query(default=2, le=4),
    relationship_types: List[str] | None = None,
) -> GraphResponse:
    """Get graph centered on a company."""
    data = export_for_visualization(graph_query, identifier, depth)
    return data


@app.get("/api/graph/industry/{sic_code}")
async def get_industry_graph(sic_code: str) -> GraphResponse:
    """Get industry relationship graph."""
    ...


@app.get("/api/graph/path")
async def find_path(
    source: str,
    target: str,
    max_depth: int = 4,
) -> PathResponse:
    """Find paths between companies."""
    ...


@app.get("/api/graph/common-suppliers")
async def common_suppliers(companies: List[str]) -> List[CompanyNode]:
    """Find suppliers shared by companies."""
    ...


# =============================================================================
# LLM / AI
# =============================================================================

@app.post("/api/ask")
async def ask_question(request: AskRequest) -> AskResponse:
    """Ask a question about a filing or company."""
    answer = await qa.ask(filing, request.question)
    return {"answer": answer}


@app.websocket("/api/ask/stream")
async def ask_stream(websocket: WebSocket):
    """Stream AI response."""
    await websocket.accept()
    data = await websocket.receive_json()

    async for chunk in qa.ask_stream(data["filing_id"], data["question"]):
        await websocket.send_text(chunk)


# =============================================================================
# SYNC / DOWNLOAD
# =============================================================================

@app.post("/api/sync")
async def start_sync(request: SyncRequest) -> SyncJobResponse:
    """Start a sync/download job."""
    job_id = await start_sync_job(request)
    return {"job_id": job_id, "status": "started"}


@app.get("/api/sync/{job_id}")
async def get_sync_status(job_id: str) -> SyncStatusResponse:
    """Get sync job status."""
    ...


@app.get("/api/sync/{job_id}/stream")
async def sync_stream(job_id: str):
    """Server-sent events for sync progress."""
    async def event_stream():
        async for event in get_sync_events(job_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## 2. React Components

### File Structure

```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── InventoryCard.tsx
│   │   │   ├── RecentFilings.tsx
│   │   │   └── SyncStatus.tsx
│   │   ├── Feed/
│   │   │   ├── FilingFeed.tsx          # Real-time filing feed
│   │   │   ├── FilingFeedItem.tsx      # Single filing in feed
│   │   │   ├── FeedFilters.tsx         # Filter by form, sector
│   │   │   └── LiveIndicator.tsx       # Shows live updates
│   │   ├── Filings/
│   │   │   ├── FilingsList.tsx
│   │   │   ├── FilingCard.tsx
│   │   │   ├── FilingDetail.tsx
│   │   │   ├── SectionViewer.tsx
│   │   │   ├── EntityList.tsx
│   │   │   ├── RiskFactors.tsx
│   │   │   └── MetadataTabs.tsx        # Multiple views of filing data
│   │   ├── Evidence/
│   │   │   ├── EvidencePanel.tsx       # Shows source context
│   │   │   ├── SentenceHighlight.tsx   # Highlights entity in sentence
│   │   │   ├── SourceLink.tsx          # Link to SEC document
│   │   │   └── SightingsTimeline.tsx   # All times we saw this
│   │   ├── Graph/
│   │   │   ├── KnowledgeGraph.tsx
│   │   │   ├── GraphControls.tsx
│   │   │   ├── NodeDetail.tsx
│   │   │   ├── PathFinder.tsx
│   │   │   └── IndustryView.tsx
│   │   ├── Search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── AdvancedSearch.tsx      # Filters for supplier/customer search
│   │   │   ├── SearchResults.tsx
│   │   │   ├── EntitySearchResults.tsx # Results with context
│   │   │   └── Filters.tsx
│   │   ├── AI/
│   │   │   ├── AskQuestion.tsx
│   │   │   ├── AnswerDisplay.tsx
│   │   │   └── ChatHistory.tsx
│   │   └── common/
│   │       ├── Layout.tsx
│   │       ├── Sidebar.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── ErrorBoundary.tsx
│   ├── hooks/
│   │   ├── useFilings.ts
│   │   ├── useFeed.ts                  # Real-time feed hook
│   │   ├── useGraph.ts
│   │   ├── useSearch.ts
│   │   ├── useEvidence.ts              # Evidence/provenance hook
│   │   └── useSync.ts
│   ├── api/
│   │   └── client.ts
│   └── types/
│       └── index.ts
├── package.json
└── vite.config.ts
```

### Dashboard Component

```tsx
// src/components/Dashboard/Dashboard.tsx
import { useInventory, useRecentFilings, useSyncStatus } from '../../hooks';
import { InventoryCard, RecentFilings, SyncStatus } from '.';
import { Card, Grid, Title } from '@tremor/react';

export function Dashboard() {
  const { data: inventory, isLoading } = useInventory();
  const { data: recent } = useRecentFilings(10);
  const { syncJobs } = useSyncStatus();

  return (
    <div className="p-6">
      <Title>SEC Filing Dashboard</Title>

      <Grid numItems={1} numItemsSm={2} numItemsLg={4} className="gap-4 mt-6">
        <InventoryCard
          title="Total Filings"
          value={inventory?.total_filings || 0}
          icon="📄"
        />
        <InventoryCard
          title="Companies"
          value={inventory?.companies || 0}
          icon="🏢"
        />
        <InventoryCard
          title="Enriched"
          value={inventory?.enriched || 0}
          percentage={(inventory?.enriched / inventory?.total_filings * 100) || 0}
          icon="✨"
        />
        <InventoryCard
          title="Pending"
          value={inventory?.pending || 0}
          icon="⏳"
        />
      </Grid>

      <Grid numItems={1} numItemsLg={2} className="gap-6 mt-6">
        <Card>
          <Title>Recent Filings</Title>
          <RecentFilings filings={recent} />
        </Card>

        <Card>
          <Title>Form Distribution</Title>
          <FormTypeChart data={inventory?.by_form} />
        </Card>
      </Grid>

      {syncJobs.length > 0 && (
        <Card className="mt-6">
          <Title>Active Sync Jobs</Title>
          {syncJobs.map(job => (
            <SyncStatus key={job.id} job={job} />
          ))}
        </Card>
      )}
    </div>
  );
}
```

### Real-Time Filing Feed Component

```tsx
// src/components/Feed/FilingFeed.tsx
import { useEffect, useState } from 'react';
import { useFeed } from '../../hooks/useFeed';

interface FilingFeedProps {
  formTypes?: string[];
  sectorFilter?: string;
}

export function FilingFeed({ formTypes, sectorFilter }: FilingFeedProps) {
  const { filings, isLive, reconnect } = useFeed({ formTypes, sectorFilter });

  return (
    <div className="filing-feed">
      {/* Live indicator */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">Latest Filings</h2>
        <LiveIndicator isLive={isLive} onReconnect={reconnect} />
      </div>

      {/* Filters */}
      <FeedFilters
        formTypes={formTypes}
        sectorFilter={sectorFilter}
        onChange={...}
      />

      {/* Filing feed items */}
      <div className="space-y-3">
        {filings.map((filing, index) => (
          <FilingFeedItem
            key={filing.accession_number}
            filing={filing}
            isNew={index < 3}  // Highlight newest
          />
        ))}
      </div>
    </div>
  );
}

function FilingFeedItem({ filing, isNew }: { filing: Filing; isNew: boolean }) {
  return (
    <div className={`
      p-4 rounded-lg border
      ${isNew ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}
      hover:shadow-md transition-shadow cursor-pointer
    `}>
      <div className="flex justify-between items-start">
        <div>
          <span className="font-semibold">{filing.company_name}</span>
          <span className="text-gray-500 ml-2">({filing.ticker})</span>
        </div>
        <Badge variant={getFormVariant(filing.form_type)}>
          {filing.form_type}
        </Badge>
      </div>

      <div className="text-sm text-gray-600 mt-1">
        Filed {formatRelativeTime(filing.filed_date)}
        {filing.is_enriched && (
          <span className="ml-2 text-green-600">✓ Enriched</span>
        )}
      </div>

      {/* Quick preview of extracted entities */}
      {filing.preview && (
        <div className="mt-2 text-sm">
          {filing.preview.supplier_count > 0 && (
            <span className="mr-3">
              🏭 {filing.preview.supplier_count} suppliers
            </span>
          )}
          {filing.preview.customer_count > 0 && (
            <span className="mr-3">
              🛒 {filing.preview.customer_count} customers
            </span>
          )}
          {filing.preview.risk_count > 0 && (
            <span>
              ⚠️ {filing.preview.risk_count} risks
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// Custom hook for real-time feed
function useFeed(filters: FeedFilters) {
  const [filings, setFilings] = useState<Filing[]>([]);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    // Initial load
    fetchLatestFilings(filters).then(setFilings);

    // WebSocket for real-time updates
    const ws = new WebSocket(`${WS_URL}/api/feed/stream`);

    ws.onopen = () => setIsLive(true);
    ws.onclose = () => setIsLive(false);

    ws.onmessage = (event) => {
      const newFiling = JSON.parse(event.data);
      setFilings(prev => [newFiling, ...prev.slice(0, 99)]);
    };

    return () => ws.close();
  }, [filters]);

  return { filings, isLive, reconnect: () => {...} };
}
```

### Evidence Panel Component (Click-through to source)

```tsx
// src/components/Evidence/EvidencePanel.tsx
import { useEvidence } from '../../hooks/useEvidence';

interface EvidencePanelProps {
  mentionId: string;
  onClose: () => void;
}

export function EvidencePanel({ mentionId, onClose }: EvidencePanelProps) {
  const { data: evidence, isLoading } = useEvidence(mentionId);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="evidence-panel bg-white rounded-lg shadow-lg p-6 max-w-2xl">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-bold">{evidence.mention.entity_name}</h3>
          <Badge>{evidence.mention.relationship_type}</Badge>
          <ConfidenceMeter value={evidence.mention.confidence} />
        </div>
        <button onClick={onClose} className="text-gray-500">×</button>
      </div>

      {/* Source context - THE KEY FEATURE */}
      <div className="source-context bg-gray-50 rounded p-4 mb-4">
        <h4 className="font-semibold text-sm text-gray-600 mb-2">
          Source: {evidence.source.filing}
        </h4>
        <p className="text-sm text-gray-500 mb-2">
          Section: {evidence.source.section}
        </p>

        {/* The highlighted sentence */}
        <blockquote className="border-l-4 border-blue-500 pl-4 py-2 bg-white">
          <SentenceWithHighlight
            sentence={evidence.source.sentence}
            highlight={evidence.mention.entity_name}
          />
        </blockquote>

        {/* Surrounding context (expandable) */}
        <details className="mt-3">
          <summary className="cursor-pointer text-blue-600 text-sm">
            Show more context
          </summary>
          <p className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
            {evidence.source.surrounding_context}
          </p>
        </details>

        {/* Link to SEC */}
        <a
          href={evidence.source.sec_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center mt-3 text-blue-600 hover:underline"
        >
          View in SEC Filing →
        </a>
      </div>

      {/* Temporal info - point in time */}
      <div className="temporal-info mb-4">
        <h4 className="font-semibold text-sm mb-2">History</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">First seen:</span>
            <p>{formatDate(evidence.temporal.first_seen)}</p>
            <p className="text-xs text-gray-400">
              in {evidence.temporal.first_seen_filing}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Last seen:</span>
            <p>{formatDate(evidence.temporal.last_seen)}</p>
            <p className="text-xs text-gray-400">
              {evidence.temporal.occurrence_count} occurrences
            </p>
          </div>
        </div>
      </div>

      {/* All sightings timeline */}
      <div className="sightings">
        <h4 className="font-semibold text-sm mb-2">
          All Sightings ({evidence.all_sightings.length})
        </h4>
        <SightingsTimeline sightings={evidence.all_sightings} />
      </div>
    </div>
  );
}

// Highlight entity in sentence
function SentenceWithHighlight({ sentence, highlight }: { sentence: string; highlight: string }) {
  const regex = new RegExp(`(${escapeRegex(highlight)})`, 'gi');
  const parts = sentence.split(regex);

  return (
    <span>
      {parts.map((part, i) =>
        part.toLowerCase() === highlight.toLowerCase() ? (
          <mark key={i} className="bg-yellow-200 px-1 rounded">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}
```

### Advanced Search Component

```tsx
// src/components/Search/AdvancedSearch.tsx
import { useState } from 'react';
import { useAdvancedSearch } from '../../hooks/useSearch';

export function AdvancedSearch() {
  const [filters, setFilters] = useState<SearchFilters>({});
  const { results, isLoading, search } = useAdvancedSearch();

  return (
    <div className="advanced-search">
      <h2 className="text-xl font-bold mb-4">Advanced Search</h2>

      {/* Basic search */}
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search filings..."
          className="w-full p-3 border rounded-lg"
          value={filters.q || ''}
          onChange={(e) => setFilters(f => ({ ...f, q: e.target.value }))}
        />
      </div>

      {/* Filter panels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {/* Company filters */}
        <div className="filter-group">
          <h3 className="font-semibold mb-2">Company</h3>
          <input
            placeholder="Ticker (e.g., AAPL)"
            value={filters.ticker || ''}
            onChange={(e) => setFilters(f => ({ ...f, ticker: e.target.value }))}
          />
          <input
            placeholder="Company name"
            value={filters.company_name || ''}
            onChange={(e) => setFilters(f => ({ ...f, company_name: e.target.value }))}
          />
          <SectorDropdown
            value={filters.sector}
            onChange={(v) => setFilters(f => ({ ...f, sector: v }))}
          />
        </div>

        {/* Relationship filters - THE COOL PART */}
        <div className="filter-group">
          <h3 className="font-semibold mb-2">Relationships</h3>
          <input
            placeholder="🏭 Supplier name (e.g., TSMC)"
            value={filters.supplier_name || ''}
            onChange={(e) => setFilters(f => ({ ...f, supplier_name: e.target.value }))}
          />
          <input
            placeholder="🛒 Customer name"
            value={filters.customer_name || ''}
            onChange={(e) => setFilters(f => ({ ...f, customer_name: e.target.value }))}
          />
          <input
            placeholder="⚔️ Competitor name"
            value={filters.competitor_name || ''}
            onChange={(e) => setFilters(f => ({ ...f, competitor_name: e.target.value }))}
          />
        </div>

        {/* Filing filters */}
        <div className="filter-group">
          <h3 className="font-semibold mb-2">Filing</h3>
          <FormTypeMultiSelect
            value={filters.form_types}
            onChange={(v) => setFilters(f => ({ ...f, form_types: v }))}
          />
          <DateRangePicker
            value={{ start: filters.start_date, end: filters.end_date }}
            onChange={(v) => setFilters(f => ({ ...f, start_date: v.start, end_date: v.end }))}
          />
        </div>
      </div>

      <button
        onClick={() => search(filters)}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Search
      </button>

      {/* Results with context */}
      {results && (
        <SearchResultsWithContext
          results={results}
          highlightEntities={[
            filters.supplier_name,
            filters.customer_name,
            filters.competitor_name,
          ].filter(Boolean)}
        />
      )}
    </div>
  );
}

// Search results that show WHY each result matched
function SearchResultsWithContext({ results, highlightEntities }) {
  return (
    <div className="search-results mt-6 space-y-4">
      {results.map(result => (
        <div key={result.accession_number} className="result-card border rounded-lg p-4">
          <div className="flex justify-between">
            <div>
              <span className="font-semibold">{result.company_name}</span>
              <span className="text-gray-500 ml-2">({result.ticker})</span>
            </div>
            <Badge>{result.form_type}</Badge>
          </div>

          {/* Show matching context - why this result matched */}
          {result.match_context && (
            <div className="mt-3 bg-gray-50 rounded p-3">
              <p className="text-sm text-gray-600 mb-1">
                Matched in: {result.match_context.section}
              </p>
              <blockquote className="text-sm">
                <SentenceWithHighlight
                  sentence={result.match_context.sentence}
                  highlight={highlightEntities[0]}
                />
              </blockquote>
            </div>
          )}

          <button
            onClick={() => navigate(`/filings/${result.accession_number}`)}
            className="mt-2 text-blue-600 hover:underline text-sm"
          >
            View filing details →
          </button>
        </div>
      ))}
    </div>
  );
}
```

### Knowledge Graph Component

```tsx
// src/components/Graph/KnowledgeGraph.tsx
import { useCallback, useEffect, useRef, useState } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import { useCompanyGraph } from '../../hooks/useGraph';

interface KnowledgeGraphProps {
  company: string;
  depth?: number;
  onNodeClick?: (node: any) => void;
}

export function KnowledgeGraph({ company, depth = 2, onNodeClick }: KnowledgeGraphProps) {
  const cyRef = useRef<any>(null);
  const { data, isLoading } = useCompanyGraph(company, depth);

  const elements = useMemo(() => {
    if (!data) return [];

    const nodes = data.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        type: node.type,
        size: Math.log(node.size + 1) * 10 + 20,
      },
    }));

    const edges = data.edges.map(edge => ({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        weight: edge.confidence,
      },
    }));

    return [...nodes, ...edges];
  }, [data]);

  const stylesheet = [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'width': 'data(size)',
        'height': 'data(size)',
        'background-color': (ele: any) => getNodeColor(ele.data('type')),
        'font-size': '10px',
        'text-valign': 'bottom',
        'text-margin-y': '5px',
      },
    },
    {
      selector: 'edge',
      style: {
        'width': (ele: any) => ele.data('weight') * 3,
        'line-color': (ele: any) => getEdgeColor(ele.data('type')),
        'target-arrow-color': (ele: any) => getEdgeColor(ele.data('type')),
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(type)',
        'font-size': '8px',
        'text-rotation': 'autorotate',
      },
    },
    {
      selector: ':selected',
      style: {
        'border-width': '3px',
        'border-color': '#2563eb',
      },
    },
  ];

  const layout = {
    name: 'cose',
    animate: true,
    animationDuration: 500,
    nodeRepulsion: 8000,
    idealEdgeLength: 100,
  };

  return (
    <div className="relative h-[600px] w-full border rounded-lg">
      {isLoading ? (
        <div className="flex items-center justify-center h-full">
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <CytoscapeComponent
            cy={(cy) => { cyRef.current = cy; }}
            elements={elements}
            stylesheet={stylesheet}
            layout={layout}
            className="h-full w-full"
          />
          <GraphLegend />
          <GraphControls cy={cyRef} />
        </>
      )}
    </div>
  );
}

function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    company: '#3b82f6',  // blue
    person: '#10b981',   // green
    product: '#f59e0b',  // amber
    industry: '#8b5cf6', // purple
  };
  return colors[type] || '#6b7280';
}

function getEdgeColor(type: string): string {
  const colors: Record<string, string> = {
    supplies_to: '#22c55e',    // green
    customer_of: '#3b82f6',    // blue
    competes_with: '#ef4444',  // red
    partners_with: '#a855f7',  // purple
    subsidiary_of: '#6b7280',  // gray
  };
  return colors[type] || '#9ca3af';
}
```

### Filing Detail Component

```tsx
// src/components/Filings/FilingDetail.tsx
import { useState } from 'react';
import { useFilingDetail } from '../../hooks/useFilings';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@tremor/react';

export function FilingDetail({ accessionNumber }: { accessionNumber: string }) {
  const { data: filing, isLoading } = useFilingDetail(accessionNumber);
  const [activeTab, setActiveTab] = useState(0);

  if (isLoading) return <LoadingSpinner />;
  if (!filing) return <NotFound />;

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold">
            {filing.company.name} ({filing.company.ticker})
          </h1>
          <p className="text-gray-500">
            {filing.identity.form_type} | Filed {filing.identity.filed_date}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => window.open(filing.identity.filing_url)}>
            View on SEC
          </Button>
          <Button variant="secondary" onClick={() => downloadFiling(filing)}>
            Download
          </Button>
        </div>
      </div>

      {/* Stats */}
      <Grid numItems={4} className="gap-4 mb-6">
        <StatCard title="Suppliers" value={filing.suppliers.length} />
        <StatCard title="Customers" value={filing.customers.length} />
        <StatCard title="Competitors" value={filing.competitors.length} />
        <StatCard title="Risk Factors" value={filing.risk_factors.length} />
      </Grid>

      {/* Tabs */}
      <TabGroup index={activeTab} onIndexChange={setActiveTab}>
        <TabList>
          <Tab>Overview</Tab>
          <Tab>Entities</Tab>
          <Tab>Risks</Tab>
          <Tab>Guidance</Tab>
          <Tab>Sections</Tab>
          <Tab>Graph</Tab>
          <Tab>Ask AI</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <FilingOverview filing={filing} />
          </TabPanel>
          <TabPanel>
            <EntityExplorer filing={filing} />
          </TabPanel>
          <TabPanel>
            <RiskFactorList risks={filing.risk_factors} />
          </TabPanel>
          <TabPanel>
            <GuidanceView guidance={filing.management_guidance} />
          </TabPanel>
          <TabPanel>
            <SectionBrowser sections={filing.sections} />
          </TabPanel>
          <TabPanel>
            <FilingGraph accessionNumber={accessionNumber} />
          </TabPanel>
          <TabPanel>
            <AskQuestion filing={filing} />
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
}
```

### Ask AI Component

```tsx
// src/components/AI/AskQuestion.tsx
import { useState, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { askQuestion } from '../../api/client';

export function AskQuestion({ filing }: { filing: EnrichedFiling }) {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<QA[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const askMutation = useMutation({
    mutationFn: (q: string) => askQuestion(filing.identity.accession_number, q),
    onSuccess: (answer, question) => {
      setHistory(prev => [...prev, { question, answer }]);
      setQuestion('');
      inputRef.current?.focus();
    },
  });

  const suggestedQuestions = [
    "What are the main supply chain risks?",
    "Who are the largest customers?",
    "What is management's outlook on revenue?",
    "Any cybersecurity incidents mentioned?",
    "What are the key growth drivers?",
  ];

  return (
    <div className="space-y-4">
      {/* Suggested questions */}
      <div className="flex flex-wrap gap-2">
        {suggestedQuestions.map(q => (
          <button
            key={q}
            onClick={() => askMutation.mutate(q)}
            className="px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100"
          >
            {q}
          </button>
        ))}
      </div>

      {/* History */}
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {history.map((qa, i) => (
          <div key={i} className="space-y-2">
            <div className="flex gap-2">
              <span className="font-semibold">Q:</span>
              <span>{qa.question}</span>
            </div>
            <div className="flex gap-2 bg-gray-50 p-3 rounded">
              <span className="font-semibold">A:</span>
              <span className="whitespace-pre-wrap">{qa.answer}</span>
            </div>
          </div>
        ))}

        {askMutation.isPending && (
          <div className="flex items-center gap-2 text-gray-500">
            <LoadingSpinner size="sm" />
            Thinking...
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (question.trim()) {
            askMutation.mutate(question);
          }
        }}
        className="flex gap-2"
      >
        <input
          ref={inputRef}
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this filing..."
          className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={askMutation.isPending || !question.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
```

---

## 3. Key Visualizations

### Supply Chain Map

```tsx
// Interactive supply chain visualization
<SupplyChainMap
  company="AAPL"
  depth={2}
  highlightRisks={true}
  // Shows Apple in center, suppliers above, customers below
  // Color-coded by geographic region
  // Size by revenue/importance
/>
```

### Risk Radar Chart

```tsx
// Spider/radar chart of risk categories
<RiskRadar
  filing={filing}
  // Shows severity across categories:
  // - Operational
  // - Financial
  // - Regulatory
  // - Cyber
  // - Competitive
  // - Legal
/>
```

### Entity Timeline

```tsx
// Timeline showing when entities were first/last mentioned
<EntityTimeline
  entity="TSMC"
  filings={filings}
  // Shows TSMC mentions across all filings over time
  // Highlights when relationship changed
/>
```

### Industry Heatmap

```tsx
// Heatmap of relationships within an industry
<IndustryHeatmap
  sicCode="3571"
  relationshipType="supplies_to"
  // Grid showing company-company relationships
  // Color intensity = relationship strength
/>
```

---

## 4. Technology Choices

### Core Stack
- **React 18** + TypeScript
- **Vite** for build/dev
- **TanStack Query** for data fetching
- **Tailwind CSS** + **Tremor** for UI components
- **React Router** for navigation

### Visualization
- **Cytoscape.js** for knowledge graph
- **Recharts** for charts
- **D3.js** for custom visualizations
- **React Flow** for flow diagrams

### State Management
- TanStack Query for server state
- Zustand for local state (minimal)

---

## 5. Getting Started

```bash
# Create frontend
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install @tanstack/react-query axios react-router-dom
npm install @tremor/react tailwindcss postcss autoprefixer
npm install cytoscape react-cytoscapejs
npm install recharts d3

# Start dev server
npm run dev
```

---

## Summary

This frontend provides:
1. **Real-time Filing Feed** - Live stream of latest SEC filings like a Twitter feed
2. **Advanced Search** - Filter by ticker, company, supplier, customer, competitor, sector
3. **Click-through Evidence** - Every extracted fact links to original sentence in SEC document
4. **Filing Explorer** - Browse and search filings with multiple metadata views/tabs
5. **Filing Detail** - Deep dive into any filing's enriched data with entity lists, risks, guidance
6. **Knowledge Graph** - Interactive Cytoscape.js relationship visualization
7. **AI Chat** - Ask questions about filings with source citations
8. **Industry Views** - Sector-level analysis and competitor mapping

Key Features:
- **Full Lineage**: Point-in-time database showing when we first/last saw each fact
- **Provenance**: Every supplier/customer/competitor links back to exact sentence
- **Entity Search**: "Find all filings mentioning TSMC as supplier"
- **Real-time**: WebSocket updates as new filings are collected

All powered by the py-sec-edgar backend with FeedSpine deduplication, EntitySpine resolution, and optional LLM enrichment.

Next: See:
- [07_DATA_LINEAGE_AND_PROVENANCE.md](07_DATA_LINEAGE_AND_PROVENANCE.md) - Point-in-time database
- [08_DOCKER_ARCHITECTURE.md](08_DOCKER_ARCHITECTURE.md) - Container deployment
- [09_SECTION_ENRICHMENT_WORKFLOW.md](09_SECTION_ENRICHMENT_WORKFLOW.md) - Section-specific enrichers
