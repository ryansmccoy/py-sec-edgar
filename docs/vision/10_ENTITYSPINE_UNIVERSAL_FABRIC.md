# EntitySpine: Universal Entity Fabric

**Purpose**: EntitySpine evolves from simple ticker resolution to a **Universal Entity Fabric** - the backbone that manages ALL entities extracted from SEC filings with full lineage, enrichment, and knowledge graph integration.

> **Updated 2026-01-27**:
> - See [14_V4_MASTER_ROADMAP.md](14_V4_MASTER_ROADMAP.md) for implementation status
> - See [15_DATA_MODEL_REFERENCE.md](15_DATA_MODEL_REFERENCE.md) for canonical data models (Entity, EntityVersion, IdentifierClaim, EntityRelationship)
> - EntitySpine now integrates with QueryService for SEC API access

---

## Vision

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ENTITYSPINE UNIVERSAL FABRIC                             │
│                                                                                  │
│     "Feed any entity data in. EntitySpine manages, links, and serves it out."   │
└─────────────────────────────────────────────────────────────────────────────────┘

                    INGEST                    MANAGE                     SERVE
               ──────────────            ──────────────             ──────────────

  SEC Filings ─────┐                 ┌─────────────────┐
  10-K Headers ────┤                 │                 │          → API Queries
  ISIN Lists ──────┤                 │   ENTITYSPINE   │          → Knowledge Graph
  Exchange Data ───┼────────────────▶│     FABRIC      │─────────▶→ Enriched Filings
  Bulk CSV/JSON ───┤                 │                 │          → Relationship Maps
  OpenFIGI ────────┤                 │  ┌───────────┐  │          → Temporal Queries
  GLEIF (LEI) ─────┘                 │  │ Lineage   │  │          → Change Detection
                                     │  │ Tracking  │  │
                                     │  └───────────┘  │
                                     └─────────────────┘
```

---

## Core Concept: Everything Is an Entity

EntitySpine doesn't just manage **tickers** - it manages **everything** that can be extracted from SEC filings:

| Entity Type | Examples | Source Sections |
|-------------|----------|-----------------|
| **Companies** | Apple, TSMC, Foxconn | Everywhere |
| **Securities** | AAPL, US0378331005 | Cover page, Exhibits |
| **People** | Tim Cook, Deirdre O'Brien | Item 10, DEF 14A |
| **Subsidiaries** | Apple Sales Ireland | Exhibit 21 |
| **Suppliers** | TSMC, Samsung | Item 1, Item 1A, Item 7 |
| **Customers** | Best Buy, Verizon | Item 1, Item 7 |
| **Competitors** | Samsung, Google | Item 1, Item 1A |
| **Products** | iPhone, Mac, iPad | Item 1, Item 7 |
| **Contracts** | Manufacturing agreements | Item 1, Exhibits |
| **Litigation** | Epic Games v. Apple | Item 3, Item 8 |
| **Auditors** | Ernst & Young | Item 9, Signatures |
| **Regulators** | FTC, DOJ, EU Commission | Item 1A, Item 3 |
| **Locations** | Cupertino, Shanghai | Item 2, Exhibit 21 |
| **Risks** | Supply chain concentration | Item 1A |

---

## Architecture: The Entity Fabric

### Layer 1: Ingestion Adapters

```python
from abc import ABC, abstractmethod
from typing import Iterator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IngestionSource:
    """Metadata about where data came from."""
    source_type: str           # "sec_filing", "csv_import", "openfigi", etc.
    source_id: str             # accession_number, file_path, api_call_id
    source_name: str           # Human-readable name
    ingested_at: datetime
    batch_id: str | None = None


class IngestionAdapter(ABC):
    """Protocol for all data ingestion sources."""

    @abstractmethod
    def ingest(self) -> Iterator["EntityRecord"]:
        """Yield entity records from source."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Type identifier for this source."""
        ...


# =============================================================================
# ADAPTER: SEC Filing Headers (10-K, 10-Q, 8-K)
# =============================================================================

class SECFilingHeaderAdapter(IngestionAdapter):
    """
    Extract entity data from SEC filing headers.

    The filing header contains rich structured data:
    - Company name, CIK, ticker
    - SIC code (industry classification)
    - State of incorporation
    - Fiscal year end
    - Business address, mailing address
    - Former names (with dates!)
    """
    source_type = "sec_filing_header"

    def __init__(
        self,
        filing_path: str | None = None,
        accession_number: str | None = None,
        download_if_needed: bool = True,
    ):
        self.filing_path = filing_path
        self.accession_number = accession_number
        self.download_if_needed = download_if_needed

    def ingest(self) -> Iterator["EntityRecord"]:
        """Parse filing header and yield entity records."""
        header = self._parse_header()

        # Main company entity
        yield EntityRecord(
            entity_type="company",
            primary_name=header.company_name,
            identifiers={
                "cik": header.cik,
                "ticker": header.ticker,
                "sic_code": header.sic_code,
                "ein": header.irs_number,
            },
            attributes={
                "state_of_incorporation": header.state,
                "fiscal_year_end": header.fiscal_year_end,
                "sic_description": header.sic_description,
            },
            addresses=[
                {"type": "business", **header.business_address},
                {"type": "mailing", **header.mailing_address},
            ],
            source=IngestionSource(
                source_type=self.source_type,
                source_id=header.accession_number,
                source_name=f"{header.form_type} for {header.company_name}",
                ingested_at=datetime.utcnow(),
            ),
        )

        # Former names (temporal entity history!)
        for former_name in header.former_names:
            yield EntityRecord(
                entity_type="former_name",
                primary_name=former_name.name,
                parent_entity_cik=header.cik,
                temporal={
                    "valid_from": former_name.date_of_change,
                    "valid_to": None,  # Until next change
                },
                source=IngestionSource(
                    source_type=self.source_type,
                    source_id=header.accession_number,
                    source_name=f"Former name from {header.form_type}",
                    ingested_at=datetime.utcnow(),
                ),
            )


# =============================================================================
# ADAPTER: Bulk File Import (CSV, JSON, Excel)
# =============================================================================

class BulkFileAdapter(IngestionAdapter):
    """
    Import entities from bulk files.

    Supports:
    - CSV/TSV with headers
    - JSON arrays
    - Excel spreadsheets
    - Parquet files

    User maps columns to entity fields via config.
    """
    source_type = "bulk_file"

    def __init__(
        self,
        file_path: str,
        mapping: "ColumnMapping",
        file_format: str = "auto",
    ):
        self.file_path = file_path
        self.mapping = mapping
        self.file_format = file_format

    def ingest(self) -> Iterator["EntityRecord"]:
        """Read file and yield entity records."""
        df = self._read_file()

        for idx, row in df.iterrows():
            yield EntityRecord(
                entity_type=self.mapping.entity_type,
                primary_name=row[self.mapping.name_column],
                identifiers=self._extract_identifiers(row),
                attributes=self._extract_attributes(row),
                source=IngestionSource(
                    source_type=self.source_type,
                    source_id=f"{self.file_path}:row_{idx}",
                    source_name=f"Row {idx} from {self.file_path}",
                    ingested_at=datetime.utcnow(),
                ),
            )


@dataclass
class ColumnMapping:
    """Map file columns to entity fields."""
    entity_type: str
    name_column: str
    identifier_columns: dict[str, str]  # {"isin": "ISIN", "ticker": "Symbol"}
    attribute_columns: dict[str, str]   # {"industry": "Industry", "country": "Country"}

    # Examples:
    # - Bloomberg terminal export: {"isin": "ID_ISIN", "ticker": "TICKER", ...}
    # - Exchange member list: {"mic": "MIC", "ticker": "Symbol", ...}
    # - Refinitiv export: {"ric": "RIC", "isin": "ISIN", ...}


# =============================================================================
# ADAPTER: Multi-Exchange Securities
# =============================================================================

class MultiExchangeAdapter(IngestionAdapter):
    """
    Parse filings for securities traded across multiple exchanges.

    Apple example:
    - AAPL on NASDAQ (primary)
    - AAPL on various exchanges (GER, UK, etc.)
    - Different ISINs per country

    EntitySpine tracks all of these as ONE entity with multiple listings.
    """
    source_type = "multi_exchange"

    def __init__(self, filing_path: str):
        self.filing_path = filing_path

    def ingest(self) -> Iterator["EntityRecord"]:
        """Extract all securities and listings from filing."""
        # Parse Exhibit 21 for foreign subsidiaries
        subsidiaries = self._parse_exhibit_21()

        # Parse cover page for all tickers
        listings = self._parse_cover_listings()

        for listing in listings:
            yield EntityRecord(
                entity_type="listing",
                primary_name=f"{listing.ticker} on {listing.exchange}",
                identifiers={
                    "ticker": listing.ticker,
                    "mic": listing.mic,
                    "isin": listing.isin,
                },
                parent_entity_cik=listing.filer_cik,
                attributes={
                    "exchange_name": listing.exchange_name,
                    "country": listing.country,
                    "currency": listing.currency,
                },
                source=IngestionSource(
                    source_type=self.source_type,
                    source_id=self.filing_path,
                    source_name=f"Listing from {listing.form_type}",
                    ingested_at=datetime.utcnow(),
                ),
            )


# =============================================================================
# ADAPTER: OpenFIGI Enrichment
# =============================================================================

class OpenFIGIAdapter(IngestionAdapter):
    """
    Enrich entities with FIGI identifiers from OpenFIGI API.

    Given: ISIN, CUSIP, or ticker
    Returns: FIGI, composite FIGI, share class FIGI
    """
    source_type = "openfigi"

    async def enrich_batch(
        self,
        identifiers: list[dict],
    ) -> list["EntityRecord"]:
        """Batch lookup FIGIs for identifiers."""
        results = await self._call_openfigi_api(identifiers)

        records = []
        for result in results:
            records.append(EntityRecord(
                entity_type="figi_mapping",
                primary_name=result.name,
                identifiers={
                    "figi": result.figi,
                    "composite_figi": result.composite_figi,
                    "share_class_figi": result.share_class_figi,
                    "isin": result.isin,
                    "ticker": result.ticker,
                    "mic": result.exchCode,
                },
                attributes={
                    "security_type": result.securityType,
                    "market_sector": result.marketSector,
                },
                source=IngestionSource(
                    source_type=self.source_type,
                    source_id=f"openfigi:{result.figi}",
                    source_name=f"OpenFIGI lookup for {result.ticker}",
                    ingested_at=datetime.utcnow(),
                ),
            ))
        return records


# =============================================================================
# ADAPTER: GLEIF (Legal Entity Identifiers)
# =============================================================================

class GLEIFAdapter(IngestionAdapter):
    """
    Fetch LEI data from GLEIF API.

    LEI provides:
    - Legal name (official)
    - Headquarters address
    - Legal address
    - Entity status (active, inactive)
    - Parent/child relationships
    """
    source_type = "gleif"

    async def lookup_lei(self, lei: str) -> "EntityRecord":
        """Lookup entity by LEI."""
        data = await self._call_gleif_api(lei)

        return EntityRecord(
            entity_type="legal_entity",
            primary_name=data.legal_name,
            identifiers={
                "lei": lei,
                "registration_authority_id": data.registration_id,
            },
            attributes={
                "legal_form": data.legal_form,
                "entity_status": data.entity_status,
                "registration_status": data.registration_status,
            },
            addresses=[
                {"type": "legal", **data.legal_address},
                {"type": "headquarters", **data.hq_address},
            ],
            relationships=[
                {
                    "type": "parent",
                    "target_lei": parent.lei,
                    "relationship_type": parent.relationship_type,
                }
                for parent in data.direct_parents
            ],
            source=IngestionSource(
                source_type=self.source_type,
                source_id=f"gleif:{lei}",
                source_name=f"GLEIF lookup for {lei}",
                ingested_at=datetime.utcnow(),
            ),
        )
```

---

## Layer 2: Entity Record with Full Lineage

```python
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any


@dataclass
class EntityRecord:
    """
    Universal entity record with full lineage.

    Every piece of data in EntitySpine has:
    1. WHAT it is (entity_type, name, identifiers)
    2. WHERE it came from (source)
    3. WHEN we learned it (temporal)
    4. HOW confident we are (confidence)
    5. HOW it relates to other entities (relationships)
    """
    # Core identity
    entity_type: str
    primary_name: str

    # Identifiers (scheme -> value)
    identifiers: dict[str, str] = field(default_factory=dict)

    # Attributes (flexible key-value)
    attributes: dict[str, Any] = field(default_factory=dict)

    # Addresses (list of address dicts)
    addresses: list[dict] = field(default_factory=list)

    # Relationships to other entities
    relationships: list[dict] = field(default_factory=list)

    # Parent entity (for subsidiaries, listings, etc.)
    parent_entity_cik: str | None = None
    parent_entity_id: str | None = None

    # LINEAGE: Where did this come from?
    source: IngestionSource | None = None

    # TEMPORAL: When was this true?
    temporal: dict | None = None  # {valid_from, valid_to}

    # CONFIDENCE: How sure are we?
    confidence: float = 1.0
    extraction_method: str = "direct"  # direct, ner, llm, pattern

    # INTERNAL: EntitySpine management
    entity_id: str | None = None  # Assigned by EntitySpine
    created_at: datetime | None = None
    updated_at: datetime | None = None
    version: int = 1


@dataclass
class LineageMetadata:
    """
    Full lineage tracking for any piece of data.

    Answers:
    - Who added this? (source)
    - When? (timestamps)
    - From what file/API? (source_id)
    - What version? (version)
    - What changed? (changes)
    """
    # Source tracking
    source_type: str
    source_id: str
    source_name: str

    # Batch tracking
    batch_id: str | None = None
    batch_index: int | None = None

    # Timestamps
    ingested_at: datetime
    processed_at: datetime | None = None
    validated_at: datetime | None = None

    # For SEC filings specifically
    accession_number: str | None = None
    form_type: str | None = None
    filed_date: date | None = None
    section_id: str | None = None

    # Extraction details
    extraction_method: str = "direct"
    model_name: str | None = None
    confidence: float = 1.0

    # Character offsets (for click-through)
    char_start: int | None = None
    char_end: int | None = None
    surrounding_text: str | None = None

    # Change tracking
    version: int = 1
    prior_version_id: str | None = None
    changes: list[dict] = field(default_factory=list)
