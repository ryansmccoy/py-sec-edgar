# py-sec-edgar Vision Documents Index

**SEC Filing Intelligence Platform**

> Transform raw SEC filings into a fully searchable, explorable knowledge graph with AI-powered insights.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SEC FILING INTELLIGENCE PLATFORM                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│  USER INTERFACE                                                                  │
│  ─────────────                                                                  │
│  • Real-time Filing Feed       • Advanced Search (by supplier/customer/sector)  │
│  • Filing Explorer + Detail    • Knowledge Graph Visualization                   │
│  • AI Q&A with Citations       • Event Timeline + Significant Developments      │
│                               [06_FRONTEND_VISUALIZATION.md]                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  API LAYER (FastAPI)                                                             │
│  ──────────────────                                                             │
│  • /api/feed/latest         • /api/search/advanced                              │
│  • /api/filings/{id}        • /api/search/by-supplier/{name}                    │
│  • /api/graph/company/{id}  • /api/events/timeline/{cik}                        │
│  • /api/ask                 • /api/lineage/suppliers/{cik}                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ENRICHMENT PIPELINE                                                             │
│  ───────────────────                                                            │
│  Section Router → EntityExtractor → RiskClassifier → GuidanceExtractor          │
│                   [02_ENRICHER_PIPELINE.md] [09_SECTION_ENRICHMENT_WORKFLOW.md]  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│  EntitySpine           │ │  LLM Providers        │ │  EventSpine           │
│  (Entity Resolution)   │ │  (Ollama/Bedrock)     │ │  (Event Timeline)     │
│  [10_ENTITYSPINE]      │ │  [05_LLM_INTEGRATION] │ │  [11_EVENTSPINE]      │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STORAGE LAYER (Bronze → Silver → Gold)                                          │
│  ──────────────────────────────────────                                         │
│  • Bronze: Raw filings, events      • Silver: Parsed, classified                │
│  • Gold: Enriched, linked           • Temporal: Point-in-time tracking          │
│                         [03_STORAGE_AND_SEARCH.md] [07_DATA_LINEAGE.md]          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  DATA COLLECTION                                                                 │
│  ───────────────                                                                │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐            │
│  │  FeedSpine (SEC Filings)     │  │  CaptureSpine (Events)       │            │
│  │  • RSS Feed    • Daily Index │  │  • Press Releases  • News    │            │
│  │  • SmartSync   • Dedup       │  │  • Conf. Calls     • PR Wire │            │
│  └──────────────────────────────┘  └──────────────────────────────┘            │
│                     [py-sec-edgar core]   [11_EVENTSPINE_AND_FUTURE_ROADMAP]    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              ┌───────────┐       ┌───────────┐       ┌───────────┐
              │SEC EDGAR  │       │PR Newswire│       │ Seeking   │
              │(filings)  │       │(press rel)│       │ Alpha     │
              └───────────┘       └───────────┘       └───────────┘
