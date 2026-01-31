# GenAI Spine - Feature Roadmap

**Last Updated:** 2026-01-31

This document provides a high-level view of planned features beyond the core MVP.

---

## Feature Categories

### 🖥️ Admin & Management

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| [GenAI Admin UI](GENAI_ADMIN_UI.md) | P1 | 📋 Proposed | Web-based management interface |
| Chat Sessions | P1 | 📋 Proposed | VS Code Copilot-style chat with persistence |
| Prompt Playground | P1 | 📋 Proposed | Testing environment for prompts |
| Model Dashboard | P2 | 📋 Proposed | Model health, costs, usage stats |

### 🔄 Workflow Automation

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| [Multi-Model Review](MULTI_MODEL_REVIEW_WORKFLOW.md) | P1 | 📋 Proposed | Cross-model review and validation |
| Pipeline Orchestration | P2 | 📋 Proposed | Chain multiple capabilities |
| Batch Processing | P2 | 📋 Proposed | Process many items efficiently |

### 🔌 Integration

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| Capture Spine Integration | P0 | ✅ Ready | Message enrichment, commits |
| FeedSpine Integration | P1 | 🟡 Planned | Article processing |
| VS Code Extension | P2 | 📋 Proposed | Direct IDE integration |

### 🚀 Performance

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| SSE Streaming | P1 | 📋 Proposed | Real-time token streaming |
| Redis Caching | P2 | 📋 Proposed | Response caching |
| Rate Limiting | P2 | 📋 Proposed | Per-provider limits |

---

## Detailed Feature Docs

- [GENAI_ADMIN_UI.md](GENAI_ADMIN_UI.md) - Full admin interface specification
- [MULTI_MODEL_REVIEW_WORKFLOW.md](MULTI_MODEL_REVIEW_WORKFLOW.md) - Cross-model review process

---

## Implementation Timeline

### Q1 2026 (Current)
- ✅ Core API (25 endpoints)
- ✅ Multi-provider support (Ollama, OpenAI, Anthropic)
- ✅ Prompt management with versioning
- ✅ Cost tracking and usage stats
- 🟡 Alembic migrations

### Q2 2026
- [ ] Admin UI MVP
- [ ] Chat sessions with persistence
- [ ] Streaming support
- [ ] Multi-model review automation

### Q3 2026
- [ ] Full Admin UI
- [ ] Pipeline orchestration
- [ ] Advanced caching
- [ ] VS Code extension (exploration)

---

## Contributing

When proposing new features:
1. Create a doc in `docs/features/`
2. Follow the template structure
3. Link from this roadmap
4. Update [TODO.md](../../TODO.md) if implementation is approved
