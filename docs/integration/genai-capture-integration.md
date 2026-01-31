# GenAI Spine ↔ Capture Spine Integration

## Overview

This document describes how Capture Spine integrates with GenAI Spine to provide LLM-powered productivity features for developer chat sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Capture Spine (Port 8000)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Chat Sessions   │  │ Productivity    │  │ Work Sessions   │  │
│  │ (PostgreSQL)    │  │ (TODOs, etc.)   │  │ (Files, Commits)│  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                │
│                    ┌───────────▼───────────┐                    │
│                    │   GenAI Client        │                    │
│                    │   (async HTTP)        │                    │
│                    └───────────┬───────────┘                    │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   GenAI Spine (8100)    │
                    │   /v1/rewrite           │
                    │   /v1/infer-title       │
                    │   /v1/generate-commit   │
                    │   /v1/execute-prompt    │
                    └─────────────────────────┘
```

## Integration Points

### 1. Message Rewriting

**Endpoint:** `POST /v1/rewrite`

**Use Case:** Clean up chat messages for better searchability and display.

```python
# In Capture Spine
from genai_spine.client import GenAIClient

client = GenAIClient("http://localhost:8100")
result = await client.rewrite(
    text=message.content,
    style="professional",
    context={"source": "copilot_chat"}
)
```

### 2. Title Inference

**Endpoint:** `POST /v1/infer-title`

**Use Case:** Generate titles for chat sessions from message content.

```python
result = await client.infer_title(
    text=first_message.content,
    max_length=80
)
session.title = result.title
```

### 3. Commit Message Generation

**Endpoint:** `POST /v1/generate-commit`

**Use Case:** Generate commit messages from work session context.

```python
result = await client.generate_commit(
    files_changed=work_session.changed_files,
    diff_summary=work_session.diff_summary,
    chat_context=recent_messages
)
```

### 4. Prompt Execution

**Endpoint:** `POST /v1/execute-prompt`

**Use Case:** Run arbitrary prompts for custom productivity features.

```python
result = await client.execute(
    prompt="Extract TODOs from this chat session",
    context={"messages": session.messages}
)
```

## Data Flow: Chat → Productivity

```
1. VS Code chat → Capture Spine (batch insert)
2. Capture Spine detects new session
3. If title missing:
   - Call GenAI /v1/infer-title
   - Update session with generated title
4. If productivity extraction enabled:
   - Call GenAI /v1/execute-prompt (TODO extraction)
   - Store extracted TODOs in productivity table
5. Notify UI of updates
```

## Configuration

```yaml
# capture-spine/config/settings.yaml
genai:
  base_url: "http://localhost:8100"
  timeout: 30
  features:
    auto_title: true
    todo_extraction: true
    message_rewrite: false  # opt-in
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GENAI_SPINE_URL` | `http://localhost:8100` | GenAI service URL |
| `GENAI_TIMEOUT` | `30` | Request timeout in seconds |
| `GENAI_AUTO_TITLE` | `true` | Auto-generate session titles |

## Error Handling

GenAI calls should be **non-blocking** and **failure-tolerant**:

```python
async def enrich_session(session: ChatSession) -> ChatSession:
    try:
        if not session.title and session.messages:
            result = await genai_client.infer_title(
                text=session.messages[0].content
            )
            session.title = result.title
    except GenAIError as e:
        logger.warning(f"GenAI title inference failed: {e}")
        session.title = f"Chat {session.external_id[:8]}"
    return session
```

## Testing

```bash
# Start GenAI Spine
cd genai-spine && uvicorn src.genai_spine.api.app:app --port 8100

# Start Capture Spine
cd capture-spine && uvicorn app.main:app --port 8000

# Test integration
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"external_id": "test-123", "messages": [{"content": "How do I parse JSON in Python?"}]}'

# Check session was enriched with title
curl http://localhost:8000/api/v1/chat/sessions/test-123
```

## Future Enhancements

1. **Streaming responses** - SSE for long-running enrichment
2. **Batch enrichment** - Process multiple sessions efficiently
3. **Custom prompts** - User-defined extraction templates
4. **Cost tracking** - Monitor LLM usage per session

## Related Documents

- [CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md](CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md) - Storage decisions
- [copilot-chat-ingestion.md](copilot-chat-ingestion.md) - Chat ingestion flow
- [../../genai-spine/docs/ECOSYSTEM_INTEGRATION.md](../../genai-spine/docs/ECOSYSTEM_INTEGRATION.md) - GenAI ecosystem role
