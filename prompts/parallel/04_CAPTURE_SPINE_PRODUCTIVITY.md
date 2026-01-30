# Prompt 04: Capture-Spine Productivity Suite (Chat + File Monitoring + Todos)

## Context
You are working on `capture-spine` in `b:\github\py-sec-edgar\capture-spine`.

This is a **comprehensive productivity feature** that includes:
1. Chat UI (ChatGPT-like interface)
2. VS Code Copilot chat ingestion
3. File/directory monitoring
4. Todo management system
5. Document lineage tracking

## Existing Documentation (READ THESE FIRST)

All specs are in `capture-spine/docs/features/productivity/`:

| File | Lines | What It Covers |
|------|-------|----------------|
| `README.md` | ~100 | Overview, feature list, implementation priorities |
| `IMPLEMENTATION_GUIDE.md` | ~277 | **Vertical slices approach, execution order** |
| `genai-chat-architecture.md` | ~556 | Full chat system with models, prompts, tracking |
| `vscode-chat-ingestion.md` | ~217 | Parse VS Code Copilot chats into feed |
| `workspace-chat-assistant.md` | ~411 | ChatGPT-like interface for workspace |
| `todo-management.md` | ~367 | Todo system with LLM extraction |
| `document-lineage.md` | ~483 | Track file origins and chat links |
| `file-upload-enhancement.md` | ~368 | Drag-drop with LLM processing |
| `content-ingestion-api.md` | ~436 | Unified API for all content |

