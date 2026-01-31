# Tier 2: Intermediate Capabilities

> Enhanced features for common use cases. Build these after Tier 1 is solid.

---

## Overview

| # | Capability | Description | Status | Priority |
|---|------------|-------------|--------|----------|
| 1 | Sentiment Analysis | Content → sentiment score | 🔴 | High |
| 2 | Question Answering | Context + question → answer | 🔴 | High |
| 3 | Content Tagging | Document → auto-generated tags | 🔴 | Medium |
| 4 | Language Detection | Text → language code | 🔴 | Medium |
| 5 | Translation | Text → translated text | 🔴 | Medium |
| 6 | Paraphrasing | Text → rewritten text | 🔴 | Medium |
| 7 | Grammar Correction | Text → corrected text | 🔴 | Low |
| 8 | Response Caching | Cache identical requests | 🔴 | High |
| 9 | Provider Routing | Intelligent model selection | 🔴 | High |
| 10 | Provider Fallback | Automatic failover | 🔴 | High |
| 11 | SSE Streaming | Real-time token streaming | 🔴 | High |
| 12 | RAG (Basic) | Retrieval-Augmented Generation | 🔴 | High |
| 13 | Embeddings API | Text → vector embeddings | 🔴 | High |
| 14 | Similarity Search | Find similar content | 🔴 | Medium |
| 15 | Cost Budgets | Daily/monthly limits | 🔴 | Medium |

---

## 1. Sentiment Analysis

**Endpoint:** `POST /v1/analyze/sentiment`

Analyze emotional tone of text.

```python
response = await client.post("/v1/analyze/sentiment", json={
    "content": "The quarterly results exceeded expectations...",
    "granularity": "sentence",  # or "document", "aspect"
    "aspects": ["product", "management", "outlook"]  # optional
})
```

**Response:**
```json
{
    "sentiment": {
        "label": "positive",
        "score": 0.85,
        "confidence": 0.92
    },
    "aspects": [
        {"aspect": "outlook", "sentiment": "positive", "score": 0.9},
        {"aspect": "management", "sentiment": "neutral", "score": 0.5}
    ],
    "sentences": [
        {"text": "The quarterly results...", "sentiment": "positive", "score": 0.85}
    ]
}
```

**Use cases:**
- News sentiment tracking
- Customer feedback analysis
- Social media monitoring
- Earnings call tone analysis

---

## 2. Question Answering

**Endpoint:** `POST /v1/qa`

Answer questions given context.

```python
response = await client.post("/v1/qa", json={
    "context": "Apple Inc. reported Q4 revenue of $94.9B, up 8% YoY...",
    "question": "What was Apple's Q4 revenue?",
    "require_evidence": True
})
```

**Response:**
```json
{
    "answer": "$94.9 billion",
    "confidence": 0.95,
    "evidence": {
        "text": "Apple Inc. reported Q4 revenue of $94.9B",
        "start": 0,
        "end": 40
    },
    "answerable": true
}
```

**Features:**
- Extractive (pull from context)
- Abstractive (generate answer)
- Evidence highlighting
- Confidence scoring
- "Unanswerable" detection

---

## 3. Content Tagging

**Endpoint:** `POST /v1/tag`

Auto-generate relevant tags.

```python
response = await client.post("/v1/tag", json={
    "content": "Tesla's new battery technology promises...",
    "max_tags": 5,
    "tag_types": ["topic", "entity", "keyword"],
    "existing_tags": ["technology", "automotive"]  # suggest similar
})
```

**Response:**
```json
{
    "tags": [
        {"tag": "electric-vehicles", "type": "topic", "confidence": 0.95},
        {"tag": "Tesla", "type": "entity", "confidence": 0.99},
        {"tag": "battery-technology", "type": "topic", "confidence": 0.88},
        {"tag": "innovation", "type": "keyword", "confidence": 0.72}
    ]
}
```

---

## 4. Language Detection

**Endpoint:** `POST /v1/detect/language`

Identify text language.

```python
response = await client.post("/v1/detect/language", json={
    "content": "Bonjour, comment allez-vous?"
})
```

**Response:**
```json
{
    "language": "fr",
    "language_name": "French",
    "confidence": 0.98,
    "alternatives": [
        {"language": "ca", "confidence": 0.02}
    ]
}
```

---

## 5. Translation

**Endpoint:** `POST /v1/translate`

Translate between languages.

```python
response = await client.post("/v1/translate", json={
    "content": "Hello, how are you?",
    "target_language": "es",
    "source_language": "en",  # optional, auto-detect
    "preserve_formatting": True
})
```

**Response:**
```json
{
    "translation": "Hola, ¿cómo estás?",
    "source_language": "en",
    "target_language": "es"
}
```

---

## 6. Paraphrasing

**Endpoint:** `POST /v1/paraphrase`

Rewrite text with different wording.

```python
response = await client.post("/v1/paraphrase", json={
    "content": "The company's revenue increased significantly.",
    "style": "formal",  # "casual", "technical", "simplified"
    "variations": 3
})
```

**Response:**
```json
{
    "paraphrases": [
        "The organization experienced substantial revenue growth.",
        "Corporate earnings saw a marked increase.",
        "The firm's income rose considerably."
    ]
}
```

