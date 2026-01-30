# Ecosystem Integration Prompt

> **Use this prompt when working across multiple projects**
> Copy and paste into new conversations for context

---

## The Prompt

```markdown
I'm working on an integrated financial data platform with these projects:

## Projects (in dependency order)

1. **py-sec-edgar** (PyPI: public)
   - SEC EDGAR filing downloader and XBRL parser
   - Fetches 10-K, 10-Q, 8-K filings
   - Low-level data acquisition

2. **entityspine** (PyPI: public)
   - Entity master / knowledge graph
   - stdlib-only core for universal compatibility
   - Links: organizations ↔ people ↔ filings ↔ tickers

3. **feedspine** (PyPI: planned 1.0.0)
   - Feed management layer
   - Observations (estimates, actuals, forecasts)
   - Comparison engine (estimates vs actuals)
   - Depends on: entityspine

4. **spine-core** (GitHub: public)
   - Pipeline/workflow framework
   - Execution tracking (ExecutionRepository)
   - Alert framework (Slack, Email, PagerDuty)
   - Depends on: entityspine, feedspine

5. **capture-spine** (PRIVATE - keep private)
   - Record-based data capture
   - LLM enrichment (local Llama + AWS Bedrock)
   - React newsfeed UI
   - Alert rules engine
   - Depends on: all above

6. **trading-desktop / MarketSpine** (PRIVATE - keep private)
   - Bloomberg Terminal-style UI (React + Vite + Tailwind)
   - Modules: Trading Center, Research Hub, Portfolio Manager, Compliance
   - Goal: integrate capture-spine into this platform
   - Depends on: entityspine for knowledge graph

## Data Flow

```
SEC EDGAR → py-sec-edgar → feedspine → capture-spine → trading-desktop
                              ↓
                         entityspine (entity resolution)
                              ↓
                         spine-core (pipeline execution)
```

## Key Features Being Built

1. **Modern Earnings Intelligence** - LLM-powered earnings analysis replacing old Excel macros
2. **8-K Release Capture** - Automated detection and parsing of SEC earnings releases
3. **Trading Desktop Integration** - Migrating capture-spine UI into MarketSpine
4. **CI/CD & PyPI** - Publishing feedspine 1.0.0, CI for all projects

## Important Notes

- entityspine: stdlib-only core, extended modules for DB/API
- feedspine: Uses Pydantic v2, async-first design
- capture-spine: Has existing LLM infrastructure, use it
- trading-desktop: React + TypeScript, Bloomberg design language
- Keep capture-spine and trading-desktop PRIVATE

## Workspace Location

- All projects under: `b:\github\py-sec-edgar\`
- Subfolders: entityspine/, feedspine/, spine-core/, capture-spine/, market-spine/
- Docs in: `feedspine/docs/features/`
```

---

## Quick Reference

### Project Purposes

| Project | One-liner |
|---------|-----------|
| py-sec-edgar | Downloads SEC filings |
| entityspine | Who/what is this entity? |
| feedspine | What data do we have about it? |
| spine-core | How do we process it? |
| capture-spine | Capture → enrich → alert |
| trading-desktop | Professional trading UI |

### Key Classes/Concepts

```python
# entityspine
Entity, Organization, Person, Ticker, CIK

# feedspine
Feed, FeedItem, Observation, ComparisonEngine

# spine-core
Pipeline, Step, WorkflowRunner, ExecutionContext
AlertRule, AlertChannel (Slack, Email, PagerDuty)

# capture-spine
Record, RecordType, LLMProvider, Enrichment
AlertRule, AlertAction, DataSource
```

### Feature Docs Location

```
feedspine/docs/features/
├── estimates-vs-actuals/      # Earnings calendar + comparison
├── modern-earnings-intelligence/  # LLM-powered analysis
├── 8k-release-capture/        # SEC 8-K parsing
├── trading-desktop-integration/   # UI migration
└── cicd-pypi-publishing/      # CI/CD setup
```

### Workspace Root Docs

```
b:\github\py-sec-edgar\
├── ECOSYSTEM.md               # Master integration doc
├── LLM_HANDOFF.md            # Context for new sessions
└── README.md                  # Project overview
```

---

## When to Use This Prompt

- Starting a new conversation about the platform
- Working on cross-project features
- Debugging integration issues
- Planning new features that span projects
- Explaining the architecture to new team members

---

## Updating This Prompt

When the ecosystem changes:
1. Update the dependency list
2. Update the data flow diagram
3. Add new features being built
4. Keep privacy settings accurate
