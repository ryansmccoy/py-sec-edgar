# Enriched Filing Model

**Purpose**: Define the rich filing object that users can explore after downloading.

---

## Vision

When a user downloads Apple's 10-K, they should get a **fully enriched Filing object** that exposes everything extractable from that filing in a structured, queryable way.

```python
from py_sec_edgar import SEC, Forms

async with SEC() as sec:
    # Download and enrich Apple's 10-K
    filing = await sec.get_filing("AAPL", Forms.FORM_10K, year=2024, enrich=True)

    # Now the filing is a rich object
    print(filing.company.name)           # "Apple Inc."
    print(filing.company.cik)            # "0000320193"
    print(filing.filed_date)             # date(2024, 11, 1)
    print(filing.period_end)             # date(2024, 9, 28)

    # Access extracted entities
    print(filing.suppliers)              # ["TSMC", "Samsung", "Foxconn", ...]
    print(filing.customers)              # ["Best Buy", "Verizon", ...]
    print(filing.competitors)            # ["Samsung", "Google", "Microsoft", ...]
    print(filing.subsidiaries)           # ["Apple Sales International", ...]

    # Access structured sections
    print(filing.risk_factors)           # List[RiskFactor]
    print(filing.management_guidance)    # ManagementGuidance object
    print(filing.product_lines)          # List[ProductLine]

    # Access raw sections too
    print(filing.sections.item_1a.text)  # Raw risk factors text
    print(filing.sections.item_7.text)   # MD&A text
```

---

## The EnrichedFiling Model

