# Integration Documentation

> **Cross-project integration examples and tracking**

This folder contains documentation for features that span multiple projects in the ecosystem.

---

## How the Ecosystem Works

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER (What)                                  │
│                                                                            │
│   entityspine (stdlib-only domain models)                                  │
│   ├── Entity, Security, Listing     ──▶ Financial entities                │
│   ├── Observation, Event            ──▶ Facts & calendar                  │
│   ├── ChatSession, ChatMessage      ──▶ AI conversation history           │
│   ├── Markets (Exchange, Broker)    ──▶ Market infrastructure             │
│   └── Extraction models (v2.3.2)    ──▶ NER, Story clusters, Links        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                       INGESTION LAYER (How)                                │
│                                                                            │
│   feedspine (feed providers & deduplication)                               │
│   ├── SEC Filing Provider           ──▶ 8-K, 10-Q, 10-K                   │
│   ├── Earnings Provider             ──▶ Estimates, actuals, calendar      │
│   ├── RSS Provider                  ──▶ News feeds                        │
│   └── CopilotChatProvider (new!)    ──▶ VS Code chat sessions             │
│                                                                            │
│   spine-core (pipeline orchestration)                                      │
│   ├── Pipeline framework            ──▶ Define data workflows             │
│   ├── Workflow steps                ──▶ Compose transformations           │
│   └── Execution tracking            ──▶ Monitor & alert                   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER (Show)                             │
│                                                                            │
│   capture-spine (content capture & productivity)                           │
│   ├── Record storage                ──▶ PostgreSQL + search               │
│   ├── LLM enrichment                ──▶ Summarize, extract TODOs          │
│   ├── Alert rules                   ──▶ Pattern matching                  │
│   └── React newsfeed UI             ──▶ Real-time updates                 │
│                                                                            │
│   trading-desktop (institutional UI)                                       │
│   ├── Bloomberg-style panels        ──▶ Portfolio, Trading, Research      │
│   ├── Earnings widgets              ──▶ Beat/miss dashboards              │
│   └── Knowledge graph               ──▶ Entity relationships              │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Why It Feels Easy

The architecture follows consistent patterns:

| Pattern | Example | Benefit |
|---------|---------|---------|
| **Stdlib-only models** | `@dataclass` in entityspine | No ORM/Pydantic complexity |
| **Composable hierarchy** | Workspace → Session → Message | Same as Entity → Security → Listing |
| **Hash-based dedup** | `content_hash`, `session_hash` | feedspine handles automatically |
| **Factory functions** | `create_chat_session()` | Consistent creation patterns |
| **Provider abstraction** | `FeedProvider` base class | Add new sources easily |

---

## Integration Documents

### Active Features

| Feature | Projects Involved | Status | Doc |
|---------|-------------------|--------|-----|
| **Copilot Chat Ingestion** | entityspine → capture-spine | ✅ Working | [copilot-chat-ingestion.md](copilot-chat-ingestion.md) |
| **Chat Storage Architecture** | feedspine ↔ capture-spine | ✅ Analyzed | [CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md](CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md) |
| **GenAI Service Integration** | genai-spine → capture-spine | 🟡 In Progress | [genai-capture-integration.md](genai-capture-integration.md) |
| **Package Release (PyPI)** | entityspine, spine-core, feedspine | 🔴 Priority | [PACKAGE_RELEASE_PLAN.md](PACKAGE_RELEASE_PLAN.md) |
| **Productivity Features** | capture-spine + genai-spine | 🟡 In Progress | [productivity-features.md](productivity-features.md) |

### Architecture Analysis

| Topic | Decision | Doc |
|-------|----------|-----|
| Chat dedup ownership | Capture Spine direct (hybrid future) | [CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md](CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md) |
| LLM service design | Centralized GenAI Spine | [../../genai-spine/docs/ECOSYSTEM_INTEGRATION.md](../../genai-spine/docs/ECOSYSTEM_INTEGRATION.md) |
| Domain model location | entityspine (stdlib-only) | [../architecture/ECOSYSTEM.md](../architecture/ECOSYSTEM.md) |

### Data Flow Examples

| Flow | Description | Doc |
|------|-------------|-----|
| Chat → Productivity | VS Code chat to TODO tracking | [copilot-chat-ingestion.md](copilot-chat-ingestion.md) |
| Message → Enrichment | Chat message to LLM rewrite | [genai-capture-integration.md](genai-capture-integration.md) |
| Files → Commit | Work session to commit message | [genai-capture-integration.md](genai-capture-integration.md) |

---

## Project Quick Reference

| Project | Location | Purpose | Language |
|---------|----------|---------|----------|
| **py-sec-edgar** | `/` (root) | SEC filing downloads | Python |
| **entityspine** | `/entityspine/` | Domain models (stdlib-only) | Python |
| **feedspine** | `/feedspine/` | Feed providers & storage | Python |
| **spine-core** | `/spine-core/` | Pipeline orchestration | Python |
| **capture-spine** | `/capture-spine/` | Content capture & UI | Python + React |
| **trading-desktop** | `/spine-core/trading-desktop/` | Institutional UI | React + Vite |
| **market-spine** | `/market-spine/` | Market data utilities | Python |

---

## User Feedback Tracking

### Jan 29, 2026 Session

**User observations:**
> "Why is it now that it feels like its so easy to implement features with this entity model system?"

> "entityspine I guess can manage this type of stuff too? How does that work? Then we also need to work on integrating this into feedspine because should be able to handle that too"

> "Make sure you are keeping track of the features and updating it with my responses so I can keep this history"

> "What about spine core and trading-desktop? Those are important to keep track of too. In fact create a markdown document for the workspace talking about how the different apps and packages interact with each other"

**Key insights:**
1. entityspine's stdlib-only approach enables rapid domain modeling
2. Same patterns work for financial data AND productivity features (Chat mirrors Entity hierarchy)
3. feedspine's deduplication applies to any feed type (SEC, RSS, or chat sessions)
4. User values historical tracking of requirements and decisions
5. spine-core provides pipeline primitives used across projects
6. trading-desktop is the end-user UI consuming all backend services

**Implementation progress:**
- ✅ entityspine: ChatWorkspace, ChatSession, ChatMessage models (v2.3.1)
- ✅ capture-spine: VS Code chat parser script working
- ✅ Documentation: integration/ folder, ECOSYSTEM.md updated
- ⏳ feedspine: CopilotChatProvider (next step)
- 🔴 capture-spine: TODO management, file upload

---

## Related Files

- [ECOSYSTEM.md](../ECOSYSTEM.md) - High-level ecosystem overview
- [LLM_HANDOFF.md](../LLM_HANDOFF.md) - Context for LLM continuity
- [INTEGRATION_MANIFESTO.md](../INTEGRATION_MANIFESTO.md) - Integration principles

---

*Update this document as integrations evolve.*