```

---

## Layer 3: The Entity Fabric Manager

```python
class EntityFabric:
    """
    The Universal Entity Fabric.

    Central service that:
    1. INGESTS from any adapter
    2. DEDUPLICATES using fuzzy matching
    3. LINKS to knowledge graph
    4. TRACKS lineage
    5. SERVES via API
    """

    def __init__(
        self,
        store: "EntityStore",
        graph: "KnowledgeGraph",
        fuzzy_matcher: "FuzzyMatcher",
    ):
        self.store = store
        self.graph = graph
        self.fuzzy = fuzzy_matcher

    # =========================================================================
    # INGESTION
    # =========================================================================

    async def ingest(
        self,
        adapter: IngestionAdapter,
        dedupe: bool = True,
        link_graph: bool = True,
    ) -> "IngestionResult":
        """
        Ingest entities from any adapter.

        Args:
            adapter: Source adapter (SEC, CSV, OpenFIGI, etc.)
            dedupe: Whether to deduplicate against existing entities
            link_graph: Whether to add to knowledge graph

        Returns:
            IngestionResult with stats and any errors
        """
        result = IngestionResult(source_type=adapter.source_type)
        batch_id = generate_ulid()

        for record in adapter.ingest():
            try:
                # 1. Check for duplicates
                if dedupe:
                    existing = await self._find_existing(record)
                    if existing:
                        # Merge new data into existing
                        await self._merge_record(existing, record)
                        result.merged_count += 1
                        continue

                # 2. Create new entity
                entity = await self._create_entity(record, batch_id)
                result.created_count += 1

                # 3. Link to knowledge graph
                if link_graph:
                    await self._link_to_graph(entity, record)

            except Exception as e:
                result.errors.append({"record": record.primary_name, "error": str(e)})

        return result

    async def _find_existing(self, record: EntityRecord) -> "Entity | None":
        """Find existing entity that matches this record."""

        # 1. Try exact identifier match (fastest)
        for scheme, value in record.identifiers.items():
            existing = await self.store.get_by_identifier(scheme, value)
            if existing:
                return existing

        # 2. Try fuzzy name match
        candidates = await self.fuzzy.search(
            record.primary_name,
            entity_type=record.entity_type,
            min_score=0.85,
        )

        if candidates and candidates[0].score > 0.95:
            return candidates[0].entity

        return None

    # =========================================================================
    # ENRICHMENT FROM SEC FILINGS
    # =========================================================================

    async def enrich_from_filing(
        self,
        accession_number: str | None = None,
        ticker: str | None = None,
        cik: str | None = None,
        form_types: list[str] | None = None,
    ) -> "EnrichmentResult":
        """
        Pull entity data from SEC filings to enrich the fabric.

        Examples:
            # Enrich from latest 10-K for Apple
            await fabric.enrich_from_filing(ticker="AAPL", form_types=["10-K"])

            # Enrich from specific filing
            await fabric.enrich_from_filing(accession_number="0000320193-24-000081")
        """
        # Download/fetch filing
        filing = await self._get_filing(accession_number, ticker, cik, form_types)

        result = EnrichmentResult(accession_number=filing.accession_number)

        # Extract from header
        header_adapter = SECFilingHeaderAdapter(filing_path=filing.path)
        for record in header_adapter.ingest():
            await self.ingest_single(record)
            result.header_entities += 1

        # Extract subsidiaries from Exhibit 21
        if filing.has_exhibit_21:
            sub_adapter = SubsidiaryAdapter(filing.exhibit_21_path)
            for record in sub_adapter.ingest():
                await self.ingest_single(record)
                result.subsidiaries += 1

        # Extract people from DEF 14A or Item 10
        if filing.form_type in ["DEF 14A", "10-K"]:
            people_adapter = ExecutiveAdapter(filing.path)
            for record in people_adapter.ingest():
                await self.ingest_single(record)
                result.people += 1

        return result

    async def enrich_sector(
        self,
        sic_code: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        limit: int = 100,
    ) -> "SectorEnrichmentResult":
        """
        Enrich all companies in a sector/industry.

        Examples:
            # Enrich all semiconductor companies
            await fabric.enrich_sector(sic_code="3674")

            # Enrich technology sector
            await fabric.enrich_sector(sector="Technology")
        """
        # Get companies in sector
        companies = await self._get_sector_companies(sic_code, sector, industry, limit)

        result = SectorEnrichmentResult(
            sic_code=sic_code,
            sector=sector,
            company_count=len(companies),
        )

        for company in companies:
            try:
                enrichment = await self.enrich_from_filing(cik=company.cik)
                result.enriched_count += 1
                result.total_entities += enrichment.total_count
            except Exception as e:
                result.errors.append({"cik": company.cik, "error": str(e)})

        return result

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    async def load_ticker_list(
        self,
        file_path: str,
        ticker_column: str = "ticker",
        enrich: bool = True,
    ) -> "BulkLoadResult":
        """
        Load tickers from file and optionally enrich from SEC.

        Typical use case:
            - User has a portfolio CSV with tickers
            - Load into EntitySpine
            - Enrich with SEC data automatically
        """
        mapping = ColumnMapping(
            entity_type="company",
            name_column=ticker_column,
            identifier_columns={"ticker": ticker_column},
            attribute_columns={},
        )

        adapter = BulkFileAdapter(file_path, mapping)
        result = await self.ingest(adapter)

        if enrich:
            for entity in result.created_entities:
                await self.enrich_from_filing(ticker=entity.ticker)

        return result

    async def load_isin_list(
        self,
        file_path: str,
        isin_column: str = "isin",
        enrich_figi: bool = True,
    ) -> "BulkLoadResult":
        """
        Load ISINs from file and enrich with FIGI/LEI.

        Use case:
            - User has institutional holdings report with ISINs
            - Load into EntitySpine
            - Enrich with FIGI for cross-referencing
        """
        mapping = ColumnMapping(
            entity_type="security",
            name_column=isin_column,  # Will be enriched with proper name
            identifier_columns={"isin": isin_column},
            attribute_columns={},
        )

        adapter = BulkFileAdapter(file_path, mapping)
        result = await self.ingest(adapter)

        if enrich_figi:
            figi_adapter = OpenFIGIAdapter()
            identifiers = [{"idType": "ID_ISIN", "idValue": e.isin} for e in result.created_entities]
            figi_records = await figi_adapter.enrich_batch(identifiers)

            for record in figi_records:
                await self.ingest_single(record)

        return result

    # =========================================================================
    # QUERYING
    # =========================================================================

    async def query(
        self,
        entity_type: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        has_recent_filing: bool = False,
        filing_form_type: str | None = None,
        added_after: datetime | None = None,
        source_type: str | None = None,
    ) -> list["Entity"]:
        """
        Query entities with flexible filters.

        Examples:
            # All tech companies that filed 10-K in last 30 days
            companies = await fabric.query(
                entity_type="company",
                sector="Technology",
                has_recent_filing=True,
                filing_form_type="10-K",
            )

            # All entities added from CSV import today
            entities = await fabric.query(
                source_type="bulk_file",
                added_after=datetime.today(),
            )
        """
        return await self.store.query(
            entity_type=entity_type,
            sector=sector,
            industry=industry,
            has_recent_filing=has_recent_filing,
            filing_form_type=filing_form_type,
            added_after=added_after,
            source_type=source_type,
        )

    async def get_filings_by_industry(
        self,
        sic_code: str | None = None,
        industry: str | None = None,
        form_type: str = "10-K",
        days_back: int = 30,
    ) -> list["FilingSummary"]:
        """
        See what companies in an industry are filing.

        Use case: "Show me all 10-K filings from semiconductor companies this month"
        """
        companies = await self.query(entity_type="company", industry=industry)

        filings = []
        for company in companies:
            recent = await self.store.get_recent_filings(
                cik=company.cik,
                form_type=form_type,
                days_back=days_back,
            )
            filings.extend(recent)

        return sorted(filings, key=lambda f: f.filed_date, reverse=True)

    # =========================================================================
    # LINEAGE QUERIES
    # =========================================================================

    async def get_lineage(self, entity_id: str) -> "EntityLineage":
        """
        Get full lineage for an entity.

        Returns:
            - When first seen
            - All sources that contributed data
            - Version history
            - Change log
        """
        return await self.store.get_lineage(entity_id)

    async def get_as_of(
        self,
        entity_id: str,
        as_of: datetime,
    ) -> "Entity | None":
        """
        Point-in-time query: What did we know about this entity at a given time?
        """
        return await self.store.get_entity_as_of(entity_id, as_of)

    async def get_changes(
        self,
        entity_id: str,
        since: datetime | None = None,
    ) -> list["EntityChange"]:
        """
        Get all changes to an entity since a given time.
        """
        return await self.store.get_entity_changes(entity_id, since)
```

---

## Layer 4: Knowledge Graph Integration

Every entity ingested connects to the knowledge graph automatically:

```python
class EntityGraphLinker:
    """Link entities to knowledge graph automatically."""

    async def link_entity(
        self,
        entity: Entity,
        record: EntityRecord,
        graph: KnowledgeGraph,
    ) -> None:
        """Create graph nodes and edges for entity."""

        # 1. Create/update node for this entity
        node = await self._ensure_node(entity, graph)

        # 2. Create edges for relationships in record
        for rel in record.relationships:
            await self._create_edge(
                source=node,
                target_ref=rel["target"],
                relationship_type=rel["type"],
                evidence=self._create_evidence(record),
                graph=graph,
            )

        # 3. Link to parent entity if specified
        if record.parent_entity_id:
            parent_node = await graph.get_node(record.parent_entity_id)
            if parent_node:
                await self._create_edge(
                    source=parent_node,
                    target_ref=node,
                    relationship_type=self._infer_parent_relationship(record),
                    evidence=self._create_evidence(record),
                    graph=graph,
                )

        # 4. Auto-detect relationships from attributes
        if record.entity_type == "company":
            # Link to industry node
            if record.attributes.get("sic_code"):
                industry_node = await self._ensure_industry_node(
                    record.attributes["sic_code"],
                    graph,
                )
                await self._create_edge(
                    source=node,
                    target_ref=industry_node,
                    relationship_type="operates_in",
                    evidence=self._create_evidence(record),
                    graph=graph,
                )
```

---

## Use Cases & Examples

### Use Case 1: Portfolio Enrichment

```python
# User has a portfolio CSV
portfolio_file = "my_portfolio.csv"
# ticker,shares,cost_basis
# AAPL,100,15000
# MSFT,50,18000
# TSMC,200,22000

# Load into EntitySpine and enrich
result = await fabric.load_ticker_list(
    portfolio_file,
    ticker_column="ticker",
    enrich=True,  # Pull latest 10-K data
)

# Now query enriched data
for ticker in ["AAPL", "MSFT", "TSMC"]:
    entity = await fabric.resolve(ticker)
    print(f"\n{entity.primary_name}")
    print(f"  Industry: {entity.sic_description}")
    print(f"  Subsidiaries: {len(entity.subsidiaries)}")
    print(f"  Executives: {len(entity.executives)}")
    print(f"  Last 10-K: {entity.latest_filing.filed_date}")
```

### Use Case 2: Sector Analysis

```python
# Find all semiconductor companies filing 10-Ks
filings = await fabric.get_filings_by_industry(
    sic_code="3674",  # Semiconductors
    form_type="10-K",
    days_back=90,
)

print(f"Found {len(filings)} semiconductor 10-Ks in last 90 days:")
for filing in filings:
    print(f"  {filing.company_name}: {filing.filed_date}")

    # Get extracted suppliers from each
    entity = await fabric.resolve(filing.cik)
    print(f"    Suppliers mentioned: {len(entity.suppliers)}")
```

### Use Case 3: Cross-Exchange Securities

```python
# Track Apple across all exchanges
apple = await fabric.resolve("AAPL")

# Get all listings (all exchanges, all ISINs)
listings = await fabric.get_listings(apple.entity_id)

for listing in listings:
    print(f"  {listing.ticker} on {listing.exchange} ({listing.country})")
    print(f"    ISIN: {listing.isin}")
    print(f"    FIGI: {listing.figi}")
```

### Use Case 4: Lineage Query

```python
# When did we first learn TSMC is an Apple supplier?
relationship = await fabric.graph.get_edge(
    source="apple",
    target="tsmc",
    type="supplier",
)

print(f"First seen: {relationship.first_seen}")
print(f"First filing: {relationship.evidence[0].accession_number}")
print(f"Section: {relationship.evidence[0].section}")
print(f"Original text: {relationship.evidence[0].text_excerpt}")
```

### Use Case 5: Point-in-Time Query

```python
# What did we know about this company 6 months ago?
entity_then = await fabric.get_as_of(
    entity_id="01HQXYZ...",
    as_of=datetime(2025, 7, 27),
)

entity_now = await fabric.resolve("AAPL")

# Compare
changes = await fabric.compare(entity_then, entity_now)
print(f"Changes since July 2025:")
for change in changes:
    print(f"  {change.field}: {change.old_value} → {change.new_value}")
```

---

## Integration with py-sec-edgar Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            PY-SEC-EDGAR ECOSYSTEM                                │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                               py-sec-edgar                                       │
│                          (Main Application Layer)                                │
│  • CLI commands        • Filing download       • API endpoints                  │
│  • Batch processing    • Report generation     • Search interface               │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │                                      │
                    ▼                                      ▼
┌───────────────────────────────┐        ┌───────────────────────────────────────┐
│          FeedSpine            │        │           EntitySpine                  │
│     (Filing Collection)       │        │        (Universal Fabric)              │
│                               │        │                                        │
│  • RSS/Index feeds            │───────▶│  • Entity resolution                   │
│  • Rate limiting              │        │  • Identity management                 │
│  • Deduplication              │        │  • Knowledge graph                     │
│  • Filing metadata            │        │  • Lineage tracking                    │
│                               │        │  • Multi-source ingestion             │
└───────────────────────────────┘        └───────────────────────────────────────┘
         │                                              │
         │         ┌────────────────────────────────────┘
         │         │
         ▼         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Enrichment Pipeline                                   │
│  Section Router → EntityExtractor → RiskClassifier → GraphBuilder              │
│                                                                                  │
│  Uses EntitySpine for:                                                          │
│  • Resolving extracted entity names to canonical entities                       │
│  • Adding new entities discovered in filings                                    │
│  • Building relationships in knowledge graph                                    │
│  • Tracking lineage for all extractions                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Storage Layer (DuckDB)                                │
│                                                                                  │
│  entities    │  securities  │  listings   │  relationships  │  lineage         │
│  filings     │  sections    │  mentions   │  graph_nodes    │  graph_edges     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema Extensions

```sql
-- =============================================================================
-- LINEAGE TRACKING TABLES
-- =============================================================================

-- Every piece of data has lineage
CREATE TABLE data_lineage (
    lineage_id          VARCHAR PRIMARY KEY,

    -- What record this lineage is for
    entity_type         VARCHAR NOT NULL,  -- 'entity', 'relationship', 'claim', etc.
    record_id           VARCHAR NOT NULL,  -- The actual record ID

    -- Source information
    source_type         VARCHAR NOT NULL,  -- 'sec_filing', 'bulk_file', 'openfigi', etc.
    source_id           VARCHAR NOT NULL,  -- accession_number, file_path, api_call_id
    source_name         VARCHAR,

    -- Batch tracking
    batch_id            VARCHAR,
    batch_index         INTEGER,

    -- SEC filing specific
    accession_number    VARCHAR,
    form_type           VARCHAR,
    filed_date          DATE,
    section_id          VARCHAR,

    -- Extraction details
    extraction_method   VARCHAR DEFAULT 'direct',
    model_name          VARCHAR,
    confidence          DECIMAL(3,2) DEFAULT 1.0,

    -- Character offsets for click-through
    char_start          INTEGER,
    char_end            INTEGER,
    surrounding_text    TEXT,

    -- Timestamps
    ingested_at         TIMESTAMPTZ NOT NULL,
    processed_at        TIMESTAMPTZ,
    validated_at        TIMESTAMPTZ,

    -- Versioning
    version             INTEGER DEFAULT 1,
    prior_version_id    VARCHAR,

    INDEX idx_lineage_record (entity_type, record_id),
    INDEX idx_lineage_source (source_type, source_id),
    INDEX idx_lineage_batch (batch_id),
    INDEX idx_lineage_accession (accession_number),
    INDEX idx_lineage_time (ingested_at)
);


