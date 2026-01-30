# V4 Data Model Reference

**Purpose**: Canonical reference for all data models across EntitySpine, FeedSpine, and py-sec-edgar.

---

## 1. Entity Models (EntitySpine)

### 1.1 Core Entity

```python
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Optional
import uuid


class EntityType(Enum):
    """Type of entity."""
    PUBLIC_COMPANY = "public_company"    # SEC filer
    PRIVATE_COMPANY = "private_company"  # Subsidiary, supplier
    INDIVIDUAL = "individual"            # Executive, director
    GOVERNMENT = "government"            # Regulator
    OTHER = "other"


@dataclass
class Entity:
    """Core entity with stable identity.

    Entities represent real-world objects that persist across time.
    The entity_id is stable; all changes create new EntityVersions.
    """
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: EntityType = EntityType.PUBLIC_COMPANY

    # Core identity (immutable after creation)
    source_system: str = ""       # "sec", "gleif", "user"
    source_id: str = ""           # CIK, LEI, user-defined

    # Current state (see EntityVersion for point-in-time)
    primary_name: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 1.2 Entity Version (Temporal)

```python
@dataclass
class EntityVersion:
    """Point-in-time snapshot of an entity.

    Implements bitemporal modeling:
    - valid_from/valid_to: When this data was true in the real world
    - recorded_at: When we learned about it
    """
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""

    # Temporal bounds
    valid_from: datetime = field(default_factory=datetime.now)
    valid_to: Optional[datetime] = None  # None = current
    recorded_at: datetime = field(default_factory=datetime.now)

    # State at this point in time
    name: str = ""
    legal_name: Optional[str] = None
    entity_type: EntityType = EntityType.PUBLIC_COMPANY

    # Identifiers active at this time
    identifiers: List["IdentifierClaim"] = field(default_factory=list)

    # Relationships active at this time
    relationships: List["EntityRelationship"] = field(default_factory=list)

    # Lineage
    source_sightings: List[str] = field(default_factory=list)
    source_filings: List["FilingReference"] = field(default_factory=list)

    # Change tracking
    change_reason: Optional[str] = None
    changed_by: str = "system"

    @property
    def is_current(self) -> bool:
        return self.valid_to is None
```

### 1.3 Identifier Claims

```python
class IdentifierScheme(Enum):
    """Identifier type/scheme."""
    CIK = "cik"           # SEC Central Index Key
    TICKER = "ticker"     # Stock ticker
    CUSIP = "cusip"       # CUSIP
    ISIN = "isin"         # ISIN
    LEI = "lei"           # Legal Entity Identifier
    FIGI = "figi"         # Bloomberg FIGI
    EIN = "ein"           # Employer ID Number
    INTERNAL = "internal" # System-generated


