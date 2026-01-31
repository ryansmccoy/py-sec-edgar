# Domain Extensions

> GenAI Spine is domain-agnostic at its core. Domain-specific capabilities live in extension modules.

---

## Philosophy

The core GenAI Spine provides:
- Generic capabilities (summarize, extract, classify)
- Provider abstraction
- Prompt management
- Infrastructure (caching, cost tracking)

Domain extensions add:
- Specialized prompts
- Domain-specific entity types
- Custom extraction schemas
- Industry terminology
- Validation rules

---

## Available Domains

| Domain | Status | Location | Description |
|--------|--------|----------|-------------|
| **Financial Markets** | 🟡 Planned | [financial-markets/](financial-markets/) | SEC filings, earnings, financial NER |
| Legal | 🔴 Future | `legal/` | Contracts, compliance, regulations |
| Healthcare | 🔴 Future | `healthcare/` | Clinical notes, research, HIPAA |
| News/Media | 🔴 Future | `news/` | Article processing, bias, fact-check |

---

## Extension Architecture

```
domains/
├── README.md                    # This file
└── {domain-name}/
    ├── README.md                # Domain overview
    ├── CAPABILITIES.md          # Domain-specific capabilities
    ├── INTEGRATION.md           # How to integrate
    ├── prompts/                  # Domain prompt library
    │   ├── summarization.yaml
    │   ├── extraction.yaml
    │   └── analysis.yaml
    └── schemas/                  # Domain data schemas
        ├── entities.py
        └── outputs.py
```

---

## Creating a Domain Extension

### 1. Define Domain Entities

```python
# domains/financial-markets/schemas/entities.py

FINANCIAL_ENTITY_TYPES = [
    "COMPANY",           # Public/private companies
    "TICKER",            # Stock symbols
    "EXECUTIVE",         # C-suite, directors
    "FINANCIAL_METRIC",  # Revenue, EPS, EBITDA
    "FILING_TYPE",       # 10-K, 10-Q, 8-K
    "FISCAL_PERIOD",     # Q1, FY2025
    "REGULATORY_BODY",   # SEC, FINRA, FDA
    "RISK_FACTOR",       # Risk categories
]
```

### 2. Create Domain Prompts

```yaml
# domains/financial-markets/prompts/extraction.yaml
prompts:
  - slug: extract-financial-entities
    name: Extract Financial Entities
    category: extraction
    domain: financial-markets
    system_prompt: |
      You are a financial analyst expert at extracting entities from SEC filings.
    user_prompt_template: |
      Extract all financial entities from this text:
      - Companies (with ticker if mentioned)
      - Executives (with role)
      - Financial metrics (with values and periods)
      - Risk factors

      Text: {{content}}

      Return as JSON array.
    variables:
      - name: content
        type: string
        required: true
```

### 3. Register Domain

```python
# domains/financial-markets/__init__.py

from genai_spine.domains import register_domain

register_domain(
    name="financial-markets",
    display_name="Financial Markets",
    description="SEC filings, earnings, financial analysis",
    prompts_path="domains/financial-markets/prompts",
    entity_types=FINANCIAL_ENTITY_TYPES,
)
```

---

## Using Domain Capabilities

```python
# Specify domain when calling capabilities
response = await client.post("/v1/extract", json={
    "content": "Apple Inc. (AAPL) reported Q4 revenue of $94.9B...",
    "domain": "financial-markets",  # Use domain-specific prompts/entities
    "entity_types": ["COMPANY", "TICKER", "FINANCIAL_METRIC"]
})
```

---

## Domain Prompt Inheritance

Domain prompts can extend core prompts:

```yaml
# Core prompt
slug: summarize-article
user_prompt_template: |
  Summarize in {{max_sentences}} sentences:
  {{content}}

# Domain extension
slug: summarize-earnings-call
extends: summarize-article
domain: financial-markets
user_prompt_template: |
  Summarize this earnings call transcript in {{max_sentences}} sentences.
  Focus on: revenue, guidance, management commentary.

  {{content}}
```

---

## See Also

- [financial-markets/README.md](financial-markets/README.md) — Financial markets domain