```python
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from enum import Enum

# =============================================================================
# CORE FILING IDENTITY
# =============================================================================

@dataclass
class FilingIdentity:
    """Core filing identifiers."""
    accession_number: str
    form_type: str
    filed_date: date
    period_of_report: date
    fiscal_year_end: str  # "0928" = Sept 28

    # URLs
    filing_url: str
    index_url: str

    # Document references
    primary_document: str  # "aapl-20240928.htm"
    document_count: int


@dataclass
class CompanyIdentity:
    """Company information from filing."""
    cik: str
    name: str
    ticker: str | None
    sic_code: str
    sic_description: str
    state_of_incorporation: str
    fiscal_year_end: str

    # From EntitySpine (if available)
    entity_id: str | None = None
    lei: str | None = None


# =============================================================================
# EXTRACTED ENTITIES
# =============================================================================

class EntityType(Enum):
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    COMPETITOR = "competitor"
    PARTNER = "partner"
    SUBSIDIARY = "subsidiary"
    REGULATOR = "regulator"
    INVESTOR = "investor"
    AUDITOR = "auditor"


class MentionContext(Enum):
    """Context where entity was mentioned."""
    RISK_FACTORS = "risk_factors"
    MDA = "mda"
    BUSINESS_DESCRIPTION = "business"
    LEGAL_PROCEEDINGS = "legal"
    RELATED_PARTIES = "related_parties"
    EXHIBIT = "exhibit"


@dataclass
class EntityMention:
    """A mention of an entity in the filing."""
    name: str
    entity_type: EntityType
    context: MentionContext
    section: str  # "Item 1A", "Item 7", etc.

    # Location in filing (for click-through provenance)
    document: str
    start_offset: int
    end_offset: int
    surrounding_text: str  # ~200 chars around mention
    sentence_text: str     # Full sentence containing mention

    # Confidence
    confidence: float  # 0.0 - 1.0
    extraction_method: str  # "ner", "pattern", "llm"

    # Resolution (if EntitySpine available)
    resolved_entity_id: str | None = None
    resolved_cik: str | None = None

    # Temporal tracking (point-in-time)
    first_seen_at: datetime | None = None
    first_seen_in_filing: str | None = None
    last_seen_at: datetime | None = None
    occurrence_count: int = 1

    # SEC URL for click-through
    @property
    def sec_url(self) -> str:
        """Direct link to view in SEC filing."""
        # Constructed from filing metadata
        return f"https://www.sec.gov/Archives/edgar/..."


@dataclass
class ExtractedEntities:
    """All entities extracted from filing."""

    # By type (deduplicated, most confident)
    suppliers: List[EntityMention]
    customers: List[EntityMention]
    competitors: List[EntityMention]
    partners: List[EntityMention]
    subsidiaries: List[EntityMention]
    regulators: List[EntityMention]
    auditors: List[EntityMention]

    # All mentions (for detailed analysis)
    all_mentions: List[EntityMention]

    # Summary stats
    @property
    def supplier_count(self) -> int:
        return len(self.suppliers)

    @property
    def unique_entities(self) -> int:
        names = {m.name for m in self.all_mentions}
        return len(names)


# =============================================================================
# STRUCTURED SECTIONS
# =============================================================================

@dataclass
class RiskFactor:
    """A single risk factor from Item 1A."""
    title: str
    text: str

    # Classification
    category: str  # "operational", "financial", "regulatory", "cyber", etc.
    severity: str  # "high", "medium", "low"

    # Change tracking
    is_new: bool = False  # New since last filing
    is_modified: bool = False
    prior_text: str | None = None  # For comparison

    # Entities mentioned in this risk
    entities_mentioned: List[str] = field(default_factory=list)


@dataclass
class ProductLine:
    """A product or service line mentioned in filing."""
    name: str
    description: str

    # Revenue contribution (if disclosed)
    revenue: float | None = None
    revenue_pct: float | None = None
    growth_rate: float | None = None

    # Commentary
    management_commentary: str | None = None
    outlook: str | None = None  # "positive", "neutral", "negative"

    # Where mentioned
    sections_mentioned: List[str] = field(default_factory=list)


@dataclass
class ManagementGuidance:
    """Forward-looking statements and guidance."""

    # Overall outlook
    outlook_summary: str
    sentiment: str  # "positive", "neutral", "cautious", "negative"

    # Specific guidance
    revenue_guidance: str | None = None
    margin_guidance: str | None = None
    capex_guidance: str | None = None

    # Key themes
    growth_drivers: List[str] = field(default_factory=list)
    headwinds: List[str] = field(default_factory=list)
    strategic_priorities: List[str] = field(default_factory=list)

    # Source sections
    source_sections: List[str] = field(default_factory=list)


@dataclass
class GeographicSegment:
    """Geographic segment disclosure."""
    region: str
    revenue: float | None = None
    revenue_pct: float | None = None
    growth_rate: float | None = None
    commentary: str | None = None


@dataclass
class LegalProceeding:
    """A legal proceeding from Item 3."""
    title: str
    description: str
    status: str  # "pending", "settled", "dismissed"
    potential_exposure: float | None = None
    parties: List[str] = field(default_factory=list)


# =============================================================================
# FINANCIAL DATA
# =============================================================================

@dataclass
class FinancialHighlight:
    """Key financial metrics (from XBRL or text)."""
    metric: str
    value: float
    unit: str  # "USD", "shares", "percent"
    period: str  # "FY2024", "Q4 2024"

    # Comparison
    prior_value: float | None = None
    change_pct: float | None = None

    # Source
    source: str  # "xbrl", "text_extraction"


@dataclass
class FinancialData:
    """Extracted financial data."""

    # Key metrics
    revenue: FinancialHighlight | None = None
    net_income: FinancialHighlight | None = None
    eps: FinancialHighlight | None = None
    total_assets: FinancialHighlight | None = None
    total_debt: FinancialHighlight | None = None
    cash: FinancialHighlight | None = None

    # All metrics
    all_metrics: List[FinancialHighlight] = field(default_factory=list)

    # Segment data
    geographic_segments: List[GeographicSegment] = field(default_factory=list)
    product_segments: List[ProductLine] = field(default_factory=list)


# =============================================================================
# EXHIBITS
# =============================================================================

@dataclass
class ClassifiedExhibit:
    """An exhibit with classification."""
    exhibit_number: str  # "10.1", "21.1", etc.
    filename: str
    description: str

    # Classification
    exhibit_type: str  # From Exhibits enum
    classified_type: str | None = None  # "employment_agreement", "credit_facility"

    # Extracted content (if applicable)
    parties: List[str] = field(default_factory=list)
    effective_date: date | None = None
    key_terms: Dict[str, Any] = field(default_factory=dict)

    # Status
    is_new: bool = False  # Filed with this filing
    is_incorporated: bool = False  # Incorporated by reference


# =============================================================================
# THE ENRICHED FILING
# =============================================================================

@dataclass
class EnrichedFiling:
    """
    The fully enriched filing object.

    This is what users interact with after downloading and enriching a filing.
    """

    # Identity
    identity: FilingIdentity
    company: CompanyIdentity

    # Raw sections (always available)
    sections: Dict[str, "FilingSection"]

    # Extracted entities
    entities: ExtractedEntities

    # Structured data
    risk_factors: List[RiskFactor]
    product_lines: List[ProductLine]
    management_guidance: ManagementGuidance | None
    legal_proceedings: List[LegalProceeding]

    # Financial data
    financials: FinancialData

    # Exhibits
    exhibits: List[ClassifiedExhibit]

    # Metadata
    enrichment_version: str
    enriched_at: datetime
    enrichment_methods: List[str]  # ["ner", "pattern", "llm:gpt-4"]

    # ==========================================================================
    # CONVENIENCE ACCESSORS
    # ==========================================================================

    @property
    def suppliers(self) -> List[str]:
        """Unique supplier names."""
        return list({e.name for e in self.entities.suppliers})

    @property
    def customers(self) -> List[str]:
        """Unique customer names."""
        return list({e.name for e in self.entities.customers})

    @property
    def competitors(self) -> List[str]:
        """Unique competitor names."""
        return list({e.name for e in self.entities.competitors})

    @property
    def subsidiaries(self) -> List[str]:
        """Unique subsidiary names."""
        return list({e.name for e in self.entities.subsidiaries})

    @property
    def key_risks(self) -> List[RiskFactor]:
        """High severity risks only."""
        return [r for r in self.risk_factors if r.severity == "high"]

    @property
    def new_risks(self) -> List[RiskFactor]:
        """Risks new since last filing."""
        return [r for r in self.risk_factors if r.is_new]

    # ==========================================================================
    # SERIALIZATION
    # ==========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON/storage."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnrichedFiling":
        """Reconstruct from dictionary."""
        ...

    def to_json(self) -> str:
        """Serialize to JSON."""
        ...

    # ==========================================================================
    # LINKING
    # ==========================================================================

    def link_to_graph(self, graph: "KnowledgeGraph") -> None:
        """Add this filing's entities to the knowledge graph."""
        ...

    def find_related_filings(self, storage: "FilingStorage") -> List["EnrichedFiling"]:
        """Find filings that mention the same entities."""
        ...


@dataclass
class FilingSection:
    """A section of the filing."""
    section_id: str  # "item_1a", "item_7"
    title: str
    text: str
    html: str | None

    # Location
    start_offset: int
    end_offset: int
    word_count: int

    # Extraction metadata
    extraction_confidence: float
```

