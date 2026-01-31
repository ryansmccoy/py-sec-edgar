# Chat Storage Architecture Analysis

**Date**: 2026-01-31
**Status**: Analysis Complete - Recommendation Provided

---

## The Question

> Should FeedSpine manage Copilot chat sessions with deduplication, or should Capture Spine/PostgreSQL handle it directly?

---

## Current Implementation

### Capture Spine (Direct PostgreSQL)

```
VS Code Chat Files
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  capture-spine/scripts/copilot_chat_parser.py                  │
│  - Parses VS Code chat JSON files                              │
│  - Extracts sessions and messages                              │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  capture-spine/app/features/chat_session/                      │
│  - ChatSessionService.ingest_sessions()                        │
│  - ChatSessionRepository.upsert_session()                      │
│  - Deduplication via UNIQUE(external_id) + message_count check │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL (chat_sessions, chat_messages tables)              │
│  - Direct storage with external_id for dedup                   │
│  - No sighting tracking                                        │
│  - No natural_key abstraction                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Current dedup logic** (from `repository.py`):
```python
# Upsert by external_id + source
existing = await self.get_by_external_id(conn, source, external_id)
if existing:
    # Only update if message_count increased
    if message_count > previous_message_count:
        await update(...)
```

---

## Option A: FeedSpine Manages Chats

```
VS Code Chat Files
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  feedspine/adapters/copilot_chat.py (CopilotChatAdapter)       │
│  - Implements FeedAdapter protocol                             │
│  - natural_key = f"{workspace}:{session_id}"                   │
│  - Returns RecordCandidate per session/message                 │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  feedspine/core/feedspine.py (FeedSpine.collect())             │
│  - exists_by_natural_key() → skip if seen                      │
│  - record_sighting() → track when seen                         │
│  - store() → save to storage backend                           │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  feedspine/storage/postgres.py (PostgresStorage)               │
│  - Generic record storage                                      │
│  - Bronze → Silver → Gold layer support                        │
│  - Sighting table for audit trail                              │
└─────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  capture-spine queries via feedspine                           │
│  - spine.query(source="copilot_chat", ...)                     │
│  - Gets records through FeedSpine API                          │
└─────────────────────────────────────────────────────────────────┘
```

### Pros
| Benefit | Description |
|---------|-------------|
| **Consistent dedup** | Same natural_key + sighting pattern as RSS, SEC filings |
| **Audit trail** | Sighting records track when chats were seen |
| **Layer support** | Bronze (raw) → Silver (enriched) → Gold (curated) |
| **Multi-source** | Same adapter pattern for ChatGPT, Claude exports |
| **Package reuse** | FeedSpine becomes THE ingestion layer |

### Cons
| Drawback | Description |
|----------|-------------|
| **Extra hop** | Capture Spine must call FeedSpine instead of direct DB |
| **Deployment complexity** | Need FeedSpine running alongside Capture Spine |
| **Schema mismatch** | FeedSpine's generic `records` table vs. typed `chat_sessions` |
| **Query complexity** | Need to decode content JSON instead of typed columns |
| **Current code works** | Rewrite working code for consistency's sake |

---

## Option B: Capture Spine Direct (Current)

```
VS Code Chat Files
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│  capture-spine (complete ownership)                            │
│  - Parser: scripts/copilot_chat_parser.py                      │
│  - Service: app/features/chat_session/service.py               │
│  - Repository: app/features/chat_session/repository.py         │
│  - Tables: chat_sessions, chat_messages (typed columns)        │
└─────────────────────────────────────────────────────────────────┘
```

### Pros
| Benefit | Description |
|---------|-------------|
| **Already working** | Code exists and functions |
| **Typed schema** | `chat_sessions.title`, `started_at`, etc. not JSON blob |
| **Direct queries** | SQL joins without decoding content |
| **Single service** | No FeedSpine dependency |
| **Simpler deployment** | Just Capture Spine + PostgreSQL |

### Cons
| Drawback | Description |
|----------|-------------|
| **Duplicate logic** | Dedup code differs from FeedSpine pattern |
| **No sightings** | Can't track when chats were re-seen |
| **No layer support** | No Bronze → Silver → Gold progression |
| **Source-specific** | ChatGPT adapter would need separate implementation |

---

## Option C: Hybrid (RECOMMENDED)

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID APPROACH                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  FEEDSPINE: Ingestion + Deduplication                           │
│  ─────────────────────────────────────                          │
│  • CopilotChatAdapter, ChatGPTAdapter, ClaudeAdapter            │
│  • Natural key deduplication                                     │
│  • Sighting tracking                                             │
│  • Emit events: "new_chat_session", "new_chat_message"          │
│                                                                  │
│                         │                                        │
│                         ▼                                        │
│                                                                  │
│  CAPTURE-SPINE: Storage + Presentation                          │
│  ─────────────────────────────────────                          │
│  • Typed tables (chat_sessions, chat_messages)                  │
│  • LLM enrichment (summarize, extract TODOs)                    │
│  • React UI (ChatFeed, WorkSessions)                            │
│  • Subscribes to feedspine events                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **FeedSpine** handles ingestion:
   ```python
   # feedspine/adapters/copilot_chat.py
   class CopilotChatAdapter(FeedAdapter):
       async def fetch(self) -> list[RecordCandidate]:
           sessions = parse_copilot_chats(self.workspace_path)
           return [
               RecordCandidate(
                   natural_key=f"vscode:{session.external_id}",
                   content=session.model_dump(),
                   metadata=Metadata(source="copilot_chat"),
               )
               for session in sessions
           ]
   ```

2. **FeedSpine** emits events on new records:
   ```python
   # feedspine/core/feedspine.py
   async def _process_candidate(self, candidate: RecordCandidate):
       if await self.storage.exists_by_natural_key(candidate.natural_key):
           await self.storage.record_sighting(...)
           return  # Already seen

       record = await self.storage.store(candidate)

       # Emit event for consumers
       await self._emit("record.new", record)
   ```

3. **Capture Spine** subscribes and stores in typed tables:
   ```python
   # capture-spine/app/features/chat_session/feedspine_sync.py
   async def on_new_chat_record(record: dict):
       """Called when FeedSpine captures a new chat."""
       if record["metadata"]["source"] == "copilot_chat":
           session_data = record["content"]
           await chat_service.create_from_feedspine(session_data)
   ```

### Implementation Plan

| Phase | Component | Work |
|-------|-----------|------|
| **1. Adapters** | FeedSpine | `CopilotChatAdapter`, `ChatGPTAdapter` |
| **2. Events** | FeedSpine | Event emission system (or use existing) |
| **3. Sync** | Capture Spine | `feedspine_sync.py` event handler |
| **4. Migration** | Capture Spine | Migrate existing data through FeedSpine |

---

## Recommendation: Start with Option B, Plan for C

### Rationale

1. **Option B works today** - Don't rewrite functioning code
2. **Productivity features are priority** - Work Sessions, Message Enrichment need focus
3. **FeedSpine needs release** - Get it on PyPI first before adding consumers
4. **Hybrid is the future** - Once FeedSpine is stable, add adapters

### Immediate Actions

1. ✅ Keep Capture Spine's direct PostgreSQL for chat sessions
2. 🔄 Release FeedSpine to PyPI (separate effort)
3. 📋 Create `feedspine/adapters/copilot_chat.py` adapter spec
4. 📋 Plan event/webhook system for FeedSpine

### Future Migration Path

Once FeedSpine is on PyPI and stable:

```python
# capture-spine/app/config/feedspine.py
FEEDSPINE_ENABLED = env.bool("FEEDSPINE_ENABLED", default=False)

