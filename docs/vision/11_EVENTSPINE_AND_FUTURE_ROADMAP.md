# EventSpine & Future Roadmap

**Purpose**: Define the Event Timeline Manager (EventSpine) for capturing, enriching, and tracking significant corporate events—and outline the future roadmap for integrating news, press releases, conference calls, and other event sources.

> **Note**: EventSpine builds on the existing **edgar_sigdev_pack** work—our proven SigDev (Significant Developments) taxonomy with 35+ event types that achieve 100% compliance across Fortune 500 SEC filings.

---

## Vision: The Event-Driven Intelligence Platform

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EVENTSPINE: SIGNIFICANT DEVELOPMENT MANAGER              │
│                                                                                  │
│   "Every corporate event—earnings, M&A, legal, product launch—captured,         │
│    enriched, and linked to filings in a unified timeline."                       │
└─────────────────────────────────────────────────────────────────────────────────┘

                                 EVENT SOURCES
                    ─────────────────────────────────────────

    SEC Filings ───────────────┐
    (8-K, 10-K, 10-Q)          │
                               │
    Press Releases ────────────┼────────────┐
    (PRNewswire, BusinessWire) │            │
                               │            ▼
    Conference Calls ──────────┤      ┌─────────────────┐
    (Earnings Calls, Analyst)  │      │   EVENTSPINE    │
                               │      │                 │
    News Articles ─────────────┤      │  ┌───────────┐  │────▶ Event Timeline
    (Major Outlets, SEC News)  │      │  │  Event    │  │────▶ Entity Linking
                               │      │  │  Graph    │  │────▶ Impact Analysis
    Social Media ──────────────┤      │  └───────────┘  │────▶ Alert Generation
    (Twitter/X, LinkedIn)      │      │                 │
                               │      └─────────────────┘
    Analyst Reports ───────────┘              │
                                              ▼
                                    ┌─────────────────┐
                                    │   ENTITYSPINE   │
                                    │   (Resolution)  │
                                    └─────────────────┘
```

---

## Part 1: EventSpine Architecture

### What is EventSpine?

EventSpine is the **Significant Development Manager**—a centralized system for:
1. **Capturing** corporate events from multiple sources
2. **Classifying** events by type, severity, and impact
3. **Linking** events to entities via EntitySpine
4. **Tracking** event evolution over time (event → filing → resolution)
5. **Alerting** on material events matching user criteria

### Event Types

| Category | Event Types | Primary Sources |
|----------|-------------|-----------------|
| **Financial** | Earnings release, guidance update, restatement | 8-K, press release, earnings call |
| **Corporate** | M&A, spin-off, restructuring, leadership change | 8-K, press release |
| **Legal** | Lawsuit filed, settlement, regulatory action | 8-K, 10-K Item 3, news |
| **Product** | Launch, recall, FDA approval/rejection | Press release, 8-K |
| **Market** | Stock split, dividend, buyback announcement | 8-K, press release |
| **Risk** | Cybersecurity incident, supply chain disruption | 8-K Item 1.05, 10-K Item 1A |
| **Governance** | Board changes, shareholder proposals, proxy fights | DEF 14A, 8-K |

### SigDev Integration (Existing Foundation)

EventSpine is built on our proven **edgar_sigdev_pack** implementation:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SIGDEV → EVENTSPINE INTEGRATION                              │
└─────────────────────────────────────────────────────────────────────────────────┘

  edgar_sigdev_pack (EXISTING)              EventSpine (FUTURE)
  ────────────────────────────              ───────────────────

  ✅ 35 Official SigDev Event Types    →    EventSpine Event Taxonomy
  ✅ Ultra-strict compliance engine    →    Event Classification Service
  ✅ 8-K Item mapping                  →    Filing → Event Router
  ✅ Qwen2.5 LLM extraction            →    Multi-LLM Event Extractor
  ✅ Multi-company analysis            →    Batch Event Detection
```

**SigDev Event Types → EventSpine Categories:**

| SigDev Category | Event Types | EventSpine Mapping |
|-----------------|-------------|-------------------|
| **Governance** | `MGMT_APPOINTMENT`, `MGMT_RESIGNATION`, `BOARD_APPOINTMENT`, `AUDITOR_CHANGE` | `EventCategory.GOVERNANCE` |
| **Financial** | `GUIDANCE_UPDATE`, `DEBT_NEW`, `EQUITY_ISSUANCE`, `BUYBACK_AUTH`, `GOING_CONCERN_WARNING` | `EventCategory.FINANCIAL` |
| **Business** | `MA_ACQUISITION`, `MA_DISPOSAL`, `SEGMENT_REORG`, `CUSTOMER_CONCENTRATION` | `EventCategory.CORPORATE` |
| **Legal** | `LEGAL_PROCEEDING`, `SETTLEMENT`, `CYBER_INCIDENT`, `SANCTIONS_EXPORT_CONTROL` | `EventCategory.LEGAL` |
| **Ownership** | `BENEFICIAL_OWNERSHIP_CHANGE`, `INSIDER_TRANSACTION`, `INSTITUTIONAL_POSITION_CHANGE` | `EventCategory.OWNERSHIP` |

> **See**: [edgar_sigdev_pack/sigdev_eventtype_to_filings.md](../../edgar_sigdev_pack/sigdev_eventtype_to_filings.md) for the complete SEC form → event type mapping.
> **See**: [py_sec_edgar/documents/sigdev_events/12_SIGDEV_EVENT_STORAGE.md](../../py_sec_edgar/documents/sigdev_events/12_SIGDEV_EVENT_STORAGE.md) for PostgreSQL schema.

---

### Core Data Model

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class EventCategory(Enum):
    FINANCIAL = "financial"
    CORPORATE = "corporate"
    LEGAL = "legal"
    PRODUCT = "product"
    MARKET = "market"
    RISK = "risk"
    GOVERNANCE = "governance"
    OTHER = "other"


class EventSeverity(Enum):
    """Material impact level."""
    CRITICAL = "critical"   # Stock-moving, immediate action
    HIGH = "high"           # Material, significant impact
    MEDIUM = "medium"       # Notable, monitor closely
    LOW = "low"             # Informational
    ROUTINE = "routine"     # Expected/scheduled (earnings date)


