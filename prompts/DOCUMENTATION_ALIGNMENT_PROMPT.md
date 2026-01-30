# LLM Prompt: Ecosystem Documentation & Architecture Alignment

> **Purpose:** Hand this prompt to an LLM to systematically align all projects in the py-sec-edgar ecosystem with best practices and create self-generating documentation.

---

## 🎯 Mission

You are tasked with aligning the documentation, architecture, and development practices across a multi-project Python/TypeScript ecosystem. The goal is to:

1. **Establish consistency** — All projects follow the same documentation patterns
2. **Enable self-generating docs** — Each project can auto-generate its own documentation
3. **Create living ecosystem docs** — Auto-generate an ECOSYSTEM.md from project metadata
4. **Improve discoverability** — Cross-link important files (manifestos, models, architecture)
5. **Automate feature tracking** — Commits generate feature entries, TODOs tracked
6. **Standardize CI/CD** — PyPI, GitHub Actions, Docker across all projects
7. **Organize by feature** — Logical folder structure with date-based grouping

---

## ⚠️ IMPORTANT CONSTRAINTS

- **DO NOT push to GitHub** without explicit user permission
- **DO NOT publish to PyPI** without explicit user permission
- Create configs and scripts but leave them ready to run manually
- Ask before any destructive operations (moving/deleting files)

---

## 📊 Per-Project Checklists

Use these checklists when working on each project. Check off items as you complete them.

### ✅ ENTITYSPINE Checklist (Gold Standard - verify complete)
**Location:** `entityspine/`

- [ ] **README.md** — Has badges, quick start, architecture diagram
- [ ] **pyproject.toml** — Has all metadata, scripts, optional deps
- [ ] **mkdocs.yml** — Configured for auto-doc generation
- [ ] **src/entityspine/__init__.py** — Has `__all__`, module docstring
- [ ] **src/entityspine/domain/__init__.py** — Exports all domain models
- [ ] **docs/ARCHITECTURE.md** — System design documented
- [ ] **docs/CHANGELOG.md** — Version history current
- [ ] **docs/DEVELOPMENT_HISTORY.md** — Session history documented
- [ ] **.github/workflows/ci.yml** — CI pipeline exists
- [ ] **All public classes** — Have docstrings with examples
- [ ] **All public functions** — Have type hints + docstrings
- [ ] **project_meta.yaml** — Created with ecosystem metadata

**Key files to reference:**
- `src/entityspine/domain/entity.py` — Entity model pattern
- `src/entityspine/domain/chat.py` — Chat model pattern (newest)
- `src/entityspine/domain/observation.py` — Observation pattern

---

### ✅ FEEDSPINE Checklist
**Location:** `feedspine/`

- [ ] **README.md** — Has badges, quick start, architecture diagram
- [ ] **pyproject.toml** — Has all metadata, scripts, optional deps
- [ ] **mkdocs.yml** — Configured for auto-doc generation
- [ ] **src/feedspine/__init__.py** — Has `__all__`, module docstring
- [ ] **docs/ARCHITECTURE.md** — System design documented
- [ ] **docs/CHANGELOG.md** — Version history current
- [ ] **docs/FEATURES.md** — Auto-generated feature list
- [ ] **docs/TODO.md** — Auto-generated TODO list
- [ ] **.github/workflows/ci.yml** — CI pipeline exists
- [ ] **.github/workflows/release.yml** — PyPI release workflow (manual trigger)
- [ ] **docker/Dockerfile** — Standardized Dockerfile
- [ ] **Makefile** — Common commands
- [ ] **All public classes** — Have docstrings with examples
- [ ] **All public functions** — Have type hints + docstrings
- [ ] **project_meta.yaml** — Created with ecosystem metadata

**Key files to reference:**
- `src/feedspine/core/feedspine.py` — Main orchestration
- `src/feedspine/adapter/base.py` — Feed adapter pattern
- `src/feedspine/models/record.py` — Record model

---

### ✅ SPINE-CORE Checklist
**Location:** `spine-core/`