# capture-spine/app/features/chat_session/service.py
async def ingest_sessions(self, request):
    if settings.FEEDSPINE_ENABLED:
        # New path: through FeedSpine
        await feedspine_client.ingest("copilot_chat", request.sessions)
    else:
        # Current path: direct PostgreSQL
        await self._direct_ingest(request)
```

---

## Package Release Priority

For ecosystem integration to work properly:

| Package | Priority | Blockers | Target |
|---------|----------|----------|--------|
| **entityspine** | ✅ On PyPI | None | Done |
| **spine-core** | P1 | Tests, docs | This week |
| **feedspine** | P1 | Event system, adapters | Next week |
| **genai-spine** | P2 | Depends on above | After feedspine |

---

## Related Documents

- [ECOSYSTEM.md](../architecture/ECOSYSTEM.md) - Full ecosystem architecture
- [copilot-chat-ingestion.md](./copilot-chat-ingestion.md) - Current integration spec
- [FEEDSPINE_INTEGRATION.md](../architecture/FEEDSPINE_INTEGRATION.md) - FeedSpine patterns

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-31 | Start with Option B (direct) | Working code, don't break it |
| 2026-01-31 | Plan for Option C (hybrid) | Best long-term architecture |
| 2026-01-31 | Prioritize FeedSpine PyPI | Required for integration |