```

---

## Vision Documents

| # | Document | Purpose |
|---|----------|---------|
| 01 | [ENRICHED_FILING_MODEL.md](01_ENRICHED_FILING_MODEL.md) | The core `EnrichedFiling` dataclass - what users interact with |
| 02 | [ENRICHER_PIPELINE.md](02_ENRICHER_PIPELINE.md) | 5-stage enrichment pipeline architecture |
| 03 | [STORAGE_AND_SEARCH.md](03_STORAGE_AND_SEARCH.md) | DuckDB schemas, search capabilities, export |
| 04 | [KNOWLEDGE_GRAPH.md](04_KNOWLEDGE_GRAPH.md) | Company relationship graph, supply chain analysis |
| 05 | [LLM_INTEGRATION.md](05_LLM_INTEGRATION.md) | Ollama/Bedrock/OpenAI provider protocol |
| 06 | [FRONTEND_VISUALIZATION.md](06_FRONTEND_VISUALIZATION.md) | React UI with real-time feed, search, evidence linking |
| 07 | [DATA_LINEAGE_AND_PROVENANCE.md](07_DATA_LINEAGE_AND_PROVENANCE.md) | Point-in-time database, full audit trail |
| 08 | [DOCKER_ARCHITECTURE.md](08_DOCKER_ARCHITECTURE.md) | Container deployment with worker consumers |
| 09 | [SECTION_ENRICHMENT_WORKFLOW.md](09_SECTION_ENRICHMENT_WORKFLOW.md) | Section-specific enrichers, EntitySpine integration |
| 10 | [ENTITYSPINE_UNIVERSAL_FABRIC.md](10_ENTITYSPINE_UNIVERSAL_FABRIC.md) | Universal entity management with lineage, bulk ingestion, multi-source enrichment |
| 11 | [EVENTSPINE_AND_FUTURE_ROADMAP.md](11_EVENTSPINE_AND_FUTURE_ROADMAP.md) | EventSpine + SigDev integration, future roadmap |
| 12 | [UNIFIED_INTERFACE_DESIGN.md](12_UNIFIED_INTERFACE_DESIGN.md) | EntitySpine + FeedSpine + py-sec-edgar: standalone vs integrated functionality |
| 13 | [COMPANY_CENTRIC_API.md](13_COMPANY_CENTRIC_API.md) | Company-centric workflows: `sec.company("AAPL")` → rich object |
| **14** | **[V4_MASTER_ROADMAP.md](14_V4_MASTER_ROADMAP.md)** | **🎯 Master implementation roadmap with feature matrix** |
| **15** | **[DATA_MODEL_REFERENCE.md](15_DATA_MODEL_REFERENCE.md)** | **📋 Canonical data model definitions** |
| **16** | **[ARCHITECTURE_UNIFIED_FEEDS_VS_APIS.md](16_ARCHITECTURE_UNIFIED_FEEDS_VS_APIS.md)** | **🏗️ Push (Feeds) vs Pull (APIs) architecture decision** |

---

## The Spine Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              THE SPINE ECOSYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  IMPLEMENTED                                                                    │
│  ───────────                                                                    │
│  py-sec-edgar ─── FeedSpine ─── EntitySpine ─── CaptureSpine ─── edgar_sigdev  │
│                                                                                 │
│  FUTURE                                                                         │
│  ──────                                                                         │
│  EventSpine ──── EstimateSpine ──── MetricSpine ──── ResearchSpine ──── AlertSpine
│  (events)        (estimates)        (KPIs)          (research)         (alerts) │
│                  (surprises)        (segments)      (ratings)          (watchlists)
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Rich Filing Objects
```python
filing = await sec.get_filing("AAPL", Forms.FORM_10K, year=2024, enrich=True)

print(filing.suppliers)              # ["TSMC", "Samsung", "Foxconn"]
print(filing.customers)              # ["Best Buy", "Verizon"]
print(filing.risk_factors)           # Classified by category and severity
print(filing.management_guidance)    # Extracted outlook and numbers
```

### 2. Click-through Evidence
Every extracted fact links back to the **exact sentence** in the SEC document:
```python
supplier_mention = filing.entities.suppliers[0]
print(supplier_mention.sentence_text)  # "We rely on TSMC for substantially all of our..."
print(supplier_mention.sec_url)        # Direct link to SEC filing
```

### 3. Point-in-Time Queries
```python
# What suppliers did we know about on June 15, 2024?
suppliers = store.get_suppliers_as_of("0000320193", datetime(2024, 6, 15))

# When did TSMC first appear as a supplier?
history = store.get_entity_history("TSMC")
```

### 4. Advanced Search
```python
# Find all filings mentioning TSMC as a supplier
results = await search(supplier_name="TSMC")

# Find semiconductor companies with cyber risks
results = await search(sic_code="3674", risk_category="cyber")
```

### 5. Knowledge Graph
```python
# Get Apple's supply chain graph
graph = await get_company_graph("AAPL", depth=2)