-- Change history (append-only audit log)
CREATE TABLE change_log (
    change_id           VARCHAR PRIMARY KEY,
    lineage_id          VARCHAR REFERENCES data_lineage(lineage_id),

    -- What changed
    entity_type         VARCHAR NOT NULL,
    record_id           VARCHAR NOT NULL,
    field_name          VARCHAR NOT NULL,
    old_value           TEXT,
    new_value           TEXT,

    -- Why it changed
    change_reason       VARCHAR,  -- 'new_filing', 'manual_update', 'merge', etc.
    change_source       VARCHAR,  -- source_id that triggered change

    -- When
    changed_at          TIMESTAMPTZ NOT NULL,
    changed_by          VARCHAR,  -- user or 'system'

    INDEX idx_change_record (entity_type, record_id),
    INDEX idx_change_time (changed_at)
);


-- =============================================================================
-- MULTI-SOURCE ENTITY VIEWS
-- =============================================================================

-- Unified entity view with all identifiers from all sources
CREATE VIEW entity_identifiers AS
SELECT
    e.entity_id,
    e.primary_name,
    c.scheme,
    c.value,
    c.source_system,
    c.confidence,
    l.source_type,
    l.accession_number,
    l.ingested_at
FROM entities e
JOIN identifier_claims c ON e.entity_id = c.entity_id
LEFT JOIN data_lineage l ON c.claim_id = l.record_id AND l.entity_type = 'claim'
ORDER BY e.entity_id, c.scheme;


-- Entity timeline (temporal view)
CREATE VIEW entity_timeline AS
SELECT
    e.entity_id,
    e.primary_name,
    l.source_type,
    l.accession_number,
    l.form_type,
    l.filed_date,
    l.ingested_at,
    l.version,
    'created' as event_type
FROM entities e
JOIN data_lineage l ON e.entity_id = l.record_id AND l.entity_type = 'entity'
UNION ALL
SELECT
    c.entity_id,
    e.primary_name,
    l.source_type,
    l.accession_number,
    l.form_type,
    l.filed_date,
    l.ingested_at,
    l.version,
    'identifier_added' as event_type
FROM identifier_claims c
JOIN entities e ON c.entity_id = e.entity_id
JOIN data_lineage l ON c.claim_id = l.record_id AND l.entity_type = 'claim'
ORDER BY entity_id, ingested_at;
```

---

## What This Enables

### 1. **Self-Enriching System**
Feed in a ticker list → EntitySpine automatically enriches with SEC data, FIGI, LEI, subsidiaries, executives, analyst coverage, ownership data, etc.

### 2. **Full Audit Trail**
Every fact has lineage: "Where did this come from? When did we learn it? How confident are we?"

### 3. **Point-in-Time Queries**
"What did we know about Apple's supply chain on January 1, 2025?"

### 4. **Industry Analysis**
"Show me all semiconductor companies that filed 10-Ks this quarter and their supply chain relationships"

### 5. **Cross-Reference Everything**
Ticker ↔ CIK ↔ ISIN ↔ FIGI ↔ LEI - all linked and searchable

### 6. **Knowledge Graph**
Every entity links to related entities: suppliers, customers, executives, subsidiaries, products, litigation, analysts, holders

### 7. **Change Detection**
"What changed in Apple's supplier list between 2024 and 2025 10-K?"

### 8. **Analyst Coverage Tracking**
"Who covers Apple? What are their ratings and price targets? What did they say in their latest research note?"

### 9. **Ownership Intelligence**
"Who owns Apple? Which funds increased their positions this quarter? What are the insider transactions?"

### 10. **Public Figure & Statement Tracking**
"What has the President said about semiconductors? Track regulatory statements affecting my portfolio."

### 11. **Signal Graph**
Every piece of information is timestamped, entity-linked, and searchable: "Show me all signals for my portfolio today"

### 12. **Morning Brief Generation**
Auto-generate daily digests of all filings, news, research, and statements affecting a portfolio

---

## The Complete Entity Ecosystem

**Vision**: EntitySpine doesn't just track entities - it tracks **everything that matters about entities**: who covers them, who owns them, what people say about them, and how those signals connect.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    THE COMPLETE ENTITY ECOSYSTEM                                 │
│                                                                                  │
│                              ┌─────────────┐                                    │
│                              │   ENTITY    │                                    │
│                              │  (Apple)    │                                    │
│                              └──────┬──────┘                                    │
│                                     │                                           │
│         ┌───────────────────────────┼───────────────────────────┐               │
│         │              │            │            │              │               │
│         ▼              ▼            ▼            ▼              ▼               │
│   ┌──────────┐   ┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐          │
│   │ ANALYSTS │   │ OWNERS   │ │ PEOPLE   │ │ EVENTS   │  │ SIGNALS  │          │
│   │          │   │          │ │          │ │          │  │          │          │
│   │ Coverage │   │ 13F      │ │ Execs    │ │ Earnings │  │ News     │          │
│   │ Ratings  │   │ Holdings │ │ Board    │ │ Conf     │  │ Research │          │
│   │ Targets  │   │ Funds    │ │ Politics │ │ Product  │  │ Social   │          │
│   │ Estimates│   │ Insiders │ │ Regulat. │ │ Legal    │  │ Filings  │          │
│   └──────────┘   └──────────┘ └──────────┘ └──────────┘  └──────────┘          │
│                                                                                  │
│   "Who analyzes?"  "Who owns?"  "Who matters?" "What happened?" "What's said?" │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Analyst Coverage & Research

**Use Case**: Track which analysts cover a stock, their ratings, price targets, and earnings estimates - all with timestamps and lineage.

```python
# =============================================================================
# ANALYST ENTITIES & COVERAGE
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum


class Rating(Enum):
    """Standardized analyst ratings."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    OUTPERFORM = "outperform"
    HOLD = "hold"
    NEUTRAL = "neutral"
    UNDERPERFORM = "underperform"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class Analyst:
    """An analyst who covers securities."""
    analyst_id: str
    name: str
    firm: str  # Links to entity_id of the firm
    firm_name: str

    # Coverage
    sectors: list[str] = field(default_factory=list)
    covered_entities: list[str] = field(default_factory=list)  # entity_ids

    # Track record (computed)
    accuracy_score: float | None = None
    avg_return_on_calls: float | None = None


@dataclass
class AnalystCoverage:
    """An analyst's coverage of a specific entity."""
    coverage_id: str
    analyst_id: str
    entity_id: str  # The company being covered

    # Current state
    rating: Rating
    price_target: Decimal | None = None
    target_currency: str = "USD"

    # When this coverage was established/updated
    initiated_at: datetime | None = None
    last_updated: datetime | None = None

    # Source
    source: "IngestionSource" | None = None


@dataclass
class EarningsEstimate:
    """An analyst's earnings estimate for a fiscal period."""
    estimate_id: str
    analyst_id: str
    entity_id: str

    # Period
    fiscal_year: int
    fiscal_quarter: int | None = None  # None = full year

    # Estimates
    eps_estimate: Decimal
    revenue_estimate: Decimal | None = None

    # When this estimate was made
    estimated_at: datetime

    # For tracking estimate revisions
    prior_eps_estimate: Decimal | None = None
    revision_direction: str | None = None  # "up", "down", "unchanged"

    # Source
    source: "IngestionSource" | None = None


@dataclass
class ResearchNote:
    """A research note or report from an analyst."""
    note_id: str
    analyst_id: str
    firm_id: str

    # What entities are discussed
    primary_entity_id: str
    mentioned_entity_ids: list[str] = field(default_factory=list)

    # Content
    title: str
    summary: str | None = None
    full_text: str | None = None

    # Ratings/targets in this note
    rating: Rating | None = None
    price_target: Decimal | None = None

    # Metadata
    published_at: datetime
    page_count: int | None = None

    # Extracted entities (via NER)
    extracted_entities: list[dict] = field(default_factory=list)

    # Source
    source: "IngestionSource" | None = None


# =============================================================================
# CONSENSUS ESTIMATES (Aggregated from multiple analysts)
# =============================================================================

@dataclass
class ConsensusEstimate:
    """Aggregated estimates from all covering analysts."""
    entity_id: str
    fiscal_year: int
    fiscal_quarter: int | None = None

    # Consensus EPS
    eps_mean: Decimal
    eps_median: Decimal
    eps_high: Decimal
    eps_low: Decimal
    eps_std_dev: Decimal

    # Consensus Revenue
    revenue_mean: Decimal | None = None
    revenue_median: Decimal | None = None

    # Coverage stats
    analyst_count: int
    estimates_updated_count: int  # How many revised in last 30 days

    # Trend
    estimate_trend: str  # "rising", "falling", "stable"
    revisions_up: int
    revisions_down: int

    # Timestamp
    computed_at: datetime


# =============================================================================
# EXAMPLE: Ingest Analyst Research
# =============================================================================

async def ingest_analyst_research_note(
    fabric: "EntityFabric",
    note_data: dict,
) -> ResearchNote:
    """
    Ingest a research note, extracting and linking all entities.

    Example input:
        {
            "analyst": "Katy Huberty",
            "firm": "Morgan Stanley",
            "title": "Apple iPhone Demand Strong in China",
            "text": "We see continued strength in iPhone 16 demand...",
            "rating": "Overweight",
            "target": 250,
            "published": "2026-01-15T08:00:00Z",
        }
    """
    # 1. Resolve or create analyst entity
    analyst = await fabric.resolve_or_create_analyst(
        name=note_data["analyst"],
        firm=note_data["firm"],
    )

    # 2. Extract entities from note text (via NER/LLM)
    extracted = await fabric.extract_entities_from_text(note_data["text"])
    # Returns: [
    #   {"text": "iPhone 16", "type": "product", "entity_id": "..."},
    #   {"text": "China", "type": "country", "entity_id": "..."},
    #   {"text": "Apple", "type": "company", "entity_id": "..."},
    # ]

    # 3. Create research note with all links
    note = ResearchNote(
        note_id=generate_id(),
        analyst_id=analyst.analyst_id,
        firm_id=analyst.firm,
        primary_entity_id=extracted[0]["entity_id"] if extracted else None,
        mentioned_entity_ids=[e["entity_id"] for e in extracted],
        title=note_data["title"],
        full_text=note_data["text"],
        rating=Rating.BUY,  # Map "Overweight" -> BUY
        price_target=Decimal(str(note_data["target"])),
        published_at=datetime.fromisoformat(note_data["published"]),
        extracted_entities=extracted,
        source=IngestionSource(
            source_type="research_note",
            source_id=f"ms-{note_data['published'][:10]}",
            source_name="Morgan Stanley Research",
            ingested_at=datetime.now(timezone.utc),
        ),
    )

    await fabric.save_research_note(note)
    return note
```

---

## Ownership & Holdings (13F, Funds, Insiders)

**Use Case**: Track who owns the stock - institutional holders from 13F filings, fund positions over time, insider transactions.

```python
# =============================================================================
# OWNERSHIP ENTITIES
# =============================================================================

@dataclass
class InstitutionalHolder:
    """An institutional investor (fund, pension, etc.)."""
    holder_id: str
    name: str
    cik: str | None = None  # SEC CIK if they file 13F
    lei: str | None = None

    # Classification
    holder_type: str  # "hedge_fund", "mutual_fund", "pension", "etf", etc.

    # AUM if known
    aum_usd: Decimal | None = None
    aum_as_of: datetime | None = None

    # Investment style
    style: str | None = None  # "growth", "value", "quantitative", etc.


@dataclass
class Holding:
    """A position held by an institutional investor."""
    holding_id: str
    holder_id: str
    entity_id: str  # The company held

    # Position
    shares: int
    value_usd: Decimal

    # Portfolio weight
    portfolio_pct: Decimal | None = None

    # Period
    report_date: datetime  # Quarter end date
    filed_date: datetime   # When 13F was filed

    # Change from prior period
    shares_change: int | None = None
    shares_change_pct: Decimal | None = None
    change_type: str | None = None  # "new", "increased", "decreased", "sold_out", "unchanged"

    # Source
    source: "IngestionSource" | None = None


@dataclass
class InsiderTransaction:
    """An insider buy/sell transaction (Form 4)."""
    transaction_id: str
    insider_id: str  # Person entity_id
    entity_id: str   # Company entity_id

    # Transaction details
    transaction_type: str  # "buy", "sell", "gift", "exercise"
    shares: int
    price_per_share: Decimal | None = None
    total_value: Decimal | None = None

    # Ownership after transaction
    shares_owned_after: int | None = None
    ownership_type: str  # "direct", "indirect"

    # Dates
    transaction_date: datetime
    filed_date: datetime

    # Relationship to company
    relationship: str  # "CEO", "CFO", "Director", "10% Owner"

    # Source
    source: "IngestionSource" | None = None


@dataclass
class OwnershipHistory:
    """Track how ownership has changed over time."""
    entity_id: str
    holder_id: str

    # Time series of positions
    positions: list[Holding]

    # Computed metrics
    first_owned: datetime
    peak_position_shares: int
    peak_position_date: datetime
    current_position_shares: int

    # Activity
    is_new_position: bool      # First appeared this quarter
    is_increasing: bool        # Added shares this quarter
    is_decreasing: bool        # Reduced shares this quarter
    is_closed: bool            # Sold entire position


# =============================================================================
# EXAMPLE: Ownership Analysis
# =============================================================================

async def analyze_ownership_changes(
    fabric: "EntityFabric",
    entity_id: str,
    quarters_back: int = 4,
) -> dict:
    """
    Analyze how institutional ownership has changed.

    Returns:
        {
            "entity": "Apple Inc.",
            "top_holders": [...],
            "new_positions": [...],
            "increased": [...],
            "decreased": [...],
            "closed": [...],
            "ownership_concentration": 0.45,  # Top 10 own 45%
        }
    """
    holdings = await fabric.get_holdings_history(entity_id, quarters_back)

    # Find changes
    new_positions = [h for h in holdings if h.change_type == "new"]
    increased = [h for h in holdings if h.change_type == "increased"]
    decreased = [h for h in holdings if h.change_type == "decreased"]
    closed = [h for h in holdings if h.change_type == "sold_out"]

    # Notable holders
    notable_new = []
    for h in new_positions:
        holder = await fabric.get_entity(h.holder_id)
        if holder.aum_usd and holder.aum_usd > 10_000_000_000:  # >$10B AUM
            notable_new.append({
                "holder": holder.name,
                "shares": h.shares,
                "value": h.value_usd,
                "holder_type": holder.holder_type,
            })

    return {
        "entity_id": entity_id,
        "new_positions_count": len(new_positions),
        "notable_new_positions": notable_new,
        "increased_count": len(increased),
        "decreased_count": len(decreased),
        "closed_count": len(closed),
    }
```

---

## Public Figures & Statements

**Use Case**: Track what influential people say about industries, companies, or markets - and connect those statements to affected entities.

```python
# =============================================================================
# PUBLIC FIGURE ENTITIES & STATEMENTS
# =============================================================================

class FigureType(Enum):
    """Types of public figures we track."""
    POLITICIAN = "politician"
    REGULATOR = "regulator"
    CENTRAL_BANKER = "central_banker"
    CEO = "ceo"
    INVESTOR = "investor"
    ANALYST = "analyst"
    JOURNALIST = "journalist"
    ACADEMIC = "academic"


