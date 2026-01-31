# GenAI Spine Implementation Prompt

Use this prompt with an AI coding assistant to build the GenAI Spine service.

---

## Context

I have a multi-project Python workspace for financial data processing:

### The "Spine" Ecosystem

1. **Capture Spine** (`capture-spine/`) - News/feed capture platform with:
   - Multi-provider LLM support (OpenAI, Anthropic, Bedrock, Ollama)
   - Chat conversations API
   - Prompt management with versioning
   - Feed categorization
   - Entity extraction (basic)
   - Cost tracking

2. **EntitySpine** (`entityspine/`) - Entity resolution for SEC data:
   - Resolve tickers, CIKs, CUSIPs to canonical entities
   - Knowledge graph for companies, people, relationships
   - Tiered storage (JSON → SQLite → DuckDB → PostgreSQL)

3. **FeedSpine** (`feedspine/`) - Feed collection framework:
   - Storage-agnostic, executor-agnostic
   - Automatic deduplication
   - Medallion architecture (Bronze → Silver → Gold)
   - Pluggable enrichers

4. **Market Spine** (`market-spine/`) - Financial market data:
   - TimescaleDB for time-series
   - Trading desktop with FlexLayout
   - OTC transparency data
   - Price/volume analytics

### Current LLM Code Location

The existing LLM infrastructure is in `capture-spine/app/llm/`:
- `providers/base.py` - Abstract LLM client interface
- `providers/openai.py` - OpenAI implementation
- `providers/anthropic.py` - Anthropic implementation
- `providers/bedrock.py` - AWS Bedrock implementation
- `providers/ollama.py` - Local Ollama implementation
- `prompts.py` - Prompt templates
- `cost.py` - Token counting & cost calculation
- `types.py` - Request/response models

---

## Task

Create a standalone **GenAI Spine** service that:

1. **Extracts and consolidates** all LLM/GenAI logic from Capture Spine
2. **Provides a unified REST API** for all AI capabilities
3. **Runs as a Docker container** alongside Ollama
4. **Supports multiple providers** (Ollama, OpenAI, Anthropic, Bedrock)
5. **Manages prompts** with versioning and CRUD operations
6. **Tracks costs** and usage per provider/model
7. **Integrates seamlessly** with all Spine projects

---

## Requirements

### API Endpoints

```
# Health
GET  /health
GET  /ready

# OpenAI-Compatible (drop-in replacement)
POST /v1/chat/completions
POST /v1/completions
POST /v1/embeddings
GET  /v1/models

# Native Capabilities
POST /v1/summarize
POST /v1/extract
POST /v1/classify
POST /v1/compare

# Prompt Management
GET  /v1/prompts
POST /v1/prompts
GET  /v1/prompts/{id}
PUT  /v1/prompts/{id}
DELETE /v1/prompts/{id}
GET  /v1/prompts/{id}/versions

# Usage & Costs
GET  /v1/usage
GET  /v1/costs
```

### Provider Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class CompletionRequest:
    messages: list[dict]
    model: str | None = None
    temperature: float = 0.1
    max_tokens: int | None = None
    output_schema: dict | None = None  # For structured output

@dataclass
class CompletionResponse:
    content: str
    parsed: dict | None = None  # If output_schema provided
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    provider: str = ""
    model: str = ""

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        pass

    @abstractmethod
    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        pass
```

### Database Schema (SQLite/PostgreSQL)

```sql
-- Prompt templates
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    category VARCHAR(50),
    tags TEXT[],
    variables JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prompt versions (immutable)
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    prompt_id UUID REFERENCES prompts(id),
    version INTEGER NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    change_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Execution history
