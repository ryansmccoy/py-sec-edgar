# Data Lineage & Provenance Architecture

**Purpose**: Full lineage tracking with point-in-time database capabilities for SEC filing data.

---

## Vision

Every piece of extracted data should have **complete provenance**:
- **What filing** it came from (accession number, form type, filed date)
- **What section** (Item 1A, Item 7, Exhibit 21)
- **What sentence** (exact text, character offsets)
- **When we discovered it** (first_seen_at, last_seen_at)
- **How we extracted it** (method: spaCy, regex, LLM)
- **How confident we are** (0.0 - 1.0)

This enables:
1. **Point-in-time queries**: "What did we know about TSMC as Apple supplier on 2024-06-15?"
2. **Audit trails**: "Where exactly did this supplier mention come from?"
3. **Change tracking**: "When did this relationship first appear/disappear?"
4. **Evidence linking**: Click on any fact → see original document context

---

## Core Data Model with Lineage

### 1. Entity Mention with Full Provenance

```python
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional
from enum import Enum


class ExtractionMethod(Enum):
    """How the entity was extracted."""
    SPACY_NER = "spacy_ner"
    REGEX_PATTERN = "regex_pattern"
    LLM_EXTRACTION = "llm_extraction"
    MANUAL = "manual"
    HEURISTIC = "heuristic"


class RelationshipType(Enum):
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    COMPETITOR = "competitor"
    PARTNER = "partner"
    SUBSIDIARY = "subsidiary"
    AUDITOR = "auditor"


@dataclass
class SourceLocation:
    """Exact location in source document."""
    # Filing identification
    accession_number: str
    form_type: str
    filed_date: date
    filer_cik: str
    filer_name: str

    # Document within filing
    document_filename: str  # "aapl-20240928.htm"
    document_type: str      # "10-K", "EX-21.1"

    # Section within document
    section_id: str         # "item_1a", "item_7", "exhibit_21"
    section_title: str      # "Risk Factors", "MD&A"

    # Exact location
    char_start: int
    char_end: int
    paragraph_index: int
    sentence_index: int

    # The actual text
    exact_text: str              # The entity mention itself
    sentence_text: str           # Full sentence containing mention
    surrounding_context: str     # ~500 chars around mention

    # URL to view in context
    @property
    def sec_url(self) -> str:
        """Direct link to filing on SEC."""
        clean_accession = self.accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{self.filer_cik}/{clean_accession}/{self.document_filename}"


@dataclass
class ExtractionMetadata:
    """How and when the extraction happened."""
    # Extraction details
    method: ExtractionMethod
    model_name: str | None = None     # "en_core_web_lg", "gpt-4", etc.
    model_version: str | None = None
    confidence: float = 1.0

    # What triggered extraction
    pattern_matched: str | None = None  # Regex pattern if applicable
    prompt_used: str | None = None      # LLM prompt if applicable

    # Processing context
    pipeline_version: str = "1.0.0"
    enricher_name: str = "entity_enricher"

    # Timing
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0


@dataclass
class TemporalTracking:
    """Point-in-time tracking for the mention."""
    # When we first saw this fact
    first_seen_at: datetime
    first_seen_in_filing: str      # accession_number

    # Most recent observation
    last_seen_at: datetime
    last_seen_in_filing: str       # accession_number

    # How many times we've seen it
    occurrence_count: int = 1

    # Change tracking
    is_new: bool = False           # New in most recent filing
    is_removed: bool = False       # Was in previous, not in current
    was_modified: bool = False     # Text changed between filings

    # Historical values (for modified mentions)
    prior_text: str | None = None
    prior_confidence: float | None = None


@dataclass
class EntityMentionWithLineage:
    """
    A fully-provenanced entity mention.

    Every fact in the system has this level of traceability.
    """
    # Unique identifier
    mention_id: str

    # What was mentioned
    entity_name: str
    entity_type: str
    relationship_type: RelationshipType | None

    # Where it came from (full provenance)
    source: SourceLocation

    # How we found it
    extraction: ExtractionMetadata

    # When we knew about it
    temporal: TemporalTracking

    # Resolution to EntitySpine (if resolved)
    resolved_entity_id: str | None = None
    resolved_cik: str | None = None
    resolution_confidence: float | None = None
    resolution_method: str | None = None  # "exact", "fuzzy", "manual"
```

