# Copilot Chat Ingestion - Cross-Project Integration

> **Flow**: VS Code Copilot → entityspine → feedspine → capture-spine

---

## Original User Request (Jan 29, 2026)

> "I want to ingest the chat sessions from my VS Code workspace into groups by like project then sessions then chat messages so I can easily replay my chat or display it in the order it happened or in reverse order"
>
> "We probably need to add like this as a model in entityspine so we can manage it but feedspine will need to be able to do the same type of logic it does RSS feeds or filings, deduplicate the blob of JSON"
>
> "I want the chats in capture spine to be basically like a real time feed I can follow that has my chat history but is enriched by LLMs and keep track of and features kept tracked of automatically, so like a todo management system"

### Follow-up (Jan 29, 2026)

> "Does this work with like chat messaging feature as well? Does it work the same as like with LLM like ChatGPT?"

**Answer**: Yes! The entityspine domain models are source-agnostic. We just need different adapters:
- VS Code Copilot (existing parser)
- ChatGPT exports (needs adapter)
- Claude exports (needs adapter)

---

## Implementation Status

| Component | Location | Status | Description |
|-----------|----------|--------|-------------|
| **Domain Models** | `entityspine/src/entityspine/domain/chat.py` | ✅ Complete | ChatWorkspace, ChatSession, ChatMessage |
| **Unit Tests** | `entityspine/tests/domain/test_chat.py` | ✅ Complete | 13 tests passing |
| **VS Code Parser** | `capture-spine/scripts/copilot_chat_parser.py` | ✅ Complete | 365 lines, tested |
| **feedspine Provider** | `feedspine/src/providers/copilot_chat.py` | ⏳ Next | CopilotChatProvider |
| **capture-spine API** | `capture-spine/app/api/routers/chat.py` | 🔴 Planned | REST endpoints |
| **capture-spine UI** | `capture-spine/frontend/components/ChatFeed.tsx` | 🔴 Planned | React component |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VS Code Copilot                                │
│                                                                             │
│   %APPDATA%\Code\User\workspaceStorage\<hash>\chatSessions\*.json          │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTITYSPINE (Domain Models)                         │
│                                                                             │
│   ChatWorkspace          ChatSession              ChatMessage               │
│   ├── workspace_id       ├── session_id          ├── message_id            │
│   ├── project_name       ├── project_name        ├── role (user/assistant) │
│   ├── sessions[]         ├── messages[]          ├── content               │
│   └── captured_at        ├── content_hash        ├── content_hash          │
│                          └── captured_at         └── timestamp             │
│                                                                             │
│   Key Features:                                                             │
│   • stdlib-only (no Pydantic)                                               │
│   • Hash-based deduplication                                                │
│   • Chronological/reverse ordering                                          │
│   • Factory functions for easy creation                                     │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FEEDSPINE (Feed Provider)                             │
│                                                                             │
│   class CopilotChatProvider(FeedProvider):                                  │
│       def fetch(self) -> list[ChatSession]:                                 │
│           # Use existing parser                                             │
│           # Deduplicate by session_hash / content_hash                      │
│           # Return only new messages                                        │
│                                                                             │
│   Key Features:                                                             │
│   • Same dedup logic as RSS/SEC providers                                   │
│   • Incremental ingestion (only new messages)                               │
│   • Multi-workspace support                                                 │
│   • ChatGPT/Claude adapter support                                          │
└────────────────────────────────────────┬────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CAPTURE-SPINE (Storage & UI)                          │
│                                                                             │
│   Backend (FastAPI):                                                        │
│   ├── POST /api/chat/ingest     ──▶ Trigger ingestion                      │
│   ├── GET  /api/chat/sessions   ──▶ List sessions by workspace             │
│   ├── GET  /api/chat/messages   ──▶ Get messages (chrono/reverse)          │
│   └── POST /api/chat/enrich     ──▶ LLM extract TODOs                      │
│                                                                             │
│   Frontend (React):                                                         │
│   ├── ChatFeed.tsx              ──▶ Real-time message stream               │
│   ├── ChatSessionList.tsx       ──▶ Session browser                        │
│   └── TodoExtractor.tsx         ──▶ View extracted TODOs                   │
│                                                                             │
│   Key Features:                                                             │
│   • Store in PostgreSQL as records                                          │
│   • LLM enrichment (summarize, extract TODOs)                               │
│   • Full-text search                                                        │
│   • WebSocket real-time updates                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Code Examples

### entityspine Domain Model

```python
from entityspine.domain import (
    ChatWorkspace, ChatSession, ChatMessage,
    create_chat_workspace, create_chat_session, create_chat_message,
    CHAT_ROLE_USER, CHAT_ROLE_ASSISTANT,
)

# Create hierarchy
workspace = create_chat_workspace("hash123", "C:/projects/py-sec-edgar")
session = create_chat_session("sess-1", "py-sec-edgar")

# Add messages
session.add_message(create_chat_message("How do I parse 8-K?", CHAT_ROLE_USER))
session.add_message(create_chat_message("Use py-sec-edgar...", CHAT_ROLE_ASSISTANT))

workspace.add_session(session)

# Query
print(workspace.sessions_chronological)  # Oldest first
print(workspace.sessions_reverse)        # Newest first
```

### feedspine Provider (Planned)

```python
from feedspine.providers import CopilotChatProvider

provider = CopilotChatProvider(
    workspaces=["py-sec-edgar", "capture-spine"],
)

# Fetch new sessions (deduplicated)
new_sessions = provider.fetch()

# Store in capture-spine
for session in new_sessions:
    capture_spine.store_record(
        record_type="chat_session",
        content=session.to_dict(),
        source="vscode-copilot",
    )
```

---

## Multi-Source Support

The domain models work with any chat source:

| Source | Storage Format | Adapter Status |
|--------|---------------|----------------|
| VS Code Copilot | Local JSON files | ✅ Parser exists |
| ChatGPT | Export ZIP | 🔴 Needs adapter |
| Claude (web) | Export JSON | 🔴 Needs adapter |
| LM Studio | Local JSON | 🔴 Needs adapter |

```python
# ChatGPT adapter example (tested and working)
def parse_chatgpt_conversation(conv: dict) -> ChatSession:
    session = create_chat_session(conv.get('id'), 'chatgpt-export')
    for msg in conv.get('mapping', {}).values():
        if msg.get('message'):
            role = msg['message']['author']['role']
            content = ''.join(msg['message']['content']['parts'])
            session.add_message(create_chat_message(content, role))
    return session
```

---

## Next Steps

1. **[ ] feedspine CopilotChatProvider** - Wire parser to provider interface
2. **[ ] capture-spine API** - `/api/chat/*` endpoints
3. **[ ] capture-spine UI** - React chat feed component
4. **[ ] LLM enrichment** - Auto-extract TODOs from conversations
5. **[ ] ChatGPT adapter** - Support exported conversations

---

## Related Documentation

- [feedspine/docs/features/copilot-chat-ingestion/](../../feedspine/docs/features/copilot-chat-ingestion/)
- [capture-spine/docs/features/productivity/](../../capture-spine/docs/features/productivity/)
- [capture-spine/docs/features/file-upload/](../../capture-spine/docs/features/file-upload/)
- [entityspine/src/entityspine/domain/chat.py](../../entityspine/src/entityspine/domain/chat.py)

---

*Last updated: Jan 29, 2026*
