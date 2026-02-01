# GenAI Spine

**Unified GenAI service for the Spine ecosystem**

A standalone, Dockerized generative AI service providing a unified API for all LLM capabilities across Capture Spine, EntitySpine, FeedSpine, and Market Spine.

[![Tests](https://img.shields.io/badge/tests-80%20passed-brightgreen)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🎯 Overview

GenAI Spine provides a production-ready, provider-agnostic API for generative AI capabilities:

- **25 API Endpoints** covering chat, summarization, extraction, classification, and more
- **Multi-Provider Support** with Ollama (local), OpenAI, Anthropic
- **OpenAI-Compatible** API for drop-in integration
- **Cost Tracking** with per-request and aggregated usage statistics
- **Prompt Management** with CRUD, versioning, and template execution

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [TODO.md](TODO.md) | Implementation roadmap and status |
| [docs/CAPTURE_SPINE_INTEGRATION.md](docs/CAPTURE_SPINE_INTEGRATION.md) | Capture Spine feature mapping |
| [docs/ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) | Full ecosystem integration guide |
| [docs/capabilities/](docs/capabilities/) | Capability tiers and details |

**Reference:** `capture-spine/docs/features/productivity/` for feature requirements.

## 🧱 Ecosystem Integration

GenAI Spine reuses types from sibling packages for consistency:

```bash
# Install with ecosystem types
pip install genai-spine[ecosystem]
```

```python
# Uses entityspine's Result[T], ExecutionContext, ErrorCategory
from genai_spine.compat import Result, Ok, Err, ExecutionContext

result: Result[str] = Ok("success")
ctx = ExecutionContext(workflow_name="rewrite")
child_ctx = ctx.child(workflow_name="infer_title")  # Linked for tracing
```

See [ECOSYSTEM_INTEGRATION.md](docs/ECOSYSTEM_INTEGRATION.md) for full type mapping.

## Quick Start

### With Docker (Recommended)

```bash
# Start the full stack (API + Frontend + Ollama)
docker compose up -d

# Pull a model
docker compose exec ollama ollama pull llama3.2:latest

# Access the services
# - Frontend UI: http://localhost:5173
# - API: http://localhost:8100
# - Ollama: http://localhost:11434

# Test the API
curl http://localhost:8100/health
curl -X POST http://localhost:8100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:latest", "messages": [{"role": "user", "content": "Hello!"}]}'
```

**Hot Reload:** The frontend automatically reloads when you edit files in `frontend/src/`.

**Ports:**
- `5173` - Frontend (Vite dev server with hot reload)
- `8100` - API
- `11434` - Ollama

### With Capture Spine (Integrated)

GenAI Spine can be added to Capture Spine's dev/qa/prod environments:

```bash
cd capture-spine

# Start search stack first (provides Ollama)
docker compose -f docker-compose.search.yml up -d

# Start dev environment with GenAI Spine
docker compose --env-file .env.dev \
  -f docker-compose.dev.yml \
  -f docker-compose.genai.yml \
  --profile dev --profile genai up -d

# Test GenAI API
curl http://localhost:8100/health
curl http://localhost:8100/v1/models
```

The `docker-compose.genai.yml` file:
- Builds genai-spine from `../genai-spine`
- Connects to the shared `spine-ollama` instance
- Exposes port 8100 for the GenAI API
- Shares network with capture-spine services

### Local Development

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv pip install -e ".[dev]"

# Run with Ollama (must be running separately)
GENAI_OLLAMA_URL=http://localhost:11434 uvicorn genai_spine.main:app --reload --port 8100
```

## Features

- **Multi-Provider Support**: Ollama, OpenAI, Anthropic, AWS Bedrock
- **OpenAI-Compatible API**: Drop-in replacement for existing tools
- **Built-in Capabilities**: Summarize, Extract, Classify, Compare, **Rewrite**, **Title Inference**, **Commit Generation**
- **Prompt Management**: CRUD with versioning, database-agnostic storage
- **Cost Tracking**: Per-request and aggregated usage stats
- **Intelligent Routing**: Fallback chains, cost optimization

## API Endpoints

### OpenAI-Compatible
```
POST /v1/chat/completions    # Chat completion
POST /v1/completions         # Text completion
POST /v1/embeddings          # Embeddings
GET  /v1/models              # List models
```

### Native Capabilities
```
POST /v1/summarize           # Summarize text
POST /v1/extract             # Extract entities/key points
POST /v1/classify            # Classify content
POST /v1/compare             # Compare documents
POST /v1/rewrite             # Rewrite content (Message Enrichment)
POST /v1/infer-title         # Generate titles
POST /v1/generate-commit     # Generate commit messages (Work Sessions)
POST /v1/execute-prompt      # Execute any prompt template
```

### Prompt Management
```
GET  /v1/prompts             # List prompts
POST /v1/prompts             # Create prompt
GET  /v1/prompts/{id}        # Get prompt
PUT  /v1/prompts/{id}        # Update prompt
DELETE /v1/prompts/{id}      # Delete prompt
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GENAI_API_HOST` | `0.0.0.0` | API bind host |
| `GENAI_API_PORT` | `8100` | API port |
| `GENAI_DEFAULT_PROVIDER` | `ollama` | Default LLM provider |
| `GENAI_DEFAULT_MODEL` | `llama3.2:latest` | Default model |
| `GENAI_OLLAMA_URL` | `http://localhost:11434` | Ollama URL |
| `GENAI_OPENAI_API_KEY` | - | OpenAI API key |
| `GENAI_ANTHROPIC_API_KEY` | - | Anthropic API key |
| `GENAI_DATABASE_URL` | `sqlite:///data/genai.db` | Database URL |

## Integration Examples

### Python Client

```python
import httpx

client = httpx.Client(base_url="http://localhost:8100")

# Chat completion
response = client.post("/v1/chat/completions", json={
    "model": "llama3.2:latest",
    "messages": [{"role": "user", "content": "Explain quantum computing"}]
})
print(response.json()["choices"][0]["message"]["content"])

# Summarization
response = client.post("/v1/summarize", json={
    "content": "Long article text here...",
    "max_sentences": 3
})
print(response.json()["summary"])

# Entity extraction
response = client.post("/v1/extract", json={
    "content": "Apple CEO Tim Cook announced...",
    "entity_types": ["PERSON", "ORG"]
})
print(response.json()["entities"])
```

### From Capture Spine

```python
# In capture-spine, use GenAI Spine instead of direct provider calls
from httpx import AsyncClient

genai = AsyncClient(base_url="http://genai-spine:8100")

async def summarize_article(content: str) -> str:
    response = await genai.post("/v1/summarize", json={"content": content})
    return response.json()["summary"]
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GenAI Spine Service                                │
│                         http://localhost:8100                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                              FastAPI App                                     │
│                                                                              │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────┐   │
│  │   Health Routes   │  │   OpenAI Routes   │  │   Capability Routes   │   │
│  │  /health          │  │  /v1/chat         │  │  /v1/summarize        │   │
│  │  /ready           │  │  /v1/completions  │  │  /v1/extract          │   │
│  │  /v1/models       │  │  /v1/embeddings   │  │  /v1/classify         │   │
│  └───────────────────┘  └───────────────────┘  │  /v1/rewrite          │   │
│                                                 │  /v1/infer-title      │   │
│  ┌───────────────────┐  ┌───────────────────┐  │  /v1/generate-commit  │   │
│  │  Prompt Routes    │  │   Usage Routes    │  └───────────────────────┘   │
│  │  /v1/prompts      │  │  /v1/pricing      │                              │
│  │  (CRUD + Execute) │  │  /v1/usage        │                              │
│  └───────────────────┘  │  /v1/estimate     │                              │
│                         └───────────────────┘                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Service Layer                                      │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │ Provider Router │  │ Prompt Manager  │  │      Cost Tracker           │ │
│  │                 │  │                 │  │  - Per-request tracking     │ │
│  │ Smart routing   │  │ CRUD + versions │  │  - Aggregated stats         │ │
│  │ Fallback chains │  │ Variable subst  │  │  - Price estimation         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Provider Layer                                      │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │   Ollama    │  │   OpenAI    │  │  Anthropic  │  │   Groq (fallback)   ││
│  │   (local)   │  │   (cloud)   │  │   (cloud)   │  │                     ││
│  │   FREE      │  │   $$$       │  │   $$$       │  │   Free tier         ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────┤
│                          Storage Layer                                       │
│                                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │      SQLite         │  │     PostgreSQL      │  │     In-Memory       │ │
│  │  (Development)      │  │    (Production)     │  │     (Testing)       │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | Purpose | Location |
|-----------|---------|----------|
| **FastAPI App** | Main application entry | `src/genai_spine/main.py` |
| **Routes** | API endpoint handlers | `src/genai_spine/routes/` |
| **Services** | Business logic | `src/genai_spine/services/` |
| **Providers** | LLM integrations | `src/genai_spine/providers/` |
| **Storage** | Database abstraction | `src/genai_spine/storage/` |
| **Models** | Pydantic schemas | `src/genai_spine/models/` |

## 🚀 Recent Features (v0.1.0)

### Core Capabilities
- ✅ **Chat Completion** - OpenAI-compatible `/v1/chat/completions`
- ✅ **Summarization** - Condense text with configurable length
- ✅ **Entity Extraction** - Extract PERSON, ORG, LOCATION, DATE, MONEY, etc.
- ✅ **Classification** - Categorize content with custom labels
- ✅ **Rewrite** - Clean, format, organize, or summarize content
- ✅ **Title Inference** - Generate titles from content
- ✅ **Commit Generation** - Create git commit messages from diffs

### Infrastructure
- ✅ **Multi-provider routing** with fallback support
- ✅ **Prompt versioning** with full CRUD operations
- ✅ **Cost tracking** with estimation endpoints
- ✅ **Docker Compose** with Ollama + GPU support
- ✅ **SQLite + PostgreSQL** storage backends

## 🔧 In Development

| Feature | Status | Target |
|---------|--------|--------|
| Redis caching | 🔄 Planned | v0.2.0 |
| AWS Bedrock provider | 🔄 Planned | v0.2.0 |
| Streaming responses | 🔄 Planned | v0.2.0 |
| Batch processing | 🔄 Planned | v0.3.0 |
| RAG integration | 📋 Backlog | v0.4.0 |

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=genai_spine

# Lint
ruff check src/

# Type check
mypy src/
```

## 📁 Examples

The `examples/` directory contains scripts demonstrating all API features:

```bash
# Run all examples (requires Docker container running)
python examples/run_all_examples.py

# Run specific example
python examples/01_health_check.py
python examples/02_chat_completion.py
python examples/03_summarization.py
# ... etc

# Quick mode (single test per feature)
python examples/run_all_examples.py --quick

# Run only specific examples
python examples/run_all_examples.py --only 1 2 3
```

| Script | Feature |
|--------|---------|
| `01_health_check.py` | Health, readiness, model listing |
| `02_chat_completion.py` | OpenAI-compatible chat |
| `03_summarization.py` | Text summarization |
| `04_entity_extraction.py` | Extract PERSON, ORG, etc. |
| `05_classification.py` | Category classification |
| `06_rewrite.py` | Content rewriting modes |
| `07_title_inference.py` | Generate titles |
| `08_commit_generation.py` | Git commit messages |
| `09_prompt_management.py` | Prompt CRUD + versioning |
| `10_cost_tracking.py` | Pricing and usage stats |

## 🖥️ Frontend UI

A React frontend is available in `frontend/` for interactive testing:

```bash
cd frontend
npm install
npm run dev     # Start dev server on http://localhost:3000
```

Features:
- Health status monitoring
- Interactive chat interface
- **Multi-turn chat sessions** (v0.2.0)
- **Knowledge explorer** - browse prompts, sessions, usage (v0.2.0)
- Summarization with sample text
- Entity extraction with type selection
- Classification with custom categories
- Rewrite mode selection
- Title generation
- Commit message generation
- Prompt management viewer
- Usage and cost statistics

### E2E Tests

```bash
cd frontend
npm install
npx playwright install
npx playwright test
```

## License

MIT