---

## 7. Grammar Correction

**Endpoint:** `POST /v1/correct`

Fix grammar and spelling.

```python
response = await client.post("/v1/correct", json={
    "content": "Their going to the store yesterday.",
    "explain_corrections": True
})
```

**Response:**
```json
{
    "corrected": "They're going to the store yesterday.",
    "corrections": [
        {
            "original": "Their",
            "corrected": "They're",
            "explanation": "Use 'they're' (they are) instead of possessive 'their'",
            "position": {"start": 0, "end": 5}
        }
    ]
}
```

---

## 8. Response Caching

Cache identical requests to reduce latency and cost.

```python
# Request with cache control
response = await client.post("/v1/chat/completions", json={
    "model": "gpt-4o-mini",
    "messages": [...],
}, headers={
    "X-Cache-Control": "max-age=3600"  # cache for 1 hour
})

# Response includes cache status
# X-Cache: HIT or X-Cache: MISS
```

**Configuration:**
```yaml
# Environment variables
GENAI_CACHE_ENABLED=true
GENAI_CACHE_TTL=3600
GENAI_CACHE_BACKEND=redis  # or "memory"
GENAI_REDIS_URL=redis://localhost:6379
```

---

## 9. Provider Routing

Intelligent model selection based on criteria.

```python
response = await client.post("/v1/chat/completions", json={
    "messages": [...],
    "routing": {
        "strategy": "cost_optimized",  # or "quality", "speed", "balanced"
        "max_cost": 0.01,
        "preferred_providers": ["ollama", "openai"]
    }
})
```

**Routing strategies:**
| Strategy | Behavior |
|----------|----------|
| `cost_optimized` | Cheapest model that meets requirements |
| `quality` | Best model regardless of cost |
| `speed` | Fastest response time |
| `balanced` | Balance of cost, quality, speed |

---

## 10. Provider Fallback

Automatic failover when provider fails.

```python
# Configuration
GENAI_FALLBACK_CHAIN=ollama,openai,anthropic

# If Ollama fails, automatically try OpenAI, then Anthropic
```

**Features:**
- Configurable fallback order
- Circuit breaker pattern
- Retry with exponential backoff
- Health check integration

---

## 11. SSE Streaming

Real-time token streaming for chat.

```python
# Request
POST /v1/chat/completions
{"model": "llama3.2:latest", "messages": [...], "stream": true}

# Response (Server-Sent Events)
data: {"choices": [{"delta": {"content": "Hello"}}]}
data: {"choices": [{"delta": {"content": " there"}}]}
data: {"choices": [{"delta": {"content": "!"}}]}
data: [DONE]
```

**Benefits:**
- Immediate feedback
- Better UX for long responses
- Early termination support

---

## 12. RAG (Basic)

**Endpoint:** `POST /v1/rag/query`

Retrieve context before generation.

```python
response = await client.post("/v1/rag/query", json={
    "query": "What is Apple's revenue guidance for Q1?",
    "collection": "sec_filings",
    "top_k": 5,
    "generate_answer": True
})
```

**Response:**
```json
{
    "answer": "Apple provided Q1 revenue guidance of $117-121B...",
    "sources": [
        {
            "content": "...management expects revenue between...",
            "metadata": {"filing": "10-K", "date": "2025-10-30"},
            "relevance_score": 0.92
        }
    ]
}
```

See [core/RAG.md](../core/RAG.md) for detailed RAG architecture.

---

## 13. Embeddings API

**Endpoint:** `POST /v1/embeddings`

Generate vector embeddings.

```python
response = await client.post("/v1/embeddings", json={
    "input": ["Text to embed", "Another text"],
    "model": "text-embedding-3-small"
})
```

**Response:**
```json
{
    "embeddings": [
        {"index": 0, "embedding": [0.123, -0.456, ...]},
        {"index": 1, "embedding": [0.789, -0.012, ...]}
    ],
    "model": "text-embedding-3-small",
    "usage": {"total_tokens": 12}
}
```

---

## 14. Similarity Search

**Endpoint:** `POST /v1/search/similar`

Find similar content using embeddings.

```python
response = await client.post("/v1/search/similar", json={
    "query": "electric vehicle market trends",
    "collection": "articles",
    "top_k": 10,
    "min_similarity": 0.7
})
```

---

## 15. Cost Budgets

Set spending limits.

```python
# Configuration
GENAI_BUDGET_DAILY=10.00  # $10/day limit
GENAI_BUDGET_MONTHLY=200.00  # $200/month limit
GENAI_BUDGET_ACTION=warn  # or "block"
```

**Endpoint:** `GET /v1/budget`

```json
{
    "daily": {"limit": 10.00, "used": 3.45, "remaining": 6.55},
    "monthly": {"limit": 200.00, "used": 45.23, "remaining": 154.77}
}
```

---

## Implementation Priority

1. **High Priority** (do first):
   - SSE Streaming
   - RAG (Basic) + Embeddings
   - Provider Routing/Fallback
   - Response Caching

2. **Medium Priority**:
   - Sentiment Analysis
   - Question Answering
   - Similarity Search

3. **Lower Priority**:
   - Translation, Paraphrasing
   - Grammar Correction
   - Language Detection
