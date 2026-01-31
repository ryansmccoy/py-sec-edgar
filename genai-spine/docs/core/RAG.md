# Retrieval-Augmented Generation (RAG)

> Ground LLM responses in your data. Reduce hallucinations, increase accuracy.

---

## Overview

RAG combines retrieval (finding relevant documents) with generation (LLM response). Instead of relying solely on the model's training data, RAG retrieves relevant context from your documents.

```
User Query → Retrieval → Context + Query → LLM → Grounded Response
```

---

## Architecture

### Tier 2: Basic RAG

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Query  │────▶│   Embedder   │────▶│ Vector Store │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┘
                     │ Top K Documents
                     ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Response   │◀────│     LLM      │◀────│Context+Query │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Tier 3: Advanced RAG

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Query  │────▶│Query Rewrite │────▶│ Hybrid Search│
└──────────────┘     └──────────────┘     │ (BM25+Vector)│
                                          └──────┬───────┘
                                                  │
                     ┌────────────────────────────┘
                     │ Candidates
                     ▼
                     ┌──────────────┐
                     │   Reranker   │ Cross-encoder
                     └──────┬───────┘
                            │ Top K Reranked
                            ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Response   │◀────│     LLM      │◀────│Context+Query │
│  + Sources   │     │              │     │  + Metadata  │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## API Endpoints

### Index Documents

```http
POST /v1/rag/index
Content-Type: application/json

{
    "collection": "sec_filings",
    "documents": [
        {
            "id": "doc1",
            "content": "Apple Inc. 10-K filing...",
            "metadata": {
                "company": "Apple",
                "cik": "0000320193",
                "form": "10-K",
                "filed": "2025-10-30"
            }
        }
    ],
    "chunk_strategy": "semantic",
    "chunk_size": 512,
    "chunk_overlap": 50
}
```

### Query

```http
POST /v1/rag/query
Content-Type: application/json

{
    "query": "What are Apple's AI-related risks?",
    "collection": "sec_filings",
    "top_k": 5,
    "filters": {
        "form": "10-K",
        "filed_after": "2024-01-01"
    },
    "generate_answer": true,
    "cite_sources": true
}
```

**Response:**

```json
{
    "answer": "According to Apple's 2025 10-K filing, the company identifies several AI-related risks including [1]: competition from other AI platforms, regulatory uncertainty around AI usage, and dependence on third-party AI technologies [2].",
    "sources": [
        {
            "id": "chunk_123",
            "content": "The company faces significant competition in AI...",
            "metadata": {"form": "10-K", "section": "Risk Factors"},
            "relevance_score": 0.92,
            "citation_index": 1
        },
        {
            "id": "chunk_456",
            "content": "Regulatory developments regarding AI...",
            "metadata": {"form": "10-K", "section": "Risk Factors"},
            "relevance_score": 0.87,
            "citation_index": 2
        }
    ],
    "usage": {
        "retrieval_latency_ms": 45,
        "generation_latency_ms": 1200,
        "tokens": 850
    }
}
```

### Search Only (No Generation)

```http
POST /v1/rag/search
Content-Type: application/json

{
    "query": "revenue guidance",
    "collection": "sec_filings",
    "top_k": 10
}
```

### List Collections

```http
GET /v1/rag/collections
```

### Delete Documents

```http
DELETE /v1/rag/collections/{collection}/documents/{id}
```

---

## Chunking Strategies

### Semantic Chunking (Recommended)

Splits on semantic boundaries (paragraphs, sentences).

```python
{
    "chunk_strategy": "semantic",
    "chunk_size": 512,  # tokens
    "chunk_overlap": 50
}
```

### Fixed Size

Simple token-based splitting.

```python
{
    "chunk_strategy": "fixed",
    "chunk_size": 256,
    "chunk_overlap": 25
}
```

### Document Structure

Respects document hierarchy (sections, headers).

```python
{
    "chunk_strategy": "structure",
    "respect_sections": true,
    "max_section_size": 1000
}
```

---

## Vector Storage Options

### PostgreSQL + pgvector (Default)

```yaml
GENAI_VECTOR_STORE=pgvector
GENAI_DATABASE_URL=postgresql://localhost/genai
```

Pros: Single database, transactional, familiar
Cons: May need tuning for scale

### Qdrant

```yaml
GENAI_VECTOR_STORE=qdrant
GENAI_QDRANT_URL=http://localhost:6333
```

Pros: Purpose-built, fast, scalable
Cons: Additional service to manage

### Pinecone (Managed)

```yaml
GENAI_VECTOR_STORE=pinecone
GENAI_PINECONE_API_KEY=xxx
GENAI_PINECONE_ENVIRONMENT=us-east-1
```

Pros: Fully managed, highly scalable
Cons: Cost, vendor lock-in