@dataclass
class PublicFigure:
    """A public figure whose statements may move markets."""
    figure_id: str
    name: str
    figure_type: FigureType

    # Current role
    title: str | None = None
    organization: str | None = None
    organization_id: str | None = None  # entity_id if we track the org

    # Influence
    influence_score: float | None = None  # 0-100
    follower_count: int | None = None

    # Topics they typically comment on
    topics: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)

    # Examples:
    # - Joe Biden, POLITICIAN, President, US Government
    # - Jerome Powell, CENTRAL_BANKER, Chair, Federal Reserve
    # - Gary Gensler, REGULATOR, Chair, SEC
    # - Warren Buffett, INVESTOR, CEO, Berkshire Hathaway
    # - Cathie Wood, INVESTOR, CEO, ARK Invest


@dataclass
class Statement:
    """A timestamped statement from a public figure."""
    statement_id: str
    figure_id: str

    # Content
    text: str
    summary: str | None = None  # LLM-generated summary

    # Classification
    sentiment: str | None = None  # "positive", "negative", "neutral"
    topics: list[str] = field(default_factory=list)

    # Affected entities (via NER/entity matching)
    mentioned_entity_ids: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)
    affected_countries: list[str] = field(default_factory=list)

    # Timing
    stated_at: datetime
    discovered_at: datetime

    # Source
    source_type: str  # "news_article", "tweet", "speech", "interview", "press_release"
    source_url: str | None = None
    source_title: str | None = None

    # Impact (can be computed/updated later)
    market_impact: dict | None = None  # {"SPY": -0.5%, "INTC": +2.3%}

    # Lineage
    source: "IngestionSource" | None = None


@dataclass
class StatementEntityLink:
    """Link between a statement and an affected entity."""
    link_id: str
    statement_id: str
    entity_id: str

    # How was entity mentioned
    mention_type: str  # "direct", "implied", "sector", "competitor"
    mention_text: str | None = None  # The actual text that mentioned it

    # Sentiment toward this specific entity
    entity_sentiment: str | None = None

    # Relevance (how important is this entity to the statement)
    relevance_score: float  # 0-1


# =============================================================================
# EXAMPLE: Track Presidential Statement About Semiconductors
# =============================================================================

async def ingest_political_statement(
    fabric: "EntityFabric",
    article: dict,
) -> Statement:
    """
    Ingest a news article with political statement, extract and link entities.

    Example input:
        {
            "title": "Biden Announces $50B CHIPS Act Funding",
            "text": "President Biden today announced major investments in
                     domestic semiconductor manufacturing, with Intel, TSMC,
                     and Samsung receiving the largest awards...",
            "published": "2026-01-20T14:30:00Z",
            "url": "https://reuters.com/...",
        }
    """
    # 1. Identify the speaker
    speaker = await fabric.resolve_or_create_figure(
        name="Joe Biden",
        figure_type=FigureType.POLITICIAN,
        title="President",
        organization="US Government",
    )

    # 2. Extract entities from text
    extracted = await fabric.extract_entities_from_text(article["text"])
    # Returns:
    # [
    #   {"text": "Intel", "type": "company", "entity_id": "..."},
    #   {"text": "TSMC", "type": "company", "entity_id": "..."},
    #   {"text": "Samsung", "type": "company", "entity_id": "..."},
    #   {"text": "semiconductor", "type": "sector", "normalized": "Semiconductors"},
    #   {"text": "CHIPS Act", "type": "legislation", "entity_id": "..."},
    # ]

    # 3. Determine sentiment and impact
    analysis = await fabric.analyze_statement(article["text"])
    # Returns: {"sentiment": "positive", "sectors": ["Semiconductors"], ...}

    # 4. Create statement with all links
    statement = Statement(
        statement_id=generate_id(),
        figure_id=speaker.figure_id,
        text=article["text"],
        summary="Biden announces $50B in CHIPS Act funding for Intel, TSMC, Samsung",
        sentiment=analysis["sentiment"],
        topics=["chips_act", "semiconductor_policy", "manufacturing"],
        mentioned_entity_ids=[e["entity_id"] for e in extracted if e.get("entity_id")],
        affected_sectors=["Semiconductors", "Technology"],
        affected_countries=["US", "Taiwan", "South Korea"],
        stated_at=datetime.fromisoformat(article["published"]),
        discovered_at=datetime.now(timezone.utc),
        source_type="news_article",
        source_url=article["url"],
        source_title=article["title"],
        source=IngestionSource(
            source_type="news",
            source_id=article["url"],
            source_name="Reuters",
            ingested_at=datetime.now(timezone.utc),
        ),
    )

    await fabric.save_statement(statement)

    # 5. Create entity links with relevance scores
    for extracted_entity in extracted:
        if extracted_entity.get("entity_id"):
            link = StatementEntityLink(
                link_id=generate_id(),
                statement_id=statement.statement_id,
                entity_id=extracted_entity["entity_id"],
                mention_type="direct" if extracted_entity["text"] in article["text"] else "implied",
                mention_text=extracted_entity["text"],
                entity_sentiment=analysis["sentiment"],
                relevance_score=0.9 if extracted_entity["type"] == "company" else 0.5,
            )
            await fabric.save_statement_link(link)

    return statement


# =============================================================================
# QUERY: What has been said about an entity?
# =============================================================================

async def get_entity_mentions(
    fabric: "EntityFabric",
    entity_id: str,
    since: datetime | None = None,
    figure_types: list[FigureType] | None = None,
) -> list[dict]:
    """
    Get all statements mentioning an entity.

    Example:
        # What have politicians said about Intel recently?
        mentions = await get_entity_mentions(
            fabric,
            entity_id="intel_entity_id",
            since=days_ago(30),
            figure_types=[FigureType.POLITICIAN, FigureType.REGULATOR],
        )
    """
    links = await fabric.get_statement_links(entity_id=entity_id)

    results = []
    for link in links:
        statement = await fabric.get_statement(link.statement_id)
        figure = await fabric.get_figure(statement.figure_id)

        if since and statement.stated_at < since:
            continue
        if figure_types and figure.figure_type not in figure_types:
            continue

        results.append({
            "statement_id": statement.statement_id,
            "figure": figure.name,
            "figure_type": figure.figure_type.value,
            "title": figure.title,
            "summary": statement.summary,
            "sentiment": statement.sentiment,
            "stated_at": statement.stated_at,
            "source": statement.source_url,
            "relevance": link.relevance_score,
        })

    return sorted(results, key=lambda x: x["stated_at"], reverse=True)
```

---

## The Signal Graph: Connecting Everything

**Vision**: Every piece of information becomes a **signal** connected to entities through time.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         THE SIGNAL GRAPH                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                          TIME AXIS →                                     │   │
│   │   ════════════════════════════════════════════════════════════════════  │   │
│   │   Jan 1        Jan 15        Feb 1         Feb 15        Mar 1          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   INTEL (INTC) ─────●────────────●──────────────●───────────────●──────────    │
│                     │            │              │               │              │
│                     │            │              │               │              │
│   Signals:     ┌────┴───┐   ┌────┴───┐    ┌────┴───┐     ┌────┴───┐          │
│                │10-K    │   │Biden   │    │Earnings│     │Analyst │          │
│                │Filed   │   │CHIPS   │    │Call    │     │Upgrade │          │
│                │        │   │Speech  │    │        │     │        │          │
│                └────────┘   └────────┘    └────────┘     └────────┘          │
│                     │            │              │               │              │
│   Extracted:   Suppliers    "Intel"        Revenue         INTC             │
│                Customers    Positive       Guidance         BUY             │
│                Execs        $8.5B          Beat            $45 PT           │
│                Subs                                                          │
│                                                                                  │
│   ──────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   Connected Entities:                                                           │
│                                                                                  │
│   TSMC ─────────────────────●──────────────────────────────────────────────    │
│                             │ (mentioned in Biden speech)                       │
│                                                                                  │
│   Samsung ──────────────────●──────────────────────────────────────────────    │
│                             │ (mentioned in Biden speech)                       │
│                                                                                  │
│   Katy Huberty ─────────────────────────────────────────────●──────────────    │
│   (Morgan Stanley)                                          │ (issued upgrade)  │
│                                                                                  │
│   Biden ────────────────────●──────────────────────────────────────────────    │
│   (President)               │ (made statement)                                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

```python
# =============================================================================
# SIGNAL MODEL: Unifying All Information
# =============================================================================

class SignalType(Enum):
    """Types of signals we track."""
    # Filings
    SEC_FILING = "sec_filing"
    PROXY_FILING = "proxy"
    FORM_4 = "form_4"
    FORM_13F = "form_13f"

    # Research
    ANALYST_RATING = "analyst_rating"
    ANALYST_ESTIMATE = "analyst_estimate"
    RESEARCH_NOTE = "research_note"

    # News & Statements
    NEWS_ARTICLE = "news_article"
    PRESS_RELEASE = "press_release"
    POLITICAL_STATEMENT = "political_statement"
    REGULATORY_ACTION = "regulatory_action"

    # Corporate Events
    EARNINGS_CALL = "earnings_call"
    INVESTOR_DAY = "investor_day"
    PRODUCT_LAUNCH = "product_launch"
    M_AND_A = "m_and_a"

    # Market Data
    PRICE_ALERT = "price_alert"
    VOLUME_SPIKE = "volume_spike"

    # Social
    SOCIAL_MENTION = "social_mention"


@dataclass
class Signal:
    """A timestamped piece of information connected to entities."""
    signal_id: str
    signal_type: SignalType

    # Timing
    timestamp: datetime          # When the signal occurred
    discovered_at: datetime      # When we learned about it

    # Content
    title: str
    summary: str | None = None
    content: dict = field(default_factory=dict)  # Type-specific payload

    # Connected entities
    primary_entity_id: str | None = None
    entity_links: list["SignalEntityLink"] = field(default_factory=list)

    # Classification
    sentiment: str | None = None
    topics: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)

    # Importance
    importance_score: float = 0.5  # 0-1

    # Source lineage
    source: "IngestionSource" | None = None


@dataclass
class SignalEntityLink:
    """Connection between a signal and an entity."""
    entity_id: str
    link_type: str  # "primary", "mentioned", "affected", "source"
    relevance: float = 0.5
    sentiment: str | None = None
    context: str | None = None  # Why this entity is linked


class SignalGraph:
    """
    The unified signal graph connecting all entities through time.

    Enables queries like:
    - "What happened to Apple this week?"
    - "What has Biden said about semiconductors?"
    - "Show me all signals for my portfolio today"
    - "Who mentioned Intel in the last 30 days?"
    """

    def __init__(self, fabric: "EntityFabric"):
        self.fabric = fabric

    async def get_entity_timeline(
        self,
        entity_id: str,
        since: datetime | None = None,
        signal_types: list[SignalType] | None = None,
    ) -> list[Signal]:
        """Get all signals for an entity, sorted by time."""
        ...

    async def get_signals_by_figure(
        self,
        figure_id: str,
        since: datetime | None = None,
    ) -> list[Signal]:
        """Get all signals from a public figure."""
        ...

    async def get_sector_signals(
        self,
        sector: str,
        since: datetime | None = None,
    ) -> list[Signal]:
        """Get all signals affecting a sector."""
        ...

    async def get_portfolio_signals(
        self,
        entity_ids: list[str],
        since: datetime | None = None,
    ) -> list[Signal]:
        """Get all signals for a list of entities (portfolio view)."""
        signals = []
        for entity_id in entity_ids:
            entity_signals = await self.get_entity_timeline(entity_id, since)
            signals.extend(entity_signals)

        # Dedupe and sort
        seen = set()
        unique = []
        for s in sorted(signals, key=lambda x: x.timestamp, reverse=True):
            if s.signal_id not in seen:
                seen.add(s.signal_id)
                unique.append(s)

        return unique

    async def search_signals(
        self,
        query: str,
        since: datetime | None = None,
        limit: int = 50,
    ) -> list[Signal]:
        """Full-text search across all signals."""
        ...


# =============================================================================
# EXAMPLE: Portfolio Morning Brief
# =============================================================================

async def generate_morning_brief(
    fabric: "EntityFabric",
    portfolio_entity_ids: list[str],
) -> str:
    """
    Generate a morning brief of all signals for a portfolio.

    Example output:

    ═══════════════════════════════════════════════════════════════════
    MORNING BRIEF - January 27, 2026
    ═══════════════════════════════════════════════════════════════════

    INTEL (INTC)
    ────────────────────────────────────────────────────────────────────
    📰 [NEWS] Biden Announces $50B CHIPS Act Funding
       Sentiment: Positive | Source: Reuters
       "Intel receiving largest award among domestic manufacturers..."

    📊 [ANALYST] Morgan Stanley Upgrades to Buy
       Analyst: Katy Huberty | Target: $45 (+20%)
       "We see inflection in data center demand..."

    APPLE (AAPL)
    ────────────────────────────────────────────────────────────────────
    📄 [FILING] Form 4: Tim Cook sold 50,000 shares
       Transaction: $11.2M at $224.50
       "Automatic sale under 10b5-1 plan"

    📈 [13F] Berkshire Hathaway reduced position by 5%
       Shares: 905M → 860M | Value: $193B → $183B

    ═══════════════════════════════════════════════════════════════════
    """
    graph = SignalGraph(fabric)

    lines = [
        "═" * 70,
        f"MORNING BRIEF - {datetime.now().strftime('%B %d, %Y')}",
        "═" * 70,
        "",
    ]

    for entity_id in portfolio_entity_ids:
        entity = await fabric.get_entity(entity_id)
        ticker = entity.identifiers.get("ticker", "???")

        signals = await graph.get_entity_timeline(
            entity_id,
            since=datetime.now(timezone.utc) - timedelta(hours=24),
        )

        if signals:
            lines.append(f"{entity.primary_name} ({ticker})")
            lines.append("─" * 70)

            for signal in signals[:5]:  # Top 5 signals
                icon = {
                    SignalType.NEWS_ARTICLE: "📰",
                    SignalType.ANALYST_RATING: "📊",
                    SignalType.SEC_FILING: "📄",
                    SignalType.FORM_13F: "📈",
                    SignalType.POLITICAL_STATEMENT: "🏛️",
                }.get(signal.signal_type, "•")

                lines.append(f"{icon} [{signal.signal_type.value.upper()}] {signal.title}")
                if signal.summary:
                    lines.append(f"   {signal.summary[:60]}...")
                lines.append("")

            lines.append("")

    lines.append("═" * 70)
    return "\n".join(lines)