class ClaimStatus(Enum):
    """Status of identifier claim."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


@dataclass
class IdentifierClaim:
    """An identifier claim with temporal validity.

    Identifiers can change over time (ticker changes, CUSIP changes).
    Claims track when an identifier was valid.
    """
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""

    # The identifier
    scheme: IdentifierScheme = IdentifierScheme.TICKER
    value: str = ""

    # Temporal validity
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None  # None = still valid

    # Claim metadata
    status: ClaimStatus = ClaimStatus.ACTIVE
    source: str = ""           # "sec_company_tickers", "user", etc.
    confidence: float = 1.0    # 0.0 - 1.0

    # Additional context
    exchange: Optional[str] = None  # For tickers
    country: Optional[str] = None   # For ISINs
```

### 1.4 Entity Relationships

```python
class RelationshipType(Enum):
    """Type of entity relationship."""
    SUBSIDIARY_OF = "subsidiary_of"
    PARENT_OF = "parent_of"
    SUPPLIER_TO = "supplier_to"
    CUSTOMER_OF = "customer_of"
    COMPETITOR_OF = "competitor_of"
    EXECUTIVE_OF = "executive_of"
    DIRECTOR_OF = "director_of"
    AUDITOR_OF = "auditor_of"
    ACQUIRED = "acquired"
    MERGED_WITH = "merged_with"


@dataclass
class EntityRelationship:
    """Relationship between two entities with temporal bounds."""
    relationship_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # The entities
    source_entity_id: str = ""
    target_entity_id: str = ""
    relationship_type: RelationshipType = RelationshipType.SUBSIDIARY_OF

    # Temporal validity
    valid_from: date = field(default_factory=date.today)
    valid_to: Optional[date] = None

    # Evidence
    source_filings: List["FilingReference"] = field(default_factory=list)
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_seen_at: datetime = field(default_factory=datetime.now)

    # Extracted details
    jurisdiction: Optional[str] = None      # For subsidiaries
    ownership_pct: Optional[float] = None   # If disclosed
    is_significant: bool = False            # SEC significance test
```

---

## 2. Filing Models (FeedSpine + py-sec-edgar)

### 2.1 Filing Sighting (Bronze Layer)

```python
@dataclass
class FilingSighting:
    """Raw filing observation from a data source.

    This is the Bronze layer - raw sightings with full lineage.
    Multiple sightings can exist for the same filing (from different sources).
    """
    sighting_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Filing identity
    accession_number: str = ""
    cik: str = ""
    form_type: str = ""

    # Filing dates
    filing_date: Optional[date] = None
    acceptance_datetime: Optional[datetime] = None
    report_date: Optional[date] = None

    # Source tracking (critical for lineage)
    source: str = ""              # "feed:rss", "feed:daily-index", "api:submissions"
    source_url: str = ""
    source_updated_at: Optional[datetime] = None
    seen_at: datetime = field(default_factory=datetime.now)

    # Deduplication
    content_hash: str = ""        # Hash of key fields for dedup

    # Processing state
    processed: bool = False
    entity_id: Optional[str] = None   # Resolved entity (after processing)

    # Raw payload (source-specific fields)
    raw_payload: dict = field(default_factory=dict)
```

### 2.2 Filing (Silver Layer)

```python
@dataclass
class Filing:
    """Resolved filing with canonical identity.

    Silver layer - deduplicated, validated, linked to entity.
    """
    filing_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    accession_number: str = ""

    # Entity link
    cik: str = ""
    entity_id: str = ""           # Canonical entity from EntitySpine
    company_name: str = ""

    # Form metadata
    form_type: str = ""
    filing_date: date = field(default_factory=date.today)
    acceptance_datetime: Optional[datetime] = None
    report_date: Optional[date] = None

    # Document info
    primary_document: str = ""
    primary_document_url: str = ""
    file_number: Optional[str] = None

    # XBRL flags
    is_xbrl: bool = False
    is_inline_xbrl: bool = False

    # Processing state
    sections_extracted: bool = False
    exhibits_indexed: bool = False
    sigdevs_detected: bool = False

    # Lineage
    source_sightings: List[str] = field(default_factory=list)
    first_seen_at: datetime = field(default_factory=datetime.now)
    last_updated_at: datetime = field(default_factory=datetime.now)
```

### 2.3 Filing Reference (For Lineage)

```python
@dataclass
class FilingReference:
    """Lightweight reference to a filing for lineage tracking."""
    cik: str = ""
    accession_number: str = ""
    form_type: str = ""
    filing_date: date = field(default_factory=date.today)
    report_date: Optional[date] = None

    # Optional: specific document/exhibit
    exhibit_type: Optional[str] = None    # "EX-21.01", etc.
    document_url: Optional[str] = None

    def to_url(self) -> str:
        """Generate SEC EDGAR URL."""
        cik_clean = self.cik.lstrip("0") or "0"
        acc_clean = self.accession_number.replace("-", "")
        return f"https://www.sec.gov/Archives/edgar/data/{cik_clean}/{acc_clean}/"
```

---

## 3. Subsidiary Models (py-sec-edgar)

### 3.1 Subsidiary Info (Parsed)

```python
@dataclass
class SubsidiaryInfo:
    """Subsidiary extracted from Exhibit 21."""
    name: str = ""
    jurisdiction: Optional[str] = None

    # Normalized for matching
    name_normalized: str = ""
    jurisdiction_normalized: Optional[str] = None

    # Entity resolution
    entity_id: Optional[str] = None   # Resolved EntitySpine ID
    is_public: bool = False           # Matched to SEC filer

    # Source
    source_filing: Optional[FilingReference] = None
    extracted_at: datetime = field(default_factory=datetime.now)
```

### 3.2 Corporate Hierarchy

```python
@dataclass
class CorporateHierarchy:
    """Full corporate structure at a point in time."""
    root_entity_id: str = ""
    as_of_date: date = field(default_factory=date.today)
    source_filing: Optional[FilingReference] = None

    # The hierarchy
    subsidiaries: List[EntityRelationship] = field(default_factory=list)

    # Computed metrics
    total_count: int = 0
    by_jurisdiction: dict = field(default_factory=dict)
    public_count: int = 0
    private_count: int = 0

    def to_tree(self) -> str:
        """Render as ASCII tree."""
        # Implementation in py-sec-edgar
        pass
```

### 3.3 Subsidiary Changes

```python
class SubsidiaryChangeType(Enum):
    """Type of subsidiary change."""
    ADDED = "added"
    REMOVED = "removed"
    RENAMED = "renamed"
    REDOMICILED = "redomiciled"


@dataclass
class SubsidiaryChange:
    """Change in subsidiary status between filings."""
    change_type: SubsidiaryChangeType
    subsidiary_name: str
    jurisdiction: Optional[str] = None

    # For renamed
    old_name: Optional[str] = None
    new_name: Optional[str] = None

    # For redomiciled
    old_jurisdiction: Optional[str] = None
    new_jurisdiction: Optional[str] = None

    # Source
    from_filing: Optional[FilingReference] = None
    to_filing: Optional[FilingReference] = None

    # Matching confidence
    match_confidence: float = 1.0


@dataclass
class SubsidiaryChanges:
    """All changes between two points in time."""
    from_date: date
    to_date: date
    from_filing: Optional[FilingReference] = None
    to_filing: Optional[FilingReference] = None

    added: List[SubsidiaryChange] = field(default_factory=list)
    removed: List[SubsidiaryChange] = field(default_factory=list)
    renamed: List[SubsidiaryChange] = field(default_factory=list)
    redomiciled: List[SubsidiaryChange] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.renamed) + len(self.redomiciled)
```

---

## 4. Company Model (py-sec-edgar)

### 4.1 Company

```python
@dataclass
class Company:
    """Rich company object for company-centric workflows.

    Combines data from:
    - EntitySpine (identity, relationships)
    - FeedSpine (filing sightings)
    - QueryService (on-demand data)
    """
    # Core identity
    cik: str = ""
    ticker: Optional[str] = None
    name: str = ""
    entity_id: str = ""           # EntitySpine canonical ID

    # Metadata (from SEC)
    sic: Optional[str] = None
    sic_description: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None

    # Computed
    exchange: Optional[str] = None

    # Internal references (not serialized)
    _sec: Optional["SEC"] = field(default=None, repr=False)
    _filings_cache: Optional[List["Filing"]] = field(default=None, repr=False)

    async def filings(
        self,
        form_types: List[str] = None,
        years: int = 5,
    ) -> List["Filing"]:
        """Get company's filings."""
        # Implementation uses FeedSpine bronze layer + QueryService
        pass

    async def subsidiaries(
        self,
        as_of: date = None,
    ) -> "CorporateHierarchy":
        """Get corporate hierarchy from Exhibit 21."""
        pass

    async def latest_10k(self) -> Optional["Filing"]:
        """Get most recent 10-K filing."""
        filings = await self.filings(form_types=["10-K"], years=1)
        return filings[0] if filings else None
