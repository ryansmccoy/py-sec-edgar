# Deployment Tiers

> Choose the right deployment complexity for your needs.

---

## Tier Overview

| Tier | Name | Cost | Complexity | Best For |
|------|------|------|------------|----------|
| **1** | Basic | Free | Low | Development, testing, privacy |
| **2** | Intermediate | $$ | Medium | Production, cost-conscious |
| **3** | Advanced | $$$ | High | Enterprise, high-volume |
| **4** | Mind-Blowing | $$$$ | Very High | Cutting-edge, autonomous |

---

## Tier 1: Basic (Ollama-Only)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Compose                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐        ┌─────────────────────────────┐ │
│  │ GenAI Spine │───────▶│         Ollama              │ │
│  │  Port 8100  │        │ llama3.2 / qwen2.5 / mistral│ │
│  └─────────────┘        │       Port 11434            │ │
│         │               └─────────────────────────────┘ │
│         ▼                                               │
│  ┌─────────────┐                                        │
│  │   SQLite    │                                        │
│  │  ./data/    │                                        │
│  └─────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

### Features

- ✅ Zero API costs
- ✅ Single Docker Compose command
- ✅ Full privacy (all data local)
- ✅ ~50-100 tokens/sec on GPU
- ❌ Limited model selection
- ❌ No redundancy/fallback

### Requirements

- 8GB+ GPU VRAM (for small models)
- 16GB+ for larger models (mistral-nemo, llama3.1)
- Docker with GPU support

### docker-compose.yml

```yaml
version: '3.8'

services:
  genai-api:
    build: .
    ports:
      - "8100:8100"
    environment:
      - GENAI_DEFAULT_PROVIDER=ollama
      - GENAI_OLLAMA_URL=http://ollama:11434
      - GENAI_DATABASE_URL=sqlite:///data/genai.db
    volumes:
      - ./data:/app/data
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

---

## Tier 2: Intermediate (Multi-Provider)

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐                                            │
│  │   GenAI Spine   │                                            │
│  │    Port 8100    │                                            │
│  └────────┬────────┘                                            │
│           │                                                      │
│     ┌─────┴─────┬─────────────┬─────────────┐                   │
│     ▼           ▼             ▼             ▼                   │
│  ┌──────┐  ┌────────┐  ┌──────────┐  ┌───────────┐             │
│  │Ollama│  │OpenAI  │  │Anthropic │  │ Bedrock   │             │
│  │Local │  │API     │  │API       │  │ (AWS)     │             │
│  └──────┘  └────────┘  └──────────┘  └───────────┘             │
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                    │
│  │   PostgreSQL    │     │      Redis      │                    │
│  │   (state)       │     │   (cache)       │                    │
│  └─────────────────┘     └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Features

- ✅ Intelligent provider routing
- ✅ Fallback chains (Ollama → OpenAI → Anthropic)
- ✅ Response caching (Redis)
- ✅ Cost tracking & budgets
- ✅ Production-ready

### Additional Configuration

```yaml
# .env
GENAI_DEFAULT_PROVIDER=ollama
GENAI_OPENAI_API_KEY=sk-...
GENAI_ANTHROPIC_API_KEY=sk-ant-...
GENAI_FALLBACK_CHAIN=ollama,openai,anthropic
GENAI_REDIS_URL=redis://redis:6379
GENAI_DATABASE_URL=postgresql://user:pass@db:5432/genai
GENAI_BUDGET_DAILY=10.00
```

### Routing Strategies

| Strategy | Behavior |
|----------|----------|
| `local_first` | Try Ollama, fallback to cloud |
| `cost_optimized` | Cheapest that meets requirements |
| `quality` | Best model regardless of cost |
| `speed` | Fastest response time |

---

## Tier 3: Advanced (Production Scale)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Kubernetes / ECS                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                   Load Balancer / API Gateway                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                    │                            │                    │
│            ┌───────┴───────┐          ┌────────┴────────┐           │
│            ▼               ▼          ▼                 ▼           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐│
│  │  GenAI API   │  │  GenAI API   │  │ SSE Worker   │  │  Batch   ││
│  │  Instance 1  │  │  Instance 2  │  │ (streaming)  │  │  Worker  ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘│
│            │               │                  │              │      │
│            └───────────────┼──────────────────┼──────────────┘      │
│                            ▼                  ▼                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Provider Router                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │ Ollama  │ │ OpenAI  │ │Anthropic│ │ Bedrock │ │  Groq   │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────────┐   │
│  │  PostgreSQL    │ │ Redis Cluster  │ │   Vector Store         │   │
│  │  (RDS/Aurora)  │ │ (ElastiCache)  │ │   (pgvector/Pinecone)  │   │
│  └────────────────┘ └────────────────┘ └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Features

- ✅ Horizontal scaling
- ✅ SSE streaming workers
- ✅ Batch processing queue
- ✅ Vector store for RAG
- ✅ Multi-region capable
- ✅ Audit logging
- ✅ A/B testing

### Infrastructure Requirements

- Kubernetes cluster or ECS
- Managed PostgreSQL (RDS Aurora)
- Managed Redis (ElastiCache)
- Vector database (pgvector or Pinecone)
- GPU nodes for Ollama (optional)

---

## Tier 4: Mind-Blowing (Agentic Platform)

### Architecture

See [TIER_4_MINDBLOWING.md](../capabilities/TIER_4_MINDBLOWING.md) for full vision.

Adds:
- Agent orchestration layer
- Tool registry
- Knowledge graph (Neo4j)
- Real-time event streaming (Kafka/NATS)
- Continuous learning pipeline

---

## Tier Selection Guide

| Scenario | Recommended Tier |
|----------|------------------|
| Local development | Tier 1 |
| Small team, limited budget | Tier 1 |
| Production, cost-conscious | Tier 2 |
| Enterprise, compliance needs | Tier 3 |
| Research/experimental | Tier 4 |

---

## Migration Path

```
Tier 1 → Tier 2
├── Add API keys for cloud providers
├── Switch SQLite → PostgreSQL
├── Add Redis for caching
└── Configure fallback chains

Tier 2 → Tier 3
├── Containerize for Kubernetes
├── Add load balancer
├── Split API/worker services
├── Add vector store for RAG
└── Implement monitoring/alerting

Tier 3 → Tier 4
├── Add agent framework
├── Integrate knowledge graph
├── Set up event streaming
└── Implement continuous learning
```

---

## Related Docs

- [OVERVIEW.md](OVERVIEW.md) — Architecture overview
- [PROVIDERS.md](PROVIDERS.md) — Provider details
- [../guides/DEPLOYMENT.md](../guides/DEPLOYMENT.md) — Deployment guide
