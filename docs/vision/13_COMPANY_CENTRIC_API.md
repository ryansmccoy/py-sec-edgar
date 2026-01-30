# 13. Company-Centric API Design

> **Updated 2026-01-27**:
> - See [14_V4_MASTER_ROADMAP.md](14_V4_MASTER_ROADMAP.md) for implementation status
> - See [15_DATA_MODEL_REFERENCE.md](15_DATA_MODEL_REFERENCE.md) for Company model definition
> - QueryService now provides cached SEC API access for company lookups
> - Unified feeds (FeedSpine) + Direct APIs (QueryService) work together

## Vision

Transform py-sec-edgar from a "filing downloader" into a **company research platform** where users work with rich company objects that automatically populate metadata, provide filing access, and scale storage based on user needs.

```python
# The Dream API
async with SEC() as sec:
    # Get company object (auto-populates from SEC data)
    apple = await sec.company("AAPL")

    # Rich metadata available immediately
    print(f"{apple.name}: {apple.ticker} (CIK: {apple.cik})")
    print(f"Industry: {apple.sic_description}")
    print(f"State: {apple.state_of_incorporation}")

    # Access filings through the company
    filings = await apple.filings(forms=["10-K", "10-Q"], limit=10)
    filings.display()  # Pretty table output

    # Get latest 10-K and auto-extract metadata
    latest_10k = await apple.latest("10-K")
    await latest_10k.enrich()  # Populates from filing header

    # Now apple has enriched data
    print(f"Fiscal Year End: {apple.fiscal_year_end}")
    print(f"Business Address: {apple.business_address}")
    print(f"Executives: {apple.executives}")  # From DEF 14A
```

## Architecture Decision: Unified Feeds + Direct APIs

The company-centric API is powered by two complementary data acquisition strategies:

| Approach | Implementation | Use Case |
|----------|---------------|----------|
| **Unified Feeds** | FeedSpine + SEC RSS/Index | Real-time monitoring, completeness |
| **Direct APIs** | QueryService | Targeted lookups, backfill |

```python
# Behind the scenes: sec.company() uses both approaches
async def company(self, identifier: str) -> Company:
    # 1. Resolve identifier via EntitySpine
    entity = await self.entity_spine.resolve(identifier)

    # 2. Check Bronze layer (FeedSpine) for known filings
    sightings = await self.bronze.query(cik=entity.cik)

    # 3. Use QueryService for fresh/detailed data
    submissions = await self.query_service.submissions.get(entity.cik)

    # 4. Return rich Company object
    return Company(
        cik=entity.cik,
        entity_id=entity.entity_id,
        name=submissions.name,
        ...
    )
```

---

## SEC Company Data: Version-Controlled Ingestion

### The Data Sources

SEC provides two key files that we ingest to populate the initial company universe:

| File | URL | Fields | Use Case |
|------|-----|--------|----------|
| `company_tickers.json` | `https://www.sec.gov/files/company_tickers.json` | CIK, ticker, name | Basic resolution |
| `company_tickers_exchange.json` | `https://www.sec.gov/files/company_tickers_exchange.json` | CIK, ticker, name, **exchange** | Full entity model |

### Real-World Change Analysis (2019 → 2025)

We analyzed 6 years of SEC company data to understand the scope of changes:

```
======================================================================
CHANGE ANALYSIS: 2019-10-12 -> 2025-09-13 (6 years)
======================================================================

Old version: 11,340 companies
New version:  7,878 companies
Net change:  -3,462

--- SUMMARY ---
Companies added:     4,083  (new IPOs, SPACs, etc.)
Companies removed:   7,545  (mergers, delistings, bankruptcies)
Ticker changes:      1,147  (rebrands, restructurings)
Name changes:          667  (corporate name changes)
```

### Notable Changes Detected

**Ticker Changes:**
```
CDSI     -> SGBX     | SAFE & GREEN HOLDINGS CORP.
HSGX     -> OCGN     | Ocugen, Inc.
NUOT     -> AURX     | Nuo Therapeutics, Inc.
PWVI     -> SCWO     | 374Water Inc.
```

**Name Changes (Major Rebrands):**
```
[MOMO  ] Momo Inc.                 -> Hello Group Inc.
[FFIV  ] F5 NETWORKS, INC.         -> F5, INC.
[RRX   ] REGAL BELOIT CORP         -> REGAL REXNORD CORP
[OCGN  ] HISTOGENICS CORP          -> Ocugen, Inc.
```

**Removed Companies (M&A, Delistings):**
```
- AABA     | ALTABA INC. (Yahoo spinoff, dissolved)
- AAI      | AIRTRAN HOLDINGS INC (acquired by Southwest)
- AAN      | AARON'S INC (restructured)
```

### Version Control Design

```python
# Ingestion with version tracking
async with SEC() as sec:
    # Download latest SEC company data
    result = await sec.sync_companies()

    # See what changed since last sync
    print(f"New companies: {result.added}")
    print(f"Removed: {result.removed}")
    print(f"Ticker changes: {result.ticker_changes}")
    print(f"Name changes: {result.name_changes}")

    # Query historical state
    apple_2020 = await sec.company("AAPL", as_of="2020-01-01")

    # Track a company's identity over time
    history = await sec.company_history("OCGN")
    # Returns: HISTOGENICS CORP (2019) -> Ocugen, Inc. (2020+)
```

### Daily Change Velocity

Even day-to-day changes are significant:

```
--- ANALYSIS: Sept 6 vs Sept 7 (1 day) ---
CIKs removed: 162  (delistings, name changes, etc.)
CIKs added:   163  (new listings, corrections, etc.)

Sample REMOVED in one day:
  - DAVI     | Davion Healthcare PLC
  - SEV      | Aptera Motors Corp
  - BDCI     | BTC Development Corp.

Sample ADDED in one day:
  + AFIB     | Acutus Medical, Inc.
  + CRGX     | CARGO Therapeutics, Inc.
  + EVOY     | Envoy Technologies, Inc.
```

