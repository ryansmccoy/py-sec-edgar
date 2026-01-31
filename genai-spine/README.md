# GenAI Spine

**Unified GenAI service for the Spine ecosystem**

A standalone, Dockerized generative AI service providing a unified API for all LLM capabilities across Capture Spine, EntitySpine, FeedSpine, and Market Spine.

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
# Start the stack (API + Ollama)
docker compose up -d

# Pull a model
docker compose exec ollama ollama pull llama3.2:latest

# Test it
curl http://localhost:8100/health
curl -X POST http://localhost:8100/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:latest", "messages": [{"role": "user", "content": "Hello!"}]}'
```

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
┌─────────────────────────────────────────────────────────────┐
│                     GenAI Spine API                          │
│                      (FastAPI)                               │
├─────────────────────────────────────────────────────────────┤
│  /v1/chat/completions  │  /v1/summarize  │  /v1/prompts     │
├─────────────────────────────────────────────────────────────┤
│                    Provider Router                           │
│   ┌─────────┬─────────┬─────────┬─────────┬─────────────┐  │
│   │ Ollama  │ OpenAI  │Anthropic│ Bedrock │   Groq      │  │
│   │ (local) │ (fast)  │ (smart) │  (AWS)  │ (fallback)  │  │
│   └─────────┴─────────┴─────────┴─────────┴─────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Prompt Manager  │  Cost Tracker  │  Cache (Redis)         │
├─────────────────────────────────────────────────────────────┤
│              SQLite / PostgreSQL Storage                     │
└─────────────────────────────────────────────────────────────┘
```

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

## License

MIT
