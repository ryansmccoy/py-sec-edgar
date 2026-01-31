# Financial Markets Integration

> How to integrate GenAI Spine financial capabilities with the Spine ecosystem.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SPINE ECOSYSTEM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  py-sec-edgar│───▶│  FeedSpine   │───▶│     Capture Spine        │  │
│  │  (SEC Data)  │    │  (Ingest)    │    │  (Store + Search)        │  │
│  └──────────────┘    └──────────────┘    └────────────┬─────────────┘  │
│                                                        │                 │
│                                                        ▼                 │
│  ┌──────────────┐                         ┌──────────────────────────┐  │
│  │  EntitySpine │◀────────────────────────│      GenAI Spine         │  │
│  │  (Resolve)   │                         │  (Financial Domain)      │  │
│  └──────────────┘                         └──────────────────────────┘  │
│                                                        │                 │
│                                                        ▼                 │
│                                           ┌──────────────────────────┐  │
│                                           │    Trading Desktop       │  │
│                                           │    (Market Spine)        │  │
│                                           └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## py-sec-edgar Integration

### Filing Processing Pipeline

```python
from py_sec_edgar import get_filings
from httpx import AsyncClient

genai = AsyncClient(base_url="http://genai-spine:8100")

async def process_recent_filings(ticker: str):
    # 1. Get filings from py-sec-edgar
    filings = get_filings(ticker=ticker, form_type="10-K", limit=2)

    for filing in filings:
        # 2. Summarize with GenAI
        summary = await genai.post("/v1/summarize", json={
            "content": filing.content,
            "domain": "financial-markets",
            "filing_type": "10-K"
        })

        # 3. Extract risk factors
        risks = await genai.post("/v1/analyze/risks", json={
            "content": filing.get_section("risk_factors"),
            "domain": "financial-markets"
        })

        # 4. Extract financial metrics
        metrics = await genai.post("/v1/extract", json={
            "content": filing.content,
            "domain": "financial-markets",
            "extraction_type": "financial_metrics"
        })

        yield {
            "filing": filing.metadata,
            "summary": summary.json(),
            "risks": risks.json(),
            "metrics": metrics.json()
        }
```

---

## EntitySpine Integration

### Entity Resolution

```python
from entityspine import EntityResolver

resolver = EntityResolver()

async def extract_and_resolve(content: str):
    # 1. Extract entities with GenAI
    response = await genai.post("/v1/extract", json={
        "content": content,
        "domain": "financial-markets",
        "entity_types": ["COMPANY", "TICKER", "EXECUTIVE"]
    })
    entities = response.json()["entities"]

    # 2. Resolve with EntitySpine
    resolved = []
    for entity in entities:
        if entity["type"] == "COMPANY":
            match = resolver.resolve(
                name=entity["text"],
                ticker=entity.get("identifiers", {}).get("ticker")
            )
            entity["entityspine_id"] = match.entity_id if match else None
        resolved.append(entity)

    return resolved
```

### Knowledge Graph Population

```python
async def populate_knowledge_graph(filing_analysis: dict):
    """Add filing analysis to EntitySpine knowledge graph."""

    # Create relationships from extracted entities
    for entity in filing_analysis["entities"]:
        if entity["type"] == "EXECUTIVE":
            # Add person-company relationship
            await entityspine.add_relationship(
                subject=entity["entityspine_id"],
                predicate="WORKS_AT",
                object=filing_analysis["company_id"],
                properties={
                    "role": entity["role"],
                    "as_of": filing_analysis["filing_date"]
                }
            )
```

---

## FeedSpine Integration

### Financial Feed Enrichment

```python
from feedspine import Enricher, Record

class FinancialEnricher(Enricher):
    """Enrich financial records with GenAI analysis."""

    def __init__(self, genai_url: str = "http://genai-spine:8100"):
        self.genai = AsyncClient(base_url=genai_url)

    async def enrich(self, record: Record) -> Record:
        enrichments = {}

        if record.type == "earnings_estimate":
            # Extract structured estimate data
            enrichments["parsed"] = await self._extract_estimate(record)

        elif record.type == "sec_filing":
            # Summarize and analyze
            enrichments["summary"] = await self._summarize_filing(record)
            enrichments["sentiment"] = await self._analyze_sentiment(record)

        elif record.type == "earnings_call":
            # Full earnings call analysis
            enrichments["analysis"] = await self._analyze_earnings_call(record)

        return record.with_enrichments(**enrichments)

    async def _analyze_earnings_call(self, record: Record) -> dict:
        response = await self.genai.post("/v1/analyze/earnings", json={
            "transcript": record.content,
            "company": record.metadata.get("ticker"),
            "period": record.metadata.get("period")
        })
        return response.json()


# Register with FeedSpine
feedspine.register_enricher(
    name="financial_genai",
    enricher=FinancialEnricher(),
    record_types=["earnings_estimate", "sec_filing", "earnings_call"]
)
```

### Earnings Comparison Pipeline

```python
async def compare_estimate_vs_actual(ticker: str, period: str):
    """Compare earnings estimates to actuals using GenAI."""

    # Get estimate from FeedSpine
    estimate = await feedspine.get_record(
        record_type="earnings_estimate",
        ticker=ticker,
        period=period
    )

    # Get actual from 8-K filing
    actual_filing = await feedspine.get_record(
        record_type="sec_filing",
        ticker=ticker,
        form_type="8-K",
        period=period
    )

    # Compare with GenAI
    comparison = await genai.post("/v1/compare", json={
        "document_a": estimate.content,
        "document_b": actual_filing.content,
        "domain": "financial-markets",
        "comparison_type": "estimate_vs_actual"
    })

    return comparison.json()
```

