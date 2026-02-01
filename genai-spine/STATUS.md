# GenAI Spine - Current Status

**Last Updated:** 2026-01-31
**Version:** 0.2.0
**Status:** ✅ Production-Ready Core + Chat Sessions

---

## 📊 Executive Summary

GenAI Spine is the **unified AI service** for the Spine ecosystem. It provides a single, consistent API for all LLM capabilities across Capture Spine, EntitySpine, FeedSpine, and Market Spine.

| Metric | Status |
|--------|--------|
| **API Endpoints** | 31 available (↑6 new) |
| **Providers** | 3 (Ollama, OpenAI, Anthropic) |
| **Test Coverage** | 91 tests passing (↑11) |
| **Database Backends** | SQLite (dev) + PostgreSQL (prod) |
| **Client Library** | Python client with types ✅ |

---

## 🆕 What's New in v0.2.0

- **Chat Sessions API** - Stateful conversations with history (Tier A - Stable)
- **Python Client Library** - Typed HTTP wrapper (`genai_spine_client`)
- **Integration Docs** - Comprehensive guides for consumer apps
- **API Tiers** - Clear stability guarantees (Tier A vs Tier B)

---

## 🚀 Available API Endpoints

### Health & Status
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/health` | GET | Health check | ✅ |
| `/ready` | GET | Readiness check | ✅ |

### Models
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/models` | GET | List available models | ✅ |
| `/v1/models/{model_id}` | GET | Get model info | ✅ |

### Completions (OpenAI-Compatible)
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/completions` | POST | Text completion | ✅ |
| `/v1/chat/completions` | POST | Chat completion | ✅ |

### Chat Sessions (Tier A - Stable) 🆕
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/sessions` | POST | Create chat session | ✅ |
| `/v1/sessions` | GET | List sessions | ✅ |
| `/v1/sessions/{id}` | GET | Get session | ✅ |
| `/v1/sessions/{id}` | DELETE | Delete session | ✅ |
| `/v1/sessions/{id}/messages` | POST | Send message | ✅ |
| `/v1/sessions/{id}/messages` | GET | Get messages | ✅ |

### Native Capabilities (Tier B - Convenience)
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/summarize` | POST | Summarize text | ✅ |
| `/v1/extract` | POST | Extract entities/key points | ✅ |
| `/v1/classify` | POST | Classify content | ✅ |
| `/v1/rewrite` | POST | Rewrite content (Message Enrichment) | ✅ |
| `/v1/infer-title` | POST | Generate titles | ✅ |
| `/v1/generate-commit` | POST | Generate commit messages | ✅ |

### Prompt Execution (Tier A - Stable)
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/execute-prompt` | POST | Execute any prompt template | ✅ |

### Prompt Management
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/prompts` | GET | List prompts | ✅ |
| `/v1/prompts` | POST | Create prompt | ✅ |
| `/v1/prompts/{id}` | GET | Get prompt | ✅ |
| `/v1/prompts/{id}` | PUT | Update prompt | ✅ |
| `/v1/prompts/{id}` | DELETE | Delete prompt | ✅ |
| `/v1/prompts/slug/{slug}` | GET | Get prompt by slug | ✅ |
| `/v1/prompts/{id}/versions` | GET | List prompt versions | ✅ |
| `/v1/prompts/{id}/versions/{v}` | GET | Get specific version | ✅ |

### Usage & Cost Tracking
| Endpoint | Method | Description | Status |
|----------|--------|-------------|--------|
| `/v1/usage` | GET | Usage stats (with date filters) | ✅ |
| `/v1/pricing` | GET | List model pricing | ✅ |
| `/v1/pricing/{model}` | GET | Get model pricing | ✅ |
| `/v1/estimate-cost` | POST | Estimate cost before execution | ✅ |

---

## 📚 Client Library

**Location:** `genai-spine/client/genai_spine_client/`

```python
from genai_spine_client import GenAIClient

async with GenAIClient(base_url="http://localhost:8100") as client:
    # Chat session
    session = await client.create_session(model="gpt-4o-mini")
    reply = await client.send_message(session.id, "Hello!")

    # Execute prompt
    result = await client.execute_prompt(
        slug="summarizer",
        variables={"text": content}
    )