This ~160+ daily change rate means version control is essential for accurate entity tracking.

### Storage Schema for Version Control

```sql
-- Company snapshots with temporal tracking
CREATE TABLE company_snapshots (
    id INTEGER PRIMARY KEY,
    cik VARCHAR NOT NULL,
    ticker VARCHAR,
    name VARCHAR NOT NULL,
    exchange VARCHAR,
    sic_code VARCHAR,

    -- Temporal fields
    valid_from DATE NOT NULL,
    valid_to DATE,  -- NULL = current
    snapshot_date DATE NOT NULL,  -- When this was captured
    source_file VARCHAR,  -- e.g., "company_tickers_2025-09-13.json"

    -- Change tracking
    change_type VARCHAR,  -- 'added', 'removed', 'ticker_change', 'name_change'
    previous_ticker VARCHAR,
    previous_name VARCHAR,

    UNIQUE(cik, valid_from)
);

-- Index for point-in-time queries
CREATE INDEX idx_company_temporal ON company_snapshots(cik, valid_from, valid_to);
```

### Test Data Available

We have version-controlled test data ready for development:

```
test_data/company_tickers_versions/
├── company_tickers_2019-10-12.json      # 11,340 companies (6 years ago)
├── company_tickers_2025-07-26.json      #  7,878 companies
├── company_tickers_2025-09-05.json      #  7,878 companies
├── company_tickers_2025-09-07.json      #  7,878 companies
├── company_tickers_2025-09-13.json      #  7,878 companies
├── company_tickers_exchange_2025-07-26.json  # With exchange info
├── company_tickers_exchange_2025-09-05.json
├── company_tickers_exchange_2025-09-06.json  # 10,116 entries
├── company_tickers_exchange_2025-09-07.json  # 10,089 entries
├── analyze_changes.py                    # Basic comparison script
└── company_version_control.py            # Full version control module
```

---

## Current State Analysis

### What We Have

| Component | Status | Location |
|-----------|--------|----------|
| EntityRegistry | ✅ Built | `core/identity/registry.py` |
| Entity model | ✅ Built | `core/identity/entity.py` |
| Ticker→CIK resolution | ✅ Built | `EntityRegistry.resolve_ticker()` |
| Filing download | ✅ Built | `SEC.download()`, `SECFeedCollector` |
| Section extraction | ✅ Built | `SEC.extract()` |
| DuckDB storage | ✅ Built | `storage/duckdb_extraction.py` |
| FeedSpine integration | ✅ Built | `services/collector.py` |
| **Version control test data** | ✅ Ready | `test_data/company_tickers_versions/` |
| **Change detection module** | ✅ Ready | `company_version_control.py` |

### What's Missing

| Feature | Priority | Complexity |
|---------|----------|------------|
| `Company` class wrapper | P0 | Medium |
| Filing header parser | P0 | Low |
| Company→Filings navigation | P0 | Low |
| Auto-enrichment workflow | P1 | Medium |
| Tiered storage abstraction | P1 | Medium |
| Pretty table display | P2 | Low |
| Executive extraction (DEF 14A) | P3 | High |

---

## Architecture

### Tier System

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User's py-sec-edgar                         │
├─────────────────────────────────────────────────────────────────────┤
│  Tier 0: In-Memory      │ No persistence, just resolution          │
│  Tier 1: SQLite/DuckDB  │ Basic metadata + filing inventory        │
│  Tier 2: PostgreSQL     │ Full metadata + relationships            │
│  Tier 3: Knowledge Graph│ EntitySpine integration                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User: sec.company("AAPL")
         │
         ▼
┌─────────────────────────┐
│  1. EntityRegistry      │  ← Resolve ticker to CIK
│     resolve_ticker()    │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  2. CompanyStore        │  ← Check if company exists in DB
│     get_by_cik()        │
└─────────────────────────┘
         │
    ┌────┴────┐
    │ Found?  │
    └────┬────┘
     No  │  Yes
         │    └──────────────────┐
         ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│  3. SEC Data API        │  │  Return cached Company  │
│     Fetch basic info    │  └─────────────────────────┘
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  4. Create Company      │
│     Store in DB         │
└─────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│  5. Return Company obj  │  ← Rich object with methods
└─────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Company Class (P0)

#### 1.1 Create `Company` Model

**File:** `py_sec_edgar/src/py_sec_edgar/models/company.py`

