# Capture Spine Productivity Features

## Overview

Productivity features in Capture Spine track actionable items extracted from developer chat sessions and work activities.

## Core Features

### 1. TODO Extraction

Extract actionable TODOs from chat conversations:

```
Chat: "I need to refactor the authentication module and add tests"
       ↓
TODOs:
  - [ ] Refactor authentication module
  - [ ] Add tests for authentication
```

### 2. Code Task Tracking

Track coding tasks mentioned in conversations:

| Task Type | Example | Priority |
|-----------|---------|----------|
| Bug Fix | "fix the null pointer" | High |
| Refactor | "clean up the utils" | Medium |
| Feature | "add pagination" | Medium |
| Test | "write unit tests" | Low |

### 3. Work Session Summaries

Aggregate work from chat sessions:

```python
@dataclass
class WorkSummary:
    session_id: str
    files_discussed: list[str]
    todos_created: int
    todos_completed: int
    time_span: timedelta
```

## Integration with GenAI Spine

Productivity features leverage GenAI Spine for intelligent extraction:

```
┌─────────────────────┐
│   Chat Session      │
│   (messages)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   GenAI Spine       │
│   /v1/execute-prompt│
│   (TODO extraction) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Productivity      │
│   (TODO storage)    │
└─────────────────────┘
```

### Extraction Prompt

```python
EXTRACTION_PROMPT = """
Analyze this chat conversation and extract actionable items.
Return as JSON with fields:
- todos: list of {task, priority, category}
- files_mentioned: list of file paths
- blockers: list of issues preventing progress

Chat:
{messages}
"""
```

## Database Schema

```sql
-- Productivity TODOs
CREATE TABLE productivity_todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    task TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'medium',
    category VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    source_message_id UUID REFERENCES chat_messages(id)
);

-- Work session aggregates
CREATE TABLE work_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id),
    files_discussed JSONB,
    todos_created INT DEFAULT 0,
    todos_completed INT DEFAULT 0,
    duration_minutes INT,
    summary_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## API Endpoints

### List TODOs

```http
GET /api/v1/productivity/todos
Query: ?status=pending&priority=high&limit=20
```

### Create TODO

```http
POST /api/v1/productivity/todos
{
  "task": "Refactor authentication",
  "priority": "high",
  "session_id": "uuid-here"
}
```

### Complete TODO

```http
PATCH /api/v1/productivity/todos/{id}
{
  "status": "completed"
}
```

### Extract TODOs from Session

```http
POST /api/v1/productivity/extract
{
  "session_id": "uuid-here"
}
```

## Event-Driven Updates

When new chat messages arrive:

```python
async def on_chat_session_updated(session_id: UUID):
    """Trigger productivity extraction after chat update."""
    session = await chat_repo.get_session(session_id)

    # Only extract if session has enough content
    if len(session.messages) >= 3:
        await extract_and_store_todos(session)
```

## Configuration

```yaml
# capture-spine/config/productivity.yaml
productivity:
  auto_extract: true
  min_messages_for_extraction: 3
  extraction_debounce_seconds: 30
  priority_keywords:
    high: ["urgent", "critical", "blocker", "asap"]
    medium: ["should", "need to", "want to"]
    low: ["maybe", "consider", "nice to have"]
```

## UI Integration

```typescript
// React component for TODO list
const ProductivityTodos: React.FC = () => {
  const { data: todos } = useQuery('todos', fetchTodos);

  return (
    <div className="todo-list">
      {todos?.map(todo => (
        <TodoItem
          key={todo.id}
          task={todo.task}
          priority={todo.priority}
          onComplete={() => completeTodo(todo.id)}
        />
      ))}
    </div>
  );
};
```

## Metrics

Track productivity feature usage:

| Metric | Description |
|--------|-------------|
| `todos_created` | TODOs extracted per day |
| `todos_completed` | TODOs marked done per day |
| `extraction_latency` | Time to extract from session |
| `sessions_with_todos` | % of sessions with actionable items |

## Future Enhancements

1. **Calendar integration** - Sync TODOs with calendar events
2. **Git integration** - Link TODOs to commits/PRs
3. **Team visibility** - Share productivity across team
4. **Burndown charts** - Visualize TODO completion

## Related Documents

- [genai-capture-integration.md](genai-capture-integration.md) - GenAI integration details
- [copilot-chat-ingestion.md](copilot-chat-ingestion.md) - How chats are captured
- [CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md](CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md) - Storage architecture