- [ ] **README.md** — Has badges, quick start, architecture diagram
- [ ] **packages/spine-core/pyproject.toml** — Has all metadata
- [ ] **packages/spine-domains/pyproject.toml** — Has all metadata
- [ ] **mkdocs.yml** — Configured for auto-doc generation
- [ ] **docs/ARCHITECTURE.md** — System design documented
- [ ] **docs/CHANGELOG.md** — Version history current
- [ ] **docs/FEATURES.md** — Auto-generated feature list
- [ ] **.github/workflows/ci.yml** — CI pipeline exists
- [ ] **docker/docker-compose.yml** — Standardized compose
- [ ] **Makefile** — Common commands
- [ ] **All public classes** — Have docstrings with examples
- [ ] **project_meta.yaml** — Created with ecosystem metadata

**Key files to reference:**
- `packages/spine-core/src/spine/core/__init__.py` — Core exports
- `packages/spine-core/src/spine/core/execution.py` — ExecutionContext
- `packages/spine-core/src/spine/core/result.py` — Result[T] pattern

---

### ✅ CAPTURE-SPINE Checklist
**Location:** `capture-spine/`

- [ ] **README.md** — Has badges, quick start, architecture diagram
- [ ] **pyproject.toml** — Has all metadata, scripts
- [ ] **app/__init__.py** — Has `__all__`, module docstring
- [ ] **docs/ARCHITECTURE.md** — System design documented
- [ ] **docs/CHANGELOG.md** — Version history current
- [ ] **docs/FEATURES.md** — Auto-generated feature list
- [ ] **docs/TODO.md** — Auto-generated TODO list
- [ ] **docs/features/** — Feature docs organized
- [ ] **.github/workflows/ci.yml** — CI pipeline exists
- [ ] **docker/Dockerfile** — Standardized Dockerfile
- [ ] **docker-compose.yml** — Standardized compose
- [ ] **Makefile** — Common commands
- [ ] **All public classes** — Have docstrings
- [ ] **project_meta.yaml** — Created with ecosystem metadata

**Key files to reference:**
- `app/api/main.py` — FastAPI app
- `app/models.py` — Pydantic models
- `scripts/copilot_chat_parser.py` — Working parser example

---

### ✅ TRADING-DESKTOP Checklist
**Location:** `spine-core/trading-desktop/trading-desktop/`

- [ ] **README.md** — Has overview, modules, tech stack
- [ ] **package.json** — Has all scripts, dependencies
- [ ] **tsconfig.json** — TypeScript config
- [ ] **typedoc.json** — TypeDoc configured
- [ ] **docs/** — Component documentation
- [ ] **src/types/** — TypeScript interfaces documented
- [ ] **docker/Dockerfile** — Standardized Dockerfile
- [ ] **.github/workflows/ci.yml** — CI pipeline (lint, build)
- [ ] **project_meta.yaml** — Created with ecosystem metadata

**Key files to reference:**
- `src/App.tsx` — Route definitions
- `src/types/` — TypeScript interfaces
- `src/api/` — API client patterns

---

### ✅ PY-SEC-EDGAR Checklist
**Location:** `.` (root)

- [ ] **README.md** — Has badges, quick start, examples
- [ ] **pyproject.toml** — Has all metadata
- [ ] **py_sec_edgar/__init__.py** — Has `__all__`, module docstring
- [ ] **docs/ARCHITECTURE.md** — System design documented
- [ ] **docs/CHANGELOG.md** — Version history current
- [ ] **.github/workflows/ci.yml** — CI pipeline exists
- [ ] **docker/Dockerfile** — Standardized Dockerfile (if needed)
- [ ] **Makefile** — Common commands
- [ ] **All public classes** — Have docstrings
- [ ] **project_meta.yaml** — Created with ecosystem metadata

---

## 📁 Projects to Align

| Project | Location | Language | Gold Standard? |
|---------|----------|----------|----------------|
| **entityspine** | `/entityspine/` | Python | ✅ YES - Use as reference |
| **feedspine** | `/feedspine/` | Python | ✅ YES - Secondary reference |
| **spine-core** | `/spine-core/` | Python | Needs alignment |
| **capture-spine** | `/capture-spine/` | Python + React | Needs alignment |
| **trading-desktop** | `/spine-core/trading-desktop/trading-desktop/` | React/TypeScript | Needs alignment |
| **py-sec-edgar** | `/` (root) | Python | Needs alignment |

---

## 📋 Task 1: Audit Each Project

For each project, gather this information:

### 1.1 Structure Audit
```
Project: {name}
Location: {path}

Source Layout:
- src/ or app/ location: {path}
- Main __init__.py exports: {list}
- Key modules: {list with purposes}

Documentation:
- README.md: {exists? quality 1-5}
- docs/ folder: {exists? structure}
- Docstrings: {coverage % estimate}
- Type hints: {coverage % estimate}

Configuration:
- pyproject.toml or package.json: {exists?}
- mkdocs.yml or similar: {exists?}
- Auto-doc generation: {configured?}
```

### 1.2 Key Files to Catalog
For each project, identify and catalog:
- `__init__.py` — Public API exports
- `README.md` — Project overview
- `ARCHITECTURE.md` or similar — System design
- `CHANGELOG.md` — Version history
- Model files (e.g., `domain/*.py`, `models/*.py`)
- Manifesto/design docs
- Example files

---

## 📋 Task 2: Apply Gold Standard (entityspine)

### 2.1 entityspine Patterns to Replicate

**Docstring Format:**
```python
"""
Module description - one line.

Extended description if needed.

DESIGN PRINCIPLES:
- Key principle 1
- Key principle 2

Example:
    >>> from entityspine.domain import Entity
    >>> entity = Entity(primary_name="Apple Inc.")
"""
```

**Class Docstring:**
```python
@dataclass
class Entity:
    """
    A legal/organizational identity (company, fund, person).

    Attributes:
        entity_id: Unique identifier (ULID)
        primary_name: Official legal name
        entity_type: Classification (COMPANY, FUND, PERSON, etc.)

    Example:
        >>> entity = Entity(primary_name="Apple Inc.", entity_type=EntityType.COMPANY)
        >>> entity.entity_id
        '01HXYZ...'
    """
```

**__init__.py Pattern:**
```python
"""
Package Name - One-line description.

This package provides:
- Feature 1
- Feature 2

Quick Start:
    >>> from package import MainClass
    >>> obj = MainClass()
"""

from .module1 import Class1, Class2
from .module2 import function1

__all__ = [
    "Class1",
    "Class2",
    "function1",
]
```

### 2.2 README.md Template

Each project README should have:
```markdown
# Project Name

> **One-line tagline**

[![Badges](...)

---

## Overview

2-3 sentences explaining what this project does.

## Quick Start

```python
# Minimal working example
```

## Architecture

```
ASCII diagram showing structure
```

## Key Modules

| Module | Purpose |
|--------|---------|
| ... | ... |

## Integration with Ecosystem

How this project connects to others.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/api/)
- [Examples](examples/)

## Related Projects

- [entityspine](../entityspine/) — Domain models
- [feedspine](../feedspine/) — Feed ingestion
- ...
```

---

## 📋 Task 3: Set Up Self-Generating Docs

### 3.1 For Python Projects (mkdocs + mkdocstrings)

Create/update these files:

**mkdocs.yml:**
```yaml
site_name: {Project Name}
site_description: {One-line description}
repo_url: https://github.com/ryansmccoy/{repo-name}

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true
            members_order: source

nav:
  - Home: index.md
  - Getting Started: getting-started.md
  - Architecture: architecture.md
  - API Reference:
    - Domain Models: api/domain.md
    - Core: api/core.md
  - Examples: examples.md
  - Changelog: changelog.md
```

**docs/api/domain.md (example):**
```markdown
# Domain Models

::: entityspine.domain
    options:
      show_root_heading: false
      members:
        - Entity
        - Security
        - Listing
```

### 3.2 For TypeScript Projects (TypeDoc)

**typedoc.json:**
```json
{
  "entryPoints": ["src/index.ts"],
  "out": "docs/api",
  "plugin": ["typedoc-plugin-markdown"],
  "readme": "README.md"
}
```

---

## 📋 Task 4: Create Ecosystem Documentation Generator

### 4.1 Create `scripts/generate_ecosystem_docs.py`

This script should:
1. Scan each project directory
2. Extract metadata from `pyproject.toml` / `package.json`
3. Parse `__init__.py` to get public exports
4. Read key markdown files
5. Generate a unified ECOSYSTEM.md

**Script outline:**
```python
#!/usr/bin/env python3
"""
Generate ECOSYSTEM.md from project metadata.

Usage:
    python scripts/generate_ecosystem_docs.py > ECOSYSTEM.md
    python scripts/generate_ecosystem_docs.py --format json > ecosystem.json
"""

import tomllib
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProjectInfo:
    name: str
    path: Path
    version: str
    description: str
    language: str
    status: str  # public/private
    key_modules: list[str]
    key_docs: list[str]
    dependencies: list[str]
    exports: list[str]

PROJECTS = [
    ("entityspine", "entityspine/"),
    ("feedspine", "feedspine/"),
    ("spine-core", "spine-core/"),
    ("capture-spine", "capture-spine/"),
    ("trading-desktop", "spine-core/trading-desktop/trading-desktop/"),
    ("py-sec-edgar", "."),
]

def scan_project(name: str, path: str) -> ProjectInfo:
    """Extract metadata from a project."""
    # Read pyproject.toml or package.json
    # Parse __init__.py for exports
    # Find key documentation files
    # Return ProjectInfo
    ...

def generate_ecosystem_md(projects: list[ProjectInfo]) -> str:
    """Generate ECOSYSTEM.md content."""
    ...

def main():
    projects = [scan_project(name, path) for name, path in PROJECTS]
    print(generate_ecosystem_md(projects))

if __name__ == "__main__":
    main()
```

### 4.2 Metadata Files Each Project Needs

Create `project_meta.yaml` in each project root:
```yaml
name: entityspine
tagline: "Zero-Dependency Entity Resolution"
status: public  # public | private
pypi: entityspine  # or null
github: ryansmccoy/entity-spine  # or null

categories:
  - domain-models
  - entity-resolution

key_features:
  - Entity → Security → Listing hierarchy
  - Multi-source identifier resolution
  - stdlib-only core (zero dependencies)

key_docs:
  - docs/ARCHITECTURE.md
  - docs/DEVELOPMENT_HISTORY.md

key_models:
  - src/entityspine/domain/entity.py
  - src/entityspine/domain/security.py
  - src/entityspine/domain/chat.py

integration_points:
  - feedspine: "Domain models for observations"
  - capture-spine: "Entity resolution for records"

recent_features:
  - date: 2026-01-29
    feature: "Chat domain models (ChatWorkspace, ChatSession, ChatMessage)"
    version: v2.3.1
```

---

## 📋 Task 5: Alignment Checklist

For each project, verify:

### Documentation
- [ ] README.md follows template
- [ ] All public classes have docstrings
- [ ] All public functions have docstrings with examples
- [ ] Type hints on all public APIs
- [ ] mkdocs.yml or typedoc.json configured
- [ ] docs/ folder has architecture.md
- [ ] CHANGELOG.md exists and is current

### Code Organization
- [ ] `__init__.py` has module docstring
- [ ] `__init__.py` exports public API with `__all__`
- [ ] Clear separation: domain/ vs adapters/ vs core/
- [ ] No circular imports

### Ecosystem Integration
- [ ] project_meta.yaml exists
- [ ] Links to related projects in README
- [ ] Integration examples documented

### Self-Generating Docs
- [ ] Can run `mkdocs build` or `typedoc` successfully
- [ ] API docs auto-generated from docstrings
- [ ] Examples render correctly

---

## 📋 Task 6: Generate Updated ECOSYSTEM.md

After aligning all projects, generate a new ECOSYSTEM.md that includes:

1. **Auto-generated project table** from project_meta.yaml files
2. **Architecture diagram** showing data flow
3. **Feature matrix** — what each project provides
4. **Recent changes** — aggregated from CHANGELOGs
5. **Links to key docs** — manifestos, architecture, models
6. **Integration patterns** — how projects connect

### Expected Output Structure:
```markdown
# Financial Data Ecosystem

> Auto-generated on {date}

## Projects

{Auto-generated table from project_meta.yaml}

## Architecture

{Diagram}

## Feature Matrix

| Feature | entityspine | feedspine | capture-spine | ... |
|---------|-------------|-----------|---------------|-----|
| Entity Resolution | ✅ | - | uses | ... |
| Feed Deduplication | - | ✅ | uses | ... |

## Recent Development

### entityspine v2.3.1 (Jan 29, 2026)
- Chat domain models

### feedspine v0.x.x
- ...

## Key Documentation

### Architecture & Design
- [entityspine Architecture](entityspine/docs/ARCHITECTURE.md)
- [feedspine Design](feedspine/docs/architecture/)
- ...

### Domain Models
- [Entity, Security, Listing](entityspine/src/entityspine/domain/)
- [Chat Models](entityspine/src/entityspine/domain/chat.py)
- [Observation Models](entityspine/src/entityspine/domain/observation.py)

### Integration Guides
- [Chat Ingestion Flow](docs/integration/copilot-chat-ingestion.md)
- ...

## User Feedback Log

{Pulled from docs or tracked separately}
```

---

## 🚀 Execution Order

1. **Audit** — Scan all projects, document current state
2. **Organize** — Group files by feature using modification dates
3. **Plan** — Identify gaps for each project
4. **Align entityspine** — Ensure gold standard is complete
5. **Align feedspine** — Secondary reference
6. **Align spine-core** — Apply patterns
7. **Align capture-spine** — Apply patterns
8. **Align trading-desktop** — TypeScript patterns
9. **Create generator script** — `generate_ecosystem_docs.py`
10. **Create project_meta.yaml** — For each project
11. **Set up Git hooks** — Commit → feature tracking
12. **Set up CI/CD** — GitHub Actions, PyPI (ready but not pushed)
13. **Standardize Docker** — Consistent Dockerfiles
14. **Test generation** — Run script, verify output

---

## 📋 Task 7: Automatic Feature Tracking from Commits

### 7.1 Git Commit Convention

All commits should follow Conventional Commits:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types that generate feature entries:
- `feat:` → New feature entry
- `fix:` → Bug fix entry
- `docs:` → Documentation update
- `refactor:` → Code improvement

Example:
```
feat(chat): add ChatWorkspace, ChatSession, ChatMessage models

- Support VS Code Copilot chat ingestion
- Hash-based deduplication
- Chronological/reverse ordering
```

### 7.2 Post-Commit Hook: `.git/hooks/post-commit`

```bash
#!/bin/bash
# Auto-generate feature entry from commit

COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_HASH=$(git log -1 --pretty=%h)
COMMIT_DATE=$(git log -1 --pretty=%ci | cut -d' ' -f1)
PROJECT_NAME=$(basename $(pwd))

# Extract type and scope
if [[ $COMMIT_MSG =~ ^(feat|fix|docs|refactor)\(([^)]+)\):(.+) ]]; then
    TYPE="${BASH_REMATCH[1]}"
    SCOPE="${BASH_REMATCH[2]}"
    DESC="${BASH_REMATCH[3]}"

    # Append to CHANGELOG.md
    if [ "$TYPE" == "feat" ]; then
        echo "### $COMMIT_DATE - $SCOPE" >> docs/FEATURES.md
        echo "- $DESC ($COMMIT_HASH)" >> docs/FEATURES.md
        echo "" >> docs/FEATURES.md
    fi
fi
```

### 7.3 Feature Tracking Files

Each project should have:

**docs/FEATURES.md** (auto-generated, newest first):
```markdown
# Feature History

<!-- Auto-generated from commits. Do not edit manually. -->

### 2026-01-29 - chat
- Add ChatWorkspace, ChatSession, ChatMessage models (a1b2c3d)

### 2026-01-28 - markets
- Add Exchange, BrokerDealer infrastructure (e4f5g6h)
```

**docs/CHANGELOG.md** (semantic versioning):
```markdown
# Changelog

## [2.3.1] - 2026-01-29
### Added
- Chat domain models for VS Code Copilot ingestion
- ChatWorkspace, ChatSession, ChatMessage dataclasses

## [2.3.0] - 2026-01-28
### Added
- Market infrastructure models
```

### 7.4 TODO Tracking

**docs/TODO.md** (auto-extracted from code):
```markdown
# TODOs

<!-- Auto-generated. Run `python scripts/extract_todos.py` to update -->

## High Priority
- [ ] Implement feedspine CopilotChatProvider (chat.py:45)

## Normal Priority
- [ ] Add pagination to chat history API (api.py:123)

## Low Priority
- [ ] Consider caching for entity lookups (resolver.py:89)
```

**scripts/extract_todos.py:**
```python
#!/usr/bin/env python3
"""Extract TODOs from source code and generate TODO.md"""

import re
from pathlib import Path

TODO_PATTERN = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):\s*(.+)', re.IGNORECASE)

def extract_todos(src_dir: Path) -> list[dict]:
    todos = []
    for py_file in src_dir.rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), 1):
            if match := TODO_PATTERN.search(line):
                todos.append({
                    "type": match.group(1).upper(),
                    "text": match.group(2),
                    "file": str(py_file.relative_to(src_dir)),
                    "line": i,
                })
    return todos

def generate_todo_md(todos: list[dict]) -> str:
    # Group by priority, format as markdown
    ...
```

---

## 📋 Task 8: Directory Organization by Feature

### 8.1 Analyze Current Structure

For each project, run:
```python
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict

def analyze_directory(project_path: str):
    """Group files by modification date and infer features."""
    files_by_week = defaultdict(list)

    for path in Path(project_path).rglob("*"):
        if path.is_file() and not any(p.startswith('.') for p in path.parts):
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            week_key = mtime.strftime("%Y-W%W")
            files_by_week[week_key].append({
                "path": str(path),
                "modified": mtime,
                "name": path.name,
            })

    return dict(files_by_week)
```

### 8.2 Recommended Directory Structure

```
project/
├── .github/
│   └── workflows/
│       ├── ci.yml           # Lint, test, type check
│       ├── release.yml      # PyPI publish (manual trigger)
│       └── docs.yml         # Auto-generate docs
├── docker/
│   ├── Dockerfile           # Production image
│   ├── Dockerfile.dev       # Development image
│   └── docker-compose.yml   # Local dev stack
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── FEATURES.md          # Auto-generated
│   ├── TODO.md              # Auto-generated
│   ├── api/                 # Auto-generated API docs
│   └── features/            # Feature-specific docs
│       └── {feature-name}/
│           └── README.md
├── examples/
│   └── {feature-name}/
├── scripts/
│   ├── extract_todos.py
│   ├── generate_docs.py
│   └── release.py
├── src/{package}/
│   ├── __init__.py
│   ├── domain/              # Domain models
│   ├── adapters/            # External integrations
│   ├── core/                # Core utilities
│   └── {feature}/           # Feature modules
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── .pre-commit-config.yaml
├── pyproject.toml
├── project_meta.yaml        # Ecosystem metadata
└── README.md
```

### 8.3 Migration Script

```python
#!/usr/bin/env python3
"""Reorganize project directory by feature."""

import shutil
from pathlib import Path
from datetime import datetime

def suggest_reorganization(project_path: str) -> dict:
    """Analyze and suggest file moves. Does NOT execute."""
    suggestions = {
        "moves": [],
        "creates": [],
        "deletes": [],
    }

    # Analyze current structure
    # Suggest moves based on file patterns and dates
    # Return suggestions for human review

    return suggestions

def execute_reorganization(suggestions: dict, dry_run: bool = True):
    """Execute suggested moves. Requires explicit confirmation."""
    if dry_run:
        print("DRY RUN - No changes will be made")

    for move in suggestions["moves"]:
        print(f"Move: {move['from']} -> {move['to']}")
        if not dry_run:
            # Actually move the file
            pass
```

---

## 📋 Task 9: CI/CD Pipeline Setup

### 9.1 GitHub Actions: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run pytest --cov=src/ --cov-report=xml
      - uses: codecov/codecov-action@v4

  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --dev
      - run: uv run mkdocs build
```

### 9.2 GitHub Actions: `.github/workflows/release.yml`

```yaml
name: Release to PyPI

on:
  workflow_dispatch:  # Manual trigger only
    inputs:
      version:
        description: 'Version to release (e.g., 1.2.3)'
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    environment: pypi  # Requires approval
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish
```

### 9.3 PyPI Configuration: `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{package-name}"
version = "0.1.0"
description = "{description}"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Ryan McCoy", email = "ryansmccoy@gmail.com" }
]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.urls]
Homepage = "https://github.com/ryansmccoy/{repo}"
Documentation = "https://ryansmccoy.github.io/{repo}/"

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy", "mkdocs-material", "mkdocstrings[python]"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

---

## 📋 Task 10: Docker Standardization

### 10.1 Standard Dockerfile (Python)

```dockerfile
# docker/Dockerfile
FROM python:3.12-slim as base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ ./src/

# Production stage
FROM base as production
CMD ["uv", "run", "python", "-m", "{package}"]

# Development stage
FROM base as development
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "pytest", "--watch"]
```

### 10.2 Standard docker-compose.yml

```yaml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: production
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data

  dev:
    build:
      context: .
      dockerfile: docker/Dockerfile
      target: development
    volumes:
      - .:/app
      - /app/.venv  # Don't mount venv
    ports:
      - "8000:8000"
```

### 10.3 Makefile for Common Commands

```makefile
.PHONY: install lint test docs build docker-build docker-run

install:
	uv sync --dev

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src/

test:
	uv run pytest

docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

build:
	uv build

docker-build:
	docker build -t {package}:latest -f docker/Dockerfile .

docker-run:
	docker compose up -d

clean:
	rm -rf dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/
```

---

## 📝 Deliverables

After completing this task, provide:

1. **Audit report** — Current state of each project
2. **Reorganization plan** — Suggested file moves (for approval)
3. **Changes made** — List of files created/modified per project
4. **Updated ECOSYSTEM.md** — Auto-generated version
5. **Generator scripts** — `generate_ecosystem_docs.py`, `extract_todos.py`
6. **CI/CD configs** — GitHub Actions workflows (ready but not pushed)
7. **Docker configs** — Standardized Dockerfiles
8. **Git hooks** — Post-commit feature tracking
9. **Recommendations** — Further improvements

---

## 💡 Tips

- Start with reading entityspine's `__init__.py` and domain/ modules to understand the gold standard
- Use `grep -r "def " --include="*.py" | head -50` to quickly find functions needing docstrings
- Check if mkdocs is already configured before creating new config
- Preserve existing good documentation, don't overwrite
- When in doubt, ask the user for clarification
- **Always show planned changes before executing**
- **Never push to GitHub or PyPI without explicit permission**

---

## 🔗 Context Files to Read First

1. `entityspine/src/entityspine/__init__.py` — Gold standard exports
2. `entityspine/src/entityspine/domain/__init__.py` — Gold standard domain
3. `entityspine/README.md` — Gold standard README
4. `feedspine/src/feedspine/__init__.py` — Secondary reference
5. `ECOSYSTEM.md` — Current ecosystem doc to improve
6. `docs/integration/README.md` — Integration patterns
7. Each project's `pyproject.toml` — Current build config
8. Each project's existing `.github/workflows/` — Current CI setup

---

## 📊 Success Criteria

After completion, the ecosystem should have:

- [ ] All 6 projects follow same README template
- [ ] All projects have `project_meta.yaml`
- [ ] All projects have consistent `pyproject.toml`
- [ ] All projects have `docs/FEATURES.md` (auto-generated)
- [ ] All projects have `docs/TODO.md` (auto-generated)
- [ ] All projects have `docs/CHANGELOG.md`
- [ ] All projects have `.github/workflows/ci.yml`
- [ ] All projects have `.github/workflows/release.yml`
- [ ] All projects have standardized Dockerfiles
- [ ] All projects have Makefile with common commands
- [ ] `generate_ecosystem_docs.py` produces valid ECOSYSTEM.md
- [ ] Git hooks auto-update feature tracking on commit
- [ ] All Python code has type hints and docstrings

---

## 📋 MASTER EXECUTION CHECKLIST

Use this checklist to track overall progress. Complete in order.

### Phase 1: Audit & Planning
- [ ] Read all gold standard files (entityspine)
- [ ] Complete Task 1 audit for each project
- [ ] Create audit report summarizing gaps
- [ ] Get user approval on reorganization plan

### Phase 2: Per-Project Alignment

**2.1 ENTITYSPINE (Gold Standard - Verify)**
- [ ] Verify README.md follows template
- [ ] Verify pyproject.toml has all fields
- [ ] Verify docs/ARCHITECTURE.md exists
- [ ] Verify docs/CHANGELOG.md exists
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Create docs/FEATURES.md (auto-gen)
- [ ] Create docs/TODO.md (auto-gen)
- [ ] Document any patterns to copy

**2.2 FEEDSPINE**
- [ ] Update README.md to match template
- [ ] Update pyproject.toml to match standard
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create docs/CHANGELOG.md
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Create .github/workflows/release.yml
- [ ] Create docker/Dockerfile
- [ ] Create Makefile
- [ ] Create docs/FEATURES.md (auto-gen)
- [ ] Create docs/TODO.md (auto-gen)

**2.3 SPINE-CORE**
- [ ] Update README.md to match template
- [ ] Verify pyproject.toml in packages/
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create docs/CHANGELOG.md
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Create Makefile
- [ ] Create docs/FEATURES.md (auto-gen)
- [ ] Create docs/TODO.md (auto-gen)

**2.4 CAPTURE-SPINE**
- [ ] Update README.md to match template
- [ ] Update pyproject.toml to match standard
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create docs/CHANGELOG.md
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Verify docker/Dockerfile exists
- [ ] Create Makefile
- [ ] Create docs/FEATURES.md (auto-gen)
- [ ] Create docs/TODO.md (auto-gen)

**2.5 TRADING-DESKTOP**
- [ ] Verify README.md (recently updated)
- [ ] Verify package.json has scripts
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create typedoc.json for API docs
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Create docker/Dockerfile
- [ ] Create Makefile

**2.6 PY-SEC-EDGAR (Root)**
- [ ] Verify README.md
- [ ] Verify pyproject.toml
- [ ] Create docs/ARCHITECTURE.md
- [ ] Create docs/CHANGELOG.md
- [ ] Create project_meta.yaml
- [ ] Create .github/workflows/ci.yml
- [ ] Create Makefile
- [ ] Create docs/FEATURES.md (auto-gen)
- [ ] Create docs/TODO.md (auto-gen)

### Phase 3: Automation Scripts
- [ ] Create scripts/generate_ecosystem_docs.py
- [ ] Create scripts/extract_todos.py
- [ ] Create scripts/feature_tracker.py
- [ ] Create .git/hooks/post-commit (optional)
- [ ] Test all scripts work correctly
- [ ] Document script usage in README

### Phase 4: Verification & Report
- [ ] Run all CI checks locally
- [ ] Verify ECOSYSTEM.md can be regenerated
- [ ] Verify docs/FEATURES.md updates from git
- [ ] Verify docs/TODO.md extracts from code
- [ ] Create final report for user
- [ ] Get user approval before any GitHub push

---

## 🔄 Ongoing Maintenance Tasks

After initial alignment, these should happen automatically:

| When | What | How |
|------|------|-----|
| Every commit | Update FEATURES.md | Git hook or script |
| Weekly | Regenerate ECOSYSTEM.md | `python scripts/generate_ecosystem_docs.py` |
| On release | Update CHANGELOG.md | Manual or conventional-commits |
| When TODOs change | Update docs/TODO.md | `python scripts/extract_todos.py` |

---

## ⏱️ Estimated Time Per Phase

| Phase | Estimated Time | Notes |
|-------|----------------|-------|
| Audit & Planning | 30-60 min | Reading existing files |
| entityspine | 15-30 min | Mostly verification |
| feedspine | 45-60 min | Full alignment |
| spine-core | 30-45 min | Monorepo complexity |
| capture-spine | 45-60 min | Full stack |
| trading-desktop | 30-45 min | TypeScript/React |
| py-sec-edgar | 30-45 min | Root project |
| Automation scripts | 60-90 min | Creating generators |
| Verification | 30-45 min | Testing everything |

**Total:** ~6-8 hours of work

---

*End of Documentation Alignment Prompt*

---

*This prompt is designed to be handed to an LLM for a multi-session documentation alignment task.*