---

## User Experience Vision

### Exploring a Single Filing

```python
# Get Apple's latest 10-K, fully enriched
filing = await sec.get_filing("AAPL", Forms.FORM_10K, latest=True, enrich=True)

# See what entities were found
print(f"Found {len(filing.suppliers)} suppliers:")
for s in filing.suppliers[:5]:
    print(f"  - {s}")

print(f"\nFound {len(filing.competitors)} competitors:")
for c in filing.competitors[:5]:
    print(f"  - {c}")

# Explore risk factors
print(f"\n{len(filing.risk_factors)} risk factors, {len(filing.key_risks)} high-severity")
for risk in filing.key_risks[:3]:
    print(f"\n[{risk.category.upper()}] {risk.title}")
    print(f"  {risk.text[:200]}...")

# See product line commentary
for product in filing.product_lines:
    print(f"\n{product.name}: {product.outlook}")
    if product.management_commentary:
        print(f"  \"{product.management_commentary[:150]}...\"")

# Check management guidance
if filing.management_guidance:
    print(f"\nOutlook: {filing.management_guidance.sentiment}")
    print(f"Growth drivers: {', '.join(filing.management_guidance.growth_drivers)}")
    print(f"Headwinds: {', '.join(filing.management_guidance.headwinds)}")
```

### Comparing Filings Over Time

```python
# Get multiple years
filings = await sec.get_filings(
    "AAPL",
    Forms.FORM_10K,
    years=[2022, 2023, 2024],
    enrich=True
)

# Track risk evolution
for filing in filings:
    new_risks = [r for r in filing.risk_factors if r.is_new]
    print(f"{filing.identity.period_of_report.year}: {len(new_risks)} new risks")
    for risk in new_risks[:2]:
        print(f"  - {risk.title}")

# Track supplier changes
suppliers_by_year = {
    f.identity.period_of_report.year: set(f.suppliers)
    for f in filings
}
# ... analyze changes
```

---

## Next Steps

See:
- [02_ENRICHER_PIPELINE.md](02_ENRICHER_PIPELINE.md) - How to extract all this data
- [03_STORAGE_AND_SEARCH.md](03_STORAGE_AND_SEARCH.md) - How to store and query
- [04_KNOWLEDGE_GRAPH.md](04_KNOWLEDGE_GRAPH.md) - Cross-filing relationships
- [05_LLM_INTEGRATION.md](05_LLM_INTEGRATION.md) - AI-powered analysis
