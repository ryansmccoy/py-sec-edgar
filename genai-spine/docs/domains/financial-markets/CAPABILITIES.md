# Financial Markets Capabilities

> Domain-specific AI capabilities for financial data analysis.

---

## Capability Matrix

| # | Capability | Tier | Status | Use Case |
|---|------------|------|--------|----------|
| 1 | Financial NER | 2 | 🔴 | Extract companies, metrics, executives |
| 2 | Filing Summarization | 2 | 🔴 | Summarize 10-K, 10-Q, 8-K |
| 3 | Earnings Call Analysis | 2 | 🔴 | Parse transcripts, sentiment |
| 4 | Guidance Extraction | 2 | 🔴 | Extract forward-looking statements |
| 5 | Risk Factor Analysis | 3 | 🔴 | Categorize and score risks |
| 6 | Year-over-Year Comparison | 3 | 🔴 | Compare filings across periods |
| 7 | Insider Activity Analysis | 3 | 🔴 | Analyze Form 4 filings |
| 8 | Material Event Detection | 3 | 🔴 | Identify significant 8-K events |
| 9 | Financial Table Extraction | 3 | 🔴 | Parse tables from filings |
| 10 | Management Tone Analysis | 3 | 🔴 | Assess executive sentiment |
| 11 | Peer Comparison | 4 | 🔴 | Compare across companies |
| 12 | Predictive Filing Analysis | 4 | 🔴 | Pattern-based predictions |

---

## 1. Financial NER

**Endpoint:** `POST /v1/extract`

Extract financial entities with domain knowledge.

```python
response = await client.post("/v1/extract", json={
    "content": "Apple Inc. (AAPL) reported Q4 2025 revenue of $94.9B, up 8% YoY. CEO Tim Cook noted...",
    "domain": "financial-markets",
    "entity_types": ["COMPANY", "TICKER", "FINANCIAL_METRIC", "EXECUTIVE"]
})
```

**Response:**
```json
{
    "entities": [
        {
            "text": "Apple Inc.",
            "type": "COMPANY",
            "normalized": "APPLE INC",
            "identifiers": {"ticker": "AAPL", "cik": "0000320193"}
        },
        {
            "text": "Q4 2025 revenue of $94.9B",
            "type": "FINANCIAL_METRIC",
            "normalized": {
                "metric": "revenue",
                "value": 94900000000,
                "currency": "USD",
                "period": "Q4 2025"
            }
        },
        {
            "text": "up 8% YoY",
            "type": "FINANCIAL_METRIC",
            "normalized": {
                "metric": "revenue_growth_yoy",
                "value": 0.08
            }
        },
        {
            "text": "Tim Cook",
            "type": "EXECUTIVE",
            "role": "CEO",
            "company": "Apple Inc."
        }
    ]
}
```

---

## 2. Filing Summarization

**Endpoint:** `POST /v1/summarize`

Summarize SEC filings with structure awareness.

```python
response = await client.post("/v1/summarize", json={
    "content": "10-K filing content...",
    "domain": "financial-markets",
    "filing_type": "10-K",
    "sections": ["business", "risk_factors", "mda"],  # Specific sections
    "output_format": "structured"
})
```

**Response:**
```json
{
    "summary": {
        "business": "Apple designs, manufactures, and markets smartphones...",
        "risk_factors": "Key risks include supply chain dependencies, competition...",
        "mda": "Revenue increased 8% driven by Services growth..."
    },
    "key_metrics": {
        "revenue": "$394.3B",
        "net_income": "$96.9B",
        "eps": "$6.13"
    },
    "notable_changes": [
        "First mention of AI-related risks",
        "Increased R&D spending disclosure"
    ]
}
```

---

## 3. Earnings Call Analysis

**Endpoint:** `POST /v1/analyze/earnings`

Comprehensive earnings call analysis.

```python
response = await client.post("/v1/analyze/earnings", json={
    "transcript": "Earnings call transcript...",
    "company": "AAPL",
    "period": "Q4 2025"
})
```

**Response:**
```json
{
    "summary": "Apple reported strong Q4 with Services as the growth driver...",
    "sentiment": {
        "overall": "positive",
        "score": 0.72,
        "by_speaker": {
            "Tim Cook": {"sentiment": "positive", "score": 0.8},
            "Luca Maestri": {"sentiment": "neutral", "score": 0.55}
        }
    },
    "guidance": {
        "revenue": {"min": 117000000000, "max": 121000000000, "period": "Q1 2026"},
        "gross_margin": {"min": 0.45, "max": 0.46}
    },
    "key_topics": [
        {"topic": "AI", "mentions": 15, "sentiment": "positive"},
        {"topic": "China", "mentions": 8, "sentiment": "cautious"},
        {"topic": "Services", "mentions": 22, "sentiment": "positive"}
    ],
    "analyst_questions": [
        {"question": "Can you elaborate on AI investments?", "sentiment": "curious"},
        {"question": "What's the China outlook?", "sentiment": "concerned"}
    ]
}
```

---

## 4. Guidance Extraction

**Endpoint:** `POST /v1/extract/guidance`

Extract forward-looking statements.

```python
response = await client.post("/v1/extract/guidance", json={
    "content": "Filing or transcript text...",
    "domain": "financial-markets"
})
```

