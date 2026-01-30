# Phase 5: Section Extraction + Entity Resolution

## ✅ STATUS: COMPLETE (January 26, 2026)

**This is the FINAL PHASE and the original motivation for EntitySpine.**

---

## Deliverables Implemented

| Component | Location | Description |
|-----------|----------|-------------|
| **EntityMention** | `py_sec_edgar/core/results.py` | Dataclass for company mentions with resolution |
| **ExtractedSection** | `py_sec_edgar/core/results.py` | Enhanced with `entity_mentions` field |
| **EntityMentionExtractor** | `py_sec_edgar/core/extraction/entity_mentions.py` | Pattern-based mention extraction |
| **FilingExtractor** | `py_sec_edgar/core/extraction/filing_extractor.py` | Orchestrator combining sections + entities |
| **CLI extract command** | `py_sec_edgar/cli/app.py` | `sec extract <file> --format json` |
| **Tests** | `py_sec_edgar/tests/test_phase5_extraction.py` | 17 tests passing |

---

## Quick Start

```python
from py_sec_edgar.core.extraction import FilingExtractor
from py_sec_edgar.integrations.entityspine import get_entity_store
from pathlib import Path

# Get EntitySpine store (optional but enables resolution)
store = get_entity_store(Path("./data/entities.db"))

# Extract from filing
extractor = FilingExtractor(store)
result = extractor.extract_from_file(
    "filing.htm",
    filer_cik="0001234567",
    filer_name="Test Corp",
)

# See results
print(result.summary())
for section in result.sections:
    for mention in section.entity_mentions:
        if mention.is_resolved:
            print(f"  {mention.text} → CIK {mention.resolved_cik}")

# Ingest to EntitySpine (optional)
ingest_result = extractor.ingest_to_entityspine(result)
```

### CLI Usage

```bash
# Extract with summary output
sec extract filing.htm

# Extract with JSON output
sec extract filing.htm --format json --output result.json

# Extract sections only (no entity resolution)
sec extract filing.htm --no-entities --format sections
```

---

## Original Specification (For Reference)

### ⚠️ CRITICAL: Study These Examples First

**Before implementing, study the working examples in EntitySpine:**

```
entityspine/examples/
├── 01_end_to_end_sec_filing_to_kg.py  # Complete pipeline
├── 02_custom_extraction_service.py    # Custom extraction logic
├── 03_multi_filing_processing.py      # Batch processing
├── 04_extraction_with_validation.py   # Quality validation
└── 05_parallel_extraction_pipeline.py # Parallel processing
```

**Especially study:** `01_end_to_end_sec_filing_to_kg.py` shows the full flow from filing → extraction → entity resolution → knowledge graph.

---

## Phase 5 Scope

Parse SEC filings, extract sections, identify entity mentions, resolve to EntitySpine.

### ✅ Use Existing Integration Contracts

EntitySpine provides ALL the contracts you need:

```python
from entityspine.integration.contracts import (
    FilingFacts,       # Filing metadata
    FilingEvidence,    # Source locations
    ExtractedEntity,   # Resolved entities
    ExtractedRelationship,  # Entity relationships
)
from entityspine.integration.ingest import ingest_filing_facts
```

### Integration Pattern

```python
@dataclass
class ExtractedSection:
    section_type: str      # ITEM_1_BUSINESS, ITEM_1A_RISK_FACTORS, etc.
    title: str
    text: str
    word_count: int
    entity_mentions: list["EntityMention"] = field(default_factory=list)

@dataclass
class EntityMention:
    text: str           # "Microsoft Corporation"
    start_offset: int
    end_offset: int
    # Resolution from EntitySpine:
    resolved_entity_id: str | None
    resolved_cik: str | None
    resolved_name: str | None
    confidence: float = 0.0
```

---

## The Vision (Why This Matters)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  $ py-sec-edgar fetch --ticker AAPL --form 10-K                             │
│            │                                                                 │
│            ▼                                                                 │
│  EntitySpine: AAPL → CIK 0000320193                                         │
│            │                                                                 │
│            ▼                                                                 │
│  Download 10-K HTML                                                          │
│            │                                                                 │
│            ▼                                                                 │
│  SectionExtractor:                                                           │
│    • ITEM 1 - Business: "We compete with Microsoft Corporation..."          │
│    • ITEM 1A - Risk Factors: "Competition from Amazon..."                   │
│            │                                                                 │
│            ▼                                                                 │
│  EntityMentionExtractor + EntitySpine:                                       │
│    • "Microsoft Corporation" → CIK 789019 (confidence: 0.95)               │
│    • "Amazon" → CIK 1018724 (confidence: 0.87)                             │
│            │                                                                 │
│            ▼                                                                 │
│  Structured Output: ExtractedEntity + ExtractedRelationship dataclasses     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Guide

