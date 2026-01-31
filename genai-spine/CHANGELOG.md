# Changelog - GenAI Spine

All notable changes to GenAI Spine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Alembic database migrations
- AWS Bedrock provider
- SSE streaming for chat completions
- Redis response caching

---

## [0.1.0] - 2026-01-31

### Added

#### Core Infrastructure
- FastAPI application with 25 API endpoints
- Multi-provider LLM abstraction (Ollama, OpenAI, Anthropic)
- Provider registry with dynamic provider loading
- Pydantic Settings for configuration management
- Docker support with docker-compose.yml

#### API Endpoints
- Health endpoints: `/health`, `/ready`
- Models endpoints: `/v1/models`, `/v1/models/{id}`
- Completions: `/v1/completions`, `/v1/chat/completions`
- Capabilities: `/v1/summarize`, `/v1/extract`, `/v1/classify`
- Message Enrichment: `/v1/rewrite`, `/v1/infer-title`
- Work Sessions: `/v1/generate-commit`
- Pipeline support: `/v1/execute-prompt`
- Prompt Management: Full CRUD with versioning
- Usage & Pricing: `/v1/usage`, `/v1/pricing`, `/v1/estimate-cost`

#### Capabilities
- Text summarization with customizable output length
- Entity extraction with configurable entity types
- Content classification with custom categories
- Content rewriting (clean, format, organize, summarize modes)
- Title inference from content
- Commit message generation from diffs

#### Storage
- Protocol-based, database-agnostic storage abstraction
- SQLite backend for development/testing
- PostgreSQL backend for production (asyncpg)
- Unit of Work pattern for transactions
- Prompt versioning with immutable history
- Soft delete support
- Execution tracking with cost attribution

#### Cost Tracking
- Per-request cost calculation
- Model pricing database (OpenAI, Anthropic models)
- Usage statistics with date filtering
- Cost estimation before execution

#### Providers
- **Ollama**: Local model support (llama3.2, mistral, codellama, etc.)
- **OpenAI**: GPT-4o, GPT-4-turbo, GPT-3.5-turbo
- **Anthropic**: Claude 3 Opus, Sonnet, Haiku (via httpx)

#### Testing
- pytest with pytest-asyncio
- 80 tests covering storage, capabilities, API endpoints
- Mock provider for isolated testing
- In-memory backend for fast tests

#### Documentation
- README with quick start guide
- TODO.md implementation roadmap
- CAPTURE_SPINE_INTEGRATION.md - feature mapping
- ECOSYSTEM_INTEGRATION.md - full ecosystem guide
- Capability tier documentation (TIER_1-4)
- Agent alignment prompts (prompts/)

---

## Version History

- **0.1.0** (2026-01-31): Initial release with full MVP feature set

---

*For the py-sec-edgar root changelog, see [../docs/CHANGELOG.md](../docs/CHANGELOG.md).*