class EventStatus(Enum):
    """Event lifecycle status."""
    DETECTED = "detected"       # Just captured
    CONFIRMED = "confirmed"     # Verified from multiple sources
    DEVELOPING = "developing"   # Updates expected
    RESOLVED = "resolved"       # Concluded
    SUPERSEDED = "superseded"   # Replaced by newer event


@dataclass
class CorporateEvent:
    """A significant corporate development."""

    # Identity
    event_id: str
    event_type: str              # "earnings_release", "acquisition_announced", etc.
    category: EventCategory

    # Core content
    headline: str
    summary: str
    full_text: Optional[str] = None

    # Temporal
    event_date: datetime         # When event occurred
    detected_at: datetime        # When we captured it
    effective_date: Optional[datetime] = None  # When it takes effect

    # Classification
    severity: EventSeverity = EventSeverity.MEDIUM
    status: EventStatus = EventStatus.DETECTED
    confidence: float = 0.0      # 0.0-1.0 classification confidence

    # Entity linking (via EntitySpine)
    primary_entity_id: str       # Main company involved
    related_entity_ids: List[str] = field(default_factory=list)

    # Source tracking
    sources: List["EventSource"] = field(default_factory=list)

    # Filing linkage
    related_filings: List["FilingReference"] = field(default_factory=list)
    triggered_by_filing: Optional[str] = None  # accession_number if from SEC

    # Enrichment results
    extracted_numbers: List["ExtractedNumber"] = field(default_factory=list)
    extracted_quotes: List["ExtractedQuote"] = field(default_factory=list)
    sentiment: Optional["SentimentScore"] = None

    # Event chain (for tracking evolution)
    parent_event_id: Optional[str] = None
    child_event_ids: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    enrichment_status: str = "pending"


@dataclass
class EventSource:
    """Where an event was captured from."""
    source_type: str        # "sec_filing", "press_release", "conference_call", "news"
    source_id: str          # accession_number, url, transcript_id
    source_name: str        # "SEC EDGAR", "PRNewswire", "Seeking Alpha"
    captured_at: datetime
    original_url: Optional[str] = None
    content_hash: Optional[str] = None  # For deduplication


@dataclass
class FilingReference:
    """Link to a related SEC filing."""
    accession_number: str
    form_type: str
    filed_date: datetime
    relationship: str       # "announced_in", "disclosed_details", "follow_up"
```

---

## Part 2: CaptureSpine Integration

### CaptureSpine as the Feed Monitor

**CaptureSpine** (already exists!) provides the infrastructure for monitoring feeds and capturing content. EventSpine builds on top:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CAPTURESPINE → EVENTSPINE FLOW                           │
└─────────────────────────────────────────────────────────────────────────────────┘

                    CAPTURESPINE                           EVENTSPINE
                    ────────────                           ──────────

    ┌─────────────┐                              ┌─────────────────────┐
    │  FEED       │                              │  EVENT              │
    │  MONITORS   │                              │  CLASSIFIERS        │
    │             │                              │                     │
    │ • SEC RSS   │                              │ • EventTypeClassifier
    │ • PRNewswire│     Raw Content              │ • SeverityClassifier│
    │ • Seeking   │────────────────────────────▶ │ • EntityLinker      │
    │   Alpha     │                              │ • FilingMatcher     │
    │ • Twitter   │                              │                     │
    └─────────────┘                              └─────────────────────┘
           │                                              │
           ▼                                              ▼
    ┌─────────────┐                              ┌─────────────────────┐
    │  CONTENT    │                              │  ENRICHER           │
    │  STORE      │                              │  ROUTER             │
    │  (dedupe)   │                              │  (by event type)    │
    └─────────────┘                              └─────────────────────┘
```

### Feed Configuration for Event Sources

```yaml
# eventspine/feeds.yaml - Feed definitions for CaptureSpine

feeds:
  # SEC Filings (already in FeedSpine, bridge to EventSpine)
  - name: sec_rss_filings
    type: sec_rss
    schedule: "*/10 * * * *"  # Every 10 minutes
    event_extractor: SECFilingEventExtractor

  # Press Release Wires
  - name: prnewswire
    type: rss
    url: "https://www.prnewswire.com/rss/financial-services-news.rss"
    schedule: "*/5 * * * *"   # Every 5 minutes
    event_extractor: PressReleaseEventExtractor
    filters:
      - type: keyword
        match: ["SEC filing", "earnings", "quarterly", "annual"]

  - name: businesswire
    type: rss
    url: "https://feed.businesswire.com/rss/home/"
    schedule: "*/5 * * * *"
    event_extractor: PressReleaseEventExtractor

  # Conference Call Transcripts
  - name: seeking_alpha_transcripts
    type: api
    provider: seeking_alpha
    schedule: "0 * * * *"     # Hourly
    event_extractor: ConferenceCallEventExtractor
    credentials_env: SEEKING_ALPHA_API_KEY

  # SEC News & Announcements
  - name: sec_news
    type: rss
    url: "https://www.sec.gov/news/pressreleases.rss"
    schedule: "*/15 * * * *"
    event_extractor: SECAnnouncementExtractor

  # Analyst Coverage (example)
  - name: analyst_ratings
    type: api
    provider: custom
    schedule: "0 6,18 * * *"  # Twice daily
    event_extractor: AnalystRatingExtractor
```

---

## Part 3: Event-to-Enricher Mapping

### The Enricher Pod Architecture

Just as sections map to enrichers, **events map to enricher pods**:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EVENT → ENRICHER POD MAPPING                             │
└─────────────────────────────────────────────────────────────────────────────────┘

    Event Type                              Enricher Pod
    ──────────                              ────────────

    Earnings Release    ───────────────▶    EarningsEnricherPod
                                            • EPS Extractor
                                            • Revenue Extractor
                                            • Guidance Extractor
                                            • YoY Comparison
                                            • Beat/Miss Classifier

    Conference Call     ───────────────▶    ConferenceCallEnricherPod
                                            • Transcript Parser
                                            • Speaker Identifier
                                            • Q&A Segmenter
                                            • Sentiment Analyzer
                                            • Key Quote Extractor
                                            • Forward Guidance Finder

    Press Release       ───────────────▶    PressReleaseEnricherPod
                                            • Event Type Classifier
                                            • Entity Extractor
                                            • Number Extractor
                                            • Sentiment Analyzer

    M&A Announcement    ───────────────▶    MergerEnricherPod
                                            • Deal Terms Extractor
                                            • Target/Acquirer Parser
                                            • Price Per Share
                                            • Expected Close Date
                                            • Regulatory Approval Status

    Legal Event         ───────────────▶    LegalEnricherPod
                                            • Case Name Parser
                                            • Plaintiff/Defendant
                                            • Claim Type
                                            • Damages Sought
                                            • Court/Jurisdiction
