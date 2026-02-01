# GenAI Spine API Documentation

**Last Updated:** 2026-01-31

---

## Documents

| Document | Description | Status |
|----------|-------------|--------|
| [API_CONTRACT.md](API_CONTRACT.md) | Full API specification | 📋 Proposal |
| [API_TIERS.md](API_TIERS.md) | Tier A (stable) vs Tier B (convenience) endpoints | 📋 Proposal |
| [AUTH.md](AUTH.md) | Authentication mechanisms | 🗓️ Planned |
| [ERRORS.md](ERRORS.md) | Error codes and handling | ✅ Active |

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

## Quick Reference

### Base URL

```
Development: http://localhost:8100
Production:  http://genai-spine:8100
```

### Tier A Endpoints (Stable Primitives)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/completions` | Generic LLM completion |
| POST | `/v1/execute-prompt` | Execute stored prompt |
| POST | `/v1/sessions` | Create chat session |
| POST | `/v1/sessions/{id}/messages` | Send message |
| GET | `/v1/prompts` | List prompts |
| POST | `/v1/prompts` | Create prompt |
| GET | `/v1/models` | List models |
| GET | `/v1/usage` | Query usage/costs |

### Tier B Endpoints (Convenience)

| Method | Endpoint | Wraps |
|--------|----------|-------|
| POST | `/v1/summarize` | `execute-prompt` with `slug=summarizer` |
| POST | `/v1/rewrite` | `execute-prompt` with `slug=rewriter` |
| POST | `/v1/extract` | `execute-prompt` with `slug=extractor` |

See [API_TIERS.md](API_TIERS.md) for stability guarantees.

---

## See Also

- [CONSUMER_QUICKSTART.md](../integration/CONSUMER_QUICKSTART.md) - How to use the API
- [ADR-0001](../adr/ADR-0001-domain-agnostic.md) - Why domain-agnostic design
