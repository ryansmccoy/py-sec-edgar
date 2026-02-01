# GenAI Spine API Tiers

**Status:** 📋 Proposal
**Last Updated:** 2026-01-31

---

## Overview

GenAI Spine organizes endpoints into two tiers to clarify stability guarantees and guide consumer adoption.

---

## Tier A: Stable Primitives

**Stability:** These endpoints are the foundational building blocks. They have the highest stability guarantees and are the recommended integration points.

| Endpoint | Description | When to Use |
|----------|-------------|-------------|
| `POST /v1/completions` | Generic LLM completion | Custom prompts, dynamic workflows |
| `POST /v1/execute-prompt` | Execute stored prompt with variables | Reusable, versioned prompt logic |
| `POST /v1/sessions` | Create chat session | Stateful conversations |
| `POST /v1/sessions/{id}/messages` | Send message in session | Multi-turn chat |
| `GET /v1/prompts` | List prompts | Prompt management UI |
| `POST /v1/prompts` | Create prompt | Authoring tools |
| `GET /v1/models` | List available models | Model selection UI |
| `GET /v1/usage` | Query usage/costs | Billing, monitoring |

### Tier A Guarantees

- ✅ **Semantic versioning** - Breaking changes require major version bump
- ✅ **6-month deprecation window** - Minimum notice before removal
- ✅ **SDK support** - All Tier A endpoints have SDK client methods
- ✅ **Full documentation** - OpenAPI spec, examples, error codes

---

## Tier B: Convenience Capabilities

**Stability:** These endpoints are wrappers over Tier A primitives with sensible defaults. They may evolve or be collapsed into Tier A.

| Endpoint | Wraps | Default Behavior |
|----------|-------|------------------|
| `POST /v1/summarize` | `execute-prompt` with `slug=summarizer` | Condense text, bullet format |
| `POST /v1/rewrite` | `execute-prompt` with `slug=rewriter` | Improve clarity, fix grammar |
| `POST /v1/extract` | `execute-prompt` with `slug=extractor` | Extract structured data |
| `POST /v1/classify` | `execute-prompt` with `slug=classifier` | Categorize text |
| `POST /v1/translate` | `execute-prompt` with `slug=translator` | Language translation |

### Tier B Characteristics

- ⚠️ **Convenience wrappers** - These are syntactic sugar over Tier A
- ⚠️ **Shorter deprecation window** - 3 months minimum notice
- ⚠️ **May be collapsed** - Could become just prompt slugs in future
- ✅ **Easier onboarding** - Good for quick integrations

### Why Tier B Exists

```python
# Tier B: Quick and easy
result = await client.post("/v1/summarize", json={"text": content})

# Tier A equivalent: More flexible, same outcome
result = await client.execute_prompt(
    slug="summarizer",
    variables={"text": content, "format": "bullets"}
)
```

Tier B endpoints exist because:
1. **Discoverability** - New users find `/summarize` intuitive
2. **Reduced boilerplate** - No need to know prompt slugs
3. **Opinionated defaults** - Good for 80% of use cases

---

## Which Tier Should Consumers Use?

| Scenario | Recommendation |
|----------|----------------|
| Building core product features | **Tier A** - More control, stable |
| Quick prototypes / experiments | **Tier B** - Fast onboarding |
| Need custom prompt parameters | **Tier A** - Full flexibility |
| Just want "summarize this" | **Tier B** - Sensible defaults |
| Building multi-step workflows | **Tier A** - Composable primitives |

### Migration Path: Tier B → Tier A

If you start with Tier B and need more control:

```python
# Before: Tier B
result = await client.summarize(text=content)

# After: Tier A (same outcome, more options)
result = await client.execute_prompt(
    slug="summarizer",
    variables={"text": content, "format": "numbered", "max_length": 500},
    model="gpt-4o"  # Override default model
)
```

---

## Deprecation Policy

### Tier A Deprecation

1. **Announcement** - Deprecation notice in CHANGELOG, API response headers
2. **Grace period** - 6 months minimum
3. **Migration guide** - Published before deprecation starts
4. **Sunset** - Endpoint returns 410 Gone after grace period

### Tier B Deprecation

1. **Announcement** - Deprecation notice in CHANGELOG
2. **Grace period** - 3 months minimum
3. **Collapse strategy** - Typically becomes a prompt slug
4. **SDK removal** - Wrapper methods removed from SDK

### Deprecation Header Example

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Aug 2026 00:00:00 GMT
Link: <https://docs.genai-spine.dev/migration/summarize>; rel="deprecation"
```

---

## Future Considerations

### Potential Tier B → Tier A Promotion

If a Tier B endpoint proves essential and stable, it may be promoted to Tier A:
- `/v1/embeddings` - If embedding use cases grow
- `/v1/structured-output` - If JSON mode becomes primary use case

### Potential Tier B Collapse

If Tier B endpoints cause confusion or maintenance burden:
- All Tier B could become "blessed prompt slugs"
- SDK would provide convenience methods that wrap `execute_prompt`
- Endpoint paths would redirect to `execute-prompt?slug=...`

---

## See Also

- [API_CONTRACT.md](API_CONTRACT.md) - Full endpoint specifications
- [ENDPOINTS.md](ENDPOINTS.md) - Detailed endpoint documentation
- [ADR-0001](../adr/ADR-0001-domain-agnostic.md) - Why domain-agnostic design