```

### Enricher Pod Protocol

```python
from abc import ABC, abstractmethod
from typing import Protocol, List, Type
from dataclasses import dataclass


class EventEnricher(Protocol):
    """Protocol for event enrichers."""

    async def enrich(
        self,
        event: "CorporateEvent",
        content: str,
        config: "EnricherConfig",
    ) -> "EventEnrichmentResult":
        """Enrich an event and return extracted data."""
        ...


@dataclass
class EventEnricherPod:
    """A pod of enrichers for a specific event type."""
    event_types: List[str]              # Event types this pod handles
    enrichers: List[Type[EventEnricher]]
    priority: int = 0
    use_llm: bool = False
    parallel_execution: bool = True

    async def process(
        self,
        event: "CorporateEvent",
        content: str,
    ) -> "CorporateEvent":
        """Run all enrichers in the pod."""
        results = []

        if self.parallel_execution:
            # Run enrichers in parallel
            tasks = [e.enrich(event, content, self.config) for e in self.enrichers]
            results = await asyncio.gather(*tasks)
        else:
            # Run sequentially
            for enricher in self.enrichers:
                result = await enricher.enrich(event, content, self.config)
                results.append(result)

        # Merge results into event
        return self._merge_results(event, results)


# =============================================================================
# ENRICHER POD REGISTRY
# =============================================================================

EVENT_ENRICHER_PODS: dict[str, EventEnricherPod] = {
    # Earnings Events
    "earnings_release": EventEnricherPod(
        event_types=["earnings_release", "quarterly_results", "annual_results"],
        enrichers=[
            EPSExtractor,
            RevenueExtractor,
            GuidanceExtractor,
            BeatMissClassifier,
            YoYComparisonEnricher,
        ],
        use_llm=True,
    ),

    # Conference Calls
    "conference_call": EventEnricherPod(
        event_types=["earnings_call", "analyst_call", "investor_day"],
        enrichers=[
            TranscriptParser,
            SpeakerIdentifier,
            QASegmenter,
            SentimentAnalyzer,
            KeyQuoteExtractor,
            ForwardGuidanceFinder,
        ],
        use_llm=True,
        parallel_execution=False,  # Sequential for transcript parsing
    ),

    # Press Releases
    "press_release": EventEnricherPod(
        event_types=["press_release", "announcement"],
        enrichers=[
            EventTypeClassifier,
            EntityExtractor,
            NumberExtractor,
            SentimentAnalyzer,
            QuoteExtractor,
        ],
        use_llm=True,
    ),

    # M&A Events
    "merger_acquisition": EventEnricherPod(
        event_types=["acquisition_announced", "merger_announced", "spin_off"],
        enrichers=[
            DealTermsExtractor,
            TargetAcquirerParser,
            ValuationExtractor,
            TimelineExtractor,
            RegulatoryStatusTracker,
        ],
        use_llm=True,
    ),

    # Legal Events
    "legal_event": EventEnricherPod(
        event_types=["lawsuit_filed", "settlement", "regulatory_action"],
        enrichers=[
            CaseNameParser,
            PartyExtractor,
            ClaimTypeClassifier,
            DamagesExtractor,
            JurisdictionParser,
        ],
        use_llm=True,
    ),
}
```

---

## Part 4: Bronze/Silver/Gold Data Architecture

### Integration with Existing Filing Pipeline

The Bronze/Silver/Gold architecture provides a **quality tiering system** that can be integrated across the entire platform:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   BRONZE / SILVER / GOLD DATA ARCHITECTURE                       │
│                   (Future Integration - Not Yet Implemented)                     │
└─────────────────────────────────────────────────────────────────────────────────┘

    BRONZE LAYER                 SILVER LAYER                GOLD LAYER
    ────────────                 ────────────                ──────────
    Raw, unprocessed             Cleaned, validated          Enriched, linked

┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  SEC FILINGS    │         │  PARSED         │         │  ENRICHED       │
│  • Raw SGML     │────────▶│  FILINGS        │────────▶│  FILINGS        │
│  • Downloaded   │         │  • Sections     │         │  • Entities     │
│    files        │         │  • Clean text   │         │  • Risks        │
│                 │         │  • Metadata     │         │  • Knowledge    │
│                 │         │    validated    │         │    graph links  │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  EVENTS         │         │  CLASSIFIED     │         │  ENRICHED       │
│  • Raw feeds    │────────▶│  EVENTS         │────────▶│  EVENTS         │
│  • Captured     │         │  • Event type   │         │  • Full NLP     │
│    content      │         │  • Severity     │         │  • Entity links │
│                 │         │  • Entities     │         │  • Filing links │
│                 │         │    (basic)      │         │  • Sentiment    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│  ENTITIES       │         │  RESOLVED       │         │  ENRICHED       │
│  • Raw mentions │────────▶│  ENTITIES       │────────▶│  ENTITIES       │
│  • Extracted    │         │  • Deduplicated │         │  • Full profile │
│    names        │         │  • CIK/ticker   │         │  • Relationships│
│                 │         │    linked       │         │  • Temporal     │
│                 │         │                 │         │    history      │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### Quality Gates Between Tiers

```python
@dataclass
class TierPromotionRules:
    """Rules for promoting data between tiers."""

    bronze_to_silver = [
        "has_valid_accession_number",
        "primary_document_parsed",
        "metadata_complete",
        "no_parsing_errors",
    ]

    silver_to_gold = [
        "all_sections_extracted",
        "entities_resolved_via_entityspine",
        "enrichment_pipeline_complete",
        "quality_score >= 0.8",
    ]
