# Prompt 01: Commit entityspine v2.3.3 Features

> **Priority:** 🔴 HIGH - Must complete before other prompts
> **Est. Time:** 30 minutes
> **Project:** entityspine

---

## Context

You are working on `entityspine`, the domain model library for a financial data ecosystem. There are 30+ uncommitted files from recent development sessions that need to be organized into logical commits.

## Workspace

```
b:\github\py-sec-edgar\entityspine\
```

## Current Git Status

The following files need to be committed (grouped by feature):

### Group 1: Workflow/Execution Models (v2.3.3)
```
src/entityspine/domain/workflow.py      # ExecutionContext, Result[T], WorkflowDefinition
src/entityspine/domain/errors.py        # ErrorCategory, ErrorContext, ErrorRecord
```

### Group 2: Extraction/NLP Models (v2.3.2)
```
src/entityspine/domain/extraction.py    # ExtractionType, StoryCluster, SignificanceScore
```

### Group 3: Chat/Productivity Models (v2.3.1)
```
src/entityspine/domain/chat.py          # ChatWorkspace, ChatSession, ChatMessage
tests/domain/test_chat.py               # Chat model tests
```

### Group 4: Market Infrastructure (v2.3.0)
```
src/entityspine/domain/markets.py       # Exchange, BrokerDealer, Clearinghouse
src/entityspine/domain/enums/markets.py # Market-related enums
src/entityspine/domain/reference_data/  # Exchange reference data
```

### Group 5: Source Adapters
```
src/entityspine/sources/base.py
src/entityspine/sources/gleif.py
src/entityspine/sources/gleif_mic_lei.py
src/entityspine/sources/iso10383.py
src/entityspine/sources/iso3166.py
src/entityspine/sources/iso4217.py
tests/sources/
```

### Group 6: Documentation
```
docs/FEATURES.md
docs/guides/
docs/INTEGRATION_IMPROVEMENTS.md
docs/MARKET_DATA_ARCHITECTURE.md
project_meta.yaml
```

### Group 7: Modified files (need to be included)
```
src/entityspine/domain/__init__.py      # Updated exports
src/entityspine/domain/enums/__init__.py
```

## Task

1. **Check current status:**
   ```bash
   cd b:\github\py-sec-edgar\entityspine
   git status
   ```

2. **Create logical commits** in this order:

   **Commit 1: Market Infrastructure (v2.3.0)**
   ```bash
   git add src/entityspine/domain/markets.py
   git add src/entityspine/domain/enums/markets.py
   git add src/entityspine/domain/reference_data/
   git commit -m "feat(markets): add Exchange, BrokerDealer, Clearinghouse models (v2.3.0)

   - Exchange with MIC codes, trading sessions, segments
   - BrokerDealer with CRD numbers, registrations, disciplinary actions
   - Clearinghouse with memberships and clearing services
   - Reference data for US/EU/APAC exchanges
   - Factory functions: create_exchange, create_broker_dealer, create_clearinghouse"
   ```

   **Commit 2: Chat Models (v2.3.1)**
   ```bash
   git add src/entityspine/domain/chat.py
   git add tests/domain/test_chat.py
   git commit -m "feat(chat): add ChatWorkspace, ChatSession, ChatMessage models (v2.3.1)

   - ChatWorkspace for project-level grouping
   - ChatSession with hash-based deduplication
   - ChatMessage with role, timestamps, metadata
   - Factory functions: create_chat_workspace, create_chat_session, create_chat_message
   - Full test coverage"
   ```

   **Commit 3: Extraction Models (v2.3.2)**
   ```bash
   git add src/entityspine/domain/extraction.py
   git commit -m "feat(extraction): add NLP/extraction models (v2.3.2)

   - ExtractionType enum (COMPANY, PERSON, INSTRUMENT, etc.)
   - ExtractedEntity, TextSpan for entity mentions
   - StoryCluster for topic/story tracking
   - SignificanceScore with composite scoring
   - ContentLink for article relationships
   - Migrated from capture-spine for ecosystem-wide reuse"
   ```

   **Commit 4: Workflow/Error Models (v2.3.3)**
   ```bash
   git add src/entityspine/domain/workflow.py
   git add src/entityspine/domain/errors.py
   git commit -m "feat(workflow): add ExecutionContext, Result[T], Error models (v2.3.3)

   - ExecutionContext for pipeline lineage tracking
   - Ok/Err Result pattern for explicit error handling
   - WorkflowDefinition, WorkflowStep, WorkflowRun
   - QualityStatus, QualityCategory, QualityResult
   - ErrorCategory with is_retryable(), is_likely_transient()
   - ErrorContext, ErrorRecord for structured error tracking
   - Migrated from spine-core for stdlib-only guarantee"
   ```

   **Commit 5: Source Adapters**
   ```bash
   git add src/entityspine/sources/
   git add tests/sources/
   git commit -m "feat(sources): add reference data source adapters

   - GLEIF LEI lookup adapter
   - ISO 10383 MIC code adapter
   - ISO 3166 country code adapter
   - ISO 4217 currency adapter
   - Base adapter protocol"
   ```

   **Commit 6: Update exports and docs**
   ```bash
   git add src/entityspine/domain/__init__.py
   git add src/entityspine/domain/enums/__init__.py
   git add docs/
   git add project_meta.yaml
   git commit -m "docs: update exports and documentation for v2.3.x

   - Export all new domain models in __init__.py
   - Add FEATURES.md with auto-generated feature list
   - Add guides/ folder with financial data pitfalls
   - Add project_meta.yaml for ecosystem metadata"
   ```

3. **Update version in pyproject.toml** to `2.3.3`

4. **Tag the release:**
   ```bash
   git tag -a v2.3.3 -m "Release v2.3.3 - Workflow, Error, and Extraction models"
   ```

5. **DO NOT push** - just commit locally. User will review and push.

## Verification

After commits, run:
```bash
git log --oneline -10
```

Should show 6 new commits with clear feature boundaries.

## Files to NOT commit (ignore)

- `entityspine_data/` (local data)
- `site/` (generated docs)
- `check_db.py` (local script)
- Any `.pyc` or `__pycache__`

---

## Success Criteria

- [ ] All 30+ files committed in logical groups
- [ ] Each commit has descriptive message with scope
- [ ] Version bumped to 2.3.3
- [ ] Tag created
- [ ] `git status` shows clean working directory

---

*This prompt is self-contained. Copy and paste into a new LLM session.*