```python
"""Company model - rich entity for company-centric workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from py_sec_edgar.sec import SEC

@dataclass
class Address:
    """Physical address."""
    street1: str = ""
    street2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "US"

    def __str__(self) -> str:
        parts = [self.street1]
        if self.street2:
            parts.append(self.street2)
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return "\n".join(parts)


@dataclass
class Company:
    """Rich company object with filing access.

    This is the primary interface for company-centric workflows.
    Users get a Company object and can navigate to filings, metadata,
    and related entities through it.

    Example:
        >>> apple = await sec.company("AAPL")
        >>> print(apple.name)
        Apple Inc.
        >>> filings = await apple.filings(forms=["10-K"])
        >>> latest = await apple.latest("10-K")
    """

    # Core identifiers
    cik: str
    ticker: Optional[str] = None
    name: str = ""

    # SEC metadata (from company_tickers.json)
    sic_code: Optional[str] = None
    sic_description: Optional[str] = None
    exchange: Optional[str] = None

    # Enriched metadata (from filing headers)
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None  # MMDD format
    business_address: Optional[Address] = None
    mailing_address: Optional[Address] = None
    phone: Optional[str] = None

    # Former names (from filing headers)
    former_names: List[dict] = field(default_factory=list)

    # Internal references
    _sec: Optional["SEC"] = field(default=None, repr=False)
    _enriched: bool = field(default=False, repr=False)
    _filing_cache: dict = field(default_factory=dict, repr=False)

    # =========================================================================
    # FILING ACCESS
    # =========================================================================

    async def filings(
        self,
        forms: Optional[List[str]] = None,
        limit: int = 20,
        include_amendments: bool = False,
    ) -> "FilingList":
        """Get filings for this company.

        Args:
            forms: Filter by form types (e.g., ["10-K", "10-Q"])
            limit: Maximum filings to return
            include_amendments: Include amendment forms (10-K/A, etc.)

        Returns:
            FilingList with display and iteration methods
        """
        if not self._sec:
            raise RuntimeError("Company not connected to SEC context")

        raw_filings = await self._sec.get_company_filings(
            cik=self.cik,
            forms=forms,
            limit=limit,
        )

        return FilingList(raw_filings, company=self)

    async def latest(self, form: str = "10-K") -> Optional["Filing"]:
        """Get the latest filing of a specific type.

        Args:
            form: Form type (default: "10-K")

        Returns:
            Most recent Filing of that type, or None
        """
        filings = await self.filings(forms=[form], limit=1)
        return filings[0] if filings else None

    async def annual_reports(self, limit: int = 5) -> "FilingList":
        """Get recent 10-K filings."""
        return await self.filings(forms=["10-K"], limit=limit)

    async def quarterly_reports(self, limit: int = 10) -> "FilingList":
        """Get recent 10-Q filings."""
        return await self.filings(forms=["10-Q"], limit=limit)

    async def current_reports(self, limit: int = 20) -> "FilingList":
        """Get recent 8-K filings."""
        return await self.filings(forms=["8-K"], limit=limit)

    # =========================================================================
    # ENRICHMENT
    # =========================================================================

    async def enrich(self, from_filing: Optional[str] = None) -> "Company":
        """Enrich company data from filing headers.

        Fetches the latest 10-K (or specified filing) and extracts
        metadata from the SGML header to populate additional fields.

        Args:
            from_filing: Specific accession number to use (default: latest 10-K)

        Returns:
            Self for chaining
        """
        if not self._sec:
            raise RuntimeError("Company not connected to SEC context")

        # Get the filing to enrich from
        if from_filing:
            filing = await self._sec.get_filing(from_filing)
        else:
            filing = await self.latest("10-K")

        if not filing:
            return self

        # Parse header and update fields
        header = await self._sec._parse_filing_header(filing)
        if header:
            self._apply_header(header)
            self._enriched = True

        return self

    def _apply_header(self, header: dict) -> None:
        """Apply parsed header data to company fields."""
        if header.get("state_of_incorporation"):
            self.state_of_incorporation = header["state_of_incorporation"]
        if header.get("fiscal_year_end"):
            self.fiscal_year_end = header["fiscal_year_end"]
        if header.get("business_address"):
            self.business_address = Address(**header["business_address"])
        if header.get("mailing_address"):
            self.mailing_address = Address(**header["mailing_address"])
        if header.get("phone"):
            self.phone = header["phone"]
        if header.get("former_names"):
            self.former_names = header["former_names"]

    # =========================================================================
    # DISPLAY
    # =========================================================================

    def display(self) -> None:
        """Print a formatted summary of the company."""
        print(f"\n{'='*60}")
        print(f"  {self.name}")
        print(f"{'='*60}")
        print(f"  Ticker: {self.ticker or 'N/A'}")
        print(f"  CIK:    {self.cik}")
        print(f"  SIC:    {self.sic_code} - {self.sic_description or 'N/A'}")

        if self._enriched:
            print(f"\n  State of Inc: {self.state_of_incorporation}")
            print(f"  Fiscal Year:  {self.fiscal_year_end}")
            if self.business_address:
                print(f"\n  Business Address:")
                for line in str(self.business_address).split("\n"):
                    print(f"    {line}")
        else:
            print(f"\n  [Not enriched - call company.enrich() for more details]")
        print()

    def __repr__(self) -> str:
        return f"Company({self.ticker or self.cik}: {self.name})"


@dataclass
class FilingList:
    """List of filings with display and navigation methods."""

    _filings: List["Filing"]
    company: Optional[Company] = None

    def __len__(self) -> int:
        return len(self._filings)

    def __iter__(self):
        return iter(self._filings)

    def __getitem__(self, idx):
        return self._filings[idx]

    def display(self, show_downloaded: bool = True) -> None:
        """Print a formatted table of filings."""
        if not self._filings:
            print("No filings found.")
            return

        header = f"{'Date':<12} {'Form':<10} {'Accession':<25} {'Downloaded':<10}"
        print(f"\n{header}")
        print("-" * len(header))

        for f in self._filings:
            downloaded = "✓" if f.is_downloaded else ""
            print(f"{f.filed_date!s:<12} {f.form_type:<10} {f.accession_number!s:<25} {downloaded:<10}")

        print(f"\nTotal: {len(self._filings)} filings")
```

#### 1.2 Add `sec.company()` Method

**File:** `py_sec_edgar/src/py_sec_edgar/sec.py` (add method)

```python
async def company(
    self,
    identifier: str,
    enrich: bool = False,
) -> Company:
    """Get a Company object by ticker, CIK, or name.

    This is the primary entry point for company-centric workflows.
    Returns a rich Company object with methods to access filings,
    metadata, and related entities.

    Args:
        identifier: Ticker (AAPL), CIK (320193), or company name
        enrich: Auto-enrich from latest 10-K (default: False)

    Returns:
        Company object with filing access methods

    Example:
        >>> apple = await sec.company("AAPL")
        >>> apple.display()
        >>> filings = await apple.filings(forms=["10-K"])
        >>> filings.display()
    """
    self._ensure_initialized()

    # Resolve identifier to entity
    entity = self.resolve_entity(identifier)
    if not entity:
        raise ValueError(f"Could not resolve '{identifier}' to a company")

    # Check company store first
    company = await self._company_store.get_by_cik(entity.cik)

    if not company:
        # Create new company from entity
        company = Company(
            cik=entity.cik,
            ticker=entity.ticker,
            name=entity.primary_name,
            sic_code=entity.sic_code,
            exchange=entity.exchange,
            _sec=self,
        )

        # Store it
        await self._company_store.save(company)
    else:
        # Reconnect to SEC context
        company._sec = self

    # Optional auto-enrichment
    if enrich and not company._enriched:
        await company.enrich()

    return company
```