```

### Storage Implications

| Tier | Storage | Retention | Query Pattern |
|------|---------|-----------|---------------|
| **Bronze** | Object storage (S3/local) | Forever | Rarely (reprocessing) |
| **Silver** | DuckDB/PostgreSQL | Forever | Analytics, debugging |
| **Gold** | PostgreSQL + Elasticsearch | Forever | Production queries |

---

## Part 5: Conference Call Enrichment

### Conference Call Pipeline

Conference calls are high-value content requiring specialized processing:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CONFERENCE CALL ENRICHMENT PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

    INPUT: Raw Transcript
           │
           ▼
    ┌──────────────────┐
    │  TRANSCRIPT      │
    │  PARSER          │
    │  ─────────────   │
    │  • Header parse  │
    │  • Speaker IDs   │
    │  • Section splits│
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │  SECTION         │
    │  SEGMENTER       │
    │  ─────────────   │
    │  • Opening       │
    │  • Prepared      │
    │  • Q&A           │
    │  • Closing       │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │  SPEAKER         │
    │  IDENTIFIER      │
    │  ─────────────   │
    │  • Name → Role   │
    │  • EntitySpine   │
    │    lookup        │
    └──────────────────┘
           │
           ▼
    ┌──────────────────┐
    │  CONTENT         │
    │  ENRICHERS       │
    │  ─────────────   │
    │  • Key quotes    │
    │  • Guidance      │
    │  • Sentiment     │
    │  • Numbers       │
    └──────────────────┘
           │
           ▼
    OUTPUT: EnrichedConferenceCall
```

### Conference Call Data Model

```python
@dataclass
class ConferenceCall:
    """Enriched conference call transcript."""

    # Identity
    call_id: str
    call_type: str              # "earnings_call", "analyst_day", "investor_call"

    # Company
    company_cik: str
    company_name: str
    fiscal_period: str          # "Q3 2025", "FY 2025"

    # Timing
    call_date: datetime
    call_duration_minutes: int

    # Participants
    speakers: List["CallSpeaker"]
    analysts: List["CallAnalyst"]

    # Content sections
    opening_remarks: "TranscriptSection"
    prepared_remarks: "TranscriptSection"
    qa_section: "QASection"
    closing_remarks: Optional["TranscriptSection"]

    # Extracted insights
    key_quotes: List["ExtractedQuote"]
    guidance_statements: List["GuidanceStatement"]
    forward_looking_statements: List["ForwardLookingStatement"]

    # Sentiment
    overall_sentiment: "SentimentScore"
    management_tone: "ToneAnalysis"

    # Linkage
    related_earnings_release: Optional[str]  # Press release ID
    related_sec_filings: List[str]          # 8-K accession numbers


@dataclass
class CallSpeaker:
    """A speaker on the call."""
    name: str
    title: str
    entity_id: Optional[str]     # EntitySpine ID
    statement_count: int
    word_count: int


@dataclass
class QASection:
    """The Q&A portion of the call."""
    questions: List["AnalystQuestion"]
    total_questions: int
    most_discussed_topics: List[str]


@dataclass
class AnalystQuestion:
    """A question from an analyst."""
    analyst_name: str
    analyst_firm: str
    question_text: str
    response_text: str
    topics: List[str]
    follow_up: bool
```

---

## Part 6: Press Release Enrichment

### Press Release Pipeline

```python
@dataclass
class PressReleaseEnricherPod:
    """Enricher pod for press releases."""

    enrichers = [
        # Stage 1: Classification
        PressReleaseTypeClassifier,  # earnings, product, M&A, etc.

        # Stage 2: Extraction
        HeadlineParser,
        DatelineExtractor,           # "CUPERTINO, Calif., Jan 27, 2026"
        BoilerplateRemover,

        # Stage 3: Content Analysis
        KeyFactExtractor,
        QuoteExtractor,
        NumberExtractor,
        ContactInfoParser,

        # Stage 4: Entity Linking
        CompanyMentionExtractor,
        PersonMentionExtractor,
        EntitySpineResolver,

        # Stage 5: Quality
        SentimentAnalyzer,
        ForwardLookingClassifier,
    ]


@dataclass
class EnrichedPressRelease:
    """A fully enriched press release."""

    # Identity
    release_id: str
    source: str                     # "PRNewswire", "BusinessWire", etc.

    # Classification
    release_type: str               # "earnings", "product_launch", "leadership"
    category: EventCategory

    # Content
    headline: str
    subheadline: Optional[str]
    dateline: "Dateline"
    body_text: str

    # Extracted data
    key_facts: List["KeyFact"]
    quotes: List["ExtractedQuote"]
    numbers: List["ExtractedNumber"]

    # Entity linking
    primary_company: "EntityReference"
    mentioned_companies: List["EntityReference"]
    mentioned_people: List["PersonReference"]

    # Related content
    related_filing: Optional[str]   # If ties to 8-K
    related_event_id: Optional[str]

    # Sentiment
    sentiment: "SentimentScore"
    has_forward_looking: bool


@dataclass
class Dateline:
    """Press release dateline."""
    city: str
    state: Optional[str]
    country: Optional[str]
    date: datetime
    raw_text: str
```

---

## Part 7: Future Roadmap

### System Component Responsibilities

| Component | Current Status | Future Additions |
|-----------|---------------|------------------|
| **py-sec-edgar** | Core filing library | Bronze/Silver/Gold storage hooks |
| **FeedSpine** | SEC feed aggregation | Event detection triggers |
| **EntitySpine** | Entity resolution | Event participant linking |
| **CaptureSpine** | Content capture system | PR/news/transcript feeds |
| **EventSpine** | **NEW** | Event timeline manager |

### Implementation Phases

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        FUTURE IMPLEMENTATION ROADMAP                             │
└─────────────────────────────────────────────────────────────────────────────────┘

PHASE 1: FOUNDATION (Q2 2026)
─────────────────────────────
[py-sec-edgar]
  • Bronze/Silver/Gold tier markers in storage
  • Quality score fields in extraction tables

[EventSpine]
  • Core event data model
  • Basic event table in DuckDB/PostgreSQL
  • SEC 8-K → Event extraction
  • Event → Filing linking

─────────────────────────────

PHASE 2: CAPTURE INTEGRATION (Q3 2026)
──────────────────────────────────────
[CaptureSpine]
  • PR Newswire feed adapter
  • BusinessWire feed adapter
  • Basic deduplication

