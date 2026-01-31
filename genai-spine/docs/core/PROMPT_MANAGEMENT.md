# Prompt Management

> Core capability for managing prompt templates with versioning, variables, and rendering.

---

## Overview

Prompts are first-class citizens in GenAI Spine. Every AI operation uses a prompt template that can be:
- Created, updated, and deleted via API
- Versioned with immutable history
- Rendered with variable substitution
- Shared across the organization
- A/B tested in production

---

## Data Model

### Prompt

```python
@dataclass
class Prompt:
    id: UUID
    name: str              # "Summarize Article"
    slug: str              # "summarize-article" (unique)
    description: str
    system_prompt: str     # System message
    user_prompt_template: str  # Jinja2 template
    category: str          # "summarization", "extraction", etc.
    tags: list[str]        # ["news", "article"]
    variables: list[Variable]  # Template variables
    is_system: bool        # Built-in (read-only)
    is_public: bool        # Shared with org
    version: int           # Current version number
    created_at: datetime
    updated_at: datetime
```

### Variable

```python
@dataclass
class Variable:
    name: str           # "content"
    type: str           # "string", "integer", "boolean", "array"
    required: bool      # Must be provided
    default: Any        # Default value if not provided
    description: str    # Documentation
    validation: dict    # Optional validation rules
```

### PromptVersion

```python
@dataclass
class PromptVersion:
    id: UUID
    prompt_id: UUID
    version: int
    system_prompt: str
    user_prompt_template: str
    change_notes: str
    created_at: datetime
    # Versions are immutable - never updated
```

---

## API Endpoints

### List Prompts

```http
GET /v1/prompts
GET /v1/prompts?category=summarization
GET /v1/prompts?tags=news,article
GET /v1/prompts?search=summary
```

### Create Prompt

```http
POST /v1/prompts
Content-Type: application/json

{
    "name": "Summarize Article",
    "slug": "summarize-article",
    "description": "Summarize news articles",
    "system_prompt": "You are a helpful summarizer.",
    "user_prompt_template": "Summarize in {{max_sentences}} sentences:\n\n{{content}}",
    "category": "summarization",
    "tags": ["news", "article"],
    "variables": [
        {"name": "content", "type": "string", "required": true},
        {"name": "max_sentences", "type": "integer", "default": 3}
    ]
}
```

### Get Prompt

```http
GET /v1/prompts/{id}
GET /v1/prompts/by-slug/{slug}
```

### Update Prompt

Updates create a new version automatically.

```http
PUT /v1/prompts/{id}
Content-Type: application/json

{
    "user_prompt_template": "Create a {{style}} summary in {{max_sentences}} sentences:\n\n{{content}}",
    "variables": [
        {"name": "content", "type": "string", "required": true},
        {"name": "max_sentences", "type": "integer", "default": 3},
        {"name": "style", "type": "string", "default": "concise"}
    ],
    "change_notes": "Added style parameter for customizable tone"
}
```

### Delete Prompt

```http
DELETE /v1/prompts/{id}
```

### Get Version History

```http
GET /v1/prompts/{id}/versions
```

Response:
```json
{
    "versions": [
        {"version": 3, "created_at": "2026-01-31T10:00:00Z", "change_notes": "Added style"},
        {"version": 2, "created_at": "2026-01-15T10:00:00Z", "change_notes": "Fixed typo"},
        {"version": 1, "created_at": "2026-01-01T10:00:00Z", "change_notes": "Initial"}
    ]
}
```

### Rollback to Version

```http
POST /v1/prompts/{id}/rollback
Content-Type: application/json

{"version": 2}
```

### Render Prompt

Preview rendered prompt without execution.

```http
POST /v1/prompts/{id}/render
Content-Type: application/json

{
    "variables": {
        "content": "Long article text...",
        "max_sentences": 5
    }
}
```

Response:
```json
{
    "system_prompt": "You are a helpful summarizer.",
    "user_prompt": "Summarize in 5 sentences:\n\nLong article text...",
    "variables_used": ["content", "max_sentences"],
    "variables_defaulted": []
}
```

---

## Template Syntax

Uses Jinja2 templating:

### Basic Variables

```jinja2
Summarize: {{content}}
```

### Conditionals

```jinja2
{% if focus %}Focus on: {{focus}}{% endif %}
```

### Loops

```jinja2
Categories: {% for cat in categories %}{{cat}}{% if not loop.last %}, {% endif %}{% endfor %}
```

### Filters

```jinja2
{{content | truncate(1000)}}
{{title | upper}}
```

### Default Values

```jinja2
{{style | default('professional')}}
```

---

## Built-in Prompt Library

GenAI Spine ships with default prompts:

| Slug | Category | Description |
|------|----------|-------------|
| `summarize-article` | summarization | Summarize news articles |
| `summarize-document` | summarization | Summarize long documents |
| `extract-entities` | extraction | NER extraction |
| `extract-key-points` | extraction | Bullet point extraction |
| `classify-content` | classification | Category classification |
| `classify-sentiment` | classification | Sentiment analysis |

Built-in prompts have `is_system: true` and cannot be deleted.

---

## Versioning Strategy

### Why Version?

1. **Audit trail** — Know what prompt produced a result
2. **Rollback** — Revert if new version performs poorly
3. **A/B testing** — Compare versions in production
4. **Compliance** — Track changes for regulatory requirements

### Version Rules

- Every update creates a new version (versions are immutable)
- Version numbers increment automatically
- Old versions remain accessible forever
- Execution logs reference specific version numbers

### Execution Tracking

```python
# When executing a prompt
execution = Execution(
    prompt_id=prompt.id,
    prompt_version=prompt.version,  # Captures exact version
    # ... other fields
)
```

---

## Best Practices

### 1. Use Descriptive Slugs

```
Good: summarize-sec-10k-risk-factors
Bad: prompt1
```

### 2. Document Variables

```json
{
    "variables": [
        {
            "name": "filing_type",
            "type": "string",
            "required": true,
            "description": "SEC filing type (10-K, 10-Q, 8-K)"
        }
    ]
}
```

### 3. Version Change Notes

```json
{
    "change_notes": "Added output_format variable to support bullet points. Fixed hallucination issue with dates."
}
```

### 4. Categorize Consistently

Use standard categories:
- `summarization`
- `extraction`
- `classification`
- `generation`
- `comparison`
- `analysis`

### 5. Test Before Promoting

```python
# Render and review before going live
rendered = await client.post(f"/v1/prompts/{prompt_id}/render", json={
    "variables": test_variables
})
print(rendered["user_prompt"])
```

---

## Storage Schema

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    category VARCHAR(50),
    tags JSONB DEFAULT '[]',
    variables JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY,
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT NOT NULL,
    change_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(prompt_id, version)
);

CREATE INDEX idx_prompts_slug ON prompts(slug);
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_prompt_versions_prompt_id ON prompt_versions(prompt_id);
```

---

## Related Docs

- [TIER_1_BASIC.md](../capabilities/TIER_1_BASIC.md) — Prompt management as Tier 1 capability
- [RAG.md](RAG.md) — How prompts work with RAG
- [../guides/ADDING_CAPABILITIES.md](../guides/ADDING_CAPABILITIES.md) — Creating new capabilities with prompts
