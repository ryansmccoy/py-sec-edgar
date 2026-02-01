# GenAI Spine Migration Checklist

**Status:** 📋 Planned
**Last Updated:** 2026-01-31

---

## Overview

This checklist guides migration of LLM functionality from consumer apps to GenAI Spine.

---

## Phase 1: SDK Setup

### 1.1 Install SDK Client
- [ ] Add `genai-spine-client` to requirements
- [ ] Configure client in app initialization
- [ ] Set up environment variables for GenAI Spine URL
- [ ] Verify connectivity with health check

### 1.2 Configure for Environment
- [ ] Development: Point to local GenAI Spine
- [ ] Staging: Point to staging GenAI Spine
- [ ] Production: Point to production GenAI Spine + API key

---

## Phase 2: Migrate Prompts

### 2.1 Inventory Existing Prompts
- [ ] List all hardcoded prompts in consumer app
- [ ] List all prompt templates in consumer app
- [ ] Document variables used by each prompt

### 2.2 Create Prompts in GenAI Spine
- [ ] Create each prompt via Admin UI or API
- [ ] Test prompts with sample variables
- [ ] Document prompt slugs for consumer app

### 2.3 Update Consumer App
- [ ] Replace hardcoded prompts with `execute_prompt` calls
- [ ] Map local template variables to prompt variables
- [ ] Remove local prompt storage code

---

## Phase 3: Migrate Chat Sessions

### 3.1 Inventory Chat Implementation
- [ ] Document current session storage (DB schema, etc.)
- [ ] Document message format and metadata
- [ ] List features that depend on chat history

### 3.2 Implement GenAI Spine Sessions
- [ ] Replace local session creation with `sessions.create`
- [ ] Replace message sending with `sessions.send_message`
- [ ] Update session retrieval to use `sessions.get`
- [ ] Migrate existing sessions (if needed)

### 3.3 Update Frontend
- [ ] Update API calls to GenAI Spine format
- [ ] Handle session ID from GenAI Spine
- [ ] Update error handling for new error format

---

## Phase 4: Migrate Provider Clients

### 4.1 Remove Duplicate Provider Code
- [ ] Identify direct LLM provider calls (OpenAI, Anthropic, etc.)
- [ ] Replace with GenAI Spine `complete` calls
- [ ] Remove provider client code
- [ ] Remove provider credentials from consumer app

### 4.2 Consolidate Cost Tracking
- [ ] Remove local cost tracking code
- [ ] Use GenAI Spine usage endpoints
- [ ] Update dashboards to query GenAI Spine

---

## Phase 5: Validation

### 5.1 Functional Testing
- [ ] All LLM features work via GenAI Spine
- [ ] Error handling works correctly
- [ ] Metadata flows through correctly

### 5.2 Performance Testing
- [ ] Latency acceptable (added network hop)
- [ ] Throughput sufficient
- [ ] Retry behavior works under load

### 5.3 Monitoring
- [ ] Logs include GenAI Spine request IDs
- [ ] Metrics capture GenAI Spine latency
- [ ] Alerts configured for GenAI Spine errors

---

## Phase 6: Cleanup

### 6.1 Remove Dead Code
- [ ] Remove old LLM provider clients
- [ ] Remove old prompt storage
- [ ] Remove old session storage (if fully migrated)
- [ ] Remove old cost tracking

### 6.2 Documentation
- [ ] Update architecture docs
- [ ] Update API docs
- [ ] Update deployment docs

---

## App-Specific Checklists

### capture-spine

| Component | Status | Notes |
|-----------|--------|-------|
| Chat sessions | ⬜ Pending | `app/features/chat/` |
| LLM transforms | ⬜ Pending | `app/features/llm_transform/` |
| Provider clients | ⬜ Pending | `app/llm/providers/` |
| Cost tracking | ⬜ Pending | `app/llm/cost_tracker.py` |
| Frontend chat | ⬜ Pending | `frontend/src/features/chat/` |
| Frontend transform | ⬜ Pending | `frontend/src/features/llm-transform/` |

### feedspine

| Component | Status | Notes |
|-----------|--------|-------|
| TBD | ⬜ Pending | Needs analysis |

### entityspine

| Component | Status | Notes |
|-----------|--------|-------|
| TBD | ⬜ Pending | Needs analysis |

---

## Rollback Plan

If migration causes issues:

1. **Keep old code available** (feature-flagged or separate branch)
2. **SDK client has fallback mode** - Can point back to local implementation
3. **Session data preserved** - Can re-sync if needed
4. **Prompts exist in both places** during transition

---

## See Also

- [CAPTURE_SPINE_INTEGRATION_ANALYSIS.md](CAPTURE_SPINE_INTEGRATION_ANALYSIS.md) - Detailed migration options
- [CONSUMER_QUICKSTART.md](CONSUMER_QUICKSTART.md) - SDK usage guide
- [API_CONTRACT.md](../api/API_CONTRACT.md) - API specification