### Step 1: Entity Resolution Service (from Phase 4)

```python
from entityspine import SqliteStore

class EntityResolutionService:
    """Resolve entity mentions to canonical EntitySpine records."""

    def __init__(self, data_dir: Path):
        self.store = SqliteStore(data_dir / "entities.db")
        # Auto-download SEC data if empty
        if self.store.count() == 0:
            self.store.load_sec_data()

    def resolve_mention(self, text: str) -> EntityMention:
        """Try to resolve a text mention to an entity."""
        # Try exact name match
        entity = self.store.get_by_name(text)
        if entity:
            return EntityMention(
                text=text,
                start_offset=0,
                end_offset=len(text),
                resolved_entity_id=entity.entity_id,
                resolved_cik=entity.get_identifier("cik"),
                resolved_name=entity.name,
                confidence=1.0
            )

        # Try fuzzy/alias matching
        candidates = self.store.search(text, limit=5)
        if candidates:
            best = candidates[0]
            return EntityMention(
                text=text,
                start_offset=0,
                end_offset=len(text),
                resolved_entity_id=best.entity_id,
                resolved_cik=best.get_identifier("cik"),
                resolved_name=best.name,
                confidence=0.8  # Fuzzy match confidence
            )

        # Unresolved
        return EntityMention(
            text=text,
            start_offset=0,
            end_offset=len(text),
            resolved_entity_id=None,
            resolved_cik=None,
            resolved_name=None,
            confidence=0.0
        )
```

### Step 2: Section Extractor

```python
class SectionExtractor:
    """Extract sections from 10-K/10-Q HTML filings."""

    # SEC Item patterns
    SECTION_PATTERNS = {
        "ITEM_1_BUSINESS": r"item\s+1[.\s]+business",
        "ITEM_1A_RISK_FACTORS": r"item\s+1a[.\s]+risk\s+factors",
        "ITEM_7_MD_AND_A": r"item\s+7[.\s]+management",
        # ... more patterns
    }

    def extract_sections(self, html_content: str) -> list[ExtractedSection]:
        """Parse filing HTML and extract sections."""
        sections = []
        # Implementation: parse HTML, find section boundaries
        # Return list of ExtractedSection objects
        return sections
```

### Step 3: Entity Mention Extractor

```python
class EntityMentionExtractor:
    """Find and resolve entity mentions in text."""

    def __init__(self, resolver: EntityResolutionService):
        self.resolver = resolver

    def extract_mentions(
        self,
        text: str,
        section_type: str | None = None
    ) -> list[EntityMention]:
        """Find company mentions in text and resolve via EntitySpine."""
        mentions = []

        # Strategy 1: NER (if available)
        # Strategy 2: Pattern matching for common company suffixes
        # Strategy 3: Known company name dictionary

        candidates = self._find_candidates(text)
        for candidate_text, start, end in candidates:
            mention = self.resolver.resolve_mention(candidate_text)
            mention.start_offset = start
            mention.end_offset = end
            mentions.append(mention)

        return mentions
```

### Step 4: Filing Extractor (Orchestrator)

```python
from entityspine.integration.contracts import (
    FilingFacts, FilingEvidence, ExtractedEntity, ExtractedRelationship
)

class FilingExtractor:
    """Main orchestrator for filing extraction."""

    def __init__(
        self,
        resolver: EntityResolutionService,
        section_extractor: SectionExtractor,
        mention_extractor: EntityMentionExtractor
    ):
        self.resolver = resolver
        self.section_extractor = section_extractor
        self.mention_extractor = mention_extractor

    def extract(self, filing_html: str, accession: str) -> FilingFacts:
        """
        Extract a filing and return FilingFacts for EntitySpine integration.
        """
        # Extract sections
        sections = self.section_extractor.extract_sections(filing_html)

        # Find entity mentions in each section
        all_entities: list[ExtractedEntity] = []
        all_relationships: list[ExtractedRelationship] = []

        for section in sections:
            mentions = self.mention_extractor.extract_mentions(
                section.text,
                section.section_type
            )
            section.entity_mentions = mentions

            # Convert to integration contracts
            for mention in mentions:
                if mention.resolved_entity_id:
                    entity = ExtractedEntity(
                        raw_text=mention.text,
                        entity_type="company",
                        resolved_id=mention.resolved_entity_id,
                        confidence=mention.confidence,
                        evidence=FilingEvidence(
                            accession_number=accession,
                            section=section.section_type,
                            page=1,
                            offset=mention.start_offset
                        )
                    )
                    all_entities.append(entity)

        # Build FilingFacts
        return FilingFacts(
            accession_number=accession,
            filing_date=None,  # TODO: extract from filing
            form_type="10-K",  # TODO: extract from filing
            entities=all_entities,
            relationships=all_relationships,
            metadata={"sections_extracted": len(sections)}
        )
```

