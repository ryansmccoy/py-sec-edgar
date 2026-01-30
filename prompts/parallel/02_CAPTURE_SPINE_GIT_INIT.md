# Prompt 02: Initialize capture-spine Git Repository

> **Priority:** 🔴 HIGH - Must complete before feature commits
> **Est. Time:** 15 minutes
> **Project:** capture-spine

---

## Context

`capture-spine` is the private full-stack application (FastAPI + React) for content capture and enrichment. It currently has **NO git repository initialized**. We need to:

1. Initialize git
2. Create comprehensive `.gitignore`
3. Make initial commit
4. Connect to private GitHub repo (if exists)

## Workspace

```
b:\github\py-sec-edgar\capture-spine\
```

## Task

### Step 1: Initialize Git

```bash
cd b:\github\py-sec-edgar\capture-spine
git init
```

### Step 2: Create .gitignore

Create `b:\github\py-sec-edgar\capture-spine\.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
.venv/
venv/
ENV/
env/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Linting
.ruff_cache/

# Environment
.env
.env.local
.env.*.local
*.env

# Database
*.db
*.sqlite3

# Logs
logs/
*.log

# Celery
celerybeat-schedule
celerybeat.pid

# React/Node (frontend/)
frontend/node_modules/
frontend/dist/
frontend/.next/
frontend/out/
frontend/.cache/
frontend/coverage/
frontend/.eslintcache

# OS
.DS_Store
Thumbs.db

# Secrets (NEVER commit)
secrets/
*.pem
*.key

# Local data
data/
uploads/
```

### Step 3: Create Initial Commit

```bash
git add -A
git commit -m "Initial commit: capture-spine full-stack application

Features:
- FastAPI backend with PostgreSQL, Redis, Elasticsearch
- React frontend with TailwindCSS
- Celery workers for async processing
- LLM enrichment (local Llama + AWS Bedrock)
- Alert rules engine

Structure:
- app/ - FastAPI application
- app/api/ - REST API endpoints
- app/features/ - Feature modules (chat, intelligence, etc.)
- frontend/ - React application
- alembic/ - Database migrations
- scripts/ - Utility scripts
- docs/ - Documentation

Status: Private repository"
```

### Step 4: Check for Existing GitHub Repo

The user mentioned there might be a private repo on GitHub. Check:

```bash
# Try to add remote (adjust URL if different)
git remote add origin https://github.com/ryansmccoy/capture-spine.git

# Or for SSH:
git remote add origin git@github.com:ryansmccoy/capture-spine.git
```

If the remote exists, you may need to:
```bash
git fetch origin
git branch --set-upstream-to=origin/main main
# Or if histories differ:
git pull origin main --allow-unrelated-histories
```

### Step 5: Create Feature Branch for Recent Work

```bash
git checkout -b feature/productivity-chat-ingestion
```

### Step 6: Commit Recent Features

**Commit 1: Chat Feature Backend**
```bash
git add app/features/chat/
git add app/api/routers/chat.py
git add alembic/versions/20260129_add_chat_tables.py
git commit -m "feat(chat): add chat feature backend

- ChatSession and ChatMessage models (Pydantic)
- ChatRepository for PostgreSQL storage
- ChatService business logic
- REST API endpoints for chat CRUD
- Alembic migration for chat tables"
```

**Commit 2: Productivity Scripts**
```bash
git add scripts/copilot_chat_parser.py
git add scripts/scan_docs.py
git add scripts/scan_python_changes.py
git add scripts/scaffold_feature.py
git commit -m "feat(scripts): add productivity tooling scripts

- copilot_chat_parser.py: Parse VS Code Copilot chat sessions
- scan_docs.py: Documentation inventory
- scan_python_changes.py: Track Python file changes
- scaffold_feature.py: Generate feature boilerplate"
```

**Commit 3: Productivity Documentation**
```bash
git add docs/features/productivity/
git add docs/features/file-upload/
git commit -m "docs(productivity): add productivity feature specifications

- VS Code chat ingestion design
- File upload enhancement spec
- Todo management system design
- GenAI chat architecture
- Document lineage tracking
- Implementation guide with vertical slices"
```

**Commit 4: Update Main App**
```bash
git add app/api/main.py
git add app/container.py
git commit -m "feat(api): register chat router and service

- Add chat router to FastAPI app
- Register ChatService in dependency container"
```

## Verification

```bash
git log --oneline -10
git status
```

Should show:
- Clean working directory (or only intentionally untracked files)
- 5+ commits with clear feature boundaries
- Remote configured (if GitHub repo exists)

## Important Notes

- **DO NOT push** without user permission (private repo)
- If `.env` or secrets exist, ensure they're in `.gitignore`
- The `frontend/` folder may have its own node_modules to ignore

---

## Success Criteria

- [ ] Git initialized in capture-spine
- [ ] Comprehensive .gitignore created
- [ ] Initial commit made
- [ ] Recent features committed in logical groups
- [ ] Feature branch created for ongoing work
- [ ] Remote configured (if exists)

---

*This prompt is self-contained. Copy and paste into a new LLM session.*