CREATE TABLE executions (
    id UUID PRIMARY KEY,
    prompt_id UUID REFERENCES prompts(id),
    prompt_version INTEGER,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cost tracking by day
CREATE TABLE daily_costs (
    date DATE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    total_input_tokens BIGINT DEFAULT 0,
    total_output_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(12, 6) DEFAULT 0,
    request_count INTEGER DEFAULT 0,
    PRIMARY KEY (date, provider, model)
);
```

### Configuration

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8100

    # Default provider
    default_provider: str = "ollama"
    default_model: str = "llama3.2:latest"

    # Ollama
    ollama_url: str = "http://localhost:11434"

    # OpenAI (optional)
    openai_api_key: str | None = None

    # Anthropic (optional)
    anthropic_api_key: str | None = None

    # AWS Bedrock (optional)
    bedrock_region: str = "us-east-1"

    # Database
    database_url: str = "sqlite:///data/genai.db"

    # Redis (optional)
    redis_url: str | None = None

    class Config:
        env_prefix = "GENAI_"
```

### Docker Compose

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
      - ./prompts:/app/prompts  # Default prompt library
    depends_on:
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 30s
      timeout: 10s
      retries: 3
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

## Project Structure

Create this structure:

```
genai-spine/
├── docker-compose.yml
├── docker-compose.dev.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── Makefile
│
├── src/genai_spine/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── settings.py          # Configuration
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py           # FastAPI app
│   │   ├── deps.py          # Dependencies
│   │   └── routers/
│   │       ├── health.py
│   │       ├── completions.py
│   │       ├── chat.py
│   │       ├── capabilities.py  # summarize, extract, classify
│   │       ├── prompts.py
│   │       └── models.py
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── ollama.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── bedrock.py
│   │
│   ├── capabilities/
│   │   ├── __init__.py
│   │   ├── summarization.py
│   │   ├── extraction.py
│   │   ├── classification.py
│   │   └── comparison.py
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── renderer.py
│   │   └── library/          # Default prompts
│   │       ├── summarize.yaml
│   │       ├── extract.yaml
│   │       └── classify.yaml
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── sqlite.py
│   │   └── models.py
│   │
│   └── observability/
│       ├── __init__.py
│       ├── cost.py
│       └── metrics.py
│
├── tests/
│   ├── conftest.py
│   ├── test_providers/
│   ├── test_capabilities/
│   └── test_api/
│
└── scripts/
    ├── seed_prompts.py
    └── pull_models.sh
```

---

## Implementation Steps

### Step 1: Project Setup

1. Create `pyproject.toml` with dependencies:
   - fastapi, uvicorn, httpx
   - pydantic, pydantic-settings
   - sqlalchemy, aiosqlite
   - jinja2 (for prompt templates)
   - structlog (logging)

2. Create Dockerfile:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY pyproject.toml .
   RUN pip install .
   COPY src/ src/
   CMD ["uvicorn", "genai_spine.main:app", "--host", "0.0.0.0", "--port", "8100"]
   ```

### Step 2: Port Providers from Capture Spine

Copy and adapt from `capture-spine/app/llm/providers/`:
- Keep the same interface but make it standalone
- Add async HTTP client pooling
- Add retry logic with exponential backoff

### Step 3: Build Core API

1. Health endpoints (simple)
2. `/v1/models` - List available models per provider
3. `/v1/chat/completions` - OpenAI-compatible
4. `/v1/completions` - OpenAI-compatible

### Step 4: Add Capabilities

1. `/v1/summarize` - Built-in prompt for summarization
2. `/v1/extract` - Entity and key point extraction
3. `/v1/classify` - Classification with custom categories

### Step 5: Prompt Management

1. Database schema for prompts
2. CRUD endpoints
3. Version tracking
4. Template rendering with Jinja2

### Step 6: Cost Tracking

1. Per-request cost calculation
2. Daily aggregation
3. Usage endpoints

---

## Example Usage

After implementation, clients use it like this:

```python
import httpx

# Simple completion
response = httpx.post("http://genai:8100/v1/chat/completions", json={
    "model": "llama3.2:latest",
    "messages": [{"role": "user", "content": "Hello!"}]
})

# Summarization
response = httpx.post("http://genai:8100/v1/summarize", json={
    "content": "Long article text...",
    "max_sentences": 3
})

# Entity extraction
response = httpx.post("http://genai:8100/v1/extract", json={
    "content": "Apple CEO Tim Cook announced...",
    "entity_types": ["PERSON", "ORG"]
})
```

---

## Testing Strategy

1. **Unit tests** for each provider (mock HTTP responses)
2. **Integration tests** with Ollama (requires running container)
3. **API tests** for all endpoints
4. **Load tests** to verify concurrency handling

---

## Migration from Capture Spine

After GenAI Spine is running:

1. Add `GENAI_SPINE_URL=http://genai:8100` to Capture Spine
2. Create `GenAIClient` wrapper in Capture Spine
3. Replace direct provider calls with GenAI Spine API calls
4. Remove `app/llm/providers/` from Capture Spine (keep as fallback initially)

---

## Start Building

Begin with Step 1 (project setup) and work through incrementally. Focus on getting a working `/v1/chat/completions` endpoint with Ollama first, then expand.