```

---

## 5. Query/API Models (py-sec-edgar)

### 5.1 Company Submissions (from SEC API)

```python
@dataclass
class CompanySubmissions:
    """Company submission history from data.sec.gov/submissions.

    Returned by QueryService.submissions.get()
    """
    cik: str = ""
    name: str = ""
    sic: Optional[str] = None
    sic_description: Optional[str] = None
    tickers: List[str] = field(default_factory=list)
    exchanges: List[str] = field(default_factory=list)
    ein: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None

    # Filing history
    filings: List["FilingInfo"] = field(default_factory=list)

    # Metadata
    fetched_at: datetime = field(default_factory=datetime.now)

    def filter_by_form(self, forms: List[str]) -> List["FilingInfo"]:
        """Filter filings by form type."""
        forms_upper = {f.upper() for f in forms}
        return [f for f in self.filings if f.get("form", "").upper() in forms_upper]
```

### 5.2 Search Results (from EFTS API)

```python
@dataclass
class SearchResults:
    """Full-text search results from EFTS API.

    Returned by QueryService.search.search()
    """
    query: str = ""
    total_hits: int = 0
    hits: List["SearchHit"] = field(default_factory=list)
    aggregations: dict = field(default_factory=dict)
    took_ms: int = 0

    def by_form(self) -> dict:
        """Get counts by form type."""
        return self.aggregations.get("form_filter", {})
```

---

## 6. Storage Schemas

### 6.1 SQLite Schema (Development)

```sql
-- Entities
CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    source_system TEXT NOT NULL,
    source_id TEXT NOT NULL,
    primary_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_system, source_id)
);

-- Entity versions (temporal)
CREATE TABLE entity_versions (
    version_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    name TEXT NOT NULL,
    legal_name TEXT,
    entity_type TEXT NOT NULL,
    change_reason TEXT,
    changed_by TEXT DEFAULT 'system'
);

CREATE INDEX idx_entity_versions_current
    ON entity_versions(entity_id) WHERE valid_to IS NULL;