```

**Installation:**
- Copy module to your app
- Or use local path: `pip install -e ../genai-spine/client`

---

## 🔌 Supported Providers

| Provider | Status | Models | Config |
|----------|--------|--------|--------|
| **Ollama** | ✅ Production | llama3.2, mistral, codellama, etc. | `GENAI_OLLAMA_URL` |
| **OpenAI** | ✅ Production | gpt-4o, gpt-4-turbo, gpt-3.5-turbo | `GENAI_OPENAI_API_KEY` |
| **Anthropic** | ✅ Production | claude-3-opus, sonnet, haiku | `GENAI_ANTHROPIC_API_KEY` |
| **AWS Bedrock** | 🔴 Not Started | claude, titan, llama | Planned P1 |

---

## 💾 Storage Backends

| Backend | Status | Use Case |
|---------|--------|----------|
| **SQLite** | ✅ Production | Local development, single-server |
| **PostgreSQL** | ✅ Production | Multi-server, high availability |
| **In-Memory** | ✅ Production | Testing only |

---

## 🧪 Test Coverage

```
80 passed, 5 skipped in 1.77s

Tests by Module:
- test_storage.py: 57 tests (CRUD, versioning, soft delete)
- test_capabilities.py: 10 tests (summarize, extract, classify)
- test_cost.py: 5 tests (pricing, calculate_cost)
- test_usage.py: 5 tests (usage API endpoints)
- test_anthropic.py: 5 tests (3 skip without API key)
- test_registry.py: 3 tests (provider registration)
```

---

## 📁 Project Structure

```
genai-spine/
├── src/genai_spine/
│   ├── api/
│   │   ├── routers/         # FastAPI routers (25 endpoints)
│   │   ├── app.py           # FastAPI app factory
│   │   ├── deps.py          # Dependency injection
│   │   └── tracking.py      # Execution tracking
│   ├── capabilities/
│   │   ├── classification.py
│   │   ├── commit.py        # Commit message generation
│   │   ├── cost.py          # Cost calculation
│   │   ├── extraction.py
│   │   ├── rewrite.py       # Rewrite & title inference
│   │   └── summarization.py
│   ├── providers/
│   │   ├── anthropic.py     # Claude models
│   │   ├── base.py          # Provider protocol
│   │   ├── ollama.py        # Local models
│   │   ├── openai.py        # GPT models
│   │   └── registry.py      # Provider registry
│   └── storage/
│       ├── models.py        # SQLAlchemy models
│       ├── protocols.py     # Repository protocols
│       ├── schemas.py       # Pydantic schemas
│       ├── seed.py          # Default prompts
│       ├── sqlite.py        # SQLite backend
│       └── postgres.py      # PostgreSQL backend
├── tests/
├── docs/
├── prompts/                 # Alignment prompts for agents
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## 🛣️ Roadmap

### P1 - Next 2 Weeks
| Feature | Status | Notes |
|---------|--------|-------|
| Alembic migrations | 🟡 In Progress | Schema evolution for production |
| Bedrock provider | 🔴 Not Started | AWS SDK integration |
| Streaming support | 🔴 Not Started | SSE for chat completions |

### P2 - Next Month
| Feature | Status | Notes |
|---------|--------|-------|
| Redis caching | 🔴 Not Started | Response caching |
| Rate limiting | 🔴 Not Started | Per-provider limits |
| Batch processing | 🔴 Not Started | Process multiple items |
| Version comparison | 🔴 Not Started | Side-by-side diff |

### Future Vision (P3+)
- Document comparison
- Multi-document synthesis
- Chain-of-thought prompting
- RAG integration
- Autonomous agents

---

## 🔗 Ecosystem Integration

GenAI Spine integrates with all Spine ecosystem projects:

| Project | Integration Status | Key Endpoints Used |
|---------|-------------------|-------------------|
| **Capture Spine** | ✅ Ready | `/v1/rewrite`, `/v1/infer-title`, `/v1/generate-commit` |
| **FeedSpine** | 🟡 Planned | `/v1/summarize`, `/v1/classify`, `/v1/extract` |
| **EntitySpine** | 🟡 Planned | Uses Result[T], ExecutionContext types |
| **Spine-Core** | 🟡 Planned | Pipeline patterns, QualityRunner |

See [ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) for detailed integration guide.

---

## 🚀 Quick Start

```bash
# With Docker
docker compose up -d
curl http://localhost:8100/health

# Local Development
pip install -e ".[dev]"
uvicorn genai_spine.main:app --reload --port 8100
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Quick start and overview |
| [TODO.md](TODO.md) | Implementation roadmap |
| [docs/CAPTURE_SPINE_INTEGRATION.md](docs/CAPTURE_SPINE_INTEGRATION.md) | Capture Spine feature mapping |
| [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) | Full ecosystem guide |
| [docs/capabilities/](docs/capabilities/) | Capability tier details |
| [prompts/](prompts/) | Agent alignment prompts |
