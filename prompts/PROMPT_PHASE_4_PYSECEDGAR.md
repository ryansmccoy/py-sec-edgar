# Phase 4: py-sec-edgar Integration Services

**STATUS: ✅ COMPLETE (January 26, 2026)**

This phase added EntitySpine integration to py-sec-edgar for ticker resolution and entity-aware filing processing.

**Location:** `py_sec_edgar/`

---

## ✅ Deliverables Implemented

| Feature | Location | Status |
|---------|----------|--------|
| EntityResolutionService | `py_sec_edgar/services/entity_service.py` | ✅ Done |
| FilingFactsGenerator | `py_sec_edgar/services/filing_facts_generator.py` | ✅ Done |
| Integration Module | `py_sec_edgar/integrations/entityspine.py` | ✅ Done |
| Integration Module | `py_sec_edgar/integrations/feedspine.py` | ✅ Done |
| CLI Commands | `entity-lookup`, `entity-search`, `symbology-refresh` | ✅ Done |
| Integration Tests | `py_sec_edgar/tests/integration/test_entityspine_integration.py` | ✅ 14 passing |

---

## What This Phase Delivers

| Feature | Description |
|---------|-------------|
| **Ticker Resolution** | `--ticker AAPL` flag resolves to CIK automatically |
| **Entity-Aware Processing** | Filings linked to EntitySpine entities |
| **FilingFacts Generation** | py-sec-edgar creates FilingFacts for EntitySpine |
| **CLI Commands** | `py-sec-edgar symbology lookup AAPL` |

---

## Prerequisites

Before starting Phase 4, ensure:

1. ✅ **EntitySpine v0.3.3+** is working
   ```bash
   pip install entityspine
   python -c "from entityspine import SqliteStore; print('OK')"
   ```

2. ✅ **Study EntitySpine integration contracts**
   ```bash
   cd entityspine
   python examples/05_filing_facts_ingestion.py
   ```

3. ✅ **py-sec-edgar tests pass**
   ```bash
   cd py_sec_edgar
   python -m pytest tests/ -q
   ```

---

## Current py-sec-edgar State

| Component | Status | Notes |
|-----------|--------|-------|
| Filing download | ✅ Done | By CIK/accession |
| Section extraction | ✅ Done | 10-K/10-Q parsing |
| Company lookup | ✅ Done | From local tickers.json |
| Tests | ⚠️ 41 passing | 1 error |

---

## Deliverable 1: EntityResolutionService

Add EntitySpine-powered ticker resolution:

```python
# py_sec_edgar/src/py_sec_edgar/services/entity_service.py

from pathlib import Path
from entityspine import SqliteStore

class EntityResolutionService:
    """Resolve tickers/names to CIK using EntitySpine."""

    def __init__(self, data_dir: Path):
        self._store = SqliteStore(data_dir / "entities.db")
        self._store.initialize()
        self._initialized = False

    def ensure_initialized(self) -> None:
        """Load SEC data if not already loaded."""
        if not self._initialized:
            if self._store.count_entities() == 0:
                self._store.load_sec_data()
            self._initialized = True

    def resolve_ticker(self, ticker: str) -> str | None:
        """Resolve ticker to CIK.

        Args:
            ticker: Stock ticker (e.g., "AAPL")

        Returns:
            CIK string if found, None otherwise
        """
        self.ensure_initialized()
        results = self._store.search_entities(ticker.upper(), limit=1)
        if results:
            entity, score = results[0]
            if score >= 0.9:  # High confidence match
                return entity.source_id
        return None

    def resolve_name(self, name: str) -> list[tuple[str, str, float]]:
        """Search entities by name.

        Returns:
            List of (cik, name, score) tuples
        """
        self.ensure_initialized()
        results = self._store.search_entities(name, limit=10)
        return [
            (entity.source_id, entity.primary_name, score)
            for entity, score in results
        ]

    def get_entity(self, cik: str):
        """Get full entity by CIK."""
        self.ensure_initialized()
        entities = self._store.get_entities_by_cik(cik)
        return entities[0] if entities else None
```

---

## Deliverable 2: CLI with Ticker Support

Add `--ticker` flag to existing commands:

```python
# py_sec_edgar/src/py_sec_edgar/cli.py

import click
from .services.entity_service import EntityResolutionService

@click.command()
@click.option("--ticker", help="Stock ticker (e.g., AAPL)")
@click.option("--cik", help="SEC CIK number")
@click.option("--form", default="10-K", help="Form type")
def fetch(ticker: str | None, cik: str | None, form: str):
    """Fetch SEC filings."""
    if ticker and not cik:
        # Resolve ticker to CIK using EntitySpine
        service = EntityResolutionService(data_dir)
        cik = service.resolve_ticker(ticker)
        if not cik:
            click.echo(f"Could not resolve ticker: {ticker}", err=True)
            return
        click.echo(f"Resolved {ticker} → CIK {cik}")

    # Continue with existing CIK-based logic
    ...

@click.group()
def symbology():
    """Symbology commands."""
    pass

@symbology.command()
@click.argument("query")
def lookup(query: str):
    """Look up entity by ticker or name."""
    service = EntityResolutionService(data_dir)
    results = service.resolve_name(query)

    for cik, name, score in results:
        click.echo(f"{score:.2f} | {name} (CIK: {cik})")
```