---

## Database Schema with Temporal Support

### DuckDB Schema for Point-in-Time Queries

```sql
-- =============================================================================
-- CORE TABLES WITH TEMPORAL TRACKING
-- =============================================================================

-- Entity mentions with full lineage
CREATE TABLE entity_mentions (
    mention_id              VARCHAR PRIMARY KEY,

    -- What was mentioned
    entity_name             VARCHAR NOT NULL,
    entity_type             VARCHAR NOT NULL,
    relationship_type       VARCHAR,  -- supplier, customer, etc.

    -- Source location (provenance)
    accession_number        VARCHAR NOT NULL,
    form_type               VARCHAR NOT NULL,
    filed_date              DATE NOT NULL,
    filer_cik               VARCHAR NOT NULL,
    filer_name              VARCHAR,

    document_filename       VARCHAR,
    document_type           VARCHAR,
    section_id              VARCHAR,
    section_title           VARCHAR,

    char_start              INTEGER,
    char_end                INTEGER,
    paragraph_index         INTEGER,
    sentence_index          INTEGER,

    exact_text              VARCHAR NOT NULL,
    sentence_text           TEXT,
    surrounding_context     TEXT,

    -- Extraction metadata
    extraction_method       VARCHAR NOT NULL,
    model_name              VARCHAR,
    model_version           VARCHAR,
    confidence              DECIMAL(3,2),
    pattern_matched         VARCHAR,
    pipeline_version        VARCHAR,
    extracted_at            TIMESTAMPTZ NOT NULL,
    processing_time_ms      DECIMAL(10,2),

    -- Temporal tracking (point-in-time)
    first_seen_at           TIMESTAMPTZ NOT NULL,
    first_seen_in_filing    VARCHAR NOT NULL,
    last_seen_at            TIMESTAMPTZ NOT NULL,
    last_seen_in_filing     VARCHAR NOT NULL,
    occurrence_count        INTEGER DEFAULT 1,
    is_new                  BOOLEAN DEFAULT FALSE,
    is_removed              BOOLEAN DEFAULT FALSE,
    was_modified            BOOLEAN DEFAULT FALSE,
    prior_text              TEXT,

    -- Resolution to EntitySpine
    resolved_entity_id      VARCHAR,
    resolved_cik            VARCHAR,
    resolution_confidence   DECIMAL(3,2),
    resolution_method       VARCHAR,

    -- Row metadata
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for point-in-time queries
CREATE INDEX idx_mentions_entity ON entity_mentions(entity_name);
CREATE INDEX idx_mentions_filer ON entity_mentions(filer_cik);
CREATE INDEX idx_mentions_filing ON entity_mentions(accession_number);
CREATE INDEX idx_mentions_first_seen ON entity_mentions(first_seen_at);
CREATE INDEX idx_mentions_last_seen ON entity_mentions(last_seen_at);
CREATE INDEX idx_mentions_relationship ON entity_mentions(relationship_type);


-- Historical sightings log (append-only)
CREATE TABLE mention_sightings (
    sighting_id             VARCHAR PRIMARY KEY,
    mention_id              VARCHAR NOT NULL REFERENCES entity_mentions(mention_id),

    -- Where we saw it this time
    accession_number        VARCHAR NOT NULL,
    filed_date              DATE NOT NULL,

    -- Exact text at this sighting (may differ)
    exact_text              VARCHAR NOT NULL,
    sentence_text           TEXT,

    -- Extraction at this sighting
    extraction_method       VARCHAR,
    confidence              DECIMAL(3,2),

    -- When we processed this sighting
    seen_at                 TIMESTAMPTZ NOT NULL,

    -- Was this a change?
    text_changed            BOOLEAN DEFAULT FALSE,
    prior_text              TEXT
);

CREATE INDEX idx_sightings_mention ON mention_sightings(mention_id);
CREATE INDEX idx_sightings_time ON mention_sightings(seen_at);


-- Relationship edges with temporal validity
CREATE TABLE relationships (
    relationship_id         VARCHAR PRIMARY KEY,

    -- The entities
    source_entity_id        VARCHAR NOT NULL,  -- EntitySpine ID
    source_name             VARCHAR NOT NULL,
    target_entity_id        VARCHAR,           -- EntitySpine ID (if resolved)
    target_name             VARCHAR NOT NULL,

    -- Relationship
    relationship_type       VARCHAR NOT NULL,
    relationship_subtype    VARCHAR,

    -- Evidence (points to mention)
    evidence_mention_id     VARCHAR REFERENCES entity_mentions(mention_id),
    evidence_count          INTEGER DEFAULT 1,

    -- Temporal validity (when this relationship was true)
    valid_from              DATE NOT NULL,      -- First filing date where mentioned
    valid_to                DATE,               -- Last filing date (NULL = still active)

    -- Confidence
    confidence              DECIMAL(3,2),

    -- Tracking
    first_seen_at           TIMESTAMPTZ NOT NULL,
    last_seen_at            TIMESTAMPTZ NOT NULL,

    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rel_source ON relationships(source_entity_id);
CREATE INDEX idx_rel_target ON relationships(target_entity_id);
CREATE INDEX idx_rel_type ON relationships(relationship_type);
CREATE INDEX idx_rel_valid ON relationships(valid_from, valid_to);
```

