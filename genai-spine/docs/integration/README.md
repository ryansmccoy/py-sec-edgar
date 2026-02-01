# GenAI Spine Integration Index

**Last Updated:** 2026-01-31

This directory contains integration documentation for connecting GenAI Spine with other applications in the Spine ecosystem.

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
| [CONSUMER_QUICKSTART.md](CONSUMER_QUICKSTART.md) | Quick start guide for consumer apps | 📋 Proposal |
| [CAPTURE_SPINE_INTEGRATION_ANALYSIS.md](CAPTURE_SPINE_INTEGRATION_ANALYSIS.md) | Analysis of capture-spine's LLM stack and migration options | 📋 Proposal |
| [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md) | Step-by-step migration guide | 🗓️ Planned |

---

## Quick Links

### API Documentation
- [API Contract](../api/API_CONTRACT.md) - Full API specification
- [API Tiers](../api/API_TIERS.md) - Tier A (stable) vs Tier B (convenience)
- [Authentication](../api/AUTH.md) - Auth mechanisms (planned)
- [Error Handling](../api/ERRORS.md) - Error codes and retry behavior

### Current State
- [GenAI Spine STATUS](../../STATUS.md) - What's implemented
- [GenAI Spine CHANGELOG](../../CHANGELOG.md) - Version history

### Feature Specs
- [Admin UI](../features/GENAI_ADMIN_UI.md) - Web-based management interface
- [Multi-Model Review](../features/MULTI_MODEL_REVIEW_WORKFLOW.md) - Cross-model validation

### Architecture Decisions
- [ADR-0001: Domain-Agnostic Design](../adr/ADR-0001-domain-agnostic.md) - Why no domain endpoints

### Ecosystem Integration
- [Ecosystem Overview](../../../docs/integration/ECOSYSTEM_GENAI_INTEGRATION.md) - Full ecosystem map
- [ECOSYSTEM.md](../../../docs/architecture/ECOSYSTEM.md) - Architecture overview

---

## Integration Principles

### 1. GenAI Spine is Domain-Agnostic

GenAI Spine provides generic LLM capabilities. It does NOT contain:
- Business logic specific to any consumer app
- Domain models (SEC filings, chat enrichment, etc.)
- Application-specific workflows

### 2. Consumer Apps Own Domain Logic

Each app calls GenAI Spine with domain context:

```python
# capture-spine owns the "enrichment" concept
result = await genai.execute_prompt(
    slug="content-rewriter",      # GenAI owns the prompt
    variables={
        "content": message.text,  # capture-spine provides context
        "mode": "clean"
    }
)
```

### 3. Single Source of Truth

| Concern | Owner |
|---------|-------|
| LLM providers & credentials | GenAI Spine |
| Cost tracking | GenAI Spine |
| Prompt templates | GenAI Spine |
| Chat session storage | GenAI Spine |
| Domain-specific logic | Consumer apps |

---

## Recommended Integration: SDK Client

```python
# Install
pip install genai-spine-client

# Use
from genai_spine_client import GenAIClient

client = GenAIClient(base_url="http://genai-spine:8100")

# Generic completion
response = await client.complete(messages=[...], model="gpt-4o")

# Execute saved prompt
result = await client.execute_prompt(slug="summarizer", variables={...})

# Chat session
session = await client.sessions.create(model="claude-3-sonnet")
message = await session.send("Hello!")
```

---

## Migration Path

1. **Phase 1:** Create SDK client library
2. **Phase 2:** Migrate chat sessions to GenAI Spine
3. **Phase 3:** Migrate prompt storage
4. **Phase 4:** Remove duplicated code from consumer apps

See [CAPTURE_SPINE_INTEGRATION_ANALYSIS.md](CAPTURE_SPINE_INTEGRATION_ANALYSIS.md) for details.