**Response:**
```json
{
    "guidance": [
        {
            "metric": "revenue",
            "type": "range",
            "min": 117000000000,
            "max": 121000000000,
            "period": "Q1 2026",
            "confidence_language": "expects",
            "source_text": "We expect revenue between $117B and $121B"
        },
        {
            "metric": "gross_margin",
            "type": "range",
            "min": 0.45,
            "max": 0.46,
            "period": "Q1 2026",
            "confidence_language": "anticipates"
        }
    ],
    "caveats": [
        "Subject to macroeconomic conditions",
        "Excluding potential acquisition impacts"
    ]
}
```

---

## 5. Risk Factor Analysis

**Endpoint:** `POST /v1/analyze/risks`

Categorize and score risk disclosures.

```python
response = await client.post("/v1/analyze/risks", json={
    "content": "Risk factors section...",
    "domain": "financial-markets",
    "compare_to_prior": True,  # Compare to previous filing
    "prior_content": "Previous risk factors..."
})
```

**Response:**
```json
{
    "risk_factors": [
        {
            "category": "OPERATIONAL",
            "subcategory": "Supply Chain",
            "title": "Dependence on third-party manufacturers",
            "severity": "high",
            "change": "unchanged",
            "summary": "Relies on limited suppliers in Asia..."
        },
        {
            "category": "REGULATORY",
            "subcategory": "AI Regulation",
            "title": "Emerging AI regulations",
            "severity": "medium",
            "change": "new",  # New in this filing
            "summary": "Potential impact from AI regulatory frameworks..."
        }
    ],
    "risk_summary": {
        "total_risks": 35,
        "new_risks": 3,
        "removed_risks": 1,
        "severity_distribution": {
            "high": 8,
            "medium": 15,
            "low": 12
        }
    }
}
```

---

## 6. Year-over-Year Comparison

**Endpoint:** `POST /v1/compare/filings`

Compare filings across periods.

```python
response = await client.post("/v1/compare/filings", json={
    "filing_a": {"content": "2024 10-K...", "period": "FY2024"},
    "filing_b": {"content": "2025 10-K...", "period": "FY2025"},
    "domain": "financial-markets",
    "sections": ["risk_factors", "mda"]
})
```

**Response:**
```json
{
    "changes": {
        "risk_factors": {
            "added": ["AI regulation risk", "Geopolitical risks expanded"],
            "removed": ["COVID-19 pandemic risk"],
            "modified": ["Supply chain risk language strengthened"]
        },
        "mda": {
            "key_changes": [
                "Services now largest revenue driver",
                "R&D spending increased 15%"
            ]
        }
    },
    "metrics_comparison": {
        "revenue": {"fy2024": 383000000000, "fy2025": 394300000000, "change": 0.029},
        "net_income": {"fy2024": 96000000000, "fy2025": 96900000000, "change": 0.009}
    }
}
```

---

## 7. Material Event Detection (8-K)

**Endpoint:** `POST /v1/analyze/8k`

Analyze 8-K filings for material events.

```python
response = await client.post("/v1/analyze/8k", json={
    "content": "8-K filing content...",
    "domain": "financial-markets"
})
```

**Response:**
```json
{
    "item_types": ["1.01", "5.02"],
    "events": [
        {
            "item": "1.01",
            "title": "Entry into Material Agreement",
            "description": "Entered into $5B credit facility...",
            "materiality": "high",
            "potential_impact": "Positive - improved liquidity"
        },
        {
            "item": "5.02",
            "title": "Executive Departure",
            "description": "CFO announcing retirement...",
            "materiality": "medium",
            "potential_impact": "Neutral - orderly transition planned"
        }
    ],
    "market_impact_assessment": {
        "likely_reaction": "neutral_to_positive",
        "confidence": 0.7
    }
}
```

---

## 8. Financial Table Extraction

**Endpoint:** `POST /v1/extract/tables`

Extract and structure financial tables.

```python
response = await client.post("/v1/extract/tables", json={
    "content": "Filing with tables...",
    "domain": "financial-markets",
    "table_types": ["income_statement", "balance_sheet", "cash_flow"]
})
```

**Response:**
```json
{
    "tables": [
        {
            "type": "income_statement",
            "periods": ["Q4 2025", "Q4 2024"],
            "data": {
                "revenue": {"Q4 2025": 94900000000, "Q4 2024": 87800000000},
                "gross_profit": {"Q4 2025": 43100000000, "Q4 2024": 39500000000},
                "net_income": {"Q4 2025": 24900000000, "Q4 2024": 22900000000}
            }
        }
    ]
}
```

---

## Prompt Library

Domain-specific prompts are stored in:

```
genai-spine/
└── src/
    └── genai_spine/
        └── domains/
            └── financial_markets/
                └── prompts/
                    ├── ner.yaml
                    ├── summarization.yaml
                    ├── earnings.yaml
                    ├── risks.yaml
                    └── comparison.yaml
```

---

## Related Docs

- [README.md](README.md) — Domain overview
- [INTEGRATION.md](INTEGRATION.md) — Integration examples
- [../../core/RAG.md](../../core/RAG.md) — RAG for SEC filings