---

## Capture Spine Integration

### Article Enrichment

```python
# capture-spine/app/features/enrichment/financial.py

from httpx import AsyncClient

class FinancialArticleEnricher:
    """Enrich news articles with financial analysis."""

    def __init__(self):
        self.genai = AsyncClient(base_url="http://genai-spine:8100")

    async def enrich(self, article: dict) -> dict:
        # Check if financial content
        classification = await self.genai.post("/v1/classify", json={
            "content": article["content"][:1000],
            "domain": "financial-markets",
            "categories": ["earnings", "m&a", "regulatory", "market", "other"]
        })

        if classification.json()["primary_category"] == "other":
            return article  # Not financial, skip

        # Extract financial entities
        entities = await self.genai.post("/v1/extract", json={
            "content": article["content"],
            "domain": "financial-markets",
            "entity_types": ["COMPANY", "TICKER", "FINANCIAL_METRIC"]
        })

        # Analyze sentiment
        sentiment = await self.genai.post("/v1/analyze/sentiment", json={
            "content": article["content"],
            "domain": "financial-markets"
        })

        return {
            **article,
            "enrichment": {
                "category": classification.json()["primary_category"],
                "entities": entities.json()["entities"],
                "sentiment": sentiment.json()["sentiment"],
                "enriched_at": datetime.utcnow().isoformat()
            }
        }
```

### RAG for SEC Filings

```python
# Index SEC filings for RAG
async def index_filings_for_rag(filings: list):
    """Index SEC filings into GenAI RAG."""

    documents = []
    for filing in filings:
        documents.append({
            "id": f"{filing.cik}_{filing.form_type}_{filing.filed_date}",
            "content": filing.content,
            "metadata": {
                "company": filing.company_name,
                "cik": filing.cik,
                "ticker": filing.ticker,
                "form_type": filing.form_type,
                "filed_date": filing.filed_date.isoformat(),
                "fiscal_period": filing.fiscal_period
            }
        })

    await genai.post("/v1/rag/index", json={
        "collection": "sec_filings",
        "documents": documents,
        "chunk_strategy": "structure",  # Respect filing sections
        "metadata_fields": ["company", "form_type", "fiscal_period"]
    })

# Query SEC filings
async def research_query(query: str, companies: list = None):
    """Answer research questions using SEC filings."""

    filters = {}
    if companies:
        filters["ticker"] = companies

    response = await genai.post("/v1/rag/query", json={
        "query": query,
        "collection": "sec_filings",
        "filters": filters,
        "top_k": 10,
        "generate_answer": True,
        "cite_sources": True
    })

    return response.json()
```

---

## Market Spine (Trading Desktop) Integration

### Research Dashboard Widget

```typescript
// trading-desktop/src/widgets/ResearchWidget.tsx

async function getCompanyResearch(ticker: string): Promise<Research> {
  // Get latest filing summary
  const filingSummary = await genaiClient.post('/v1/summarize', {
    content: await fetchLatestFiling(ticker),
    domain: 'financial-markets',
    filing_type: '10-K'
  });

  // Get risk assessment
  const risks = await genaiClient.post('/v1/analyze/risks', {
    content: await fetchRiskFactors(ticker),
    domain: 'financial-markets'
  });

  // Get earnings sentiment
  const sentiment = await genaiClient.post('/v1/analyze/earnings', {
    transcript: await fetchLatestEarningsCall(ticker),
    company: ticker
  });

  return {
    summary: filingSummary.data.summary,
    risks: risks.data.risk_factors,
    sentiment: sentiment.data.sentiment,
    guidance: sentiment.data.guidance
  };
}
```

### Natural Language Research

```typescript
// Allow traders to ask questions in natural language
async function askResearchQuestion(question: string): Promise<Answer> {
  const response = await genaiClient.post('/v1/rag/query', {
    query: question,
    collections: ['sec_filings', 'earnings_calls', 'analyst_reports'],
    domain: 'financial-markets',
    generate_answer: true,
    cite_sources: true
  });

  return {
    answer: response.data.answer,
    sources: response.data.sources,
    confidence: response.data.confidence
  };
}

// Example usage in Trading Desktop
<ResearchChat
  onQuestion={askResearchQuestion}
  placeholder="Ask about any company's financials..."
/>
```

---

## Docker Compose Example

```yaml
# docker-compose.yml for full financial stack

version: '3.8'

services:
  genai-spine:
    build: ./genai-spine
    ports:
      - "8100:8100"
    environment:
      - GENAI_DEFAULT_PROVIDER=ollama
      - GENAI_OLLAMA_URL=http://ollama:11434
      - GENAI_DATABASE_URL=postgresql://postgres:pass@db:5432/genai
    depends_on:
      - ollama
      - db

  capture-spine:
    build: ./capture-spine
    ports:
      - "8000:8000"
    environment:
      - GENAI_SPINE_URL=http://genai-spine:8100
    depends_on:
      - genai-spine

  feedspine:
    build: ./feedspine
    environment:
      - GENAI_SPINE_URL=http://genai-spine:8100
    depends_on:
      - genai-spine

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  db:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=pass
    volumes:
      - pg_data:/var/lib/postgresql/data

volumes:
  ollama_data:
  pg_data:
```

---

## Related Docs

- [README.md](README.md) — Domain overview
- [CAPABILITIES.md](CAPABILITIES.md) — Capability specifications
- [../../core/RAG.md](../../core/RAG.md) — RAG architecture