---

### Phase 2: Filing Header Parser (P0)

#### 2.1 SGML Header Parser

**File:** `py_sec_edgar/src/py_sec_edgar/extractor/header_parser.py`

```python
"""Parse SEC filing SGML headers for company metadata."""

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

@dataclass
class FilingHeader:
    """Parsed SEC filing header."""

    # Filing info
    accession_number: str
    form_type: str
    filed_date: Optional[date] = None

    # Filer info
    cik: str = ""
    company_name: str = ""

    # Company details
    sic_code: Optional[str] = None
    sic_description: Optional[str] = None
    state_of_incorporation: Optional[str] = None
    fiscal_year_end: Optional[str] = None

    # Addresses
    business_address: Optional[Dict[str, str]] = None
    mailing_address: Optional[Dict[str, str]] = None

    # Contact
    phone: Optional[str] = None

    # Historical
    former_names: list = None


class FilingHeaderParser:
    """Parse SGML headers from SEC filings."""

    def parse(self, content: str) -> FilingHeader:
        """Parse filing content and extract header metadata.

        Args:
            content: Raw filing content (complete-submission.txt)

        Returns:
            FilingHeader with extracted metadata
        """
        # Extract SEC-HEADER section
        header_match = re.search(
            r'<SEC-HEADER>(.*?)</SEC-HEADER>',
            content,
            re.DOTALL | re.IGNORECASE
        )

        if not header_match:
            # Try alternate format
            header_match = re.search(
                r'<IMS-HEADER>(.*?)</IMS-HEADER>',
                content,
                re.DOTALL | re.IGNORECASE
            )

        header_text = header_match.group(1) if header_match else content[:5000]

        return FilingHeader(
            accession_number=self._extract("ACCESSION NUMBER", header_text) or "",
            form_type=self._extract("FORM TYPE", header_text) or "",
            filed_date=self._extract_date("FILED AS OF DATE", header_text),
            cik=self._extract("CENTRAL INDEX KEY", header_text) or "",
            company_name=self._extract("COMPANY CONFORMED NAME", header_text) or "",
            sic_code=self._extract("STANDARD INDUSTRIAL CLASSIFICATION", header_text),
            state_of_incorporation=self._extract("STATE OF INCORPORATION", header_text),
            fiscal_year_end=self._extract("FISCAL YEAR END", header_text),
            business_address=self._extract_address("BUSINESS ADDRESS", header_text),
            mailing_address=self._extract_address("MAIL ADDRESS", header_text),
            phone=self._extract("BUSINESS PHONE", header_text),
            former_names=self._extract_former_names(header_text),
        )

    def _extract(self, field: str, text: str) -> Optional[str]:
        """Extract a single field value."""
        pattern = rf'{field}[:\s]+([^\n<]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_date(self, field: str, text: str) -> Optional[date]:
        """Extract and parse a date field."""
        value = self._extract(field, text)
        if value and len(value) == 8:
            try:
                return date(int(value[:4]), int(value[4:6]), int(value[6:8]))
            except ValueError:
                pass
        return None

    def _extract_address(self, section: str, text: str) -> Optional[Dict[str, str]]:
        """Extract address fields from a section."""
        # Find the address section
        pattern = rf'{section}[:\s]*(.*?)(?=\n\t[A-Z]|\n[A-Z]{{2,}}|$)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if not match:
            return None

        addr_text = match.group(1)

        return {
            "street1": self._extract("STREET 1", addr_text) or "",
            "street2": self._extract("STREET 2", addr_text) or "",
            "city": self._extract("CITY", addr_text) or "",
            "state": self._extract("STATE", addr_text) or "",
            "zip": self._extract("ZIP", addr_text) or "",
        }

    def _extract_former_names(self, text: str) -> list:
        """Extract former company names."""
        former = []
        pattern = r'FORMER COMPANY[:\s]*(.*?)(?=FORMER COMPANY|FILER:|$)'

        for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
            name_text = match.group(1)
            name = self._extract("FORMER CONFORMED NAME", name_text)
            date_str = self._extract("DATE OF NAME CHANGE", name_text)

            if name:
                former.append({
                    "name": name,
                    "date": date_str,
                })

        return former
```

---

### Phase 3: Company Storage (P1)

#### 3.1 Storage Interface

**File:** `py_sec_edgar/src/py_sec_edgar/storage/company_store.py`

```python
"""Company storage with tiered backends."""

from abc import ABC, abstractmethod
from typing import List, Optional

from py_sec_edgar.models.company import Company


class CompanyStore(ABC):
    """Abstract interface for company storage."""

    @abstractmethod
    async def get_by_cik(self, cik: str) -> Optional[Company]:
        """Get company by CIK."""
        pass

    @abstractmethod
    async def get_by_ticker(self, ticker: str) -> Optional[Company]:
        """Get company by ticker."""
        pass

    @abstractmethod
    async def save(self, company: Company) -> None:
        """Save or update a company."""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Company]:
        """Search companies by name."""
        pass


class DuckDBCompanyStore(CompanyStore):
    """DuckDB implementation for Tier 1 storage."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._conn = None

    async def initialize(self) -> None:
        """Create tables if needed."""
        import duckdb
        self._conn = duckdb.connect(self._db_path)

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                cik VARCHAR PRIMARY KEY,
                ticker VARCHAR,
                name VARCHAR,
                sic_code VARCHAR,
                sic_description VARCHAR,
                exchange VARCHAR,
                state_of_incorporation VARCHAR,
                fiscal_year_end VARCHAR,
                business_address JSON,
                mailing_address JSON,
                phone VARCHAR,
                former_names JSON,
                enriched BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON companies(ticker)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON companies(name)")

    async def get_by_cik(self, cik: str) -> Optional[Company]:
        """Get company by CIK."""
        cik_padded = cik.zfill(10)
        result = self._conn.execute(
            "SELECT * FROM companies WHERE cik = ?",
            [cik_padded]
        ).fetchone()

        if result:
            return self._row_to_company(result)
        return None

    # ... other methods
```

