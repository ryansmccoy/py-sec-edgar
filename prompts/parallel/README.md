# Parallel Implementation Prompts

> **Purpose:** Hand each prompt to a separate LLM session to implement features in parallel.

**IMPORTANT**: Each prompt has been updated with full context from existing documentation. Read the referenced docs before starting.

---

## Current Date: January 29, 2026

## Prompt Index

| # | Prompt File | Project | Feature | Priority | Est. Time |
|---|-------------|---------|---------|----------|-----------|
| 1 | [01_ENTITYSPINE_COMMIT.md](01_ENTITYSPINE_COMMIT.md) | entityspine | Commit v2.3.3 features | 🔴 HIGH | 30 min |
| 2 | [02_CAPTURE_SPINE_GIT_INIT.md](02_CAPTURE_SPINE_GIT_INIT.md) | capture-spine | Initialize git repo | 🔴 HIGH | 15 min |
| 3 | [03_FEEDSPINE_CHAT_PROVIDER.md](03_FEEDSPINE_CHAT_PROVIDER.md) | feedspine | CopilotChatProvider | 🟡 MED | 2-3 hrs |
| 4 | [04_CAPTURE_SPINE_PRODUCTIVITY.md](04_CAPTURE_SPINE_PRODUCTIVITY.md) | capture-spine | **Full Productivity Suite** | 🟡 MED | 6-8 hrs |
| 5 | [05_EARNINGS_FEATURE_COMPLETE.md](05_EARNINGS_FEATURE_COMPLETE.md) | ALL | Earnings estimates vs actuals | 🟡 MED | 4-6 hrs |
| 6 | [06_DOCUMENTATION_ALIGNMENT.md](06_DOCUMENTATION_ALIGNMENT.md) | ALL | Docs standardization | 🟢 LOW | 2-3 hrs |
| 7 | [07_EVERYTHING_SEARCH_INTEGRATION.md](07_EVERYTHING_SEARCH_INTEGRATION.md) | capture-spine | Everything Search + File Monitoring | 🟡 MED | 3-4 hrs |

## What's In Each Prompt

| Prompt | Existing Docs Referenced | Key Feature |
|--------|--------------------------|-------------|
| **03** | `capture-spine/scripts/copilot_chat_parser.py` (365 lines) | Ingest VS Code chats as observations |
| **04** | `capture-spine/docs/features/productivity/` (8 files, ~3000 lines) | Chat UI, File Monitor, Todos, Lineage |
| **05** | `feedspine/docs/features/estimates-vs-actuals/` (6 files, ~2500 lines) | Earnings comparison engine |
| **07** | Everything HTTP API, document-lineage.md | Track file changes in capture-spine |

## Execution Order

```
MUST DO FIRST (blocking):
├── 01_ENTITYSPINE_COMMIT.md    ← Commit before others depend on it
└── 02_CAPTURE_SPINE_GIT_INIT.md ← Need git before feature commits

CAN RUN IN PARALLEL:
├── 03_FEEDSPINE_CHAT_PROVIDER.md   ← Creates observations from VS Code chats
├── 04_CAPTURE_SPINE_PRODUCTIVITY.md ← Full productivity: chat UI, todos, file monitor
├── 05_EARNINGS_FEATURE_COMPLETE.md  ← Spans all projects
└── 07_EVERYTHING_SEARCH_INTEGRATION.md ← File monitoring, links to 04

RUN LAST:
└── 06_DOCUMENTATION_ALIGNMENT.md
```

## Integration Notes

### Chat/Productivity Flow
```
VS Code Copilot Chat Sessions
    ↓
03: CopilotChatProvider (feedspine) ← Creates ChatSessionObservation
    ↓
04: Content Ingestion API (capture-spine) ← Stores in database
    ↓
04: Chat UI (capture-spine) ← View/search chat history
    ↓
04: Todo Extraction (capture-spine) ← LLM extracts tasks from chats
```

### File Monitoring Flow
```
Everything Search API (Windows)
    ↓
07: EverythingSearchService ← Fast file search with date filtering
    ↓
04/07: FileMonitorService ← Track file changes
    ↓
04/07: Document Lineage ← Link files to originating chats
```

## How to Use

1. **Read the prompt** - Each has detailed context from existing docs
2. **Start with 01 & 02** - These are blocking
3. **Pick a feature prompt** (03-07) - Each is self-contained
4. **Copy entire prompt** into a new LLM session
5. **Follow the slices** - Prompt 04 has vertical slices, do them in order

## Existing Scripts (ALREADY BUILT - LEVERAGE THESE!)

In `capture-spine/scripts/`:
- ✅ `copilot_chat_parser.py` - Parse VS Code chats (365 lines)
- ✅ `scan_docs.py` - Scan documentation folders (333 lines)
- ✅ `scan_python_changes.py` - Track Python file changes (311 lines)
- ✅ `scaffold_feature.py` - Generate feature boilerplate

---

*Generated: Jan 29, 2026*