---

## Point-in-Time Query Interface

```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional


@dataclass
class PointInTimeQuery:
    """Query what we knew at a specific point in time."""
    as_of: datetime | date
    entity_name: str | None = None
    filer_cik: str | None = None
    relationship_type: str | None = None


class LineageStore:
    """Store with full lineage and point-in-time queries."""

    def __init__(self, db_path: str = "lineage.duckdb"):
        self.db_path = db_path

    # =========================================================================
    # POINT-IN-TIME QUERIES
    # =========================================================================

    def get_suppliers_as_of(
        self,
        company_cik: str,
        as_of: datetime | date
    ) -> List[EntityMentionWithLineage]:
        """
        Get suppliers we knew about at a specific point in time.

        Example: "What suppliers did we know about for Apple on 2024-06-15?"
        """
        query = """
        SELECT * FROM entity_mentions
        WHERE filer_cik = ?
          AND relationship_type = 'supplier'
          AND first_seen_at <= ?
          AND (is_removed = FALSE OR last_seen_at > ?)
        ORDER BY confidence DESC
        """
        # ... execute and return

    def get_entity_history(
        self,
        entity_name: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[dict]:
        """
        Get full history of an entity across all filings.

        Returns timeline of when/where entity was mentioned.
        """
        query = """
        SELECT
            m.entity_name,
            m.filer_name,
            m.relationship_type,
            m.accession_number,
            m.filed_date,
            m.section_title,
            m.first_seen_at,
            m.confidence,
            m.sentence_text
        FROM entity_mentions m
        WHERE LOWER(m.entity_name) LIKE LOWER(?)
        ORDER BY m.filed_date DESC
        """
        # ... execute

    def get_relationship_changes(
        self,
        company_cik: str,
        relationship_type: str,
        since_date: date,
    ) -> dict:
        """
        Get relationship changes since a date.

        Returns:
            {
                "added": [...],      # New relationships
                "removed": [...],    # Relationships no longer mentioned
                "modified": [...]    # Text changed
            }
        """
        query = """
        SELECT * FROM entity_mentions
        WHERE filer_cik = ?
          AND relationship_type = ?
          AND (
              (is_new = TRUE AND first_seen_at >= ?)
              OR (is_removed = TRUE AND last_seen_at >= ?)
              OR (was_modified = TRUE AND last_seen_at >= ?)
          )
        """
        # ... categorize results

    # =========================================================================
    # EVIDENCE LINKING
    # =========================================================================

    def get_evidence_for_fact(
        self,
        mention_id: str
    ) -> SourceLocation:
        """Get full source location for any fact."""
        # Returns exact document, section, sentence
        # User can click through to see in context

    def get_all_sightings(
        self,
        mention_id: str
    ) -> List[dict]:
        """Get all times we saw this mention across filings."""
        query = """
        SELECT
            s.accession_number,
            s.filed_date,
            s.exact_text,
            s.confidence,
            s.seen_at,
            s.text_changed,
            s.prior_text
        FROM mention_sightings s
        WHERE s.mention_id = ?
        ORDER BY s.filed_date DESC
        """

    # =========================================================================
    # SEARCH WITH CONTEXT
    # =========================================================================

    def search_with_context(
        self,
        query: str,
        include_sentence: bool = True,
        include_surrounding: bool = False,
    ) -> List[dict]:
        """
        Search and return results with original context.

        Each result includes the sentence/paragraph where found.
        """
        results = []
        # ... search logic

        for mention in raw_results:
            result = {
                "entity_name": mention.entity_name,
                "relationship_type": mention.relationship_type,
                "filer_name": mention.filer_name,
                "filed_date": mention.filed_date,
                "confidence": mention.confidence,
                # The key: original context
                "exact_text": mention.exact_text,
                "sentence": mention.sentence_text if include_sentence else None,
                "surrounding": mention.surrounding_context if include_surrounding else None,
                # Link to source
                "source_url": mention.source.sec_url,
                "section": mention.section_title,
            }
            results.append(result)

        return results
```