[EventSpine]
  • Press release event extraction
  • Event classification (LLM-based)
  • EntitySpine integration for event entities

─────────────────────────────

PHASE 3: CONFERENCE CALLS (Q4 2026)
───────────────────────────────────
[CaptureSpine]
  • Seeking Alpha transcript adapter
  • Transcript storage

[EventSpine]
  • Conference call parser
  • Speaker identification
  • Q&A segmentation
  • Guidance extraction from calls

─────────────────────────────

PHASE 4: ADVANCED ENRICHMENT (Q1 2027)
─────────────────────────────────────
[EventSpine]
  • Event chain tracking (announcement → filing → resolution)
  • Cross-event sentiment analysis
  • Event impact scoring
  • Alert system for material events

[EntitySpine]
  • Event participant profiles
  • Executive statement tracking
  • Analyst coverage mapping

─────────────────────────────

PHASE 5: UNIFIED TIMELINE (Q2 2027)
──────────────────────────────────
[All Components]
  • Unified event timeline API
  • Event → Filing → Entity graph
  • Point-in-time event queries
  • "What happened to {company} between {dates}"
```

---

## Part 8: Integration Points

### How Components Connect

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        COMPONENT INTEGRATION MAP                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

                              py-sec-edgar
                              ────────────
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │FeedSpine │  │EntitySpine│  │Enrichers │
              │ (feeds)  │  │(entities) │  │(pipeline)│
              └──────────┘  └──────────┘  └──────────┘
                    │              │              │
                    │              │              │
                    ▼              ▼              ▼
              ┌───────────────────────────────────────┐
              │              CaptureSpine              │
              │      (content capture & storage)       │
              │                                        │
              │  • SEC RSS → Filing events             │
              │  • PR feeds → Press release events     │
              │  • Transcript APIs → Call events       │
              └───────────────────────────────────────┘
                                   │
                                   ▼
              ┌───────────────────────────────────────┐
              │              EventSpine                │
              │     (significant development mgr)      │
              │                                        │
              │  • Event classification                │
              │  • Event → Filing linking              │
              │  • Event → Entity linking              │
              │  • Event timeline                      │
              │  • Event enrichment routing            │
              └───────────────────────────────────────┘
```

### API Examples (Future)

```python
# Get all events for a company
events = await eventspine.get_events(
    cik="0000320193",           # Apple
    start_date="2025-01-01",
    event_types=["earnings_release", "conference_call"],
)

# Get event timeline with related filings
timeline = await eventspine.get_timeline(
    cik="0000320193",
    include_filings=True,
    include_press_releases=True,
    include_conference_calls=True,
)

# Track an M&A event chain
event_chain = await eventspine.get_event_chain(
    event_id="evt_abc123",      # Original announcement
    include_follow_ups=True,    # Subsequent filings/updates
)

# Search events across companies
results = await eventspine.search_events(
    query="AI chip supply",
    event_types=["earnings_call"],
    sentiment="negative",
    date_range=("2025-01-01", "2025-12-31"),
)
```

---

## Part 9: Additional Spine Projects

### The Complete Spine Ecosystem

Beyond the current components, we need **additional spine projects** to manage the full investment intelligence lifecycle:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        THE SPINE ECOSYSTEM                                       │
│           "Each spine manages a specific domain of financial intelligence"       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────┐
│  CORE INFRASTRUCTURE (Implemented)                                             │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ py-sec-edgar│  │  FeedSpine  │  │ EntitySpine │  │CaptureSpine │         │
│  │   (core)    │  │   (feeds)   │  │ (entities)  │  │  (capture)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│  EVENT LAYER (Planned)                                                        │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐         │
│  │                        EventSpine                                │         │
│  │  • SigDev event detection (35+ types)                           │         │
│  │  • Event → Filing linking                                        │         │
│  │  • Event chains (announcement → filing → resolution)            │         │
│  │  • Earnings/guidance events, M&A events, legal events           │         │
│  └─────────────────────────────────────────────────────────────────┘         │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│  QUANTITATIVE LAYER (Future)                                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │     EstimateSpine       │  │     MetricSpine         │                   │
│  │  • Analyst estimates    │  │  • KPIs over time       │                   │
│  │  • Consensus tracking   │  │  • Segment metrics      │                   │
│  │  • Surprise calculation │  │  • Product line data    │                   │
│  │  • Revision history     │  │  • Geographic breakdown │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
│                                                                               │
├───────────────────────────────────────────────────────────────────────────────┤
│  RESEARCH LAYER (Future)                                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │     ResearchSpine       │  │      AlertSpine         │                   │
│  │  • Analyst reports      │  │  • User watchlists      │                   │
│  │  • Price targets        │  │  • Event triggers       │                   │
│  │  • Rating changes       │  │  • Threshold alerts     │                   │
│  │  • Research notes       │  │  • Notification mgmt    │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

### EstimateSpine: Analyst Estimates & Surprises

**Purpose**: Manage analyst estimates, consensus tracking, and earnings/revenue surprise calculations.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ESTIMATESPINE                                         │
│        "Track what the Street expects vs. what companies deliver"               │
└─────────────────────────────────────────────────────────────────────────────────┘

                    ESTIMATES                    ACTUALS                 ANALYSIS
               ──────────────               ──────────────            ──────────────

  Analyst EPS ─────────┐                 ┌─────────────────┐
  Analyst Revenue ─────┤                 │                 │      → Surprise %
  Segment Estimates ───┤                 │  ESTIMATESPINE  │      → Beat/Miss
  Product Line Est. ───┼────────────────▶│                 │──────→ Revision Trend
  Consensus (Mean) ────┤                 │  ┌───────────┐  │      → Analyst Accuracy
  High/Low Range ──────┤                 │  │ Temporal  │  │      → Guidance vs Est
  # of Analysts ───────┘                 │  │ Tracking  │  │      → Historical Beats
                                         │  └───────────┘  │
                   Earnings Releases ───▶│                 │
                   8-K Item 2.02 ───────▶│                 │
                   10-Q/10-K Actuals ───▶│                 │
                                         └─────────────────┘