---

### Phase 4: Example Workflows (P2)

#### 4.1 Basic Company Lookup

```python
"""Example: Basic company lookup and filing access."""

import asyncio
from py_sec_edgar import SEC

async def main():
    async with SEC() as sec:
        # Get Apple
        apple = await sec.company("AAPL")
        apple.display()

        # Get filings
        filings = await apple.filings(forms=["10-K", "10-Q"], limit=10)
        filings.display()

        # Download latest 10-K
        latest = await apple.latest("10-K")
        if latest:
            path = await sec.download_filing(latest)
            print(f"Downloaded to: {path}")

asyncio.run(main())
```

#### 4.2 Enriched Company Data

```python
"""Example: Enrich company from 10-K header."""

import asyncio
from py_sec_edgar import SEC

async def main():
    async with SEC() as sec:
        # Get and enrich Apple
        apple = await sec.company("AAPL", enrich=True)

        # Now we have detailed info
        print(f"Company: {apple.name}")
        print(f"State: {apple.state_of_incorporation}")
        print(f"Fiscal Year End: {apple.fiscal_year_end}")
        print(f"Phone: {apple.phone}")

        if apple.business_address:
            print(f"\nBusiness Address:")
            print(apple.business_address)

        if apple.former_names:
            print(f"\nFormer Names:")
            for fn in apple.former_names:
                print(f"  - {fn['name']} (changed: {fn['date']})")

asyncio.run(main())
```

#### 4.3 Multi-Company Comparison

```python
"""Example: Compare filings across companies."""

import asyncio
from py_sec_edgar import SEC

async def main():
    async with SEC() as sec:
        # Get tech giants
        companies = await asyncio.gather(
            sec.company("AAPL"),
            sec.company("MSFT"),
            sec.company("GOOGL"),
            sec.company("AMZN"),
        )

        print(f"{'Company':<30} {'Ticker':<8} {'SIC':<6} {'State'}")
        print("-" * 60)

        for c in companies:
            await c.enrich()
            print(f"{c.name:<30} {c.ticker:<8} {c.sic_code or 'N/A':<6} {c.state_of_incorporation or 'N/A'}")

asyncio.run(main())
```

---

## Tiered Feature Matrix

| Feature | Tier 0 (Memory) | Tier 1 (DuckDB) | Tier 2 (Postgres) | Tier 3 (EntitySpine) |
|---------|-----------------|-----------------|-------------------|----------------------|
| Ticker resolution | ✅ | ✅ | ✅ | ✅ |
| Basic company info | ✅ | ✅ | ✅ | ✅ |
| Filing access | ✅ | ✅ | ✅ | ✅ |
| Enriched metadata | ❌ | ✅ | ✅ | ✅ |
| Company persistence | ❌ | ✅ | ✅ | ✅ |
| Former names history | ❌ | ✅ | ✅ | ✅ |
| **Version control** | ❌ | ✅ | ✅ | ✅ |
| **Change detection** | ❌ | ✅ | ✅ | ✅ |
| Point-in-time queries | ❌ | ❌ | ✅ | ✅ |
| Subsidiary tracking | ❌ | ❌ | ✅ | ✅ |
| Executive/officer data | ❌ | ❌ | ✅ | ✅ |
| Relationship graph | ❌ | ❌ | ❌ | ✅ |
| Cross-company links | ❌ | ❌ | ❌ | ✅ |
| Timeline/history | ❌ | ❌ | ❌ | ✅ |

---

## Implementation Checklist

### P0 - Core (Must Have)

- [ ] Create `Company` dataclass model
- [ ] Create `FilingList` with display methods
- [ ] Add `SEC.company()` method
- [ ] Create `FilingHeaderParser`
- [ ] Add `Company.enrich()` method
- [ ] Create `DuckDBCompanyStore`
- [ ] Wire into `SEC.__aenter__`

### P0.5 - SEC Data Ingestion (Must Have)

- [ ] Download `company_tickers.json` from SEC
- [ ] Download `company_tickers_exchange.json` from SEC
- [ ] Parse and normalize both formats
- [ ] Populate EntityRegistry from SEC data
- [ ] Store snapshot with timestamp
- [ ] Create `SEC.sync_companies()` method

### P1 - Version Control (Should Have)

- [ ] Compare current vs previous snapshot
- [ ] Detect new companies (added)
- [ ] Detect removed companies (delisted/merged)
- [ ] Detect ticker changes
- [ ] Detect name changes
- [ ] Generate change report
- [ ] Store change history in DB
- [ ] Add `SEC.company_changes()` method

### P1 - Enhanced (Should Have)

- [ ] Add `Company.filings()` filtering
- [ ] Add `Company.latest()` method
- [ ] Add `Company.annual_reports()` shortcut
- [ ] Add `Company.quarterly_reports()` shortcut
- [ ] Add `Company.current_reports()` shortcut
- [ ] Add caching for company objects
- [ ] Add filing download status tracking

### P2 - Polish (Nice to Have)

- [ ] Pretty table output (rich library)
- [ ] Progress bars for bulk operations
- [ ] Export to JSON/CSV
- [ ] Interactive mode support
- [ ] Point-in-time company queries (`as_of` parameter)
- [ ] Company history timeline

### P3 - Advanced (Future)

- [ ] DEF 14A executive extraction
- [ ] Exhibit 21 subsidiary extraction
- [ ] PostgreSQL backend
- [ ] EntitySpine integration
- [ ] Relationship graph building

---

## Integration with EntitySpine

When user has EntitySpine installed, the Company object can delegate to EntitySpine's richer models:

```python
# With EntitySpine (Tier 3)
async with SEC(tier="entityspine") as sec:
    apple = await sec.company("AAPL")

    # EntitySpine features become available
    subsidiaries = await apple.subsidiaries()
    executives = await apple.executives()

    # Graph traversal
    suppliers = await apple.relationships(type="SUPPLIER")
    customers = await apple.relationships(type="CUSTOMER")

    # Timeline
    history = await apple.timeline()
    for event in history:
        print(f"{event.date}: {event.description}")
```