---

## API Endpoints for Lineage

```python
from fastapi import FastAPI, Query
from datetime import datetime, date

app = FastAPI()


@app.get("/api/lineage/suppliers/{cik}")
async def get_supplier_lineage(
    cik: str,
    as_of: datetime | None = None,
) -> SuppliersResponse:
    """
    Get suppliers for a company, optionally at a point in time.

    Each supplier includes full provenance.
    """
    as_of = as_of or datetime.now()
    suppliers = store.get_suppliers_as_of(cik, as_of)

    return {
        "company_cik": cik,
        "as_of": as_of.isoformat(),
        "suppliers": [
            {
                "name": s.entity_name,
                "confidence": s.extraction.confidence,
                "first_seen": s.temporal.first_seen_at.isoformat(),
                "last_seen": s.temporal.last_seen_at.isoformat(),
                "occurrence_count": s.temporal.occurrence_count,
                "evidence": {
                    "filing": s.source.accession_number,
                    "section": s.source.section_title,
                    "sentence": s.source.sentence_text,
                    "url": s.source.sec_url,
                },
                "resolved_entity_id": s.resolved_entity_id,
            }
            for s in suppliers
        ],
    }


@app.get("/api/lineage/entity/{entity_name}/history")
async def get_entity_history(
    entity_name: str,
    start: date | None = None,
    end: date | None = None,
) -> EntityHistoryResponse:
    """
    Get full history of an entity across all filings.

    Shows when/where/how the entity was mentioned over time.
    """
    history = store.get_entity_history(entity_name, start, end)
    return {"entity_name": entity_name, "history": history}


@app.get("/api/lineage/changes/{cik}")
async def get_relationship_changes(
    cik: str,
    relationship_type: str = Query(...),
    since: date = Query(...),
) -> ChangesResponse:
    """
    Get relationship changes since a date.

    Shows added/removed/modified relationships.
    """
    changes = store.get_relationship_changes(cik, relationship_type, since)
    return changes


@app.get("/api/evidence/{mention_id}")
async def get_evidence(mention_id: str) -> EvidenceResponse:
    """
    Get full evidence trail for a specific mention.

    Includes original text, all sightings, resolution history.
    """
    mention = store.get_mention(mention_id)
    sightings = store.get_all_sightings(mention_id)

    return {
        "mention": mention.to_dict(),
        "sightings": sightings,
        "source_url": mention.source.sec_url,
    }
```

---

## Frontend: Evidence Linking UI