```

---

## Complete Entity Type Reference

| Category | Entity Type | Sources | Key Identifiers |
|----------|-------------|---------|-----------------|
| **Core** | Company | SEC, GLEIF, D&B | CIK, LEI, DUNS, ticker |
| | Security | SEC, OpenFIGI | ISIN, CUSIP, FIGI, SEDOL |
| | Person | SEC (10-K, DEF 14A) | Name, CRD# |
| **Corporate** | Subsidiary | Exhibit 21 | Name, Jurisdiction |
| | Product | Item 1 | Name, Category |
| | Contract | Exhibits | Parties, Type |
| **Relationships** | Supplier | Item 1, 1A, 7 | Name, Relationship |
| | Customer | Item 1, 7 | Name, Channel |
| | Competitor | Item 1A | Name, Segment |
| **People** | Executive | Item 10, DEF 14A | Name, Title |
| | Director | DEF 14A | Name, Committee |
| | Analyst | Research | Name, Firm |
| | Public Figure | News | Name, Title, Org |
| **Ownership** | Inst. Holder | 13F | CIK, Name |
| | Fund | 13F | Name, Type |
| | Insider | Form 4 | Name, Relationship |
| **Legal** | Litigation | Item 3 | Case, Court |
| | Regulator | Item 1A, 3 | Name, Jurisdiction |
| | Auditor | Signatures | Firm, City |
| **Signals** | Statement | News, Social | Speaker, Time |
| | Research Note | Brokers | Analyst, Date |
| | Filing | SEC | Accession# |
| | Event | Calendar | Type, Date |

---

## Enterprise Feature: Security Master Ingestion

**Use Case**: An investment firm wants to ingest their internal Security Master tables from Bloomberg, Refinitiv, or proprietary databases - and have EntitySpine manage the unified entity history.

### The Problem

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INVESTMENT FIRM DATA CHALLENGE                                │
│                                                                                  │
│  Bloomberg Security Master        Internal Portfolio DB        SEC Filings       │
│  ─────────────────────────       ────────────────────         ─────────────      │
│  ISIN: US0378331005              Ticker: AAPL                 CIK: 0000320193   │
│  FIGI: BBG000B9XRY4              CUSIP: 037833100             Ticker: AAPL      │
│  Ticker: AAPL US                 Our ID: INT-12345            LEI: HWUPK...     │
│                                                                                  │
│                          ▼ ALL REFER TO SAME ENTITY ▼                           │
│                                                                                  │
│  But how do you:                                                                │
│  - Confirm they're the same entity?                                             │
│  - Track when Bloomberg added a new field?                                      │
│  - Know which source to trust for each field?                                   │
│  - Detect when a new ticker gets added to Bloomberg but not your DB?            │
│  - Build a unified view across all sources?                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Solution: Security Master Adapter

```python
# =============================================================================
# ADAPTER: Security Master Database Ingestion
# =============================================================================

from typing import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
import pandas as pd


@dataclass
class SecurityMasterConfig:
    """Configuration for connecting to a Security Master database."""
    connection_string: str
    query: str
    source_name: str

    # Column mappings to EntitySpine fields
    identifier_columns: dict[str, str]  # EntitySpine field -> source column
    attribute_columns: dict[str, str]

    # Example configurations:

    @classmethod
    def bloomberg(cls, conn_str: str) -> "SecurityMasterConfig":
        """Pre-configured for Bloomberg Terminal exports."""
        return cls(
            connection_string=conn_str,
            query="SELECT * FROM security_master WHERE active = 1",
            source_name="bloomberg_terminal",
            identifier_columns={
                "isin": "ID_ISIN",
                "figi": "ID_BB_GLOBAL",
                "cusip": "ID_CUSIP",
                "sedol": "ID_SEDOL1",
                "ticker": "TICKER",
                "exchange": "EXCH_CODE",
            },
            attribute_columns={
                "name": "NAME",
                "country": "CNTRY_OF_RISK",
                "industry": "INDUSTRY_SECTOR",
                "currency": "CRNCY",
                "security_type": "SECURITY_TYP",
            },
        )

    @classmethod
    def refinitiv(cls, conn_str: str) -> "SecurityMasterConfig":
        """Pre-configured for Refinitiv/Reuters exports."""
        return cls(
            connection_string=conn_str,
            query="SELECT * FROM instruments",
            source_name="refinitiv",
            identifier_columns={
                "ric": "RIC",
                "isin": "ISIN",
                "cusip": "CUSIP",
                "sedol": "SEDOL",
                "ticker": "TICKER",
            },
            attribute_columns={
                "name": "LONGNAME",
                "country": "COUNTRY",
                "exchange": "EXCHANGE",
            },
        )

    @classmethod
    def custom(
        cls,
        conn_str: str,
        query: str,
        source_name: str,
        **column_mappings,
    ) -> "SecurityMasterConfig":
        """Custom configuration for proprietary databases."""
        return cls(
            connection_string=conn_str,
            query=query,
            source_name=source_name,
            identifier_columns=column_mappings.get("identifiers", {}),
            attribute_columns=column_mappings.get("attributes", {}),
        )


class SecurityMasterAdapter(IngestionAdapter):
    """
    Ingest securities from investment firm databases.

    Supports:
    - Bloomberg Terminal exports
    - Refinitiv/Reuters feeds
    - Proprietary Security Master databases
    - CSV/Excel exports from trading systems

    Example:
        config = SecurityMasterConfig.bloomberg("postgresql://...")
        adapter = SecurityMasterAdapter(config)

        for entity_record in adapter.ingest():
            fabric.ingest(entity_record)
    """
    source_type = "security_master"

    def __init__(self, config: SecurityMasterConfig):
        self.config = config
        self._batch_id = f"secmaster-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    def ingest(self) -> Iterator["EntityRecord"]:
        """Connect to database and yield entity records."""
        df = self._execute_query()

        for idx, row in df.iterrows():
            # Extract identifiers from mapped columns
            identifiers = {}
            for entity_field, source_col in self.config.identifier_columns.items():
                if source_col in row and pd.notna(row[source_col]):
                    identifiers[entity_field] = str(row[source_col])

            # Extract attributes
            attributes = {}
            for entity_field, source_col in self.config.attribute_columns.items():
                if source_col in row and pd.notna(row[source_col]):
                    attributes[entity_field] = row[source_col]

            # Determine primary name
            primary_name = (
                attributes.get("name")
                or identifiers.get("ticker")
                or f"Unknown-{idx}"
            )

            yield EntityRecord(
                entity_type="security",
                primary_name=primary_name,
                identifiers=identifiers,
                attributes=attributes,
                source=IngestionSource(
                    source_type=self.source_type,
                    source_id=f"{self.config.source_name}:row_{idx}",
                    source_name=f"{self.config.source_name} Security Master",
                    ingested_at=datetime.now(timezone.utc),
                    batch_id=self._batch_id,
                ),
            )

    def _execute_query(self) -> pd.DataFrame:
        """Execute query and return DataFrame."""
        # Implementation handles multiple backends:
        # - PostgreSQL/MySQL via SQLAlchemy
        # - Excel via pandas.read_excel
        # - CSV via pandas.read_csv
        ...


# =============================================================================
# USAGE EXAMPLE: Investment Firm Workflow
# =============================================================================

async def ingest_firm_security_master():
    """
    Example: Investment firm daily security master sync.

    This runs nightly to:
    1. Pull latest data from Bloomberg
    2. Detect new/changed/removed securities
    3. Update EntitySpine with full lineage
    4. Generate change report for operations team
    """
    fabric = EntityFabric(store=SqliteStore("firm_entities.db"))

    # Configure Bloomberg adapter
    bloomberg_config = SecurityMasterConfig.bloomberg(
        conn_str="postgresql://user:pass@bloomberg-proxy/secmaster"
    )

    # Ingest with change detection
    result = await fabric.ingest_with_diff(
        adapter=SecurityMasterAdapter(bloomberg_config),
        diff_key="isin",  # Use ISIN as the unique key for diffing
    )

    # Report changes
    print(f"Security Master Sync Complete:")
    print(f"  New securities:     {result.added_count}")
    print(f"  Modified:           {result.modified_count}")
    print(f"  Removed:            {result.removed_count}")
    print(f"  Unchanged:          {result.unchanged_count}")

    # Alert on significant changes
    if result.added_count > 100:
        alert_ops_team(f"Unusual number of new securities: {result.added_count}")

    if result.removed_count > 0:
        for removed in result.removed:
            print(f"  ⚠️  REMOVED: {removed.primary_name} ({removed.isin})")
```

---

## FeedSpine Integration: Change Detection & History

**Insight**: FeedSpine solves "Have I seen this record before?" while EntitySpine solves "What entity does this identifier belong to?" They're perfect complements.

### Change Detection Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     ENTITYSPINE + FEEDSPINE CHANGE DETECTION                     │
│                                                                                  │
│                                                                                  │
│   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐               │
│   │  Bloomberg  │         │   Refinitiv │         │ SEC Filings │               │
│   │  Security   │         │     Feed    │         │    Feed     │               │
│   │   Master    │         │             │         │             │               │
│   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘               │
│          │                       │                       │                       │
│          ▼                       ▼                       ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                          FEEDSPINE LAYER                                 │   │
│   │                                                                          │   │
│   │   • Sighting tracking (first seen, last seen)                           │   │
│   │   • Deduplication (same record from multiple sources)                   │   │
│   │   • Change detection (SnapshotDiff: added/removed/modified)             │   │
│   │   • Content hashing (detect if data actually changed)                   │   │
│   │                                                                          │   │
│   └───────────────────────────────┬─────────────────────────────────────────┘   │
│                                   │                                             │
│                                   │ NEW/CHANGED records only                    │
│                                   ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         ENTITYSPINE LAYER                                │   │
│   │                                                                          │   │
│   │   • Entity resolution (is this the same entity?)                        │   │
│   │   • Identifier linking (ISIN ↔ CUSIP ↔ CIK ↔ FIGI)                      │   │
│   │   • Lineage tracking (where did this data come from?)                   │   │
│   │   • Confidence scoring (which source to trust?)                         │   │
│   │   • Knowledge graph (relationships between entities)                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The ChangeTracker Service

```python
# =============================================================================
# CHANGE TRACKING: Unified History & Change Detection
# =============================================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator
from enum import Enum


class ChangeType(Enum):
    """Types of entity changes."""
    CREATED = "created"           # New entity added
    IDENTIFIER_ADDED = "id_added" # New identifier for existing entity
    IDENTIFIER_REMOVED = "id_rem" # Identifier removed (rare)
    ATTRIBUTE_CHANGED = "attr"    # Attribute value changed
    RELATIONSHIP_ADDED = "rel_add"
    RELATIONSHIP_REMOVED = "rel_rem"
    MERGED = "merged"             # Two entities merged into one
    DEACTIVATED = "deactivated"   # Entity no longer active


@dataclass
class EntityChange:
    """Record of a single change to an entity."""
    change_id: str
    entity_id: str
    change_type: ChangeType

    # What changed
    field_name: str | None = None
    old_value: str | None = None
    new_value: str | None = None

    # Context
    source: IngestionSource | None = None
    changed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changed_by: str = "system"
    reason: str | None = None


@dataclass
class ChangeReport:
    """Summary of changes from an ingestion run."""
    batch_id: str
    source_name: str
    started_at: datetime
    completed_at: datetime

    # Counts
    new_entities: int = 0
    modified_entities: int = 0
    removed_entities: int = 0
    unchanged_entities: int = 0

    # Details
    changes: list[EntityChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return self.new_entities > 0 or self.modified_entities > 0 or self.removed_entities > 0

    def summary(self) -> str:
        return (
            f"Change Report [{self.source_name}]\n"
            f"  New:       {self.new_entities:,}\n"
            f"  Modified:  {self.modified_entities:,}\n"
            f"  Removed:   {self.removed_entities:,}\n"
            f"  Unchanged: {self.unchanged_entities:,}"
        )


class ChangeTracker:
    """
    Tracks all changes to entities over time.

    Enables:
    - "What changed since last week?"
    - "Show me the history of this entity"
    - "When did we first learn about this ticker?"
    - "What entities were removed from Bloomberg this month?"
    """

    def __init__(self, store: "EntityStore"):
        self.store = store

    # =========================================================================
    # CHANGE DETECTION
    # =========================================================================

    async def compute_diff(
        self,
        current_records: list["EntityRecord"],
        source_name: str,
        key_field: str = "isin",
    ) -> "SnapshotDiff":
        """
        Compare current records against what's stored.

        Args:
            current_records: Records from latest source fetch
            source_name: Name of the source being compared
            key_field: Which identifier to use for matching

        Returns:
            SnapshotDiff with added/removed/modified/unchanged
        """
        diff = SnapshotDiff()

        # Get previous snapshot from this source
        previous = await self.store.get_entities_from_source(source_name)
        previous_by_key = {e.identifiers.get(key_field): e for e in previous}

        # Current by key
        current_by_key = {r.identifiers.get(key_field): r for r in current_records}

        # Find additions
        for key, record in current_by_key.items():
            if key and key not in previous_by_key:
                diff.added[key] = record

        # Find removals
        for key, entity in previous_by_key.items():
            if key and key not in current_by_key:
                diff.removed[key] = entity

        # Find modifications
        for key in set(current_by_key.keys()) & set(previous_by_key.keys()):
            if key:
                current = current_by_key[key]
                previous_entity = previous_by_key[key]
                changes = self._compute_field_changes(previous_entity, current)
                if changes:
                    diff.modified[key] = (previous_entity, current, changes)
                else:
                    diff.unchanged_count += 1

        return diff

    def _compute_field_changes(
        self,
        old: "Entity",
        new: "EntityRecord",
    ) -> list[tuple[str, str, str]]:
        """Compare two records field by field."""
        changes = []

        # Compare identifiers
        all_schemes = set(old.identifiers.keys()) | set(new.identifiers.keys())
        for scheme in all_schemes:
            old_val = old.identifiers.get(scheme)
            new_val = new.identifiers.get(scheme)
            if old_val != new_val:
                changes.append((f"identifier.{scheme}", old_val, new_val))

        # Compare attributes
        all_attrs = set(old.attributes.keys()) | set(new.attributes.keys())
        for attr in all_attrs:
            old_val = old.attributes.get(attr)
            new_val = new.attributes.get(attr)
            if old_val != new_val:
                changes.append((f"attribute.{attr}", old_val, new_val))

        return changes

    # =========================================================================
    # HISTORY QUERIES
    # =========================================================================

    async def changes_since(
        self,
        since: datetime,
        source_name: str | None = None,
        change_type: ChangeType | None = None,
    ) -> Iterator[EntityChange]:
        """
        Get all changes since a date.

        Example:
            # What changed this week?
            for change in tracker.changes_since(days_ago(7)):
                print(f"{change.entity_id}: {change.change_type}")
        """
        ...

    async def entity_history(self, entity_id: str) -> list[EntityChange]:
        """
        Get full history of an entity.

        Example:
            history = await tracker.entity_history("ent_abc123")
            for change in history:
                print(f"{change.changed_at}: {change.field_name} = {change.new_value}")
        """
        ...

    async def first_seen(self, entity_id: str) -> datetime | None:
        """When was this entity first ingested?"""
        ...

    async def last_seen(
        self,
        entity_id: str,
        source_name: str | None = None,
    ) -> datetime | None:
        """When was this entity last seen in a source?"""
        ...

    # =========================================================================
    # SPECIALIZED QUERIES
    # =========================================================================

    async def new_tickers_since(self, since: datetime) -> list[str]:
        """Find tickers that were added since a date."""
        changes = await self.changes_since(
            since=since,
            change_type=ChangeType.CREATED,
        )
        return [
            c.new_value for c in changes
            if c.field_name == "identifier.ticker"
        ]

    async def removed_from_source(
        self,
        source_name: str,
        since: datetime,
    ) -> list["Entity"]:
        """
        Find entities that were in a source but no longer appear.

        Use case: "What securities were removed from Bloomberg this month?"
        """
        ...

    async def ticker_changes(self, since: datetime) -> list[dict]:
        """
        Find entities whose ticker symbol changed.

        Returns list of {entity_id, old_ticker, new_ticker, changed_at}
        """
        changes = await self.changes_since(
            since=since,
            change_type=ChangeType.ATTRIBUTE_CHANGED,
        )
        return [
            {
                "entity_id": c.entity_id,
                "old_ticker": c.old_value,
                "new_ticker": c.new_value,
                "changed_at": c.changed_at,
            }
            for c in changes
            if c.field_name == "identifier.ticker"
        ]


@dataclass
class SnapshotDiff:
    """Difference between two snapshots of entity data."""
    added: dict[str, "EntityRecord"] = field(default_factory=dict)
    removed: dict[str, "Entity"] = field(default_factory=dict)
    modified: dict[str, tuple["Entity", "EntityRecord", list]] = field(default_factory=dict)
    unchanged_count: int = 0

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "modified": len(self.modified),
            "unchanged": self.unchanged_count,
        }