This is handled by swapping the `Company` implementation based on tier:

```python
class SEC:
    def __init__(self, tier: str = "duckdb"):
        if tier == "entityspine":
            from py_sec_edgar.integrations.entityspine import EntitySpineCompany
            self._company_class = EntitySpineCompany
        else:
            from py_sec_edgar.models.company import Company
            self._company_class = Company
```

---

## FeedSpine + EntitySpine: Dual-Spine Architecture

### Why Two Spines?

The company data workflow naturally separates into two concerns:

| Concern | Owner | Responsibility |
|---------|-------|----------------|
| **Collection & Deduplication** | FeedSpine | Ingest SEC data feeds, track sightings, handle duplicates |
| **Entity Resolution & Relationships** | EntitySpine | Resolve identities, model corporate structure, build knowledge graph |

```
                        SEC Data Sources
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FeedSpine (Collection Layer)                     │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ company_tickers │  │ full-index.idx  │  │  Daily RSS      │         │
│  │   .json feed    │  │  quarterly feed │  │   10-K/10-Q     │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                   │
│           └────────────────────┼────────────────────┘                   │
│                                ▼                                        │
│                    ┌─────────────────────┐                              │
│                    │   Deduplication     │  natural_key = f"{cik}:{acc}"│
│                    │   Sighting History  │  "Same filing seen in 3 feeds"│
│                    └──────────┬──────────┘                              │
│                               │                                         │
│                    ┌──────────▼──────────┐                              │
│                    │   Bronze → Silver   │  Raw → Validated → Enriched │
│                    │   Medallion Layers  │                              │
│                    └──────────┬──────────┘                              │
└───────────────────────────────┼─────────────────────────────────────────┘
                                │
                                ▼  "Hand off deduplicated records"
┌─────────────────────────────────────────────────────────────────────────┐
│                       EntitySpine (Entity Layer)                         │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                     Entity Resolution                           │    │
│   │  "AAPL" → CIK 0000320193 → Entity(Apple Inc.)                  │    │
│   │  "Facebook" → "Meta Platforms" (name change tracked)            │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                │                                         │
│   ┌────────────────────────────▼────────────────────────────────────┐   │
│   │                    Knowledge Graph                               │   │
│   │                                                                  │   │
│   │  ┌─────────┐    SUBSIDIARY    ┌─────────────────┐               │   │
│   │  │ Alphabet├───────────────►│ Google LLC       │               │   │
│   │  │  Inc.   │                 │                  │               │   │
│   │  └────┬────┘                 └──────────────────┘               │   │
│   │       │ SUBSIDIARY                                              │   │
│   │       ▼                                                         │   │
│   │  ┌──────────────────┐                                           │   │
│   │  │ YouTube, LLC      │                                          │   │
│   │  └──────────────────┘                                           │   │
│   │                                                                  │   │
│   └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### FeedSpine's Role: Collection & Deduplication

FeedSpine handles the **data collection problem**:

```python
from feedspine import FeedSpine, DuckDBStorage
from feedspine.models import Record, Sighting

# SEC company tickers as a FeedSpine feed
class SECCompanyTickersFeed:
    """Collect SEC company_tickers.json as a feed."""

    name = "sec-company-tickers"
    url = "https://www.sec.gov/files/company_tickers_exchange.json"

    def parse(self, raw_data: bytes) -> list[Record]:
        """Parse SEC JSON into FeedSpine records."""
        data = json.loads(raw_data)
        records = []

        for row in data["data"]:
            cik, name, ticker, exchange = row
            records.append(Record(
                # Natural key for deduplication
                natural_key=f"sec:company:{cik}",

                # Metadata
                content={
                    "cik": str(cik).zfill(10),
                    "name": name,
                    "ticker": ticker,
                    "exchange": exchange,
                },
                source_feed=self.name,
                captured_at=datetime.utcnow(),
            ))

        return records

# Run collection
async with FeedSpine(storage=DuckDBStorage("feeds.db")) as spine:
    spine.register_feed(SECCompanyTickersFeed())

    result = await spine.collect()

    # FeedSpine tracks sightings automatically
    # "This company was seen in 5 different snapshots"
    print(f"New companies: {result.total_new}")
    print(f"Updated: {result.total_updated}")
    print(f"Unchanged (deduped): {result.total_duplicates}")
```

**Key FeedSpine Features Used:**

| Feature | Purpose |
|---------|---------|
| `natural_key` | Deduplication: `sec:company:{cik}` ensures one record per CIK |
| `Sighting` | Track when/where we saw each company (temporal audit trail) |
| `Bronze → Silver` | Raw SEC data → Validated/normalized data |
| Batch processing | Efficient handling of ~14,000 companies per snapshot |

### EntitySpine's Role: Resolution & Relationships

EntitySpine handles the **entity identity problem**:

```python
from entityspine import SqliteStore
from entityspine.domain import Entity, EntityRelationship, RelationshipType

# EntitySpine consumes deduplicated records from FeedSpine
async def ingest_from_feedspine(spine: FeedSpine, entity_store: SqliteStore):
    """Transfer validated company records to EntitySpine."""

    # Get Silver-tier (validated) records from FeedSpine
    async for record in spine.storage.query(layer=Layer.SILVER):
        content = record.content

        # Create or update Entity in EntitySpine
        entity = Entity(
            primary_name=content["name"],
            entity_type=EntityType.ORGANIZATION,
            source_system="sec",
            source_id=content["cik"],
        )

        # EntitySpine handles identity resolution
        # "Is this the same company we saw yesterday?"
        await entity_store.upsert_entity(entity)

        # Register identifiers (CIK, ticker)
        await entity_store.add_identifier_claim(
            entity_id=entity.entity_id,
            scheme=IdentifierScheme.CIK,
            value=content["cik"],
        )

        if content.get("ticker"):
            await entity_store.add_ticker_listing(
                entity_id=entity.entity_id,
                ticker=content["ticker"],
                exchange=content.get("exchange"),
            )