```tsx
// Click any extracted fact → see evidence panel

interface EvidencePanel {
  // The extracted fact
  fact: {
    entity: string;
    type: string;
    confidence: number;
  };

  // Where it came from
  source: {
    filingName: string;    // "Apple Inc. 10-K (2024-11-01)"
    section: string;       // "Risk Factors"
    sentence: string;      // Full sentence
    highlighted: string;   // Sentence with entity highlighted
    secUrl: string;        // Link to SEC document
  };

  // Timeline
  history: {
    firstSeen: string;
    lastSeen: string;
    occurrences: number;
    filings: string[];     // List of accession numbers
  };
}

function EvidencePanel({ mentionId }: { mentionId: string }) {
  const { data: evidence } = useEvidence(mentionId);

  return (
    <div className="evidence-panel">
      {/* The fact */}
      <div className="fact-header">
        <Badge>{evidence.fact.type}</Badge>
        <span className="entity-name">{evidence.fact.entity}</span>
        <ConfidenceBar value={evidence.fact.confidence} />
      </div>

      {/* Original context */}
      <div className="source-context">
        <h4>Source</h4>
        <p className="filing-ref">{evidence.source.filingName}</p>
        <p className="section-ref">{evidence.source.section}</p>

        <blockquote className="sentence">
          <HighlightedText
            text={evidence.source.sentence}
            highlight={evidence.fact.entity}
          />
        </blockquote>

        <a href={evidence.source.secUrl} target="_blank">
          View in SEC Filing →
        </a>
      </div>

      {/* History timeline */}
      <div className="history">
        <h4>History</h4>
        <Timeline events={evidence.history.filings.map(f => ({
          date: f.filedDate,
          label: `${f.formType} (${f.accession})`,
        }))} />
        <p>
          First seen: {evidence.history.firstSeen}<br/>
          Seen in {evidence.history.occurrences} filings
        </p>
      </div>
    </div>
  );
}
```

---

## Enricher with Lineage Capture

```python
class EntityEnricherWithLineage:
    """
    Entity enricher that captures full lineage.
    """

    async def enrich(
        self,
        filing: Filing,
        section: FilingSection,
    ) -> List[EntityMentionWithLineage]:
        """Extract entities with full provenance."""

        mentions = []

        # Run NER
        doc = self.nlp(section.text)

        for ent in doc.ents:
            # Classify relationship type
            rel_type = self._classify_relationship(ent, doc)

            # Get sentence context
            sentence = self._get_sentence(doc, ent.start_char)
            surrounding = self._get_surrounding(section.text, ent.start_char, 500)

            mention = EntityMentionWithLineage(
                mention_id=generate_ulid(),
                entity_name=ent.text,
                entity_type=ent.label_,
                relationship_type=rel_type,

                # Full source location
                source=SourceLocation(
                    accession_number=filing.accession_number,
                    form_type=filing.form_type,
                    filed_date=filing.filed_date,
                    filer_cik=filing.cik,
                    filer_name=filing.company_name,
                    document_filename=section.document,
                    document_type=filing.form_type,
                    section_id=section.section_id,
                    section_title=section.title,
                    char_start=ent.start_char,
                    char_end=ent.end_char,
                    paragraph_index=self._get_paragraph_index(section.text, ent.start_char),
                    sentence_index=self._get_sentence_index(doc, ent.start_char),
                    exact_text=ent.text,
                    sentence_text=sentence,
                    surrounding_context=surrounding,
                ),

                # Extraction metadata
                extraction=ExtractionMetadata(
                    method=ExtractionMethod.SPACY_NER,
                    model_name="en_core_web_lg",
                    model_version="3.7.0",
                    confidence=self._calculate_confidence(ent),
                    extracted_at=datetime.utcnow(),
                    pipeline_version="1.0.0",
                    enricher_name="entity_enricher",
                ),

                # Temporal (will be updated on store)
                temporal=TemporalTracking(
                    first_seen_at=datetime.utcnow(),
                    first_seen_in_filing=filing.accession_number,
                    last_seen_at=datetime.utcnow(),
                    last_seen_in_filing=filing.accession_number,
                    is_new=True,  # Will be updated if we've seen before
                ),
            )

            mentions.append(mention)

        return mentions
```

---

## Summary

This architecture provides:

1. **Full Provenance**: Every fact links back to exact filing, section, sentence
2. **Point-in-Time Queries**: Query what we knew at any historical moment
3. **Change Tracking**: See when relationships were added/removed/modified
4. **Evidence Linking**: Click any fact → see original document context
5. **Audit Trail**: Complete extraction metadata (method, model, confidence)

Next: See [08_DOCKER_ARCHITECTURE.md](08_DOCKER_ARCHITECTURE.md) for containerized deployment.
