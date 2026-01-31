# Package Release Plan (PyPI)

## Overview

This document tracks the release status and plan for publishing ecosystem packages to PyPI.

## Package Status

| Package | Current | Target | PyPI Status | Priority |
|---------|---------|--------|-------------|----------|
| **entityspine** | 2.3.3 | 2.3.3 | ✅ Published | - |
| **spine-core** | 0.1.0 | 1.0.0 | 🔴 Not published | P1 |
| **feedspine** | 0.1.0 | 1.0.0 | 🔴 Not published | P1 |
| **genai-spine** | 0.1.0 | 1.0.0 | 🔴 Not published | P2 |

## Release Order

```
Week 1: spine-core → PyPI
        ↓
Week 2: feedspine → PyPI (depends on entityspine)
        ↓
Week 3: genai-spine → PyPI (depends on entityspine)
        ↓
Week 4: capture-spine → PyPI (depends on all)
```

## entityspine (✅ Complete)

**Status:** Published to PyPI as `entityspine==2.3.3`

**Installation:**
```bash
pip install entityspine
```

**Key exports:**
- `ExecutionContext`, `Result[T]`, `ErrorCategory`
- `ChatWorkspace`, `ChatSession`, `ChatMessage`
- `Company`, `Filing`, `Earnings`

---

## spine-core (P1)

**Status:** 🔴 Needs release preparation

### Pre-Release Checklist

- [ ] **pyproject.toml** - Verify metadata
- [ ] **README.md** - Update with usage examples
- [ ] **Tests** - Ensure >80% coverage
- [ ] **Type hints** - Run mypy, fix errors
- [ ] **Dependencies** - Pin versions
- [ ] **Changelog** - Create CHANGELOG.md
- [ ] **License** - MIT license file

### Package Contents

```
spine-core/
├── src/spine_core/
│   ├── __init__.py
│   ├── manifest.py          # WorkManifest
│   ├── quality.py           # QualityRunner
│   └── idempotency.py       # Idempotency helpers
├── tests/
├── pyproject.toml
├── README.md
└── CHANGELOG.md
```

### Build & Publish

```bash
cd spine-core

# Build
python -m build

# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Install and verify
pip install --index-url https://test.pypi.org/simple/ spine-core

# Publish to PyPI
twine upload dist/*
```

---

## feedspine (P1)

**Status:** 🔴 Needs release preparation

### Pre-Release Checklist

- [ ] **pyproject.toml** - Add entityspine dependency
- [ ] **Event system** - Implement record_event
- [ ] **PostgreSQL adapter** - Complete implementation
- [ ] **Tests** - Integration tests with SQLite
- [ ] **Documentation** - Usage examples

### Dependencies

```toml
[project]
dependencies = [
    "entityspine>=2.3.0",
]

[project.optional-dependencies]
postgres = ["asyncpg>=0.28.0"]
sqlite = ["aiosqlite>=0.19.0"]
```

### Package Contents

```
feedspine/
├── src/feedspine/
│   ├── __init__.py
│   ├── core/
│   │   └── feedspine.py      # FeedSpine orchestrator
│   ├── protocols/
│   │   └── storage.py        # StorageBackend protocol
│   ├── models/
│   │   ├── record.py         # Record, RecordCandidate
│   │   └── sighting.py       # Sighting audit trail
│   └── adapters/
│       ├── postgres.py
│       └── sqlite.py
├── tests/
├── pyproject.toml
└── README.md
```

---

## genai-spine (P2)

**Status:** 🔴 Needs release preparation

### Pre-Release Checklist

- [ ] **Core complete** - Rewrite, commit, execute endpoints
- [ ] **Providers** - OpenAI, Anthropic, Local
- [ ] **Cost tracking** - Usage metrics
- [ ] **Tests** - Mock provider tests
- [ ] **Dependencies** - entityspine, openai, anthropic

### Dependencies

```toml
[project]
dependencies = [
    "entityspine>=2.3.0",
    "fastapi>=0.104.0",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
openai = ["openai>=1.0.0"]
anthropic = ["anthropic>=0.18.0"]
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

## Version Strategy

Use semantic versioning:

- **1.0.0** - Initial stable release
- **1.0.x** - Bug fixes only
- **1.x.0** - New features, backward compatible
- **2.0.0** - Breaking changes

## Post-Release Verification

After each release:

```bash
# Fresh environment test
python -m venv test-env
source test-env/bin/activate  # or test-env\Scripts\activate on Windows

# Install from PyPI
pip install spine-core feedspine genai-spine

# Verify imports
python -c "from spine_core import WorkManifest; print('spine-core OK')"
python -c "from feedspine import FeedSpine; print('feedspine OK')"
python -c "from genai_spine import GenAIClient; print('genai-spine OK')"
```

## Related Documents

- [../architecture/ECOSYSTEM.md](../architecture/ECOSYSTEM.md) - Package ecosystem overview
- [CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md](CHAT_STORAGE_ARCHITECTURE_ANALYSIS.md) - Integration decisions
