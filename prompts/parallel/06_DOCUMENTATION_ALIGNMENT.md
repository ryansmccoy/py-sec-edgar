# Prompt 06: Documentation Alignment & Ecosystem Overview

## Context
You are aligning documentation across the multi-package financial data ecosystem.

## Package Overview

| Package | Purpose | Key Features |
|---------|---------|--------------|
| **entityspine** | Domain models | Shared types, enums, base classes |
| **feedspine** | Data ingestion | Observations, connectors, storage |
| **spine-core** | Orchestration | Pipelines, workflows, execution |
| **capture-spine** | UI + Storage | Research capture, React frontend |
| **py-sec-edgar** | SEC data | EDGAR API, filings, parsing |

## Dependency Flow
```
py-sec-edgar  →  feedspine  →  spine-core  →  capture-spine
                    ↑              ↑              ↑
                    └──────── entityspine ────────┘
```

## Your Task

### 1. Update Each Package's README

#### entityspine/README.md
Should document:
- All domain models exported
- Version compatibility
- How other packages use it
- Quick import examples

Current version: 2.3.3 with:
- Market enums (exchanges, sectors)
- Chat models (workspace, session, message)
- Extraction models (chunked files)
- Workflow models (WorkflowRun, StepExecution)
- Error models (ErrorRecord, ErrorCategory)

#### feedspine/README.md
Should document:
- Observation pattern
- Available connectors
- Storage backends
- Integration with spine-core

#### spine-core/README.md
Should document:
- Pipeline pattern
- Workflow management
- Step types (fetch, transform, store, observe)
- Registry system

#### capture-spine/README.md
Should document:
- Architecture (FastAPI + React)
- Available features (chat, records, search)
- API endpoints
- How to run locally

### 2. Create Ecosystem Overview

Create `docs/ECOSYSTEM.md` in the workspace root with:
- Architecture diagram (ASCII or Mermaid)
- Package responsibilities
- Data flow examples
- Getting started guide

### 3. Align Feature Documentation

For each major feature, ensure docs exist in the implementing package:

| Feature | Primary Package | Doc Location |
|---------|-----------------|--------------|
| Earnings | feedspine | `feedspine/docs/features/estimates-vs-actuals/` |
| Chat | capture-spine | `capture-spine/docs/features/chat/` |
| Observations | feedspine | `feedspine/docs/concepts/observations.md` |
| Pipelines | spine-core | `spine-core/docs/concepts/pipelines.md` |
| Workflows | spine-core | `spine-core/docs/concepts/workflows.md` |

### 4. Update CHANGELOG Files

Each package should have a CHANGELOG.md:
- entityspine: v2.3.0 → 2.3.3 changes
- feedspine: Recent earnings work
- spine-core: Pipeline/workflow changes
- capture-spine: Chat feature addition

## Files to Check/Update

### entityspine
- [ ] `entityspine/README.md` - Update with v2.3.3 content
- [ ] `entityspine/CHANGELOG.md` - Add recent versions
- [ ] `entityspine/docs/models.md` - Document all models

### feedspine
- [ ] `feedspine/README.md` - Ensure complete
- [ ] `feedspine/docs/features/` - Feature docs
- [ ] `feedspine/CHANGELOG.md` - Recent changes

### spine-core
- [ ] `spine-core/README.md` - Update if needed
- [ ] `spine-core/docs/concepts/` - Core concepts
- [ ] `spine-core/CHANGELOG.md` - Recent changes

### capture-spine
- [ ] `capture-spine/README.md` - Create/update
- [ ] `capture-spine/docs/` - Architecture docs
- [ ] `capture-spine/CHANGELOG.md` - Create

### Root workspace
- [ ] `docs/ECOSYSTEM.md` - Create overview
- [ ] `docs/GETTING_STARTED.md` - Unified getting started
- [ ] `docs/DEVELOPMENT.md` - Development setup

## Documentation Standards

### README Structure
```markdown
# Package Name

One-line description.

## Installation

## Quick Start

## Features

## API Reference

## Configuration

## Contributing
```

### Changelog Format (Keep a Changelog)
```markdown
# Changelog

## [Unreleased]

## [2.3.3] - 2024-XX-XX
### Added
- Feature X

### Changed
- Behavior Y

### Fixed
- Bug Z
```

## Success Criteria
- [ ] All package READMEs are complete and accurate
- [ ] Ecosystem overview explains architecture
- [ ] Feature docs are in correct locations
- [ ] CHANGELOGs reflect recent changes
- [ ] Cross-references between packages work
- [ ] New developer can understand system in 15 minutes

## Notes
- Don't duplicate content - link between packages
- Use consistent terminology
- Include diagrams where helpful
- Keep docs close to code they document
