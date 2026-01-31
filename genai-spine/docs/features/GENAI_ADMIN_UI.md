# GenAI Admin UI - Feature Specification

**Status:** Proposed
**Priority:** P1
**Created:** 2026-01-31

---

## Overview

A standalone web-based admin interface for managing and interacting with the GenAI Spine service, independent of Capture Spine or any other application. This provides a unified control plane for prompt management, model testing, and conversational AI interactions.

---

## Problem Statement

Currently, to interact with GenAI Spine you must:
1. Use curl/httpie for API calls
2. Build capabilities into each consuming app (Capture Spine, FeedSpine, etc.)
3. No unified way to test prompts, manage models, or have exploratory conversations

**Need:** A dedicated UI that serves as the "control tower" for all GenAI operations.

---

## Core Features

### 1. Chat Interface (VS Code Copilot Style)

A conversational interface similar to VS Code Copilot Chat:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Model Selector** | Dropdown to pick any available model (Ollama, OpenAI, Anthropic) | P0 |
| **Chat Sessions** | Create, name, and organize chat sessions | P0 |
| **Session Persistence** | Save all chats to database for future reference | P0 |
| **Context Attachments** | Attach files, code, or documents as context | P1 |
| **System Prompt Override** | Set custom system prompts per session | P1 |
| **Temperature/Settings** | Adjust model parameters per chat | P1 |
| **Export** | Export chat as Markdown, JSON, or share link | P2 |
| **Search** | Full-text search across all saved chats | P2 |

**UI Concept:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  GenAI Admin                                    [Model: gpt-4o ▼]  │
├──────────────────┬──────────────────────────────────────────────────┤
│  SESSIONS        │                                                  │
│  ───────────     │  You: Can you review this architecture doc?     │
│  > New Chat      │                                                  │
│  📁 Today        │  [architecture.md attached]                      │
│    └ API Review  │                                                  │
│    └ Prompt Test │  ─────────────────────────────────────────────  │
│  📁 Yesterday    │                                                  │
│    └ SWOT Analys │  Assistant: I've reviewed the architecture...   │
│    └ Code Review │                                                  │
│                  │  The main strengths are:                        │
│  [+ New Session] │  1. Clean separation of concerns...             │
│                  │                                                  │
├──────────────────┼──────────────────────────────────────────────────┤
│  PROMPTS         │  ┌─────────────────────────────────────────────┐ │
│  ───────────     │  │ Type your message...              [Send ➤] │ │
│  📝 Rewrite      │  └─────────────────────────────────────────────┘ │
│  📝 Summarize    │  [📎 Attach] [⚙️ Settings] [🔄 Switch Model]    │
│  📝 SWOT Review  │                                                  │
└──────────────────┴──────────────────────────────────────────────────┘
```

### 2. Prompt Management Dashboard

Full CRUD interface for prompt templates:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Prompt Library** | Browse all prompts with search/filter | P0 |
| **Prompt Editor** | Edit system prompt, user template, variables | P0 |
| **Version History** | View and rollback to previous versions | P0 |
| **Test Playground** | Test prompt with sample inputs | P0 |
| **Variable Preview** | See how variables render in templates | P1 |
| **Import/Export** | Bulk import/export prompts as YAML | P1 |
| **Categories/Tags** | Organize prompts by category | P1 |
| **Usage Stats** | See which prompts are used most | P2 |

**Prompt Editor UI:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  Edit Prompt: code-review                              [Save] [Test]│
├─────────────────────────────────────────────────────────────────────┤
│  Name: Code Review Assistant                                        │
│  Slug: code-review                                                  │
│  Category: [Development ▼]                                          │
│                                                                     │
│  System Prompt:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ You are an expert code reviewer. Review the provided code for   ││
│  │ best practices, security issues, and potential improvements.    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  User Template:                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Please review this {{language}} code:                           ││
│  │                                                                 ││
│  │ ```{{language}}                                                 ││
│  │ {{code}}                                                        ││
│  │ ```                                                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
│  Variables: language, code                                          │
│  Version: 3 (last edited 2026-01-30)                               │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Model Management

View and configure available models:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Model List** | See all available models across providers | P0 |
| **Model Info** | Context length, pricing, capabilities | P0 |
| **Health Status** | Real-time provider health checks | P1 |
| **Default Model** | Set default model for new chats | P1 |
| **Model Comparison** | Side-by-side response comparison | P2 |
| **Cost Dashboard** | Track costs by model/day/user | P2 |

### 4. Testing Playground

Environment for testing new ideas and enrichments:

| Feature | Description | Priority |
|---------|-------------|----------|
| **Quick Test** | One-off prompt execution with any model | P0 |
| **A/B Compare** | Run same prompt on multiple models | P1 |
| **Batch Test** | Test prompt with multiple inputs | P1 |
| **Response Diff** | Visual diff between model responses | P1 |
| **Latency Metrics** | Track response times | P1 |
| **Save as Prompt** | Convert successful test to saved prompt | P2 |

---

## Technical Architecture

### Stack Options

**Option A: Lightweight (Recommended for MVP)**
- Frontend: React + Tailwind CSS + shadcn/ui
- State: React Query for API calls
- Storage: Uses GenAI Spine's existing database

**Option B: Full-Featured**
- Frontend: Next.js with App Router
- Auth: NextAuth.js or Clerk
- Real-time: WebSockets for streaming responses

### API Requirements

New endpoints needed in GenAI Spine:

```
# Chat Sessions
POST   /v1/sessions              # Create session
GET    /v1/sessions              # List sessions
GET    /v1/sessions/{id}         # Get session with messages
DELETE /v1/sessions/{id}         # Delete session
POST   /v1/sessions/{id}/messages # Add message to session

# Enhanced Models
GET    /v1/models/health         # Provider health status
GET    /v1/models/compare        # Side-by-side comparison

# Enhanced Prompts (existing, may need additions)
GET    /v1/prompts/export        # Export all as YAML
POST   /v1/prompts/import        # Bulk import
```

### Database Schema Additions

```sql
-- Chat sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    model VARCHAR(100),
    system_prompt TEXT,
    settings JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Chat messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20),  -- 'user', 'assistant', 'system'
    content TEXT,
    attachments JSONB,  -- [{filename, content, type}]
    tokens_used INTEGER,
    created_at TIMESTAMP
);
```

---

## Implementation Phases

### Phase 1: MVP (2 weeks)
- [ ] Basic chat interface with model selection
- [ ] Session persistence (create, list, view)
- [ ] Prompt library browser
- [ ] Simple prompt editor

### Phase 2: Enhanced (2 weeks)
- [ ] Prompt testing playground
- [ ] Version history viewer
- [ ] File attachments
- [ ] Settings per session

### Phase 3: Advanced (2 weeks)
- [ ] Model comparison tool
- [ ] Cost tracking dashboard
- [ ] Export/import
- [ ] Search across chats

---

## Related Documents

- [MULTI_MODEL_REVIEW_WORKFLOW.md](MULTI_MODEL_REVIEW_WORKFLOW.md) - Cross-model review process
- [../STATUS.md](../STATUS.md) - Current GenAI Spine status
- [../TODO.md](../TODO.md) - Implementation roadmap