## Existing Scripts (ALREADY BUILT)

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/copilot_chat_parser.py` | ✅ Parse VS Code chats | 365 lines, working |
| `scripts/scan_docs.py` | ✅ Scan docs folder | 333 lines, working |
| `scripts/scan_python_changes.py` | ✅ Track Python changes | 311 lines, working |
| `scripts/scaffold_feature.py` | Scaffold new features | Exists |

## Existing Backend (PARTIALLY BUILT)

From `genai-chat-architecture.md`:

| Component | Location | Status |
|-----------|----------|--------|
| LLM Provider Abstraction | `app/llm/providers/base.py` | ✅ Complete |
| OpenAI/Anthropic/Ollama | `app/llm/providers/*.py` | ✅ Working |
| Prompt Management | `app/features/llm_transform/` | ✅ CRUD + Versions |
| Transform History | `transformations` table | ✅ Full tracking |
| **Chat Backend** | `app/features/chat/` | ⚠️ Basic (from entityspine migration) |

## Your Task: Follow the Implementation Guide

The IMPLEMENTATION_GUIDE.md defines **vertical slices**. Follow them:

### Slice 1: Chat Ingest (2-3 days) - PRIORITY
**Goal**: Ingest VS Code Copilot chats as records

```
Day 1: Backend
├── Create migration: chat_sessions, chat_messages tables
├── Create ChatSessionRepository
├── Add POST /api/v1/ingest/chat-session endpoint
└── Test: curl can insert session

Day 2: Integration
├── Update copilot_chat_parser.py to POST to API
├── Add CLI: uv run python -m app.cli ingest chat-session --workspace capture-spine
└── Test: Run CLI, see record in database

Day 3: Frontend
├── Add "Import Chats" button to sidebar
├── Show chat sessions in timeline with special card
└── Test: Click button, see imported chat
```

### Slice 2: Basic Chat UI (3-4 days)
**Goal**: ChatGPT-like interface

```
Day 1: Backend
├── Create conversations, conversation_messages tables (see genai-chat-architecture.md)
├── Create ConversationRepository, ConversationService

Day 2: API
├── POST /api/v2/chat/conversations
├── GET /api/v2/chat/conversations/{id}
├── POST /api/v2/chat/conversations/{id}/messages
├── SSE streaming endpoint

Day 3-4: Frontend
├── ChatSidebar (conversation list)
├── ChatWindow (messages with streaming)
├── ChatInput (with attachments)
├── Model selector (extract from TransformModal)
```

### Slice 3: File Monitoring (NEW - for Everything Search)
**Goal**: Monitor workspace for file changes, track in capture-spine

This combines with the Everything Search integration:

```python
# app/features/file_monitor/service.py
class FileMonitorService:
    """
    Monitors directories for file changes.
    Uses Everything Search API for efficient Windows file tracking.
    """

    async def scan_directory(
        self,
        path: str,
        extensions: list[str] = [".md", ".py", ".ts"],
        since_hours: int = 24,
    ) -> list[FileChange]:
        """Scan for recent file changes using Everything API."""
        # Use Everything Search HTTP API
        query = f'path:"{path}" dm:last{since_hours}hours ({" ".join(f"*.{ext}" for ext in extensions)})'
        ...

    async def track_changes(
        self,
        path: str,
        poll_interval: int = 300,  # 5 minutes
    ) -> AsyncIterator[FileChange]:
        """Continuously monitor for changes."""
        ...

    async def create_lineage_record(
        self,
        file_path: str,
        chat_session_id: str | None = None,
    ) -> DocumentLineage:
        """Create document lineage record linking file to origin."""
        ...
```

**Database Tables** (from document-lineage.md):
```sql
CREATE TABLE document_lineage (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    version INTEGER DEFAULT 1,
    origin_type VARCHAR(50),  -- 'vscode_copilot', 'capture_chat', 'manual'
    origin_chat_session_id UUID,
    git_commit_hash VARCHAR(40),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE document_chat_links (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    chat_session_id UUID NOT NULL,
    link_type VARCHAR(50),  -- 'created', 'modified', 'referenced'
    context_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Slice 4: Todo Extraction (2-3 days)
**Goal**: LLM extracts todos from chats

```sql
CREATE TABLE todos (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    source_type VARCHAR(50),  -- 'chat', 'code', 'manual'
    source_id VARCHAR(255),
    source_context TEXT,
    project VARCHAR(100),
    tags TEXT[],
    ai_summary TEXT,
    ai_effort_estimate VARCHAR(20),  -- 'small', 'medium', 'large'
    created_at TIMESTAMPTZ DEFAULT now(),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
```

## Frontend Components Needed

```
frontend/src/features/chat/
├── ChatSidebar.tsx          # Conversation list
├── ChatWindow.tsx           # Message display
├── ChatInput.tsx            # Input with attachments
├── ChatMessage.tsx          # Single message
├── ModelSelector.tsx        # Provider/model picker
└── index.ts

frontend/src/features/productivity/
├── FileMonitor.tsx          # Show recent file changes
├── TodoList.tsx             # Todo management
├── TodoItem.tsx             # Single todo with context
├── DocumentLineage.tsx      # Show file origins
└── index.ts
```

## Integration with Everything Search

The file monitoring should use Everything Search API when available:

```python
# Check if Everything is running
async def everything_available() -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8080/?search=test&json=1&count=1")
            return response.status_code == 200
    except:
        return False

# Use Everything for fast file search
async def find_recent_files_everything(path: str, hours: int) -> list[dict]:
    query = f'path:"{path}" dm:last{hours}hours'
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8080/",
            params={"search": query, "json": 1, "count": 1000}
        )
        return response.json().get("results", [])

# Fallback to filesystem scan
async def find_recent_files_fs(path: str, hours: int) -> list[dict]:
    # Use scan_docs.py / scan_python_changes.py logic
    ...
```

## Success Criteria

### Slice 1 (Chat Ingest)
- [ ] Can run `python scripts/copilot_chat_parser.py --workspace capture-spine --post`
- [ ] Chat sessions appear in database
- [ ] Timeline shows imported chats

### Slice 2 (Chat UI)
- [ ] Can create new conversation
- [ ] Can send message, get streaming response
- [ ] Can switch models (OpenAI ↔ Anthropic ↔ Ollama)
- [ ] History persists

### Slice 3 (File Monitor)
- [ ] Everything Search integration works (when available)
- [ ] Falls back to filesystem scan
- [ ] Document lineage records created
- [ ] Files linked to originating chat sessions

### Slice 4 (Todos)
- [ ] "Extract Todos" button in chat
- [ ] LLM extracts todos with context
- [ ] Todos linked to source conversation
- [ ] Todo list UI with status management

## Notes
- Follow the IMPLEMENTATION_GUIDE.md vertical slice approach
- Build one thing that works end-to-end before moving to next
- The scripts already exist - leverage them!
- Backend LLM infrastructure is solid - focus on chat-specific pieces