-- Identifier claims
CREATE TABLE identifier_claims (
    claim_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    scheme TEXT NOT NULL,
    value TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    status TEXT DEFAULT 'active',
    source TEXT,
    confidence REAL DEFAULT 1.0,
    exchange TEXT,
    country TEXT
);

CREATE INDEX idx_claims_lookup ON identifier_claims(scheme, value);

-- Entity relationships
CREATE TABLE entity_relationships (
    relationship_id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    target_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    relationship_type TEXT NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    jurisdiction TEXT,
    ownership_pct REAL,
    is_significant BOOLEAN DEFAULT FALSE,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_relationships_parent
    ON entity_relationships(source_entity_id, relationship_type);

-- Filing sightings (Bronze)
CREATE TABLE filing_sightings (
    sighting_id TEXT PRIMARY KEY,
    accession_number TEXT NOT NULL,
    cik TEXT NOT NULL,
    form_type TEXT NOT NULL,
    filing_date DATE,
    source TEXT NOT NULL,
    source_url TEXT,
    source_updated_at TIMESTAMP,
    seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_hash TEXT,
    processed BOOLEAN DEFAULT FALSE,
    entity_id TEXT REFERENCES entities(entity_id),
    raw_payload JSON
);

CREATE INDEX idx_sightings_accession ON filing_sightings(accession_number);
CREATE INDEX idx_sightings_cik ON filing_sightings(cik, filing_date DESC);

-- Filings (Silver)
CREATE TABLE filings (
    filing_id TEXT PRIMARY KEY,
    accession_number TEXT UNIQUE NOT NULL,
    cik TEXT NOT NULL,
    entity_id TEXT REFERENCES entities(entity_id),
    company_name TEXT NOT NULL,
    form_type TEXT NOT NULL,
    filing_date DATE NOT NULL,
    acceptance_datetime TIMESTAMP,
    report_date DATE,
    primary_document TEXT,
    is_xbrl BOOLEAN DEFAULT FALSE,
    is_inline_xbrl BOOLEAN DEFAULT FALSE,
    sections_extracted BOOLEAN DEFAULT FALSE,
    exhibits_indexed BOOLEAN DEFAULT FALSE,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_filings_cik ON filings(cik, filing_date DESC);
CREATE INDEX idx_filings_form ON filings(form_type, filing_date DESC);
```

### 6.2 DuckDB Schema (Analytics)

```sql
-- Same schema as SQLite, optimized for analytics
-- DuckDB auto-optimizes for columnar storage

-- Additional analytics views
CREATE VIEW v_filings_by_month AS
SELECT
    date_trunc('month', filing_date) as month,
    form_type,
    COUNT(*) as filing_count
FROM filings
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

CREATE VIEW v_subsidiary_changes AS
SELECT
    e.primary_name as parent_name,
    er.relationship_type,
    te.primary_name as subsidiary_name,
    er.jurisdiction,
    er.valid_from,
    er.valid_to
FROM entity_relationships er
JOIN entities e ON er.source_entity_id = e.entity_id
JOIN entities te ON er.target_entity_id = te.entity_id
WHERE er.relationship_type = 'subsidiary_of'
ORDER BY e.primary_name, er.valid_from DESC;
```

---

## 7. Type Definitions Summary

| Type | Package | Purpose |
|------|---------|---------|
| `Entity` | EntitySpine | Core identity |
| `EntityVersion` | EntitySpine | Point-in-time state |
| `IdentifierClaim` | EntitySpine | Temporal identifiers |
| `EntityRelationship` | EntitySpine | Entity connections |
| `FilingSighting` | FeedSpine | Raw filing observation (Bronze) |
| `Filing` | py-sec-edgar | Resolved filing (Silver) |
| `FilingReference` | py-sec-edgar | Lightweight reference for lineage |
| `SubsidiaryInfo` | py-sec-edgar | Parsed Exhibit 21 data |
| `CorporateHierarchy` | py-sec-edgar | Full subsidiary tree |
| `Company` | py-sec-edgar | Rich company object |
| `CompanySubmissions` | py-sec-edgar | SEC API response |
| `SearchResults` | py-sec-edgar | EFTS API response |

---

## Related Documents

- [14_V4_MASTER_ROADMAP.md](14_V4_MASTER_ROADMAP.md) - Implementation roadmap
- [10_ENTITYSPINE_UNIVERSAL_FABRIC.md](10_ENTITYSPINE_UNIVERSAL_FABRIC.md) - EntitySpine architecture
- [13_COMPANY_CENTRIC_API.md](13_COMPANY_CENTRIC_API.md) - Company API design