```

### Unified Feed Management

```python
# =============================================================================
# UNIFIED FEED MANAGEMENT
# =============================================================================

@dataclass
class FeedConfig:
    """Configuration for an entity data feed."""
    name: str
    adapter_class: type
    adapter_config: dict

    # Scheduling
    schedule: str = "daily"  # cron expression or preset

    # Change detection
    track_changes: bool = True
    diff_key: str = "isin"

    # Priority for conflict resolution
    priority: int = 50  # Higher = more trusted


class UnifiedFeedManager:
    """
    Manages multiple entity data feeds into a single EntitySpine.

    Example:
        manager = UnifiedFeedManager(fabric)

        # Register feeds
        manager.register_feed(FeedConfig(
            name="bloomberg",
            adapter_class=SecurityMasterAdapter,
            adapter_config=SecurityMasterConfig.bloomberg(...),
            priority=90,  # High trust
        ))

        manager.register_feed(FeedConfig(
            name="sec_filings",
            adapter_class=SECFilingAdapter,
            adapter_config={"form_types": ["10-K", "10-Q"]},
            priority=100,  # Highest trust (official source)
        ))

        manager.register_feed(FeedConfig(
            name="internal_db",
            adapter_class=BulkFileAdapter,
            adapter_config={"path": "security_master.csv"},
            priority=50,
        ))

        # Run all feeds
        results = await manager.run_all()

        # Or run specific feed
        result = await manager.run("bloomberg")
    """

    def __init__(self, fabric: "EntityFabric"):
        self.fabric = fabric
        self.feeds: dict[str, FeedConfig] = {}
        self.change_tracker = ChangeTracker(fabric.store)

    def register_feed(self, config: FeedConfig) -> None:
        """Register a new feed."""
        self.feeds[config.name] = config

    async def run(self, feed_name: str) -> ChangeReport:
        """Run a single feed with change detection."""
        config = self.feeds[feed_name]
        adapter = config.adapter_class(**config.adapter_config)

        # Collect all records
        records = list(adapter.ingest())

        # Compute diff if enabled
        if config.track_changes:
            diff = await self.change_tracker.compute_diff(
                records,
                source_name=feed_name,
                key_field=config.diff_key,
            )

            # Apply changes
            for key, record in diff.added.items():
                await self.fabric.ingest(record)

            for key, (old, new, changes) in diff.modified.items():
                await self.fabric.update(old.entity_id, new)

            # Mark removed (don't delete, just flag)
            for key, entity in diff.removed.items():
                await self.fabric.mark_removed(entity.entity_id, source=feed_name)

            return ChangeReport(
                batch_id=adapter._batch_id,
                source_name=feed_name,
                started_at=...,
                completed_at=datetime.now(timezone.utc),
                new_entities=len(diff.added),
                modified_entities=len(diff.modified),
                removed_entities=len(diff.removed),
                unchanged_entities=diff.unchanged_count,
            )
        else:
            # Just ingest everything
            for record in records:
                await self.fabric.ingest(record)

            return ChangeReport(...)

    async def run_all(self) -> dict[str, ChangeReport]:
        """Run all registered feeds."""
        results = {}
        for name in self.feeds:
            results[name] = await self.run(name)
        return results

    async def generate_daily_report(self) -> str:
        """Generate a daily change summary across all feeds."""
        reports = await self.run_all()

        lines = ["=" * 60, "DAILY ENTITY FEED REPORT", "=" * 60, ""]

        total_new = total_mod = total_rem = 0

        for name, report in reports.items():
            lines.append(report.summary())
            lines.append("")
            total_new += report.new_entities
            total_mod += report.modified_entities
            total_rem += report.removed_entities

        lines.extend([
            "-" * 60,
            f"TOTALS: {total_new} new, {total_mod} modified, {total_rem} removed",
            "=" * 60,
        ])

        return "\n".join(lines)
```

---

## Comprehensive Entity Extraction from 10-K

**Vision**: EntitySpine automatically extracts and manages ALL entity types from SEC filings.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    10-K FILING → ENTITYSPINE ENTITY MAP                          │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                           10-K DOCUMENT                                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                    │                                            │
│    ┌───────────────────────────────┼───────────────────────────────┐            │
│    │               │               │               │               │            │
│    ▼               ▼               ▼               ▼               ▼            │
│  ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐               │
│  │Cover│       │Item1│       │Item1A│      │Item3│       │Item10│              │
│  │Page │       │Bus. │       │Risks │      │Legal│       │Dirs. │              │
│  └──┬──┘       └──┬──┘       └──┬──┘       └──┬──┘       └──┬──┘               │
│     │             │             │             │             │                   │
│     ▼             ▼             ▼             ▼             ▼                   │
│  Company      Products      Risk Factors  Litigation   Executives              │
│  CIK          Services      Competitors   Plaintiffs   Directors               │
│  Ticker       Suppliers     Regulators    Defendants   Committees              │
│  SIC Code     Customers     Countries                                          │
│  State Inc.   Partners                                                         │
│                                                                                  │
│    ┌───────────────────────────────┼───────────────────────────────┐            │
│    │               │               │               │               │            │
│    ▼               ▼               ▼               ▼               ▼            │
│  ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐               │
│  │Ex 21│       │Ex 23│       │Sigs │       │Item7│       │Item8│               │
│  │Subs │       │Cons │       │     │       │MD&A │       │Fins │               │
│  └──┬──┘       └──┬──┘       └──┬──┘       └──┬──┘       └──┬──┘               │
│     │             │             │             │             │                   │
│     ▼             ▼             ▼             ▼             ▼                   │
│  Subsidiaries  Auditors     Officers     Contracts    Debt holders             │
│  Countries     Audit Firm   Signatures   Agreements   Counterparties           │
│  Ownership %                                          Related Parties          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Entity Extraction Examples

```python
# =============================================================================
# WHAT ENTITYSPINE EXTRACTS FROM A 10-K
# =============================================================================

filing_entities = {
    # Cover Page / Header
    "company": {
        "name": "Apple Inc.",
        "identifiers": {"cik": "0000320193", "ticker": "AAPL", "sic": "3571"},
        "attributes": {"state": "CA", "fiscal_year_end": "09-30"},
    },

    # Item 1: Business Description
    "products": [
        {"name": "iPhone", "category": "hardware", "segment": "Products"},
        {"name": "Mac", "category": "hardware", "segment": "Products"},
        {"name": "iPad", "category": "hardware", "segment": "Products"},
        {"name": "Apple Watch", "category": "hardware", "segment": "Products"},
        {"name": "Apple TV+", "category": "service", "segment": "Services"},
        {"name": "App Store", "category": "service", "segment": "Services"},
    ],

    "suppliers": [
        {"name": "Taiwan Semiconductor (TSMC)", "relationship": "manufacturing", "critical": True},
        {"name": "Samsung Electronics", "relationship": "components", "critical": True},
        {"name": "Foxconn (Hon Hai)", "relationship": "assembly", "critical": True},
    ],

    "customers": [
        {"name": "Best Buy", "channel": "retail"},
        {"name": "Verizon", "channel": "carrier"},
        {"name": "Amazon", "channel": "online"},
    ],

    # Item 1A: Risk Factors
    "risk_entities": [
        {"name": "China", "risk_type": "geographic_concentration"},
        {"name": "European Commission", "risk_type": "regulatory"},
        {"name": "DOJ", "risk_type": "antitrust"},
    ],

    "competitors": [
        {"name": "Samsung Electronics", "segment": "smartphones"},
        {"name": "Google", "segment": "mobile_os"},
        {"name": "Microsoft", "segment": "personal_computers"},
    ],

    # Item 3: Legal Proceedings
    "litigation": [
        {
            "case": "Epic Games v. Apple",
            "plaintiff": "Epic Games",
            "defendant": "Apple",
            "court": "N.D. Cal.",
            "status": "ongoing",
        },
    ],

    # Item 10: Directors, Executive Officers
    "executives": [
        {"name": "Tim Cook", "role": "CEO", "since": 2011},
        {"name": "Luca Maestri", "role": "CFO", "since": 2014},
        {"name": "Jeff Williams", "role": "COO", "since": 2015},
        {"name": "Katherine Adams", "role": "CLO", "since": 2017},
        {"name": "Deirdre O'Brien", "role": "SVP Retail", "since": 2019},
    ],

    "directors": [
        {"name": "Arthur Levinson", "role": "Chairman", "independent": True},
        {"name": "Tim Cook", "role": "Director", "independent": False},
        # ...
    ],

    # Exhibit 21: Subsidiaries
    "subsidiaries": [
        {"name": "Apple Sales International", "jurisdiction": "Ireland", "ownership": 100},
        {"name": "Apple Operations International", "jurisdiction": "Ireland", "ownership": 100},
        {"name": "Beats Electronics, LLC", "jurisdiction": "Delaware", "ownership": 100},
        {"name": "Apple Japan Inc.", "jurisdiction": "Japan", "ownership": 100},
    ],

    # Signatures / Exhibit 23
    "auditors": [
        {"name": "Ernst & Young LLP", "role": "independent_auditor", "city": "San Jose"},
    ],

    # Item 8: Financial Statements (counterparties, debt holders)
    "counterparties": [
        {"name": "Goldman Sachs", "relationship": "underwriter"},
        {"name": "JP Morgan", "relationship": "credit_facility"},
    ],
}
```

---

## Next Steps

### Phase 1: Core Infrastructure
1. **Implement Core Adapters**
   - SECFilingHeaderAdapter
   - BulkFileAdapter
   - OpenFIGIAdapter
   - GLEIFAdapter
   - **SecurityMasterAdapter** (Bloomberg, Refinitiv, custom)

2. **Extend EntitySpine Store**
   - Add lineage table support
   - Implement point-in-time queries
   - Add change tracking
   - **ChangeTracker service**

### Phase 2: Analyst & Ownership
3. **Analyst Coverage System**
   - Analyst entity model
   - Research note ingestion
   - Earnings estimate tracking
   - Consensus computation
   - `GET /api/entities/{id}/coverage` - analyst coverage
   - `GET /api/entities/{id}/estimates` - earnings estimates

4. **Ownership Intelligence**
   - 13F filing ingestion (Form13FAdapter)
   - Form 4 insider transaction ingestion
   - Ownership history tracking
   - `GET /api/entities/{id}/holders` - institutional holders
   - `GET /api/entities/{id}/insiders` - insider transactions

### Phase 3: Signals & Statements
5. **Public Figure & Statement System**
   - PublicFigure entity model
   - Statement ingestion with NER
   - Entity linking for statements
   - Sentiment analysis integration
   - `GET /api/figures/{id}/statements` - what they've said
   - `GET /api/entities/{id}/mentions` - who mentioned them

6. **Signal Graph**
   - Unified Signal model
   - SignalGraph service
   - Timeline queries
   - Portfolio signal aggregation
   - `GET /api/signals?portfolio=AAPL,MSFT,GOOG&since=7d`

### Phase 4: Intelligence Products
7. **Build CLI Commands**
   - `entityspine ingest --file portfolio.csv`
   - `entityspine enrich --ticker AAPL`
   - `entityspine enrich --sector Technology`
   - `entityspine feed sync --name bloomberg`
   - `entityspine changes --since 7d`
   - `entityspine brief --portfolio my_portfolio.csv`

8. **Morning Brief Generator**
   - Portfolio signal aggregation
   - Templated report generation
   - Email/Slack delivery integration
   - `entityspine brief generate --portfolio tech_holdings`

9. **Build UnifiedFeedManager**
   - Multi-source ingestion
   - Priority-based conflict resolution
   - Daily change reports
   - Scheduled feed execution

### Phase 5: Integration & Scale
10. **API Endpoints**
    - `POST /api/entities/ingest`
    - `GET /api/entities/{id}/lineage`
    - `GET /api/entities/{id}/as-of?date=2025-01-01`
    - `GET /api/changes?since=2025-01-01&source=bloomberg`
    - `POST /api/feeds/{name}/sync`
    - `GET /api/graph/entity/{id}` - full knowledge graph
    - `POST /api/signals/ingest` - ingest news/statements
    - `GET /api/brief/{portfolio_id}` - morning brief

11. **Integrate with Enrichment Pipeline**
    - Hook EntityFabric into EntityExtractor
    - Auto-link extracted entities to graph
    - Real-time signal processing

---

## What's Missing? The Complete System Map

Before diving into financial data, let's map out EVERYTHING a complete system needs:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    THE COMPLETE FINANCIAL DATA ECOSYSTEM                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         ENTITYSPINE (Identity)                           │    │
│  │  Companies, Securities, People, Funds, Analysts, Public Figures          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│         ┌────────────────────────────┼────────────────────────────┐             │
│         │              │             │             │              │             │
│         ▼              ▼             ▼             ▼              ▼             │
│  ┌───────────┐  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│  │ FINANCIAL │  │ CORPORATE │ │ REFERENCE │ │  MARKET   │ │  CONTENT  │        │
│  │   DATA    │  │  ACTIONS  │ │   DATA    │ │   DATA    │ │MANAGEMENT │        │
│  │           │  │           │ │           │ │           │ │           │        │
│  │ • XBRL    │  │ • M&A     │ │ • Exch.   │ │ • Prices  │ │ • Filings │        │
│  │ • Income  │  │ • Spinoff │ │ • Country │ │ • Volume  │ │ • Exhibits│        │
│  │ • Balance │  │ • Divid.  │ │ • Currency│ │ • Mkt Cap │ │ • PDFs    │        │
│  │ • CashFlow│  │ • Splits  │ │ • Industry│ │ • Returns │ │ • Search  │        │
│  │ • Segments│  │ • IPO/Del │ │ • Indices │ │ • Beta    │ │ • Version │        │
│  └───────────┘  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │
│         │              │             │             │              │             │
│         └────────────────────────────┼────────────────────────────┘             │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        FEEDSPINE (Ingestion)                             │    │
│  │  Change Detection, Sightings, Deduplication, Scheduling                  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                          │
│         ┌────────────────────────────┼────────────────────────────┐             │
│         │              │             │             │              │             │
│         ▼              ▼             ▼             ▼              ▼             │
│  ┌───────────┐  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐        │
│  │ CALENDARS │  │   ALERTS  │ │  DERIVED  │ │   DATA    │ │INTELLIGENCE│       │
│  │           │  │           │ │  METRICS  │ │  QUALITY  │ │  PRODUCTS │        │
│  │ • Earnings│  │ • Filing  │ │ • Ratios  │ │ • Valid.  │ │ • Briefs  │        │
│  │ • Ex-Div  │  │ • Owner   │ │ • Growth  │ │ • Recon.  │ │ • Screens │        │
│  │ • Conf.   │  │ • Price   │ │ • Comps   │ │ • Scores  │ │ • Reports │        │
│  │ • Deadlin │  │ • Rating  │ │ • Peers   │ │ • Lineage │ │ • Alerts  │        │
│  └───────────┘  └───────────┘ └───────────┘ └───────────┘ └───────────┘        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Financial Data (XBRL Integration)

**The Missing Link**: We track WHO filed, but not WHAT the numbers are.

```python
# =============================================================================
# FINANCIAL DATA MODEL
# =============================================================================

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class StatementType(Enum):
    """Types of financial statements."""
    INCOME = "income_statement"
    BALANCE = "balance_sheet"
    CASH_FLOW = "cash_flow"
    EQUITY = "stockholders_equity"
    COMPREHENSIVE_INCOME = "comprehensive_income"


