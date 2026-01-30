# Model Migration Guide: capture-spine → entityspine

> **Summary**: Domain models for extraction, story clustering, and significance scoring
> have been migrated from capture-spine to entityspine for ecosystem-wide reuse.

---

## What Moved

| Model | Old Location | New Location |
|-------|--------------|--------------|
| `EntityType` (extraction) | `capture-spine/app/features/intelligence/models.py` | `entityspine.domain.extraction.ExtractionType` |
| `EntityMention` | `capture-spine/...` | `entityspine.domain.extraction.ExtractedEntity` |
| `StoryCluster` | `capture-spine/...` | `entityspine.domain.extraction.StoryCluster` |
| `StoryStatus` | `capture-spine/...` | `entityspine.domain.extraction.StoryStatus` |
| `ArticleLink` | `capture-spine/...` | `entityspine.domain.extraction.ContentLink` |
| `SignificanceScore` | `capture-spine/...` | `entityspine.domain.extraction.SignificanceScore` |

---

## Why We Moved Them

1. **Reusability** — feedspine can use these for content deduplication
2. **Consistency** — stdlib-only dataclasses match entityspine patterns
3. **Dependency flow** — capture-spine depends on entityspine (not vice versa)

```
entityspine (domain models)
    ↓ depends on
feedspine (ingestion)
    ↓ depends on
capture-spine (storage + UI)
```

---

## Migration Guide for capture-spine

### Before (local Pydantic models)

```python
# capture-spine/app/features/intelligence/models.py
from pydantic import BaseModel

class EntityType(str, Enum):
    COMPANY = "COMPANY"
    PERSON = "PERSON"
    ...

class EntityMention(BaseModel):
    type: EntityType
    text: str
    normalized: str
    confidence: float
    ...
```

### After (import from entityspine)

```python
# capture-spine/app/features/intelligence/models.py
from entityspine.domain import (
    ExtractionType,  # renamed from EntityType for clarity
    ExtractedEntity,  # stdlib dataclass (convert to Pydantic for API)
    StoryCluster,
    StoryStatus,
    ContentLink,
    SignificanceScore,
)

# For API responses, create Pydantic wrappers if needed:
class EntityMentionResponse(BaseModel):
    """Pydantic wrapper for API serialization."""

    @classmethod
    def from_domain(cls, entity: ExtractedEntity) -> "EntityMentionResponse":
        return cls(
            type=entity.extraction_type.value,
            text=entity.text,
            normalized=entity.normalized,
            confidence=entity.confidence,
            ...
        )
```

---

## Available Models

### ExtractionType (enum)

```python
from entityspine.domain import ExtractionType

ExtractionType.COMPANY     # → EntityType.ORGANIZATION
ExtractionType.PERSON      # → EntityType.PERSON
ExtractionType.LOCATION    # → EntityType.GEO
ExtractionType.ORG         # Government, NGO
ExtractionType.INSTRUMENT  # Tickers, indices
ExtractionType.METRIC      # Revenue, EPS
ExtractionType.FILING      # 10-K, 8-K
ExtractionType.EVENT       # Earnings, M&A
```

### ExtractedEntity (dataclass)

```python
from entityspine.domain import ExtractedEntity, ExtractionType, TextSpan

entity = ExtractedEntity(
    extraction_type=ExtractionType.COMPANY,
    text="Apple Inc.",
    normalized="AAPL",
    confidence=0.95,
    span=TextSpan(start=0, end=10),
    source="title",
    metadata={"cik": "0000320193"}
)
```

### StoryCluster (dataclass)

```python
from entityspine.domain import (
    StoryCluster, StoryStatus, StoryEntity,
    StoryTimeline, StoryMetrics, ExtractionType
)
from datetime import datetime

cluster = StoryCluster(
    cluster_id="story_abc123",
    status=StoryStatus.ACTIVE,
    headline="Apple Reports Q4 Earnings",
    primary_entities=[
        StoryEntity(ExtractionType.COMPANY, "AAPL"),
    ],
    timeline=StoryTimeline(
        first_article_at=datetime.now(),
        last_article_at=datetime.now(),
    ),
    metrics=StoryMetrics(article_count=15, unique_sources=8),
)
```

### SignificanceScore (dataclass)

```python
from entityspine.domain import SignificanceScore, SignificanceComponent

score = SignificanceScore(
    novelty=SignificanceComponent(0.9, 0.3, "First report"),
    velocity=SignificanceComponent(0.7, 0.2, "Spreading fast"),
    source_diversity=SignificanceComponent(0.8, 0.15, "12 sources"),
    entity_importance=SignificanceComponent(0.85, 0.2, "AAPL tier-1"),
    temporal_decay=SignificanceComponent(0.95, 0.15, "2 hours ago"),
)

print(score.composite_score)  # 0.834
print(score.explanation)      # "High significance due to novelty and entity_importance"
```

### ContentLink (dataclass)

```python
from entityspine.domain import (
    ContentLink, LinkType, LinkDirection, LinkEvidence
)

link = ContentLink(
    source_id="article_123",
    target_id="article_456",
    link_type=LinkType.FOLLOW_UP,
    direction=LinkDirection.REFERENCES,
    confidence=0.87,
    explanation="Article 123 references article 456 published yesterday",
)
```

---

## Dependency Setup

### capture-spine pyproject.toml

```toml
[project]
dependencies = [
    "entityspine>=2.3.2",
    "feedspine>=0.1.0",
    # ... other deps
]
```

### Install for development

```bash
cd capture-spine
uv add ../entityspine
uv add ../feedspine
```

---

## Mapping to entityspine EntityType

For cases where you need to map `ExtractionType` to the core `EntityType`:

```python
from entityspine.domain import ExtractionType, EntityType

EXTRACTION_TO_ENTITY = {
    ExtractionType.COMPANY: EntityType.ORGANIZATION,
    ExtractionType.PERSON: EntityType.PERSON,
    ExtractionType.LOCATION: EntityType.GEO,
    ExtractionType.ORG: EntityType.ORGANIZATION,
    # These don't map directly - they're extraction-specific
    ExtractionType.INSTRUMENT: None,
    ExtractionType.METRIC: None,
    ExtractionType.FILING: None,
    ExtractionType.EVENT: None,
}
```

---

## Testing

```python
# Test that imports work
from entityspine.domain import (
    ExtractionType,
    ExtractedEntity,
    StoryCluster,
    StoryStatus,
    ContentLink,
    SignificanceScore,
)

# Should not raise
assert ExtractionType.COMPANY.value == "COMPANY"
```

---

*Last updated: Jan 29, 2026*
