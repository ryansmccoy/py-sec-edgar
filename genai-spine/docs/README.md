# GenAI Spine Documentation

**Last Updated:** 2026-01-31

> **Auto-generated friendly** — These docs are structured to work with AI coding assistants.

---

## 🚀 Quick Start

| You Want To... | Go Here |
|----------------|---------|
| Integrate your app with GenAI Spine | [Consumer Quickstart](integration/CONSUMER_QUICKSTART.md) |
| See the API specification | [API Contract](api/API_CONTRACT.md) |
| Understand the architecture | [ADR-0001: Domain-Agnostic](adr/ADR-0001-domain-agnostic.md) |
| Handle errors correctly | [Error Handling](api/ERRORS.md) |
| Migrate from local LLM code | [Migration Checklist](integration/MIGRATION_CHECKLIST.md) |

---

## Status Legend

All documents use consistent status labels:

| Status | Meaning |
|--------|---------|
| 📝 Draft | Can change without notice |
| 📋 Proposal | Stable intent, not yet implemented |
| 🗓️ Planned | Scheduled for next milestone |
| ✅ Active | Implemented and in use |
| ⚠️ Deprecated | Do not use for new integrations |

---

## Documentation Structure

```
docs/
├── api/                          # API specifications
│   ├── README.md                 # API quick reference
│   ├── API_CONTRACT.md           # Full endpoint specification
│   ├── API_TIERS.md              # Tier A vs Tier B endpoints
│   ├── AUTH.md                   # Authentication (planned)
│   └── ERRORS.md                 # Error codes and handling
│
├── integration/                  # Consumer integration guides
│   ├── README.md                 # Integration index
│   ├── CONSUMER_QUICKSTART.md    # Quick start for consumers
│   ├── CAPTURE_SPINE_INTEGRATION_ANALYSIS.md
│   └── MIGRATION_CHECKLIST.md
│
├── features/                     # Feature specifications
│   ├── README.md                 # Feature roadmap
│   ├── GENAI_ADMIN_UI.md         # Admin UI spec
│   ├── MULTI_MODEL_REVIEW_WORKFLOW.md
│   └── REVIEW_ANALYSIS_PROMPT.md
│
└── adr/                          # Architecture Decision Records
    ├── README.md                 # ADR index
    └── ADR-0001-domain-agnostic.md
```

---

## Core Principle: Domain-Agnostic Design

GenAI Spine provides **generic LLM building blocks**, not domain-specific endpoints.

```python
# ✅ GOOD: Generic endpoint, domain context in prompt
result = await genai.execute_prompt(
    slug="summarizer",                 # Generic capability
    variables={"text": filing_text}    # Consumer provides context
)

# ❌ BAD: Domain-specific endpoint
result = await genai.summarize_filing(filing_id)
```

See [ADR-0001](adr/ADR-0001-domain-agnostic.md) for full rationale.

---

## Legacy Documentation

> **Note:** The documents below are from earlier planning phases. They may contain outdated information.

| Document | Purpose |
|----------|---------|
| [CAPTURE_SPINE_INTEGRATION.md](CAPTURE_SPINE_INTEGRATION.md) | Earlier capture-spine integration notes |
| [ECOSYSTEM_INTEGRATION.md](ECOSYSTEM_INTEGRATION.md) | Earlier ecosystem integration notes |

---

## See Also

- [STATUS.md](../STATUS.md) - Current implementation status
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [TODO.md](../TODO.md) - Detailed task breakdown
| What capabilities exist? | [capabilities/README.md](capabilities/README.md) |
| How do tiers work? | [architecture/TIERS.md](architecture/TIERS.md) |
| How to add a capability? | [guides/ADDING_CAPABILITIES.md](guides/ADDING_CAPABILITIES.md) |
| Financial market features? | [domains/financial-markets/](domains/financial-markets/) |
| Prompt management? | [core/PROMPT_MANAGEMENT.md](core/PROMPT_MANAGEMENT.md) |
| RAG implementation? | [core/RAG.md](core/RAG.md) |
| Testing standards? | [guides/TESTING.md](guides/TESTING.md) |
| Code conventions? | [guides/CONVENTIONS.md](guides/CONVENTIONS.md) |
| Alignment prompts? | [../prompts/README.md](../prompts/README.md) |

---

## Alignment System

We maintain project alignment using AI-assisted review prompts. See [../prompts/](../prompts/) for:

| Prompt | Purpose | Frequency |
|--------|---------|-----------|
| Documentation Review | Check doc completeness | Weekly |
| Testing Review | Verify test coverage | Per PR |
| Architecture Review | Check layer boundaries | Per PR |
| Code Conventions | Style and type hints | Per PR |
| Guardrails Review | Security and reliability | Monthly |
| TODO Review | Track in-progress work | Weekly |
| Commit Organization | Structure commits | As needed |
| Changelog Update | Document releases | Before release |

**Workflow:**
1. Copy prompt into fresh AI chat
2. AI reviews and creates plan in `alignment/plans/`
3. Fix issues
4. Track status in `alignment/status.md`

---

## Contributing to Docs

See [guides/DOCUMENTATION_BEST_PRACTICES.md](guides/DOCUMENTATION_BEST_PRACTICES.md) for our documentation philosophy in the age of AI coding assistants.

**TL;DR:**
- Prefer docstrings in code over separate docs
- Keep docs small and feature-focused
- Use tables and code blocks for machine readability
- Update docs alongside code changes
