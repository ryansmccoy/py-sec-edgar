# Manifests & Configuration Files

> Reference for all configuration files in GenAI Spine.

---

## Overview

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package definition, dependencies, tool config |
| `pytest.ini` | Test configuration |
| `.env` | Environment variables (local) |
| `.env.example` | Environment template |
| `docker-compose.yml` | Local development stack |
| `Dockerfile` | Container image |

---

## pyproject.toml

Main package manifest:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "genai-spine"
version = "0.1.0"
description = "Unified GenAI service for the Spine ecosystem"
readme = "README.md"
license = "MIT"
requires-python = ">=3.12"
authors = [
    { name = "Your Name", email = "you@example.com" },
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Framework :: FastAPI",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
keywords = ["llm", "genai", "fastapi", "ollama", "openai"]

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "httpx>=0.26.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]
openai = [
    "openai>=1.10.0",
]
anthropic = [
    "anthropic>=0.18.0",
]
all = [
    "genai-spine[dev,openai,anthropic]",
]

[project.scripts]
genai-spine = "genai_spine.main:main"

[project.urls]
Homepage = "https://github.com/yourorg/genai-spine"
Documentation = "https://github.com/yourorg/genai-spine/docs"
Repository = "https://github.com/yourorg/genai-spine"

# ============================================================================
# Tool Configuration
# ============================================================================

[tool.hatch.build.targets.wheel]
packages = ["src/genai_spine"]

[tool.ruff]
line-length = 88
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",     # pycodestyle errors
    "F",     # pyflakes
    "I",     # isort
    "UP",    # pyupgrade
    "B",     # bugbear
    "SIM",   # simplify
    "ASYNC", # async
]
ignore = [
    "E501",  # Line length (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["genai_spine"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["httpx.*", "ollama.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: Fast unit tests",
    "integration: Tests requiring external services",
    "slow: Tests > 10 seconds",
    "ollama: Tests requiring Ollama",
    "openai: Tests requiring OpenAI API key",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src/genai_spine"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

---

## .env.example

Template for environment configuration:

```bash
# =============================================================================
# GenAI Spine Configuration
# =============================================================================
# Copy this file to .env and fill in your values

# -----------------------------------------------------------------------------
# API Configuration
# -----------------------------------------------------------------------------
GENAI_API_HOST=0.0.0.0
GENAI_API_PORT=8100
GENAI_DEBUG=false

# -----------------------------------------------------------------------------
# Provider Configuration
# -----------------------------------------------------------------------------
# Default provider: ollama, openai, anthropic, bedrock
GENAI_DEFAULT_PROVIDER=ollama

# Ollama (local)
GENAI_OLLAMA_URL=http://localhost:11434
GENAI_OLLAMA_DEFAULT_MODEL=llama3.2:latest

# OpenAI (optional)
GENAI_OPENAI_API_KEY=
GENAI_OPENAI_DEFAULT_MODEL=gpt-4o-mini

# Anthropic (optional)
GENAI_ANTHROPIC_API_KEY=
GENAI_ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022

# AWS Bedrock (optional)
GENAI_BEDROCK_REGION=us-east-1

# -----------------------------------------------------------------------------
# Fallback & Routing
# -----------------------------------------------------------------------------
# Comma-separated provider fallback order
GENAI_FALLBACK_CHAIN=ollama,openai

# Routing strategy: local_first, cost_optimized, quality, speed
GENAI_ROUTING_STRATEGY=local_first

# -----------------------------------------------------------------------------
# Storage Configuration
# -----------------------------------------------------------------------------
# SQLite (development)
GENAI_DATABASE_URL=sqlite+aiosqlite:///./data/genai.db

# PostgreSQL (production)
# GENAI_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/genai

# -----------------------------------------------------------------------------
# Cache Configuration
# -----------------------------------------------------------------------------
GENAI_CACHE_ENABLED=false
GENAI_CACHE_TTL=3600
# GENAI_REDIS_URL=redis://localhost:6379

# -----------------------------------------------------------------------------
# Cost Controls
# -----------------------------------------------------------------------------
GENAI_BUDGET_DAILY=10.00
GENAI_BUDGET_MONTHLY=200.00

# -----------------------------------------------------------------------------
# Guardrails
# -----------------------------------------------------------------------------
GENAI_GUARDRAIL_ENABLE_CONTENT_FILTERING=true
GENAI_GUARDRAIL_RATE_LIMIT_PER_MINUTE=60
GENAI_GUARDRAIL_MAX_INPUT_TOKENS=100000
GENAI_GUARDRAIL_MAX_OUTPUT_TOKENS=4000

# -----------------------------------------------------------------------------
# Observability
# -----------------------------------------------------------------------------
GENAI_LOG_LEVEL=INFO
GENAI_LOG_FORMAT=json
# GENAI_OTLP_ENDPOINT=http://localhost:4317
```

---

## docker-compose.yml

Development stack:

```yaml
version: '3.8'

services:
  # GenAI API Service
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8100:8100"
    environment:
      - GENAI_DEBUG=true
      - GENAI_DEFAULT_PROVIDER=ollama
      - GENAI_OLLAMA_URL=http://ollama:11434
      - GENAI_DATABASE_URL=sqlite+aiosqlite:///data/genai.db
    volumes:
      - ./src:/app/src:ro  # Hot reload
      - api_data:/app/data
    depends_on:
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Ollama LLM Server
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
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5

  # PostgreSQL (optional, for production-like setup)
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: genai
      POSTGRES_PASSWORD: genai_dev
      POSTGRES_DB: genai
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    profiles:
      - production

  # Redis (optional, for caching)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    profiles:
      - production

volumes:
  api_data:
  ollama_data:
  postgres_data:
  redis_data:
```

---

## Dockerfile

```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatch

# Copy source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build wheel
RUN hatch build -t wheel

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy wheel from builder
COPY --from=builder /app/dist/*.whl ./

# Install package
RUN pip install --no-cache-dir *.whl && rm *.whl

# Create data directory
RUN mkdir -p /app/data

# Non-root user
RUN useradd -m -u 1000 genai && chown -R genai:genai /app
USER genai

EXPOSE 8100

CMD ["uvicorn", "genai_spine.main:app", "--host", "0.0.0.0", "--port", "8100"]
```

---

## .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual environments
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/

# Environment
.env
.env.local

# Data
data/
*.db
*.sqlite

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
```

---

## Related Docs

- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment instructions
- [CONVENTIONS.md](CONVENTIONS.md) — Code conventions