### CLI Examples

```bash
# Fetch by ticker (resolves automatically)
py-sec-edgar fetch --ticker AAPL --form 10-K
# Resolved AAPL → CIK 0000320193
# Fetching filings...

# Look up entity
py-sec-edgar symbology lookup "Apple"
# 1.00 | Apple Inc. (CIK: 0000320193)
# 0.85 | Apple Hospitality REIT Inc. (CIK: 0001418121)

# Look up by ticker
py-sec-edgar symbology lookup NVDA
# 1.00 | NVIDIA Corporation (CIK: 0001045810)
```

---

## Deliverable 3: FilingFacts Generator

py-sec-edgar generates FilingFacts for EntitySpine ingestion:

```python
# py_sec_edgar/src/py_sec_edgar/services/filing_facts_generator.py

from datetime import date
from entityspine.integration import FilingFacts, FilingEvidence
from entityspine.integration.contracts import (
    ExtractedEntity,
    ExtractedRelationship,
)

class FilingFactsGenerator:
    """Generate EntitySpine FilingFacts from parsed SEC filings."""

    def generate(self, filing_data: dict) -> FilingFacts:
        """Convert py-sec-edgar filing data to FilingFacts.

        Args:
            filing_data: Parsed filing with header, sections, etc.

        Returns:
            FilingFacts ready for EntitySpine ingestion
        """
        header = filing_data.get("header", {})

        return FilingFacts(
            evidence=FilingEvidence(
                accession_number=header.get("accession_number"),
                form_type=header.get("form_type"),
                filed_date=date.fromisoformat(header.get("filed_date")),
                cik=header.get("cik"),
            ),
            registrant_name=header.get("company_name"),
            registrant_cik=header.get("cik"),
            registrant_ticker=header.get("ticker"),
            registrant_sic=header.get("sic_code"),
            # Extract entities from sections
            entities=self._extract_entities(filing_data),
            # Extract relationships
            relationships=self._extract_relationships(filing_data),
        )

    def _extract_entities(self, filing_data: dict) -> list[ExtractedEntity]:
        """Extract entity mentions from filing sections."""
        # Implementation depends on py-sec-edgar's extraction logic
        entities = []
        # ... extract executives, subsidiaries, partners
        return entities

    def _extract_relationships(self, filing_data: dict) -> list[ExtractedRelationship]:
        """Extract relationships from filing text."""
        relationships = []
        # ... extract supplier/customer/competitor mentions
        return relationships
```

### Usage with EntitySpine

```python
from py_sec_edgar.services.filing_facts_generator import FilingFactsGenerator
from entityspine import SqliteStore
from entityspine.integration import ingest_filing_facts

# py-sec-edgar parses a filing
filing_data = download_and_parse("0001045810-24-000029")

# Generate FilingFacts
generator = FilingFactsGenerator()
facts = generator.generate(filing_data)

# Ingest into EntitySpine
store = SqliteStore("entities.db")
store.initialize()
result = ingest_filing_facts(store, facts)

print(f"Created {result.entities_created} entities")
print(f"Created {result.relationships_created} relationships")
```

---

## Deliverable 4: Graceful Degradation

EntitySpine is optional - py-sec-edgar works without it:

```python
# py_sec_edgar/src/py_sec_edgar/services/entity_service.py

try:
    from entityspine import SqliteStore
    ENTITYSPINE_AVAILABLE = True
except ImportError:
    ENTITYSPINE_AVAILABLE = False

class EntityResolutionService:
    def __init__(self, data_dir: Path):
        if not ENTITYSPINE_AVAILABLE:
            raise ImportError(
                "EntitySpine not installed. Install with:\n"
                "  pip install entityspine\n"
                "Or for full features:\n"
                "  pip install py-sec-edgar[entityspine]"
            )
        # ... rest of init
```

### pyproject.toml Update

```toml
[project.optional-dependencies]
entityspine = ["entityspine>=0.3.3"]
full = ["entityspine>=0.3.3", "feedspine>=1.0.0"]
```

---

## Pattern Reference: EntitySpine Examples

Study these files to understand integration patterns:

| File | Pattern |
|------|---------|
| `entityspine/examples/01_end_to_end_sec_filing_to_kg.py` | Complete data flow |
| `entityspine/examples/02_load_sec_company_tickers.py` | Loading SEC data |
| `entityspine/examples/05_filing_facts_ingestion.py` | FilingFacts usage |
| `entityspine/src/entityspine/integration/contracts.py` | Contract definitions |

---

## Acceptance Criteria

```bash
# CLI resolves ticker
py-sec-edgar fetch --ticker AAPL --form 10-K
# Resolved AAPL → CIK 0000320193

# Symbology lookup
py-sec-edgar symbology lookup "NVIDIA"
# 1.00 | NVIDIA Corporation (CIK: 0001045810)

# Python API
python -c "
from py_sec_edgar.services.entity_service import EntityResolutionService
from pathlib import Path

service = EntityResolutionService(Path('./data'))
cik = service.resolve_ticker('AAPL')
print(f'AAPL → {cik}')
"
# AAPL → 0000320193
```

---

## What's Next?

After Phase 4:
- **Phase 5**: Enhanced section extraction with entity linking

---

*Phase 4 of 5 | ❌ NOT STARTED | Depends on: Phase 3*