# Find common suppliers between Apple and Google
common = await find_common_suppliers(["AAPL", "GOOGL"])
```

### 6. LLM-Powered Analysis
```python
# Ask questions with source citations
answer = await qa.ask(filing, "What are the main supply chain risks?")
print(answer.text)      # "The company faces several supply chain risks..."
print(answer.sources)   # Links to specific sentences in filing
```

---

## Package Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              py-sec-edgar ecosystem                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│   │  py-sec-edgar   │    │    FeedSpine    │    │   EntitySpine   │           │
│   │                 │    │                 │    │                 │           │
│   │ • SEC filing    │───▶│ • SEC feed      │    │ • Entity        │           │
│   │   collection    │    │   capture       │    │   resolution    │           │
│   │ • Enrichment    │    │ • Deduplication │    │ • CIK→Entity    │           │
│   │   pipeline      │    │ • Sync strategy │    │ • Merge tracking│           │
│   │ • Storage       │◀───│                 │◀───│                 │           │
│   │                 │    │                 │    │                 │           │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘           │
│           │                      │                       ▲                     │
│           │                      │                       │                     │
│           │              ┌───────▼───────┐               │                     │
│           │              │ CaptureSpine  │               │                     │
│           │              │               │               │                     │
│           │              │ • PR Newswire │               │                     │
│           │              │ • News feeds  │               │                     │
│           │              │ • Transcripts │               │                     │
│           │              │ • Content     │               │                     │
│           │              │   dedup       │               │                     │
│           │              └───────┬───────┘               │                     │
│           │                      │                       │                     │
│           │              ┌───────▼───────┐               │                     │
│           │              │  EventSpine   │───────────────┘                     │
│           │              │               │                                     │
│           │              │ • Event       │                                     │
│           │              │   timeline    │                                     │
│           └─────────────▶│ • Event→      │                                     │
│                          │   Filing link │                                     │
│                          │ • PR/Call     │                                     │
│                          │   enrichers   │                                     │
│                          └───────────────┘                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Core (MVP)
- [ ] EnrichedFiling model with sections
- [ ] Basic entity extraction (spaCy NER)
- [ ] DuckDB storage with lineage
- [ ] Simple CLI for downloading + enriching

### Phase 2: Search & Evidence
- [ ] Full-text search with filters
- [ ] Entity search (by supplier/customer)
- [ ] Evidence API (sentence + context)
- [ ] Basic React dashboard

### Phase 3: Graph & LLM
- [ ] Knowledge graph storage
- [ ] Relationship extraction
- [ ] Ollama LLM integration
- [ ] Guidance extraction

### Phase 4: Scale & Polish
- [ ] Docker deployment
- [ ] Worker consumers
- [ ] Real-time feed
- [ ] Advanced visualizations

### Phase 5: EventSpine (Future)
- [ ] EventSpine core data model (builds on edgar_sigdev_pack)
- [ ] SEC 8-K → SigDev event extraction
- [ ] CaptureSpine integration (PR Newswire, BusinessWire)
- [ ] Conference call transcript parsing
- [ ] Event → Filing linking & event chains
- [ ] Bronze/Silver/Gold data tiers

### Phase 6: Quantitative Spines (Future)
- [ ] **EstimateSpine**: Analyst estimates, consensus tracking, earnings surprises
- [ ] **MetricSpine**: KPIs, segment data, product line metrics, time series
- [ ] Estimate → Event linking (guidance vs consensus)

### Phase 7: Research & Alerts (Future)
- [ ] **ResearchSpine**: Analyst ratings, price targets, research reports
- [ ] **AlertSpine**: User watchlists, event triggers, notifications
- [ ] Cross-spine queries for comprehensive analysis

→ See [11_EVENTSPINE_AND_FUTURE_ROADMAP.md](11_EVENTSPINE_AND_FUTURE_ROADMAP.md) for detailed roadmap

- [V4_IMPROVEMENTS_NEEDED.md](../V4_IMPROVEMENTS_NEEDED.md) - Bugs to fix before release
- [V4_POTENTIAL_FEATURES.md](../V4_POTENTIAL_FEATURES.md) - Feature tiers for release
