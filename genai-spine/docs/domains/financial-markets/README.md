# Financial Markets Domain

> Specialized GenAI capabilities for SEC filings, earnings analysis, and financial data.

---

## Overview

The financial markets domain extends GenAI Spine with:
- Financial entity extraction (companies, metrics, filings)
- SEC filing analysis (10-K, 10-Q, 8-K)
- Earnings call processing
- Financial sentiment analysis
- Risk factor extraction

---

## Status

| Capability | Status | Priority |
|------------|--------|----------|
| Financial NER | 🔴 Not Started | High |
| Filing Summarization | 🔴 Not Started | High |
| Earnings Sentiment | 🔴 Not Started | High |
| Risk Factor Extraction | 🔴 Not Started | Medium |
| 10-K Comparison | 🔴 Not Started | Medium |
| Guidance Extraction | 🔴 Not Started | Medium |
| Insider Transaction Analysis | 🔴 Not Started | Low |
| Material Event Detection | 🔴 Not Started | Low |

---

## Entity Types

| Entity Type | Description | Examples |
|-------------|-------------|----------|
| `COMPANY` | Public/private companies | "Apple Inc.", "Microsoft" |
| `TICKER` | Stock symbols | "AAPL", "MSFT" |
| `CIK` | SEC Central Index Key | "0000320193" |
| `CUSIP` | Security identifier | "037833100" |
| `EXECUTIVE` | Named executives | "Tim Cook", "Satya Nadella" |
| `ROLE` | Executive roles | "CEO", "CFO", "Board Member" |
| `FINANCIAL_METRIC` | Quantitative metrics | "Revenue", "EPS", "EBITDA" |
| `METRIC_VALUE` | Metric values | "$94.9B", "8%", "$2.10" |
| `FISCAL_PERIOD` | Time periods | "Q4 2025", "FY2025", "TTM" |
| `FILING_TYPE` | SEC form types | "10-K", "10-Q", "8-K", "DEF 14A" |
| `REGULATORY_BODY` | Regulators | "SEC", "FINRA", "DOJ" |
| `RISK_CATEGORY` | Risk types | "Market Risk", "Regulatory Risk" |
| `GUIDANCE` | Forward-looking statements | "expects", "anticipates" |

---

## Integration Points

### With EntitySpine

```python
# Extract entities and resolve with EntitySpine
response = await genai_client.post("/v1/extract", json={
    "content": "Apple (AAPL) announced...",
    "domain": "financial-markets",
    "resolve_entities": True  # Cross-reference with EntitySpine
})

# Response includes EntitySpine IDs
{
    "entities": [
        {
            "text": "Apple",
            "type": "COMPANY",
            "entityspine_id": "entity:0000320193",
            "ticker": "AAPL",
            "cik": "0000320193"
        }
    ]
}
```

### With FeedSpine

```python
# Enrich earnings data from FeedSpine
class FinancialEnricher(Enricher):
    async def enrich(self, record: Record) -> Record:
        if record.type == "earnings_call":
            # Extract financial metrics
            metrics = await genai.extract(
                record.content,
                domain="financial-markets",
                extraction_type="financial_metrics"
            )
            return record.with_enrichments(metrics=metrics)
```

### With Capture Spine

```python
# Process SEC filings from Capture Spine
async def process_filing(filing: dict):
    # Summarize
    summary = await genai.summarize(
        filing["content"],
        domain="financial-markets",
        filing_type=filing["form_type"]
    )

    # Extract risk factors
    risks = await genai.extract(
        filing["content"],
        domain="financial-markets",
        extraction_type="risk_factors"
    )

    return {**summary, "risks": risks}
```

---

## Related Docs

- [CAPABILITIES.md](CAPABILITIES.md) — Detailed capability specifications
- [INTEGRATION.md](INTEGRATION.md) — Integration examples
- [../../capabilities/](../../capabilities/) — Core capabilities
