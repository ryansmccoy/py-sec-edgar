# Prompt 03: FeedSpine Chat/Copilot Provider

## Context
You are working on `feedspine` in `b:\github\py-sec-edgar\feedspine`.

FeedSpine is a data ingestion framework that creates **observations** from various data sources. We're adding a **CopilotChatProvider** that ingests VS Code Copilot chat sessions as observations.

## Integration with Capture-Spine Productivity Suite

**CRITICAL**: This connects to a larger productivity feature in capture-spine:
- `capture-spine/docs/features/productivity/vscode-chat-ingestion.md` - Full spec
- `capture-spine/docs/features/productivity/workspace-chat-assistant.md` - Chat UI vision
- `capture-spine/scripts/copilot_chat_parser.py` - **Already exists** (365 lines)

### Existing Parser Script
The parser already exists! Located at: `capture-spine/scripts/copilot_chat_parser.py`

Key functions:
- `list_workspaces()` - Lists all VS Code workspaces with folder mappings
- `find_workspace_by_name(name)` - Finds workspace by folder name
- `parse_chat_session(session_path)` - Parses a chat JSON file
- `extract_tool_calls(response_parts)` - Gets tool usage
- `extract_files_referenced(response_parts)` - Gets files mentioned

### VS Code Chat Storage Location
```
%APPDATA%\Code\User\workspaceStorage\{workspace-hash}\chatSessions\*.json
```

### Chat Session JSON Structure
```json
{
  "version": 3,
  "sessionId": "uuid",
  "creationDate": 1769033019392,  // Unix ms
  "lastMessageDate": 1769744819937,
  "responderUsername": "GitHub Copilot",
  "requests": [
    {
      "message": {"parts": [...], "text": "user prompt"},
      "response": [...],  // Tool calls, responses
      "timestamp": 1769744674566,
      "modelId": "copilot/claude-opus-4.5"
    }
  ]
}
```

## Your Task

### 1. Create FeedSpine Observation Type for Chat Sessions

In `feedspine/observations/chat.py`:

```python
"""Chat session observations for VS Code Copilot ingestion."""
from datetime import datetime
from typing import Literal
from feedspine.core import BaseObservation

class ChatSessionObservation(BaseObservation):
    """Observation for a VS Code Copilot chat session."""

    observation_type: Literal["chat_session"] = "chat_session"

    # Session identity
    session_id: str
    workspace_name: str
    workspace_hash: str

    # Timing
    created_at: datetime
    last_message_at: datetime
    duration_seconds: int | None

    # Content
    title: str | None  # First prompt or auto-generated
    message_count: int
    user_message_count: int
    assistant_message_count: int

    # AI model info
    model_id: str | None
    responder: str  # "GitHub Copilot"

    # Context extraction
    tools_used: list[str]  # ["grep_search", "read_file", ...]
    files_referenced: list[str]  # ["/app/main.py", ...]
    files_created: list[str]
    files_modified: list[str]

    # For deduplication
    @property
    def fingerprint(self) -> str:
        return f"copilot:{self.workspace_hash}:{self.session_id}"

class ChatMessageObservation(BaseObservation):
    """Individual message within a chat session."""

    observation_type: Literal["chat_message"] = "chat_message"

    session_id: str
    message_index: int
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime

    # For assistant messages
    model_id: str | None
    tool_calls: list[dict] | None
    files_referenced: list[str]
```

### 2. Create CopilotChatProvider

In `feedspine/providers/copilot_chat.py`:

```python
"""Provider for VS Code Copilot chat sessions."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from feedspine.core import BaseProvider
from feedspine.observations.chat import ChatSessionObservation, ChatMessageObservation

class CopilotChatProvider(BaseProvider):
    """
    Ingests VS Code Copilot chat sessions as observations.

    Uses the existing parser logic from capture-spine.
    """

    provider_type = "copilot_chat"

    def __init__(
        self,
        workspace_filter: str | None = None,  # Filter to specific workspace
        since: datetime | None = None,  # Only sessions modified after
        include_messages: bool = False,  # Also emit individual messages
    ):
        self.workspace_filter = workspace_filter
        self.since = since
        self.include_messages = include_messages
        self._storage_path = self._get_storage_path()

    def _get_storage_path(self) -> Path:
        """Get VS Code workspace storage path."""
        import sys
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            return Path(appdata) / "Code" / "User" / "workspaceStorage"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Code" / "User" / "workspaceStorage"
        else:
            return Path.home() / ".config" / "Code" / "User" / "workspaceStorage"

    async def fetch(self) -> AsyncIterator[ChatSessionObservation]:
        """Yield chat session observations from VS Code storage."""
        for workspace_dir in self._storage_path.iterdir():
            if not workspace_dir.is_dir():
                continue

            # Check workspace filter
            workspace_info = self._get_workspace_info(workspace_dir)
            if self.workspace_filter and self.workspace_filter not in workspace_info.get("folder", ""):
                continue

            # Find chat sessions
            chat_dir = workspace_dir / "chatSessions"
            if not chat_dir.exists():
                continue

            for session_file in chat_dir.glob("*.json"):
                observation = await self._parse_session(session_file, workspace_info)
                if observation:
                    yield observation

                    if self.include_messages:
                        async for msg_obs in self._yield_messages(session_file, observation.session_id):
                            yield msg_obs

    async def _parse_session(self, path: Path, workspace_info: dict) -> ChatSessionObservation | None:
        """Parse a chat session file into an observation."""
        # Implementation using existing parser logic
        ...
```

### 3. Register with FeedSpine

Update `feedspine/__init__.py`:
```python
from feedspine.providers.copilot_chat import CopilotChatProvider
from feedspine.observations.chat import ChatSessionObservation, ChatMessageObservation

__all__ = [
    ...,
    "CopilotChatProvider",
    "ChatSessionObservation",
    "ChatMessageObservation",
]
```

### 4. Add CLI Command

```bash
# Sync chat sessions from workspace
feedspine ingest copilot-chats --workspace capture-spine

# List available workspaces
feedspine copilot list-workspaces

# Sync all workspaces
feedspine ingest copilot-chats --all
```

## Integration Points

### With capture-spine (Content Ingestion API)
The observations should be POSTed to capture-spine's ingestion API:
```
POST /api/v1/ingest
{
  "content_type": "chat_session",
  "source": {"type": "vscode_copilot", "identifier": "session-uuid"},
  "content": {...}
}
```

See: `capture-spine/docs/features/productivity/content-ingestion-api.md`

### With spine-core (Pipelines)
Create a pipeline to run this regularly:
```python
class IngestCopilotChatsPipeline(Pipeline):
    steps = [
        Step.fetch("fetch_sessions", fetch_copilot_sessions),
        Step.transform("enrich", extract_todos_and_summaries),
        Step.store("store", post_to_capture_spine),
    ]
```

## Success Criteria
- [ ] `ChatSessionObservation` and `ChatMessageObservation` classes defined
- [ ] `CopilotChatProvider` can read VS Code chat sessions
- [ ] Deduplication by session_id works
- [ ] Files referenced/created are extracted
- [ ] Tool usage is tracked
- [ ] CLI commands work
- [ ] Tests pass

## Reference Files
- `capture-spine/scripts/copilot_chat_parser.py` - Existing parser (use as reference)
- `capture-spine/docs/features/productivity/vscode-chat-ingestion.md` - Full spec
- `feedspine/providers/` - Existing provider patterns
