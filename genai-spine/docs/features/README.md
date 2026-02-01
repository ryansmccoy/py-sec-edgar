# GenAI Spine Feature Specifications

**Last Updated:** 2026-01-31

---

## Status Legend

| Status | Meaning |
|--------|---------|
| 📝 Draft | Can change without notice |
| 📋 Proposal | Stable intent, not yet implemented |
| 🗓️ Planned | Scheduled for next milestone |
| ✅ Active | Implemented and in use |
| ⚠️ Deprecated | Do not use for new integrations |

---

## Documents

| Document | Description | Status |
|----------|-------------|--------|
| [GENAI_ADMIN_UI.md](GENAI_ADMIN_UI.md) | Web-based management interface | 📋 Proposal |
| [MULTI_MODEL_REVIEW_WORKFLOW.md](MULTI_MODEL_REVIEW_WORKFLOW.md) | Cross-model validation workflow | 📋 Proposal |
| [REVIEW_ANALYSIS_PROMPT.md](REVIEW_ANALYSIS_PROMPT.md) | Prompt template for model review | 📋 Proposal |

---

## Feature Categories

### 🖥️ Admin & Management

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| [GenAI Admin UI](GENAI_ADMIN_UI.md) | P1 | 📋 Proposal | Web-based management interface |
| Chat Sessions | P1 | 📋 Proposal | VS Code Copilot-style chat with persistence |
| Prompt Playground | P1 | 📋 Proposal | Testing environment for prompts |
| Model Dashboard | P2 | 📋 Proposal | Model health, costs, usage stats |

### 🔄 Workflow Automation

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| [Multi-Model Review](MULTI_MODEL_REVIEW_WORKFLOW.md) | P1 | 📋 Proposal | Cross-model review and validation |
| Pipeline Orchestration | P2 | 📋 Proposal | Chain multiple capabilities |
| Batch Processing | P2 | 📋 Proposal | Process many items efficiently |

### 🔌 Integration

| Feature | Priority | Status | Description |
|---------|----------|--------|-------------|
| Capture Spine Integration | P0 | ✅ Active | Message enrichment, commits |
| FeedSpine Integration | P1 | 🗓️ Planned | Article processing |
| VS Code Extension | P2 | 📋 Proposal | Direct IDE integration |

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
