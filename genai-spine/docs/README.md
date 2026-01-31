# GenAI Spine Documentation

> **Auto-generated friendly** — These docs are structured to work with AI coding assistants.
> Focus on small, feature-oriented files that can be easily referenced and updated.

---

## 🚀 Quick Links

| Document | Purpose |
|----------|---------|
| **[CAPTURE_SPINE_INTEGRATION.md](./CAPTURE_SPINE_INTEGRATION.md)** | Capture Spine feature requirements |
| **[ECOSYSTEM_INTEGRATION.md](./ECOSYSTEM_INTEGRATION.md)** | FeedSpine, Spine-Core, EntitySpine opportunities |
| **[../prompts/PARALLEL_AGENT_PROMPT.md](../prompts/PARALLEL_AGENT_PROMPT.md)** | Agent guidance for parallel development |
| **[../TODO.md](../TODO.md)** | Implementation status and priorities |

---

## Documentation Philosophy

1. **Small, focused files** — Each doc covers one concept
2. **Machine-readable structure** — Consistent headers, tables, code blocks
3. **Living documentation** — Update alongside code changes
4. **Docstring priority** — Code is the source of truth; docs provide context

---

## Documentation Map

```
docs/
├── README.md                    # This file
├── CAPTURE_SPINE_INTEGRATION.md # ⭐ Capture Spine integration specs
├── ECOSYSTEM_INTEGRATION.md     # ⭐ Full ecosystem integration guide
│
├── architecture/
│   ├── OVERVIEW.md              # High-level architecture
│   ├── TIERS.md                 # Tier 1-4 deployment options
│   └── PROVIDERS.md             # LLM provider abstraction
│
├── capabilities/
│   ├── README.md                # Capabilities overview
│   ├── TIER_1_BASIC.md          # Basic capabilities (must-have)
│   ├── TIER_2_INTERMEDIATE.md   # Intermediate capabilities
│   ├── TIER_3_ADVANCED.md       # Advanced capabilities
│   └── TIER_4_MINDBLOWING.md    # Future vision capabilities
│
├── core/
│   ├── PROMPT_MANAGEMENT.md     # Prompt CRUD, versioning, templates
│   ├── RAG.md                   # Retrieval-Augmented Generation
│   ├── COST_TRACKING.md         # Token counting, budgets
│   ├── CACHING.md               # Response caching strategies
│   └── OBSERVABILITY.md         # Metrics, logging, tracing
│
├── domains/
│   ├── README.md                # Domain extension overview
│   └── financial-markets/       # Financial market domain
│       ├── README.md
│       ├── CAPABILITIES.md
│       └── INTEGRATION.md
│
├── integration/
│   ├── CAPTURE_SPINE.md         # Integration with Capture Spine
│   ├── ENTITY_SPINE.md          # Integration with EntitySpine
│   ├── FEED_SPINE.md            # Integration with FeedSpine
│   └── CLIENT_SDK.md            # Python client library
│
└── guides/
    ├── DOCUMENTATION_BEST_PRACTICES.md
    ├── ADDING_CAPABILITIES.md
    ├── ADDING_PROVIDERS.md
    └── DEPLOYMENT.md
```

---

## Quick Links

| Topic | Document |
|-------|----------|
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