# EntitySpine resolves across identifier types
results = entity_store.search_entities("AAPL")       # By ticker
results = entity_store.get_entities_by_cik("0000320193")  # By CIK
```

**Key EntitySpine Features Used:**

| Feature | Purpose |
|---------|---------|
| `Entity` | Canonical identity across all identifier types |
| `IdentifierClaim` | Link CIK, LEI, ticker to same entity |
| `EntityRelationship` | Model parent/subsidiary relationships |
| `PersonRole` | Link executives to companies |
| Redirect/merge | Handle M&A, name changes |

### Change Detection: FeedSpine Detects, EntitySpine Acts

```python
# FeedSpine detects changes between snapshots
async def detect_company_changes(spine: FeedSpine) -> ChangeReport:
    """Compare current and previous SEC snapshots."""

    # Get records from two different sighting dates
    current = await spine.storage.query(
        filters={"captured_at__gte": today}
    )
    previous = await spine.storage.query(
        filters={"captured_at__lt": today, "captured_at__gte": yesterday}
    )

    current_by_cik = {r.content["cik"]: r for r in current}
    previous_by_cik = {r.content["cik"]: r for r in previous}

    return ChangeReport(
        added=[c for c in current_by_cik if c not in previous_by_cik],
        removed=[c for c in previous_by_cik if c not in current_by_cik],
        ticker_changes=[
            (c, previous_by_cik[c].content["ticker"], current_by_cik[c].content["ticker"])
            for c in current_by_cik
            if c in previous_by_cik
            and current_by_cik[c].content["ticker"] != previous_by_cik[c].content["ticker"]
        ],
    )

# EntitySpine acts on changes
async def apply_changes_to_entities(changes: ChangeReport, entity_store: SqliteStore):
    """Update EntitySpine based on detected changes."""

    for cik in changes.removed:
        # Mark entity as inactive (don't delete - preserve history)
        entity = await entity_store.get_by_source_id("sec", cik)
        if entity:
            await entity_store.update_entity(
                entity.with_update(status=EntityStatus.INACTIVE)
            )

    for cik, old_ticker, new_ticker in changes.ticker_changes:
        entity = await entity_store.get_by_source_id("sec", cik)
        if entity:
            # Add name change to history
            await entity_store.add_identifier_claim(
                entity_id=entity.entity_id,
                scheme=IdentifierScheme.TICKER,
                value=new_ticker,
                valid_from=date.today(),
            )
            # Mark old ticker as superseded
            await entity_store.expire_identifier(
                entity_id=entity.entity_id,
                scheme=IdentifierScheme.TICKER,
                value=old_ticker,
                valid_to=date.today() - timedelta(days=1),
            )
```

---

## Corporate Structure: Exhibit 21 Extraction

### The Data Source: Exhibit 21

Every public company's 10-K includes **Exhibit 21: List of Subsidiaries**. This is a goldmine for corporate structure:

```
EXHIBIT 21.1
SUBSIDIARIES OF ALPHABET INC.

Name                                     State or Country of Incorporation
----                                     ---------------------------------
Google LLC                               Delaware
YouTube, LLC                             Delaware
Waymo LLC                                Delaware
Wing Aviation LLC                        Delaware
Verily Life Sciences LLC                 Delaware
Chronicle Security Holdings, LLC          Delaware
Google Cloud EMEA Limited                Ireland
Google Asia Pacific Pte. Ltd.            Singapore
...
(hundreds more)
```

### Extraction Pipeline

```python
from py_sec_edgar import SEC
from py_sec_edgar.parse import ExhibitExtractor
from entityspine.domain import EntityRelationship, RelationshipType

