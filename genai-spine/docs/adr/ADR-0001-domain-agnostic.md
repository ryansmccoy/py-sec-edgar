# ADR-0001: Domain-Agnostic API Design

**Status:** ✅ Accepted
**Date:** 2026-01-31

---

## Context

GenAI Spine serves multiple applications in the Spine ecosystem:
- **capture-spine** - Document capture, chat, content transformation
- **feedspine** - SEC filing processing, feed management
- **entityspine** - Entity resolution and enrichment
- **py-sec-edgar** - SEC data retrieval and analysis

Each application has domain-specific needs:
- capture-spine needs "message enrichment"
- feedspine needs "filing summarization"
- entityspine needs "entity extraction"

The question: Should GenAI Spine have domain-specific endpoints like `/v1/enrich-message` and `/v1/summarize-filing`, or generic endpoints like `/v1/completions` and `/v1/execute-prompt`?

### Forces

1. **Ease of use** - Domain-specific endpoints are discoverable and self-documenting
2. **Flexibility** - Generic endpoints work for any use case
3. **Maintenance** - Domain-specific endpoints create coupling
4. **Scalability** - Adding new apps shouldn't require GenAI Spine changes
5. **Single responsibility** - GenAI Spine should do one thing well (LLM operations)

---

## Decision

**GenAI Spine will provide domain-agnostic APIs only.**

### What This Means

**✅ GenAI Spine WILL provide:**
- Generic completion endpoints (`/v1/completions`)
- Prompt template execution (`/v1/execute-prompt`)
- Chat session management (`/v1/sessions`)
- Prompt CRUD (`/v1/prompts`)
- Model listing (`/v1/models`)
- Usage tracking (`/v1/usage`)

**❌ GenAI Spine will NOT provide:**
- `/v1/enrich-message` (capture-spine domain)
- `/v1/summarize-filing` (feedspine domain)
- `/v1/resolve-entity` (entityspine domain)
- Any endpoint with domain-specific semantics

### How Consumers Get Domain Behavior

Domain logic lives in prompts, not endpoints:

```python
# capture-spine: "enrich message" via generic endpoint
result = await genai.execute_prompt(
    slug="message-enricher",        # Prompt defines "enrichment"
    variables={"message": text}     # capture-spine provides context
)

# feedspine: "summarize filing" via same endpoint
result = await genai.execute_prompt(
    slug="filing-summarizer",       # Prompt defines "summarization"
    variables={"filing": text}      # feedspine provides context
)
```

### Convenience Endpoints as Tier B

We allow "convenience" endpoints (`/v1/summarize`, `/v1/rewrite`) as Tier B:
- They are wrappers over `execute-prompt` with default prompts
- They have shorter deprecation windows
- They may be collapsed into prompt slugs in future
- They contain NO domain logic, only generic capabilities

---

## Consequences

### Positive

1. **Clear separation of concerns**
   - GenAI Spine: LLM operations
   - Consumer apps: Domain logic

2. **Easy to add new consumers**
   - New app just needs SDK + prompts
   - No GenAI Spine changes required

3. **Prompts are the configuration layer**
   - Domain experts can modify behavior without code changes
   - A/B testing via prompt versions

4. **Single codebase serves all apps**
   - No risk of capture-spine-specific bugs affecting feedspine
   - Easier testing and maintenance

### Negative

1. **More setup for consumers**
   - Must create prompts before use
   - Must understand prompt templating

2. **Less discoverable**
   - `/v1/enrich-message` is more obvious than `/v1/execute-prompt?slug=enricher`
   - Mitigated by: good documentation, SDK helper methods

3. **Prompt management overhead**
   - Many prompts to track across apps
   - Mitigated by: Admin UI, prompt versioning

### Neutral

1. **Tier B convenience endpoints**
   - Provides discoverability without domain coupling
   - Requires discipline to not let them grow into domain endpoints

---

## Alternatives Considered

### A: Domain-Specific Endpoints

```
POST /v1/capture/enrich-message
POST /v1/feedspine/summarize-filing
POST /v1/entityspine/extract-entities
```

**Rejected because:**
- Creates coupling between GenAI Spine and consumers
- Every new consumer needs GenAI Spine changes
- Violates single responsibility principle

### B: Plugin Architecture

Consumer apps register "plugins" that add domain endpoints to GenAI Spine.

**Rejected because:**
- Complexity of plugin loading/isolation
- Still couples GenAI Spine deployment to consumer changes
- Hard to test and debug

### C: Separate Services Per Domain

Each consumer gets its own LLM service (`capture-llm-service`, `feed-llm-service`).

**Rejected because:**
- Duplicates infrastructure
- Inconsistent capabilities across apps
- Higher operational cost

---

## Related Decisions

- [API_TIERS.md](../api/API_TIERS.md) - Tier A vs Tier B endpoint classification
- [API_CONTRACT.md](../api/API_CONTRACT.md) - Full API specification

---

## Review History

| Date | Reviewer | Decision |
|------|----------|----------|
| 2026-01-31 | Architecture Review | Accepted |