---

## Embedding Models

| Model | Dimensions | Speed | Quality | Cost |
|-------|------------|-------|---------|------|
| `text-embedding-3-small` | 1536 | Fast | Good | $ |
| `text-embedding-3-large` | 3072 | Medium | Better | $$ |
| `nomic-embed-text` (Ollama) | 768 | Fast | Good | Free |
| `bge-large-en` | 1024 | Medium | Excellent | Free |

Configuration:

```yaml
GENAI_EMBEDDING_MODEL=text-embedding-3-small
GENAI_EMBEDDING_PROVIDER=openai
# or
GENAI_EMBEDDING_MODEL=nomic-embed-text
GENAI_EMBEDDING_PROVIDER=ollama
```

---

## Advanced Features

### Hybrid Search

Combine keyword (BM25) and semantic search.

```python
{
    "retrieval": {
        "strategy": "hybrid",
        "bm25_weight": 0.3,
        "semantic_weight": 0.7
    }
}
```

### Reranking

Use cross-encoder for more accurate ranking.

```python
{
    "retrieval": {
        "top_k": 20,  # Retrieve more initially
        "rerank": true,
        "rerank_top_k": 5,  # Return fewer after reranking
        "rerank_model": "cross-encoder/ms-marco-MiniLM-L-12-v2"
    }
}
```

### Query Rewriting

Expand or clarify queries.

```python
{
    "query_processing": {
        "rewrite": true,  # "AI risks" → "artificial intelligence risks challenges dangers"
        "expand": true,   # Add related terms
        "decompose": true # Split complex queries
    }
}
```

### Metadata Filtering

```python
{
    "filters": {
        "company": "Apple",
        "form": ["10-K", "10-Q"],
        "filed_after": "2024-01-01",
        "section": "Risk Factors"
    }
}
```

---

## RAG Prompts

Built-in prompts for RAG:

### rag-answer

```jinja2
Answer the question based on the provided context. If the context doesn't contain enough information, say so.

Context:
{% for doc in documents %}
[{{loop.index}}] {{doc.content}}
{% endfor %}

Question: {{query}}

Answer (cite sources using [n]):
```

### rag-summarize

```jinja2
Summarize the key information from these documents related to: {{query}}

Documents:
{% for doc in documents %}
---
Source: {{doc.metadata.source}}
{{doc.content}}
{% endfor %}

Summary:
```

---

## Performance Tuning

### Indexing Performance

```yaml
# Batch size for indexing
GENAI_RAG_INDEX_BATCH_SIZE=100

# Parallel embedding requests
GENAI_RAG_EMBEDDING_CONCURRENCY=5
```

### Query Performance

```yaml
# Cache embeddings for repeated queries
GENAI_RAG_CACHE_EMBEDDINGS=true

# Approximate nearest neighbor (faster, slightly less accurate)
GENAI_RAG_USE_ANN=true
GENAI_RAG_ANN_EF_SEARCH=100
```

### Memory Management

```yaml
# Maximum documents to keep in memory
GENAI_RAG_MAX_MEMORY_DOCS=10000

# Flush to disk threshold
GENAI_RAG_FLUSH_THRESHOLD=1000
```

---

## Integration with Other Spines

### Capture Spine

```python
# Index articles from Capture Spine
POST /v1/rag/index
{
    "collection": "news_articles",
    "documents": capture_spine_articles,
    "metadata_fields": ["source", "published_at", "categories"]
}
```

### EntitySpine

```python
# Include entity metadata in chunks
{
    "document": {
        "content": "...",
        "metadata": {
            "entities": ["Apple Inc.", "Tim Cook"],
            "entity_ids": ["entity:0000320193", "person:tim-cook"]
        }
    }
}
```

### FeedSpine

```python
# Index earnings call transcripts
{
    "collection": "earnings_calls",
    "documents": feedspine_transcripts,
    "chunk_strategy": "speaker_turns"  # Special strategy for transcripts
}
```

---

## Evaluation

### Retrieval Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Recall@K | % of relevant docs in top K | > 80% |
| MRR | Mean Reciprocal Rank | > 0.7 |
| NDCG | Normalized Discounted Cumulative Gain | > 0.8 |

### Generation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Faithfulness | Answer grounded in context | > 90% |
| Relevance | Answer addresses question | > 85% |
| Citation Accuracy | Citations match claims | > 95% |

---

## Related Docs

- [TIER_2_INTERMEDIATE.md](../capabilities/TIER_2_INTERMEDIATE.md) — Basic RAG capability
- [TIER_3_ADVANCED.md](../capabilities/TIER_3_ADVANCED.md) — Advanced RAG with reranking
- [COST_TRACKING.md](COST_TRACKING.md) — Embedding costs