class PeriodType(Enum):
    """Reporting period types."""
    ANNUAL = "annual"         # 10-K, full year
    QUARTERLY = "quarterly"   # 10-Q
    YTD = "year_to_date"      # Cumulative
    TRAILING_12M = "ttm"      # Trailing twelve months


@dataclass
class FinancialFact:
    """
    A single financial fact from XBRL.

    This is the atomic unit of financial data:
    "Apple's Revenue for FY2025 was $450B"
    """
    fact_id: str
    entity_id: str            # Links to EntitySpine

    # What is this fact?
    concept: str              # XBRL concept: "us-gaap:Revenues"
    label: str                # Human readable: "Total Revenue"

    # The value
    value: Decimal
    unit: str                 # "USD", "shares", "pure" (ratio)
    decimals: int             # Precision indicator

    # Time context
    period_type: PeriodType
    period_start: date
    period_end: date
    instant: date | None      # For balance sheet items (point in time)
    fiscal_year: int
    fiscal_quarter: int | None

    # Filing context
    accession_number: str
    form_type: str            # "10-K", "10-Q"
    filed_date: date

    # Segment/dimension context (optional)
    segment: str | None = None          # "iPhone", "Services", etc.
    geography: str | None = None        # "Americas", "Europe", etc.
    dimensions: dict = field(default_factory=dict)

    # Lineage
    source: "IngestionSource" | None = None


@dataclass
class FinancialStatement:
    """
    A complete financial statement for a period.
    """
    statement_id: str
    entity_id: str
    statement_type: StatementType

    # Period
    fiscal_year: int
    fiscal_quarter: int | None
    period_end: date

    # All line items
    line_items: dict[str, Decimal]  # concept -> value

    # Standard mappings (normalized names)
    revenue: Decimal | None = None
    cost_of_revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    eps_basic: Decimal | None = None
    eps_diluted: Decimal | None = None

    # Balance sheet
    total_assets: Decimal | None = None
    total_liabilities: Decimal | None = None
    total_equity: Decimal | None = None
    cash: Decimal | None = None
    total_debt: Decimal | None = None

    # Cash flow
    operating_cash_flow: Decimal | None = None
    capex: Decimal | None = None
    free_cash_flow: Decimal | None = None

    # Filing source
    accession_number: str | None = None
    filed_date: date | None = None


@dataclass
class SegmentData:
    """
    Financial data broken down by business segment.

    Example: Apple reports iPhone, Mac, iPad, Services, etc.
    """
    entity_id: str
    fiscal_year: int
    fiscal_quarter: int | None

    segments: dict[str, dict[str, Decimal]]
    # {
    #   "iPhone": {"revenue": 200B, "operating_income": 80B},
    #   "Services": {"revenue": 100B, "operating_income": 70B},
    #   "Mac": {"revenue": 40B, "operating_income": 15B},
    # }

    geographic: dict[str, dict[str, Decimal]] | None = None
    # {
    #   "Americas": {"revenue": 180B},
    #   "Europe": {"revenue": 100B},
    #   "Greater China": {"revenue": 75B},
    # }


# =============================================================================
# XBRL ADAPTER: Ingest Financial Data
# =============================================================================

class XBRLAdapter(IngestionAdapter):
    """
    Ingest XBRL financial data from SEC filings.

    Connects to your existing XBRL project!
    """
    source_type = "xbrl"

    def __init__(
        self,
        xbrl_db_path: str,        # Path to your XBRL project's database
        entity_id: str | None = None,
        since_date: date | None = None,
    ):
        self.xbrl_db_path = xbrl_db_path
        self.entity_id = entity_id
        self.since_date = since_date

    def ingest(self) -> Iterator["FinancialFact"]:
        """Pull facts from XBRL database."""
        # Connect to your XBRL project
        # Query for facts
        # Yield FinancialFact objects
        ...

    def get_statement(
        self,
        entity_id: str,
        statement_type: StatementType,
        fiscal_year: int,
        fiscal_quarter: int | None = None,
    ) -> FinancialStatement:
        """Get a complete financial statement."""
        ...


# =============================================================================
# CONNECTING FINANCIAL DATA TO ENTITYSPINE
# =============================================================================

class FinancialDataService:
    """
    Service layer connecting XBRL financial data to EntitySpine.
    """

    def __init__(
        self,
        fabric: "EntityFabric",
        xbrl_adapter: XBRLAdapter,
    ):
        self.fabric = fabric
        self.xbrl = xbrl_adapter

    async def get_financials(
        self,
        entity_id: str,
        years: int = 5,
    ) -> list[FinancialStatement]:
        """Get historical financial statements for an entity."""
        ...

    async def compare_to_estimates(
        self,
        entity_id: str,
        fiscal_year: int,
        fiscal_quarter: int,
    ) -> dict:
        """
        Compare actual results to analyst estimates.

        Returns:
            {
                "eps_actual": 1.52,
                "eps_estimate": 1.48,
                "eps_surprise": 0.04,
                "eps_surprise_pct": 2.7%,
                "beat": True,

                "revenue_actual": 94.8B,
                "revenue_estimate": 93.5B,
                "revenue_surprise": 1.3B,
                "revenue_beat": True,
            }
        """
        # Get actual from XBRL
        actual = await self.xbrl.get_statement(
            entity_id, StatementType.INCOME, fiscal_year, fiscal_quarter
        )

        # Get estimates from EntitySpine
        estimates = await self.fabric.get_consensus_estimate(
            entity_id, fiscal_year, fiscal_quarter
        )

        return {
            "eps_actual": actual.eps_diluted,
            "eps_estimate": estimates.eps_mean,
            "eps_surprise": actual.eps_diluted - estimates.eps_mean,
            "eps_surprise_pct": (actual.eps_diluted - estimates.eps_mean) / estimates.eps_mean * 100,
            "beat": actual.eps_diluted > estimates.eps_mean,
            # ... revenue comparison ...
        }

    async def get_segment_trends(
        self,
        entity_id: str,
        segment: str,
        years: int = 5,
    ) -> list[dict]:
        """Track a segment's performance over time."""
        ...
```

---

## 2. Corporate Actions & Events

**Missing**: Stock splits, dividends, M&A, spinoffs, delistings, ticker changes, IPOs.

```python
# =============================================================================
# CORPORATE ACTIONS
# =============================================================================

class ActionType(Enum):
    """Types of corporate actions."""
    # Capital structure
    STOCK_SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    STOCK_DIVIDEND = "stock_dividend"
    CASH_DIVIDEND = "cash_dividend"
    SPECIAL_DIVIDEND = "special_dividend"
    BUYBACK = "buyback"

    # Corporate events
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SPINOFF = "spinoff"
    IPO = "ipo"
    DELISTING = "delisting"
    BANKRUPTCY = "bankruptcy"

    # Changes
    TICKER_CHANGE = "ticker_change"
    NAME_CHANGE = "name_change"
    EXCHANGE_CHANGE = "exchange_change"

    # Other
    RIGHTS_OFFERING = "rights_offering"
    TENDER_OFFER = "tender_offer"


@dataclass
class CorporateAction:
    """A corporate action affecting a security."""
    action_id: str
    entity_id: str
    action_type: ActionType

    # Dates
    announcement_date: date
    ex_date: date | None = None       # When price adjusts
    record_date: date | None = None   # Who gets the benefit
    effective_date: date | None = None
    payment_date: date | None = None  # For dividends

    # Action-specific data
    details: dict = field(default_factory=dict)
    # Split: {"ratio": "4:1", "factor": 4.0}
    # Dividend: {"amount": 0.25, "currency": "USD", "frequency": "quarterly"}
    # M&A: {"acquirer_id": "...", "price_per_share": 150.0, "all_cash": True}
    # Spinoff: {"new_entity_id": "...", "ratio": "1:10"}

    # Related entities (for M&A, spinoffs)
    related_entity_ids: list[str] = field(default_factory=list)

    # Status
    status: str = "announced"  # "announced", "completed", "cancelled"

    # Source
    source: "IngestionSource" | None = None


@dataclass
class DividendHistory:
    """Track dividend history for an entity."""
    entity_id: str

    # Current policy
    current_annual_dividend: Decimal | None
    dividend_yield: Decimal | None
    payout_ratio: Decimal | None

    # History
    dividends: list[CorporateAction]

    # Streaks
    years_of_increases: int = 0
    years_of_payments: int = 0

    # Classification
    dividend_aristocrat: bool = False    # 25+ years of increases
    dividend_king: bool = False          # 50+ years of increases


# =============================================================================
# WHY THIS MATTERS
# =============================================================================

# 1. Price adjustments - splits affect historical prices
# 2. Return calculations - need to include dividends
# 3. Portfolio tracking - shares change on splits
# 4. Entity lifecycle - mergers change entity relationships
# 5. Timeline accuracy - "Apple before/after split"
```

---

## 3. Reference Data

**Missing**: Exchanges, countries, currencies, industries, indices.

```python
# =============================================================================
# REFERENCE DATA
# =============================================================================

@dataclass
class Exchange:
    """Stock exchange reference data."""
    mic: str                  # Market Identifier Code (ISO 10383)
    name: str                 # "NASDAQ Global Select Market"
    acronym: str              # "NASDAQ"
    country: str              # ISO country code
    city: str
    timezone: str

    # Trading hours
    open_time: str            # "09:30"
    close_time: str           # "16:00"

    # Status
    is_active: bool = True


@dataclass
class Industry:
    """Industry classification."""
    code: str                 # SIC: "3571", GICS: "45202010"
    scheme: str               # "SIC", "NAICS", "GICS"
    name: str                 # "Electronic Computers"

    # Hierarchy
    sector: str | None = None
    industry_group: str | None = None
    sub_industry: str | None = None

    # Parent code for hierarchy
    parent_code: str | None = None


@dataclass
class Index:
    """Market index reference data."""
    index_id: str
    symbol: str               # "SPX", "NDX", "DJI"
    name: str                 # "S&P 500"
    provider: str             # "S&P Dow Jones Indices"

    # Composition
    member_count: int
    weighting: str            # "market_cap", "price", "equal"

    # Constituents (links to entity_ids)
    constituents: list[str] = field(default_factory=list)

    # Rebalance schedule
    rebalance_frequency: str  # "quarterly", "annually"


@dataclass
class Currency:
    """Currency reference data."""
    code: str                 # ISO 4217: "USD", "EUR"
    name: str                 # "US Dollar"
    symbol: str               # "$"
    decimals: int             # 2

    # For FX
    base_currency: str | None = None
    exchange_rate: Decimal | None = None
    rate_as_of: date | None = None
```

---

## 4. Market Data (Prices, Returns, Valuations)

**Missing**: How do we connect entities to their market prices?

```python
# =============================================================================
# MARKET DATA
# =============================================================================

@dataclass
class PriceBar:
    """OHLCV price data."""
    entity_id: str
    security_id: str

    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    # Adjusted prices (for splits/dividends)
    adj_close: Decimal

    # Source
    source: str  # "polygon", "yahoo", "bloomberg"


@dataclass
class MarketSnapshot:
    """Current market data for an entity."""
    entity_id: str
    as_of: datetime

    # Prices
    price: Decimal
    change: Decimal
    change_pct: Decimal

    # Volume
    volume: int
    avg_volume_30d: int

    # Valuation
    market_cap: Decimal
    enterprise_value: Decimal | None = None

    # Multiples (computed from financial data)
    pe_ratio: Decimal | None = None
    forward_pe: Decimal | None = None
    peg_ratio: Decimal | None = None
    price_to_sales: Decimal | None = None
    price_to_book: Decimal | None = None
    ev_to_ebitda: Decimal | None = None

    # Technicals
    sma_50: Decimal | None = None
    sma_200: Decimal | None = None
    rsi_14: Decimal | None = None

    # Ranges
    high_52w: Decimal | None = None
    low_52w: Decimal | None = None


@dataclass
class Returns:
    """Computed returns for an entity."""
    entity_id: str
    as_of: date

    # Price returns
    return_1d: Decimal
    return_1w: Decimal
    return_1m: Decimal
    return_3m: Decimal
    return_ytd: Decimal
    return_1y: Decimal
    return_3y: Decimal
    return_5y: Decimal

    # Total returns (including dividends)
    total_return_1y: Decimal | None = None
    total_return_3y: Decimal | None = None
    total_return_5y: Decimal | None = None

    # Risk metrics
    volatility_30d: Decimal | None = None
    beta: Decimal | None = None
    sharpe_ratio: Decimal | None = None
```

---

## 5. Calendars & Scheduling

**Missing**: When do things happen?

```python
# =============================================================================
# EVENT CALENDARS
# =============================================================================

class EventType(Enum):
    """Types of scheduled events."""
    EARNINGS_RELEASE = "earnings"
    EARNINGS_CALL = "earnings_call"
    INVESTOR_DAY = "investor_day"
    ANNUAL_MEETING = "annual_meeting"
    CONFERENCE = "conference"

    EX_DIVIDEND = "ex_div"
    DIVIDEND_PAYMENT = "div_payment"

    FILING_DEADLINE = "filing_deadline"

    OPTIONS_EXPIRATION = "options_exp"
    INDEX_REBALANCE = "index_rebalance"


@dataclass
class CalendarEvent:
    """A scheduled event."""
    event_id: str
    event_type: EventType
    entity_id: str | None = None

    # When
    date: date
    time: str | None = None
    timezone: str = "America/New_York"

    # Details
    title: str
    description: str | None = None

    # For earnings
    fiscal_year: int | None = None
    fiscal_quarter: int | None = None

    # Estimates (for earnings)
    eps_estimate: Decimal | None = None
    revenue_estimate: Decimal | None = None

    # Status
    confirmed: bool = True

    # Source
    source: str | None = None


class CalendarService:
    """
    Manage event calendars.

    Enables:
    - "When does Apple report earnings?"
    - "What companies report this week?"
    - "Show me all ex-dividend dates in my portfolio"
    """

    async def get_upcoming_earnings(
        self,
        entity_ids: list[str] | None = None,
        days_ahead: int = 30,
    ) -> list[CalendarEvent]:
        """Get upcoming earnings for entities or all."""
        ...

    async def get_portfolio_calendar(
        self,
        entity_ids: list[str],
        days_ahead: int = 30,
    ) -> list[CalendarEvent]:
        """Get all events for a portfolio."""
        ...

    async def get_filing_deadlines(
        self,
        entity_id: str,
    ) -> list[CalendarEvent]:
        """Get SEC filing deadlines for an entity."""
        ...
```

---

## 6. Document & Content Management

**Missing**: The actual documents, full-text search, attachments.

```python
# =============================================================================
# DOCUMENT MANAGEMENT
# =============================================================================