```

#### EstimateSpine Data Model

```python
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class EstimateType(Enum):
    EPS = "eps"                          # Earnings per share
    EPS_GAAP = "eps_gaap"                # GAAP EPS
    EPS_NON_GAAP = "eps_non_gaap"        # Adjusted/Non-GAAP EPS
    REVENUE = "revenue"                   # Total revenue
    REVENUE_SEGMENT = "revenue_segment"   # Segment revenue
    REVENUE_PRODUCT = "revenue_product"   # Product line revenue
    REVENUE_GEO = "revenue_geo"           # Geographic revenue
    EBITDA = "ebitda"                     # EBITDA
    GROSS_MARGIN = "gross_margin"         # Gross margin %
    OPERATING_MARGIN = "op_margin"        # Operating margin %
    FREE_CASH_FLOW = "fcf"               # Free cash flow
    CAPEX = "capex"                       # Capital expenditure
    GUIDANCE_LOW = "guidance_low"         # Company guidance low
    GUIDANCE_HIGH = "guidance_high"       # Company guidance high
    GUIDANCE_MID = "guidance_mid"         # Company guidance midpoint


class FiscalPeriod(Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
    FY = "FY"          # Full year
    H1 = "H1"          # First half
    H2 = "H2"          # Second half


@dataclass
class AnalystEstimate:
    """A single analyst's estimate."""

    # Identity
    estimate_id: str
    analyst_name: str
    analyst_firm: str
    analyst_firm_id: Optional[str] = None  # EntitySpine ID

    # Target
    company_cik: str
    company_name: str

    # Period
    fiscal_year: int
    fiscal_period: FiscalPeriod

    # Estimate
    estimate_type: EstimateType
    value: Decimal
    currency: str = "USD"

    # Segment/Product (if applicable)
    segment_name: Optional[str] = None
    product_name: Optional[str] = None
    geography: Optional[str] = None

    # Metadata
    estimate_date: date                  # When estimate was made
    prior_estimate: Optional[Decimal] = None  # Previous estimate
    revision_direction: Optional[str] = None  # "up", "down", "unchanged"

    # Source
    source: str                          # "bloomberg", "refinitiv", "manual"
    source_id: Optional[str] = None


@dataclass
class ConsensusEstimate:
    """Aggregated consensus estimate."""

    # Target
    company_cik: str
    fiscal_year: int
    fiscal_period: FiscalPeriod
    estimate_type: EstimateType

    # Consensus values
    mean: Decimal
    median: Decimal
    high: Decimal
    low: Decimal
    std_dev: Decimal
    num_analysts: int

    # Temporal
    as_of_date: date

    # Revision tracking
    mean_30d_ago: Optional[Decimal] = None
    mean_90d_ago: Optional[Decimal] = None
    revision_trend: Optional[str] = None  # "up", "down", "stable"


@dataclass
class ActualResult:
    """Reported actual result from earnings."""

    # Identity
    company_cik: str
    fiscal_year: int
    fiscal_period: FiscalPeriod
    estimate_type: EstimateType

    # Actual
    reported_value: Decimal
    currency: str = "USD"

    # Source
    source_filing: Optional[str] = None   # accession_number
    source_press_release: Optional[str] = None
    reported_date: date

    # Segment/Product (if applicable)
    segment_name: Optional[str] = None
    product_name: Optional[str] = None


@dataclass
class EarningsSurprise:
    """Calculated surprise vs. consensus."""

    # Identity
    company_cik: str
    fiscal_year: int
    fiscal_period: FiscalPeriod
    estimate_type: EstimateType

    # Values
    consensus_estimate: Decimal
    actual_result: Decimal

    # Surprise calculation
    surprise_amount: Decimal             # actual - estimate
    surprise_percent: Decimal            # (actual - estimate) / estimate * 100
    beat_or_miss: str                    # "beat", "miss", "inline"

    # Context
    guidance_midpoint: Optional[Decimal] = None
    vs_guidance: Optional[str] = None    # "above", "below", "inline"

    # Historical context
    consecutive_beats: int = 0
    consecutive_misses: int = 0

    # Linked event
    event_id: Optional[str] = None       # EventSpine event


# Example: Track quarterly estimates over time
@dataclass
class EstimateTimeSeries:
    """Track how estimates evolved leading up to earnings."""

    company_cik: str
    fiscal_year: int
    fiscal_period: FiscalPeriod
    estimate_type: EstimateType

    # Time series of consensus
    history: List[tuple[date, Decimal]]  # [(date, consensus_mean), ...]

    # Key dates
    quarter_start: date
    earnings_date: date

    # Analysis
    starting_estimate: Decimal
    final_estimate: Decimal
    total_revision_pct: Decimal
```

#### EstimateSpine API Examples

```python
# Get current consensus for Apple Q1 2026
consensus = await estimatespine.get_consensus(
    cik="0000320193",
    fiscal_year=2026,
    fiscal_period="Q1",
    estimate_type="eps_non_gaap",
)
print(f"EPS Consensus: ${consensus.mean:.2f} ({consensus.num_analysts} analysts)")

# Get earnings surprise history
surprises = await estimatespine.get_surprise_history(
    cik="0000320193",
    periods=8,  # Last 8 quarters
)
for s in surprises:
    print(f"{s.fiscal_period} {s.fiscal_year}: {s.beat_or_miss} by {s.surprise_percent:.1f}%")

# Track estimate revisions
revisions = await estimatespine.get_revision_trend(
    cik="0000320193",
    fiscal_year=2026,
    fiscal_period="Q1",
    lookback_days=90,
)

# Get segment-level estimates
segment_estimates = await estimatespine.get_segment_estimates(
    cik="0000320193",
    fiscal_year=2026,
    fiscal_period="Q1",
    segments=["iPhone", "Services", "Mac", "iPad", "Wearables"],
)
```

---

### MetricSpine: KPIs & Operating Metrics

**Purpose**: Track operational KPIs, segment metrics, and product line data over time.

```python
@dataclass
class OperatingMetric:
    """A company's operating KPI over time."""

    # Identity
    metric_id: str
    company_cik: str

    # Metric definition
    metric_name: str                     # "iPhone Units", "AWS Revenue", "Subscribers"
    metric_type: str                     # "units", "revenue", "margin", "count", "rate"
    unit: str                            # "millions", "billions", "$M", "%"

    # Classification
    segment: Optional[str] = None        # "iPhone", "Cloud", "Devices"
    product_line: Optional[str] = None   # "iPhone Pro", "EC2", "Surface Pro"
    geography: Optional[str] = None      # "Americas", "EMEA", "APAC"

    # Value
    fiscal_year: int
    fiscal_period: str                   # "Q1", "FY", "H1"
    value: Decimal
    prior_period_value: Optional[Decimal] = None
    yoy_change_pct: Optional[Decimal] = None

    # Source
    source_filing: Optional[str] = None
    source_section: Optional[str] = None  # "MD&A", "Segment Notes"
    extraction_confidence: float = 0.0

    # Metadata
    disclosed_date: date
    is_gaap: bool = True
    company_definition: Optional[str] = None  # How company defines it


@dataclass
class MetricTimeSeries:
    """Time series of a metric."""

    company_cik: str
    metric_name: str

    # Quarterly history
    quarterly: List[tuple[str, Decimal]]   # [("Q1 2024", 50.1), ("Q2 2024", 52.3), ...]

    # Annual history
    annual: List[tuple[int, Decimal]]      # [(2023, 200.5), (2024, 210.2), ...]

    # Trend analysis
    cagr_3yr: Optional[Decimal] = None
    cagr_5yr: Optional[Decimal] = None
    trend_direction: Optional[str] = None  # "growing", "declining", "stable"
```

#### MetricSpine API Examples

```python
# Get iPhone revenue over time
iphone_revenue = await metricspine.get_metric_series(
    cik="0000320193",
    metric_name="iPhone Revenue",
    periods=12,  # Last 12 quarters
)

# Get all segments for a company
segments = await metricspine.get_segment_breakdown(
    cik="0000320193",
    fiscal_year=2025,
    fiscal_period="Q4",
)

# Compare metric across companies
comparison = await metricspine.compare_metric(
    ciks=["0000320193", "0001018724", "0001652044"],  # Apple, Amazon, Google
    metric_type="services_revenue",
    periods=8,
)
```

---

### ResearchSpine: Analyst Research & Ratings

**Purpose**: Manage analyst ratings, price targets, research reports, and coverage tracking.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RESEARCHSPINE                                         │
│              "Aggregate and track Wall Street research coverage"                │
└─────────────────────────────────────────────────────────────────────────────────┘

                    INPUTS                      ANALYSIS                 OUTPUTS
               ──────────────               ──────────────            ──────────────

  Rating Changes ──────┐                 ┌─────────────────┐
  (Upgrade/Downgrade)  │                 │                 │      → Consensus Rating
                       │                 │  RESEARCHSPINE  │      → Avg Price Target
  Price Target ────────┤                 │                 │──────→ Bull/Bear Cases
  Changes              │                 │  ┌───────────┐  │      → Coverage Changes
                       ├────────────────▶│  │ Analyst   │  │      → Rating History
  Research Notes ──────┤                 │  │ Profiles  │  │      → Target Accuracy
                       │                 │  └───────────┘  │      → Sentiment Trend
  Earnings Revisions ──┤                 │                 │
                       │                 └─────────────────┘
  Coverage Initiation ─┘
  /Termination
```

```python
class AnalystRating(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    OUTPERFORM = "outperform"
    HOLD = "hold"
    NEUTRAL = "neutral"
    UNDERPERFORM = "underperform"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class ResearchCoverage:
    """Analyst coverage of a company."""

    # Analyst
    analyst_name: str
    analyst_firm: str
    analyst_id: Optional[str] = None     # EntitySpine ID

    # Target company
    company_cik: str
    company_name: str

    # Rating
    current_rating: AnalystRating
    prior_rating: Optional[AnalystRating] = None
    rating_date: date

    # Price target
    price_target: Optional[Decimal] = None
    prior_price_target: Optional[Decimal] = None
    price_target_date: Optional[date] = None

    # Coverage status
    coverage_status: str                 # "active", "suspended", "terminated"
    coverage_initiated: date

    # Track record
    accuracy_score: Optional[float] = None  # Historical accuracy


@dataclass
class ConsensusRating:
    """Aggregated analyst consensus."""

    company_cik: str
    as_of_date: date

    # Rating distribution
    strong_buy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strong_sell: int = 0
    total_analysts: int = 0

    # Consensus metrics
    consensus_rating: str                # "Buy", "Hold", "Sell"
    consensus_score: Decimal             # 1.0-5.0 scale

    # Price targets
    avg_price_target: Decimal
    high_price_target: Decimal
    low_price_target: Decimal
    median_price_target: Decimal

    # vs current price
    current_price: Optional[Decimal] = None
    upside_to_target_pct: Optional[Decimal] = None

    # Momentum
    upgrades_30d: int = 0
    downgrades_30d: int = 0
    rating_momentum: str = "stable"      # "improving", "deteriorating", "stable"


@dataclass
class RatingChange:
    """A rating or price target change event."""

    # Change details
    analyst_name: str
    analyst_firm: str
    company_cik: str
    change_date: date

    # Rating change
    old_rating: Optional[AnalystRating] = None
    new_rating: Optional[AnalystRating] = None
    rating_action: Optional[str] = None  # "upgrade", "downgrade", "initiate", "reiterate"

    # Price target change
    old_price_target: Optional[Decimal] = None
    new_price_target: Optional[Decimal] = None

    # Context
    headline: Optional[str] = None
    rationale: Optional[str] = None

    # Link to events
    related_event_id: Optional[str] = None  # If triggered by earnings, etc.
```

---

### AlertSpine: Watchlists & Notifications

**Purpose**: Manage user watchlists, event triggers, and real-time notifications.

```python
class AlertTriggerType(Enum):
    FILING_NEW = "filing_new"            # New filing of type X
    EVENT_DETECTED = "event_detected"    # SigDev event of type X
    RATING_CHANGE = "rating_change"      # Upgrade/downgrade
    PRICE_TARGET = "price_target"        # PT change > threshold
    ESTIMATE_REVISION = "estimate_rev"   # Estimate revision > threshold
    EARNINGS_SURPRISE = "earnings_surp"  # Beat/miss > threshold
    INSIDER_TRADE = "insider_trade"      # Form 4 filed
    OWNERSHIP_CHANGE = "ownership"       # 13D/13G filed


@dataclass
class AlertRule:
    """A user-defined alert trigger."""

    rule_id: str
    user_id: str

    # Trigger
    trigger_type: AlertTriggerType

    # Filters
    company_ciks: List[str] = field(default_factory=list)  # Empty = all
    form_types: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)

    # Thresholds
    threshold_value: Optional[Decimal] = None
    threshold_direction: Optional[str] = None  # "above", "below", "any"

    # Notification
    notification_channels: List[str] = field(default_factory=list)  # "email", "slack", "webhook"

    # Status
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Watchlist:
    """A user's company watchlist."""

    watchlist_id: str
    user_id: str
    name: str

    # Companies
    companies: List["WatchlistCompany"] = field(default_factory=list)

    # Settings
    alert_rules: List[str] = field(default_factory=list)  # AlertRule IDs
    email_digest: str = "daily"          # "realtime", "daily", "weekly", "none"


@dataclass
class WatchlistCompany:
    """A company in a watchlist."""
    cik: str
    ticker: str
    company_name: str
    added_at: datetime
    notes: Optional[str] = None
    custom_tags: List[str] = field(default_factory=list)
```

---

## Part 10: Complete Ecosystem Integration

### Full Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE SPINE ECOSYSTEM DATA FLOW                            │
└─────────────────────────────────────────────────────────────────────────────────┘

                              EXTERNAL DATA SOURCES
     ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
     │SEC EDGAR │ │PR Wires  │ │Transcripts│ │Bloomberg │ │ News     │
     └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
          │            │            │            │            │
          └────────────┴────────────┼────────────┴────────────┘
                                    │
                                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                        CAPTURE LAYER                            │
     │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
     │  │  FeedSpine  │  │CaptureSpine │  │  External Data Adapters │ │
     │  │(SEC Filings)│  │(News/PR/CC) │  │ (Estimates, Research)   │ │
     │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
     └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                      ENRICHMENT LAYER                           │
     │  ┌─────────────────────────────────────────────────────────────┐│
     │  │                     py-sec-edgar                            ││
     │  │  Parse → Section Extract → Entity Extract → Classify → XBRL ││
     │  └─────────────────────────────────────────────────────────────┘│
     └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                      RESOLUTION LAYER                           │
     │  ┌─────────────────────────────────────────────────────────────┐│
     │  │                      EntitySpine                            ││
     │  │  Company ↔ Ticker ↔ CIK ↔ People ↔ Subsidiaries ↔ Products  ││
     │  └─────────────────────────────────────────────────────────────┘│
     └─────────────────────────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
     ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
     │ EventSpine  │         │EstimateSpine│         │ResearchSpine│
     │             │         │             │         │             │
     │ • SigDev    │◀───────▶│ • Consensus │◀───────▶│ • Ratings   │
     │   events    │         │ • Surprises │         │ • Targets   │
     │ • Event     │         │ • Guidance  │         │ • Reports   │
     │   chains    │         │ • Segments  │         │ • Coverage  │
     └─────────────┘         └─────────────┘         └─────────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                       METRICS LAYER                             │
     │  ┌─────────────────────────────────────────────────────────────┐│
     │  │                      MetricSpine                            ││
     │  │  KPIs • Segment Data • Product Lines • Time Series • Trends ││
     │  └─────────────────────────────────────────────────────────────┘│
     └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
     ┌─────────────────────────────────────────────────────────────────┐
     │                      DELIVERY LAYER                             │
     │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
     │  │ AlertSpine  │  │    API      │  │      Frontend           │ │
     │  │(Watchlists) │  │  (FastAPI)  │  │  (React Dashboard)      │ │
     │  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
     └─────────────────────────────────────────────────────────────────┘
```

### Cross-Spine Queries

```python
# "Show me Apple's last earnings: estimate, actual, surprise, and all related events"

# 1. Get earnings event from EventSpine
earnings_event = await eventspine.get_latest_event(
    cik="0000320193",
    event_type="GUIDANCE_UPDATE",
)

# 2. Get estimate/actual from EstimateSpine
surprise = await estimatespine.get_surprise(
    cik="0000320193",
    fiscal_year=earnings_event.fiscal_year,
    fiscal_period=earnings_event.fiscal_period,
)

# 3. Get rating changes around earnings from ResearchSpine
rating_changes = await researchspine.get_rating_changes(
    cik="0000320193",
    days_around=7,
    reference_date=earnings_event.event_date,
)

# 4. Get related filings from py-sec-edgar
filings = await sec.get_related_filings(
    event_id=earnings_event.event_id,
)

# 5. Combine into comprehensive view
earnings_report = EarningsReport(
    event=earnings_event,
    surprise=surprise,
    rating_changes=rating_changes,
    filings=filings,
    conference_call=await eventspine.get_related_call(earnings_event.event_id),
)
```

---

## Summary

| System | Purpose | Status |
|--------|---------|--------|
| **py-sec-edgar** | Core SEC filing library | ✅ Implemented |
| **FeedSpine** | SEC feed aggregation | ✅ Implemented |
| **EntitySpine** | Entity resolution & management | ✅ Implemented |
| **CaptureSpine** | Universal content capture | ✅ Implemented (separate) |
| **edgar_sigdev_pack** | SigDev event detection | ✅ Implemented |
| **EventSpine** | Event timeline management | 🔮 Future (builds on SigDev) |
| **EstimateSpine** | Analyst estimates & surprises | 🔮 Future |
| **MetricSpine** | KPIs & operating metrics | 🔮 Future |
| **ResearchSpine** | Analyst research & ratings | 🔮 Future |
| **AlertSpine** | Watchlists & notifications | 🔮 Future |
| **Bronze/Silver/Gold** | Data quality tiers | 🔮 Future integration |

### Key Ideas

1. **EventSpine** builds on proven **edgar_sigdev_pack** with 35+ event types
2. **EstimateSpine** manages the full analyst estimate lifecycle (estimates → actuals → surprises)
3. **MetricSpine** tracks operational KPIs and segment data over time
4. **ResearchSpine** aggregates analyst ratings, targets, and coverage
5. **AlertSpine** delivers personalized notifications based on user watchlists
6. **All spines link** through EntitySpine for consistent entity resolution
7. **Cross-spine queries** enable comprehensive investment analysis