class Exhibit21Extractor:
    """Extract subsidiary list from 10-K Exhibit 21."""

    async def extract(
        self,
        filing_content: str,
        parent_entity_id: str,
    ) -> list[EntityRelationship]:
        """Extract subsidiaries from Exhibit 21.

        Args:
            filing_content: Complete 10-K submission content
            parent_entity_id: EntitySpine ID of the parent company

        Returns:
            List of SUBSIDIARY relationships
        """
        # 1. Extract Exhibit 21 document from the filing
        exhibit = self._extract_exhibit_21(filing_content)
        if not exhibit:
            return []

        # 2. Parse the subsidiary table
        subsidiaries = self._parse_subsidiary_table(exhibit)

        # 3. Create relationships
        relationships = []
        for sub in subsidiaries:
            # Create or resolve subsidiary entity
            sub_entity = await self._resolve_or_create_entity(sub)

            relationships.append(EntityRelationship(
                source_entity_id=parent_entity_id,  # Alphabet Inc.
                target_entity_id=sub_entity.entity_id,  # Google LLC
                relationship_type=RelationshipType.SUBSIDIARY,
                valid_from=filing.filed_date,
                source_ref=filing.accession_number,
                evidence_snippet=f"Listed in Exhibit 21: {sub['name']}",
                confidence=0.95,  # High confidence - direct disclosure
            ))

        return relationships

    def _extract_exhibit_21(self, content: str) -> str | None:
        """Extract EX-21 document from complete-submission.txt."""
        # Look for <TYPE>EX-21 or EX-21.1
        pattern = r'<TYPE>EX-21[.\d]*\s*\n.*?(?=<TYPE>|</DOCUMENT>|$)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(0) if match else None

    def _parse_subsidiary_table(self, exhibit: str) -> list[dict]:
        """Parse subsidiary names and jurisdictions from exhibit."""
        subsidiaries = []

        # Multiple parsing strategies for different formats
        # Strategy 1: HTML table
        if '<table' in exhibit.lower():
            subsidiaries = self._parse_html_table(exhibit)

        # Strategy 2: Plain text with alignment
        elif '----' in exhibit:
            subsidiaries = self._parse_text_table(exhibit)

        # Strategy 3: Simple line-by-line
        else:
            subsidiaries = self._parse_line_by_line(exhibit)

        return subsidiaries

    def _parse_html_table(self, html: str) -> list[dict]:
        """Parse HTML table format."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        subsidiaries = []
        for row in soup.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                subsidiaries.append({
                    'name': cells[0].get_text(strip=True),
                    'jurisdiction': cells[1].get_text(strip=True),
                })

        return subsidiaries


# Usage in Company workflow
async def populate_corporate_structure(company: Company):
    """Populate subsidiaries from latest 10-K Exhibit 21."""

    # Get latest 10-K
    latest_10k = await company.latest("10-K")
    if not latest_10k:
        return

    # Download complete submission
    content = await latest_10k.download_complete()

    # Extract subsidiaries
    extractor = Exhibit21Extractor()
    relationships = await extractor.extract(
        content,
        parent_entity_id=company.entity_id,
    )

    # Store in EntitySpine
    for rel in relationships:
        await entity_store.add_relationship(rel)

    print(f"Found {len(relationships)} subsidiaries for {company.name}")
```

### Where Each System Fits

```
10-K Filing Download
        │
        ▼
┌───────────────────────────────────────────────┐
│              FeedSpine (Collection)           │
│                                               │
│  • Download filing from SEC                   │
│  • Deduplicate (same filing seen in RSS,      │
│    full-index, etc.)                          │
│  • Store raw filing (Bronze tier)             │
│  • Store parsed metadata (Silver tier)        │
└───────────────────┬───────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────┐
│           py-sec-edgar (Extraction)           │
│                                               │
│  • Extract Exhibit 21 from filing             │
│  • Parse subsidiary table                     │
│  • Normalize names and jurisdictions          │
└───────────────────┬───────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────┐
│         EntitySpine (Entity Resolution)       │
│                                               │
│  • Resolve each subsidiary:                   │
│    - Is "Google LLC" already in our graph?    │
│    - If yes, link to existing entity          │
│    - If no, create new entity                 │
│                                               │
│  • Create SUBSIDIARY relationships            │
│  • Handle entity merges/splits                │
│  • Track relationship validity over time      │
└───────────────────────────────────────────────┘
```

### Handling Subsidiary Deduplication

The tricky part: subsidiaries from different parent filings might refer to the same entity:

```python
# Problem: Same subsidiary, different parent filings
# Alphabet's 10-K: "Google Cloud EMEA Limited" (Ireland)
# Google's 10-K: "Google Cloud EMEA Limited" (Ireland)

class SubsidiaryResolver:
    """Resolve subsidiaries to canonical entities."""

    async def resolve_or_create(
        self,
        name: str,
        jurisdiction: str,
        parent_entity_id: str,
        entity_store: SqliteStore,
    ) -> Entity:
        """Find existing entity or create new one.

        Resolution order:
        1. Exact name + jurisdiction match
        2. Fuzzy name match in same jurisdiction
        3. Create new entity
        """
        # Try exact match
        existing = await entity_store.find_entity_by_name_jurisdiction(
            name=name,
            jurisdiction=jurisdiction,
        )

        if existing:
            return existing

        # Try fuzzy match
        candidates = await entity_store.search_entities(
            query=name,
            entity_type=EntityType.ORGANIZATION,
            min_score=0.85,
        )

        for candidate, score in candidates:
            if candidate.jurisdiction == jurisdiction:
                return candidate

        # Create new entity
        new_entity = Entity(
            primary_name=name,
            entity_type=EntityType.ORGANIZATION,
            jurisdiction=jurisdiction,
            source_system="sec-exhibit-21",
            status=EntityStatus.ACTIVE,
        )

        await entity_store.add_entity(new_entity)
        return new_entity
```

---

## Unified API: py-sec-edgar Orchestrates Both Spines

From the user's perspective, they just call `sec.company()`:

```python
async with SEC(tier="entityspine") as sec:
    # Under the hood:
    # 1. FeedSpine syncs company_tickers.json (deduplicated)
    # 2. EntitySpine resolves "GOOG" → Alphabet Inc. entity
    # 3. FeedSpine fetches latest 10-K (deduplicated)
    # 4. py-sec-edgar extracts Exhibit 21
    # 5. EntitySpine creates/resolves subsidiary entities
    # 6. EntitySpine stores SUBSIDIARY relationships

    alphabet = await sec.company("GOOG")

    # Get corporate structure (EntitySpine query)
    subsidiaries = await alphabet.subsidiaries()

    for sub in subsidiaries:
        print(f"  └── {sub.name} ({sub.jurisdiction})")

        # Nested subsidiaries (if we parsed their filings too)
        nested = await sub.subsidiaries()
        for nested_sub in nested:
            print(f"      └── {nested_sub.name}")
```

Output:
```
Alphabet Inc. (CIK: 0001652044)
  └── Google LLC (Delaware)
      └── YouTube, LLC (Delaware)
      └── Google Cloud EMEA Limited (Ireland)
  └── Waymo LLC (Delaware)
  └── Wing Aviation LLC (Delaware)
  └── Verily Life Sciences LLC (Delaware)
  └── Chronicle Security Holdings, LLC (Delaware)
  ...
```

---

## Next Steps

1. **Start with P0** - Get basic `Company` working with `filings()` and `display()`
2. **Add header parsing** - Extract metadata from 10-K SGML headers
3. **Add storage** - DuckDB store for persistence
4. **Create examples** - Document workflows in `examples/` folder
5. **Iterate on P1/P2** - Polish based on user feedback

---

## Related Documents

- [12_UNIFIED_INTERFACE_DESIGN.md](12_UNIFIED_INTERFACE_DESIGN.md) - Overall API design
- [11_EVENTSPINE_AND_FUTURE_ROADMAP.md](11_EVENTSPINE_AND_FUTURE_ROADMAP.md) - EntitySpine integration plans
- [UNIFIED_DATA_MODEL.md](../../UNIFIED_DATA_MODEL.md) - Data model architecture