---

## Acceptance Criteria

```python
from py_sec_edgar.extraction import FilingExtractor
from py_sec_edgar.services import EntityResolutionService
from entityspine.integration.ingest import ingest_filing_facts
from entityspine import SqliteStore

# Setup
store = SqliteStore(data_dir / "entities.db")
store.load_sec_data()  # Auto-download SEC data

resolver = EntityResolutionService(data_dir)
extractor = FilingExtractor(resolver, ...)

# Extract filing
facts = extractor.extract(filing_html, "0000320193-23-000077")

# Verify entity extraction
microsoft_entity = next(
    e for e in facts.entities
    if "Microsoft" in e.raw_text
)
assert microsoft_entity.resolved_id is not None

# Ingest into EntitySpine for relationship tracking
ingest_filing_facts(store, facts)
```

### CLI Integration

```bash
# Extract sections from a filing
$ py-sec-edgar extract --accession 0000320193-23-000077
Filing: 0000320193-23-000077
Form: 10-K
Sections found: 15

  ITEM_1_BUSINESS:
    Words: 12,345
    Entities: 47 resolved, 12 unresolved

# Export as FilingFacts JSON
$ py-sec-edgar extract --accession 0000320193-23-000077 --format json
{
  "accession_number": "0000320193-23-000077",
  "entities": [...],
  "relationships": [...]
}
```

---

## Key Files to Study

### EntitySpine Examples
- [01_end_to_end_sec_filing_to_kg.py](../entityspine/examples/01_end_to_end_sec_filing_to_kg.py) - Complete extraction pipeline
- [02_custom_extraction_service.py](../entityspine/examples/02_custom_extraction_service.py) - Custom extraction patterns

### EntitySpine Integration Module
- `entityspine/integration/contracts.py` - FilingFacts, ExtractedEntity contracts
- `entityspine/integration/ingest.py` - ingest_filing_facts() function

### Existing py-sec-edgar Code
- `py_sec_edgar/extractor/` - Existing extraction code (enhance, don't rewrite)
- `py_sec_edgar/documents/PROMPT_SECTION_EXTRACTION_V1_1.md` - Detailed extraction spec

---

## 🎉 Ecosystem Complete!

After Phase 5, the full ecosystem is functional:

| Package | Role |
|---------|------|
| **EntitySpine** | Master entity resolution, CIK/ticker/CUSIP lookup |
| **FeedSpine** | Feed tracking, record deduplication |
| **py-sec-edgar** | CLI, filing download, section extraction |

### Complete Flow

```
User runs: py-sec-edgar fetch --ticker AAPL --form 10-K
    │
    ├─► EntitySpine: AAPL → CIK 0000320193
    │
    ├─► Download 10-K filing HTML
    │
    ├─► SectionExtractor: Parse into ITEM_1, ITEM_1A, etc.
    │
    ├─► EntityMentionExtractor: Find "Microsoft", "Amazon", etc.
    │
    ├─► EntitySpine: Resolve mentions to CIKs
    │
    └─► Output: FilingFacts with resolved entities + relationships
```

---

## Verification Commands

```bash
# EntitySpine resolution works
python -c "from entityspine import SqliteStore; s = SqliteStore(':memory:'); s.load_sec_data(); print(s.search('Apple')[0].cik)"

# Integration contracts available
python -c "from entityspine.integration.contracts import FilingFacts, ExtractedEntity; print('OK')"

# py-sec-edgar can import EntitySpine
python -c "from py_sec_edgar.services import EntityResolutionService; print('OK')"
```

---

*Phase 5 of 5 | FINAL PHASE | Depends on: Phase 4*
*Key Integration: entityspine.integration.contracts → py-sec-edgar extraction*
