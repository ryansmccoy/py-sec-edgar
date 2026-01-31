# Cost Tracking

> Monitor and control LLM spending across providers and models.

---

## Overview

GenAI Spine tracks costs at multiple levels:
- Per-request costs
- Per-model costs
- Per-provider costs
- Daily/monthly aggregates
- Budget enforcement

---

## How Costs Are Calculated

### Token-Based Pricing

Most providers charge per token (input + output):

```python
cost = (input_tokens * input_price / 1_000_000) +
       (output_tokens * output_price / 1_000_000)
```

### Price Table

| Provider | Model | Input ($/1M) | Output ($/1M) |
|----------|-------|--------------|---------------|
| OpenAI | gpt-4o | $2.50 | $10.00 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | o1 | $15.00 | $60.00 |
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 |
| Anthropic | claude-haiku | $0.25 | $1.25 |
| Bedrock | nova-lite | $0.06 | $0.24 |
| Ollama | * | $0.00 | $0.00 |

---

## API Response

Every response includes usage data:

```json
{
    "content": "...",
    "usage": {
        "input_tokens": 150,
        "output_tokens": 85,
        "total_tokens": 235,
        "cost_usd": 0.0023,
        "provider": "openai",
        "model": "gpt-4o-mini"
    }
}
```

---

## Cost Endpoints

### Get Usage Summary

```http
GET /v1/usage?start_date=2026-01-01&end_date=2026-01-31
```

Response:
```json
{
    "period": {"start": "2026-01-01", "end": "2026-01-31"},
    "total": {
        "requests": 15420,
        "input_tokens": 4520000,
        "output_tokens": 1230000,
        "cost_usd": 45.23
    },
    "by_provider": {
        "openai": {"requests": 5000, "cost_usd": 35.00},
        "ollama": {"requests": 10420, "cost_usd": 0.00}
    },
    "by_model": {
        "gpt-4o-mini": {"requests": 5000, "cost_usd": 35.00},
        "llama3.2:latest": {"requests": 10420, "cost_usd": 0.00}
    }
}
```

### Get Daily Breakdown

```http
GET /v1/costs?start_date=2026-01-01&end_date=2026-01-07
```

Response:
```json
{
    "daily": [
        {"date": "2026-01-01", "cost_usd": 5.23, "requests": 2000},
        {"date": "2026-01-02", "cost_usd": 6.10, "requests": 2500},
        ...
    ]
}
```

### Get Budget Status

```http
GET /v1/budget
```

Response:
```json
{
    "daily": {
        "limit": 10.00,
        "used": 3.45,
        "remaining": 6.55,
        "percentage_used": 34.5
    },
    "monthly": {
        "limit": 200.00,
        "used": 45.23,
        "remaining": 154.77,
        "percentage_used": 22.6
    },
    "alerts": {
        "daily_warning_threshold": 0.8,
        "monthly_warning_threshold": 0.9
    }
}
```

---

## Budget Configuration

### Environment Variables

```yaml
# Daily budget limit (USD)
GENAI_BUDGET_DAILY=10.00

# Monthly budget limit (USD)
GENAI_BUDGET_MONTHLY=200.00

# Action when budget exceeded
GENAI_BUDGET_ACTION=warn  # "warn", "block", "fallback"

# Warning thresholds (percentage)
GENAI_BUDGET_WARN_DAILY=0.8
GENAI_BUDGET_WARN_MONTHLY=0.9

# Notification webhook
GENAI_BUDGET_WEBHOOK_URL=https://my-app/budget-alert
```

### Budget Actions

| Action | Behavior |
|--------|----------|
| `warn` | Log warning, allow request |
| `block` | Reject request with error |
| `fallback` | Route to free provider (Ollama) |

---

## Cost Optimization

### 1. Use Routing Strategies

```python
POST /v1/chat/completions
{
    "routing": {
        "strategy": "cost_optimized",
        "max_cost": 0.01
    }
}
```

### 2. Leverage Caching

Identical requests return cached responses (cost = $0).

```python
POST /v1/chat/completions
Headers: {"X-Cache-Control": "max-age=3600"}
```

### 3. Use Ollama for Development

```yaml
GENAI_DEFAULT_PROVIDER=ollama
GENAI_DEFAULT_MODEL=llama3.2:latest
```

### 4. Right-Size Models

| Use Case | Recommended Model | Cost Level |
|----------|-------------------|------------|
| Simple classification | gpt-4o-mini, llama3.2 | $ |
| Summarization | gpt-4o-mini, qwen2.5 | $ |
| Complex reasoning | gpt-4o, claude-sonnet | $$$ |
| Simple chat | llama3.2, mistral | Free |

---

## Storage Schema

```sql
CREATE TABLE daily_costs (
    date DATE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    capability VARCHAR(50),  -- "summarize", "extract", etc.
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(12, 6) DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    cache_hit_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    PRIMARY KEY (date, provider, model, capability)
);

CREATE INDEX idx_daily_costs_date ON daily_costs(date);
```

---

## Alerts

### Budget Warning

```json
{
    "type": "budget_warning",
    "level": "warning",
    "budget_type": "daily",
    "limit": 10.00,
    "current": 8.50,
    "percentage": 85,
    "timestamp": "2026-01-31T14:30:00Z"
}
```

### Budget Exceeded

```json
{
    "type": "budget_exceeded",
    "level": "critical",
    "budget_type": "daily",
    "limit": 10.00,
    "current": 10.23,
    "action_taken": "fallback_to_ollama",
    "timestamp": "2026-01-31T16:45:00Z"
}
```

---

## Related Docs

- [../capabilities/TIER_2_INTERMEDIATE.md](../capabilities/TIER_2_INTERMEDIATE.md) — Cost budgets capability
- [CACHING.md](CACHING.md) — Reduce costs with caching