@dataclass
class Document:
    """A document (filing, exhibit, attachment)."""
    document_id: str
    entity_id: str | None = None

    # Type
    document_type: str        # "10-K", "10-Q", "8-K", "exhibit", "press_release"

    # Identification
    accession_number: str | None = None
    sequence: int | None = None  # For exhibits

    # Content
    filename: str
    description: str | None = None
    mime_type: str            # "text/html", "application/pdf"

    # Storage
    storage_path: str         # Local or S3 path
    file_size: int
    content_hash: str         # For deduplication

    # Extracted text (for search)
    extracted_text: str | None = None

    # Dates
    filed_date: date | None = None
    period_end: date | None = None

    # Parsing status
    parsed: bool = False
    parsed_at: datetime | None = None

    # Extracted entities from this document
    extracted_entity_ids: list[str] = field(default_factory=list)


class DocumentStore:
    """
    Manage document storage and retrieval.
    """

    async def store(self, document: Document, content: bytes) -> str:
        """Store document content, return storage path."""
        ...

    async def get_content(self, document_id: str) -> bytes:
        """Retrieve document content."""
        ...

    async def search(
        self,
        query: str,
        entity_ids: list[str] | None = None,
        document_types: list[str] | None = None,
        since: date | None = None,
    ) -> list[Document]:
        """Full-text search across documents."""
        ...

    async def get_exhibits(
        self,
        accession_number: str,
    ) -> list[Document]:
        """Get all exhibits for a filing."""
        ...
```

---

## 7. Derived Metrics & Peer Comparison

**Missing**: Computed ratios, growth rates, peer groups.

```python
# =============================================================================
# DERIVED METRICS
# =============================================================================

@dataclass
class DerivedMetrics:
    """Computed metrics for an entity."""
    entity_id: str
    as_of: date

    # Growth rates
    revenue_growth_yoy: Decimal | None = None
    revenue_growth_3y_cagr: Decimal | None = None
    eps_growth_yoy: Decimal | None = None

    # Profitability
    gross_margin: Decimal | None = None
    operating_margin: Decimal | None = None
    net_margin: Decimal | None = None
    roe: Decimal | None = None
    roa: Decimal | None = None
    roic: Decimal | None = None

    # Leverage
    debt_to_equity: Decimal | None = None
    debt_to_ebitda: Decimal | None = None
    interest_coverage: Decimal | None = None

    # Liquidity
    current_ratio: Decimal | None = None
    quick_ratio: Decimal | None = None

    # Efficiency
    asset_turnover: Decimal | None = None
    inventory_turnover: Decimal | None = None
    receivables_turnover: Decimal | None = None


@dataclass
class PeerGroup:
    """A group of comparable companies."""
    peer_group_id: str
    name: str                 # "Large Cap Tech Hardware"

    # How peers were selected
    criteria: dict            # {"sector": "Technology", "market_cap_min": 100B}

    # Members
    member_entity_ids: list[str]

    # Computed aggregates
    median_pe: Decimal | None = None
    median_growth: Decimal | None = None
    median_margin: Decimal | None = None


class PeerAnalysisService:
    """
    Compare entities to peers.
    """

    async def get_peer_group(
        self,
        entity_id: str,
        method: str = "industry",  # "industry", "custom", "size"
    ) -> PeerGroup:
        """Find peers for an entity."""
        ...

    async def rank_in_peers(
        self,
        entity_id: str,
        metric: str,
        peer_group: PeerGroup,
    ) -> dict:
        """
        Rank entity on a metric vs peers.

        Returns:
            {
                "metric": "revenue_growth_yoy",
                "value": 15.2,
                "rank": 3,
                "total": 15,
                "percentile": 80,
                "peer_median": 8.5,
                "peer_mean": 9.2,
            }
        """
        ...
```

---

## 8. Data Quality & Reconciliation

**Missing**: How do we know the data is correct?

```python
# =============================================================================
# DATA QUALITY
# =============================================================================

class ValidationLevel(Enum):
    """Severity of validation issues."""
    ERROR = "error"       # Data is wrong
    WARNING = "warning"   # Data is suspicious
    INFO = "info"         # FYI


@dataclass
class ValidationIssue:
    """A data quality issue."""
    issue_id: str
    entity_id: str
    field: str

    level: ValidationLevel
    rule: str             # "eps_sign_change", "revenue_implausible", etc.
    message: str

    # Context
    expected_value: str | None = None
    actual_value: str | None = None

    # Resolution
    resolved: bool = False
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None


class DataQualityService:
    """
    Validate and reconcile data.
    """

    async def validate_entity(self, entity_id: str) -> list[ValidationIssue]:
        """Run all validation rules on an entity."""
        issues = []

        # Check for missing identifiers
        entity = await self.fabric.get_entity(entity_id)
        if not entity.identifiers.get("cik"):
            issues.append(ValidationIssue(
                issue_id=generate_id(),
                entity_id=entity_id,
                field="identifiers.cik",
                level=ValidationLevel.WARNING,
                rule="missing_cik",
                message="Entity has no CIK - cannot link to SEC filings",
            ))

        # Check for stale data
        last_updated = await self.fabric.get_last_updated(entity_id)
        if last_updated < datetime.now() - timedelta(days=90):
            issues.append(ValidationIssue(
                issue_id=generate_id(),
                entity_id=entity_id,
                field="last_updated",
                level=ValidationLevel.INFO,
                rule="stale_data",
                message=f"Entity not updated since {last_updated}",
            ))

        # Check financial data sanity
        financials = await self.financials.get_latest(entity_id)
        if financials and financials.revenue and financials.revenue < 0:
            issues.append(ValidationIssue(
                issue_id=generate_id(),
                entity_id=entity_id,
                field="revenue",
                level=ValidationLevel.ERROR,
                rule="negative_revenue",
                message="Revenue is negative - likely data error",
                actual_value=str(financials.revenue),
            ))

        return issues

    async def reconcile_sources(
        self,
        entity_id: str,
        field: str,
    ) -> dict:
        """
        Compare values from different sources.

        Returns:
            {
                "field": "market_cap",
                "sources": {
                    "bloomberg": 3_000_000_000_000,
                    "refinitiv": 2_998_500_000_000,
                    "yahoo": 2_999_000_000_000,
                },
                "variance_pct": 0.05,
                "consensus_value": 2_999_166_666_666,
            }
        """
        ...
```

---

## 9. Alerts & Real-Time Notifications

**Missing**: How do users get notified?

```python
# =============================================================================
# ALERTS & NOTIFICATIONS
# =============================================================================

class AlertType(Enum):
    """Types of alerts."""
    NEW_FILING = "new_filing"
    EARNINGS_BEAT = "earnings_beat"
    EARNINGS_MISS = "earnings_miss"
    PRICE_TARGET_CHANGE = "price_target"
    RATING_CHANGE = "rating_change"
    OWNERSHIP_CHANGE = "ownership_change"
    INSIDER_TRADE = "insider_trade"
    DIVIDEND_CHANGE = "dividend_change"
    CORPORATE_ACTION = "corporate_action"
    PRICE_ALERT = "price_alert"
    VOLUME_SPIKE = "volume_spike"


@dataclass
class AlertRule:
    """User-defined alert rule."""
    rule_id: str
    user_id: str

    alert_type: AlertType
    entity_ids: list[str] | None = None   # Specific entities or all

    # Conditions
    conditions: dict = field(default_factory=dict)
    # Examples:
    # {"rating_direction": "downgrade"}
    # {"ownership_change_pct_min": 5}
    # {"price_below": 150}

    # Delivery
    channels: list[str] = field(default_factory=list)  # ["email", "slack", "sms"]

    # Status
    active: bool = True


@dataclass
class Alert:
    """A triggered alert."""
    alert_id: str
    rule_id: str
    entity_id: str
    alert_type: AlertType

    # What triggered it
    signal_id: str | None = None
    trigger_value: str | None = None

    # Content
    title: str
    message: str

    # Status
    triggered_at: datetime
    delivered: bool = False
    delivered_at: datetime | None = None
    read: bool = False
    read_at: datetime | None = None


class AlertService:
    """
    Manage alerts and notifications.
    """

    async def create_rule(self, rule: AlertRule) -> str:
        """Create a new alert rule."""
        ...

    async def process_signal(self, signal: Signal) -> list[Alert]:
        """Check if signal triggers any rules, create alerts."""
        triggered = []

        # Find matching rules
        rules = await self.get_rules_for_signal(signal)

        for rule in rules:
            if self._matches_conditions(signal, rule):
                alert = Alert(
                    alert_id=generate_id(),
                    rule_id=rule.rule_id,
                    entity_id=signal.primary_entity_id,
                    alert_type=rule.alert_type,
                    signal_id=signal.signal_id,
                    title=self._generate_title(signal, rule),
                    message=self._generate_message(signal, rule),
                    triggered_at=datetime.now(timezone.utc),
                )
                triggered.append(alert)
                await self._deliver(alert, rule.channels)

        return triggered
```

---

## 10. The Complete Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PY-SEC-EDGAR COMPLETE SYSTEM                             │
│                                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  SEC EDGAR  │  │ XBRL DATA   │  │  BLOOMBERG  │  │    NEWS     │             │
│  │  Filings    │  │ (Your Proj) │  │  Refinitiv  │  │  Research   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                │                     │
│         └────────────────┴────────────────┴────────────────┘                     │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                            FEEDSPINE                                       │  │
│  │   • Adapters (SEC, XBRL, CSV, API, RSS)                                   │  │
│  │   • Change Detection (new/modified/removed)                               │  │
│  │   • Deduplication (sightings)                                             │  │
│  │   • Scheduling (cron, on-demand)                                          │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           ENTITYSPINE                                      │  │
│  │                                                                            │  │
│  │   IDENTITY          FINANCIAL        MARKET          CONTENT               │  │
│  │   ────────          ─────────        ──────          ───────               │  │
│  │   Companies         XBRL Facts       Prices          Documents             │  │
│  │   Securities        Statements       Returns         Full-text             │  │
│  │   People            Segments         Valuations      Exhibits              │  │
│  │   Analysts          Estimates        Technicals                            │  │
│  │   Funds             Actuals vs Est                                         │  │
│  │                                                                            │  │
│  │   RELATIONSHIPS     SIGNALS          REFERENCE       CALENDAR              │  │
│  │   ─────────────     ───────          ─────────       ────────              │  │
│  │   Supply Chain      Filings          Exchanges       Earnings              │  │
│  │   Ownership         Research         Industries      Dividends             │  │
│  │   Coverage          News             Currencies      Conferences           │  │
│  │   Executives        Statements       Indices         Deadlines             │  │
│  │                     Corp Actions     Countries                             │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                         INTELLIGENCE LAYER                                 │  │
│  │                                                                            │  │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │   │ Morning  │  │  Peer    │  │  Alerts  │  │ Screens  │  │  Custom  │   │  │
│  │   │ Briefs   │  │ Analysis │  │          │  │          │  │ Reports  │   │  │
│  │   └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  │                                                                            │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                             │
│                                    ▼                                             │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           DELIVERY                                         │  │
│  │   CLI    │    API    │    Web UI    │    Email    │    Slack    │  SDK    │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## XBRL Integration Approach

Since you have a separate XBRL project, here's how to integrate:

```python
# =============================================================================
# OPTION 1: XBRL as a FeedSpine Adapter
# =============================================================================

class XBRLFeedAdapter(BaseFeedAdapter):
    """
    Treat your XBRL database as a feed source.

    Pros:
    - Uses existing FeedSpine infrastructure
    - Gets change detection for free
    - Sightings track when data was ingested

    Cons:
    - May not need full FeedSpine overhead for internal data
    """

    def __init__(self, xbrl_db_connection: str):
        self.conn = xbrl_db_connection

    async def fetch(self) -> AsyncIterator[RecordCandidate]:
        """Pull new/changed facts from XBRL database."""
        # Query your XBRL database for recent facts
        facts = await self._query_new_facts()

        for fact in facts:
            yield RecordCandidate(
                natural_key=f"{fact.entity_cik}:{fact.concept}:{fact.period}",
                published_at=fact.filed_date,
                content={
                    "concept": fact.concept,
                    "value": fact.value,
                    "period": fact.period,
                    # ...
                },
            )


# =============================================================================
# OPTION 2: Direct Service Integration
# =============================================================================

class XBRLService:
    """
    Direct integration with your XBRL project.

    Pros:
    - Simpler architecture
    - Direct queries without adapter overhead

    Cons:
    - Need to implement change detection separately
    """

    def __init__(
        self,
        fabric: "EntityFabric",
        xbrl_db_path: str,
    ):
        self.fabric = fabric
        self.xbrl_db = self._connect(xbrl_db_path)

    async def get_financials(
        self,
        entity_id: str,
        years: int = 5,
    ) -> list[FinancialStatement]:
        """Get financials, resolving entity_id to CIK."""
        entity = await self.fabric.get_entity(entity_id)
        cik = entity.identifiers.get("cik")

        if not cik:
            raise ValueError(f"Entity {entity_id} has no CIK")

        # Query your XBRL database
        return await self.xbrl_db.get_statements(cik=cik, years=years)


# =============================================================================
# OPTION 3: Shared Database (Ideal Long-Term)
# =============================================================================

# If both projects use the same database schema:

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SHARED DATABASE SCHEMA                               │
│                                                                              │
│  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐        │
│  │   entities    │───────▶│    filings    │───────▶│  xbrl_facts   │        │
│  │               │        │               │        │               │        │
│  │ entity_id     │        │ accession_num │        │ fact_id       │        │
│  │ cik           │        │ entity_id     │        │ filing_id     │        │
│  │ name          │        │ form_type     │        │ concept       │        │
│  │ identifiers   │        │ filed_date    │        │ value         │        │
│  └───────────────┘        └───────────────┘        │ period        │        │
│         │                                          └───────────────┘        │
│         │                                                                    │
│         ▼                                                                    │
│  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐        │
│  │   signals     │        │  analysts     │        │   holdings    │        │
│  │               │        │               │        │               │        │
│  │ signal_id     │        │ analyst_id    │        │ holding_id    │        │
│  │ entity_id     │        │ firm_id       │        │ entity_id     │        │
│  │ signal_type   │        │ coverage      │        │ holder_id     │        │
│  └───────────────┘        └───────────────┘        └───────────────┘        │
│                                                                              │
│  py-sec-edgar owns: entities, signals, analysts, holdings                    │
│  XBRL project owns: filings, xbrl_facts                                      │
│  Both can read everything                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""
```

---

## Summary: What Was Missing

| Category | What's Missing | Why It Matters |
|----------|---------------|----------------|
| **Financial Data** | XBRL integration, statements, segments | Can't analyze without the numbers |
| **Corporate Actions** | Splits, dividends, M&A, delistings | Timeline accuracy, price adjustments |
| **Reference Data** | Exchanges, industries, currencies | Standardized lookups, classification |
| **Market Data** | Prices, returns, valuations | Can't compute multiples without prices |
| **Calendars** | Earnings dates, dividends, deadlines | Know when things happen |
| **Documents** | Full-text, exhibits, attachments | The actual content |
| **Derived Metrics** | Ratios, growth, peer comparison | Analysis-ready data |
| **Data Quality** | Validation, reconciliation | Trust the data |
| **Alerts** | Real-time notifications | Timely action |

---

*EntitySpine Universal Fabric v2.0 | January 2026*
