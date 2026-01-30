# Spine Ecosystem Integration Manifesto

**Unified Financial Data Stack Integration Guide**

*Version: 1.0*
*Updated: January 27, 2026*

---

## The Vision

Four packages that work seamlessly together OR independently:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE SPINE ECOSYSTEM                                 │
│                                                                             │
│   ┌─────────────────┐                           ┌─────────────────┐         │
│   │ capture-spine   │                           │   EntitySpine   │         │
│   │ (Acquisition)   │                           │  (Resolution)   │         │
│   │                 │                           │                 │         │
│   │ • Web capture   │                           │ • Entity resolve│         │
│   │ • Rate limiting │                           │ • Knowledge graph│        │
│   │ • Provenance    │                           │ • Claims/Evidence│        │
│   └────────┬────────┘                           └────────▲────────┘         │
│            │                                             │                  │
│            │ CapturedContent                  FilingFacts│                  │
│            ▼                                             │                  │
│   ┌─────────────────┐                           ┌────────┴────────┐         │
│   │   FeedSpine     │                           │  py-sec-edgar   │         │
│   │   (Pipelines)   │◄──────FeedRecord──────────│    (Parsing)    │         │
│   │                 │                           │                 │         │
│   │ • Bronze/Silver │         FilingFacts       │ • Exhibits      │         │
│   │ • Change detect │──────────────────────────►│ • Forms         │         │
│   │ • Deduplication │                           │ • Companies     │         │
│   └─────────────────┘                           └─────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package Responsibilities

| Package | Domain | Core Responsibility | Key Output |
|---------|--------|---------------------|------------|
| **capture-spine** | Acquisition | Get content from web | `CapturedContent` |
| **py-sec-edgar** | SEC Domain | Parse SEC filings | `ExhibitData`, `FormData` |
| **FeedSpine** | Pipelines | Data flow & change detection | `FeedRecord`, `ChangeEvent` |
| **EntitySpine** | Resolution | Entity identity & graph | `Entity`, `Claim`, `Evidence` |

---

## Integration Contracts

### Contract 1: CapturedContent (capture-spine → all)

```python
@dataclass
class CapturedContent:
    """Raw captured content with provenance."""
    url: str
    content: bytes
    content_type: str
    captured_at: datetime
    content_hash: str
    profile: str
```

### Contract 2: FilingFacts (py-sec-edgar → EntitySpine)

```python
@dataclass
class FilingFacts:
    """Extracted facts from SEC filing for entity ingestion."""
    evidence: FilingEvidence
    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]
    events: list[ExtractedEvent]
```

### Contract 3: FeedRecord (any → FeedSpine)

```python
@dataclass
class FeedRecord:
    """Normalized record for pipeline processing."""
    natural_key: str
    content: dict
    source_feed: str
    captured_at: datetime
    dedup_key: str
```

### Contract 4: Sighting (FeedSpine → EntitySpine)

```python
@dataclass
class Sighting:
    """Entity sighting from a feed for resolution."""
    natural_key: str
    identifiers: dict[str, str]  # cik, ticker, lei, etc.
    attributes: dict[str, Any]
    source: str
    observed_at: datetime
```

---

## Integration Levels

### Level 0: Package Standalone

Each package works independently:

```python
# capture-spine alone
from capture_spine import CaptureService
content = CaptureService().fetch(url)

# py-sec-edgar alone
from py_sec_edgar.exhibits import ExhibitService
data = ExhibitService().get_exhibit(cik, "21")

# FeedSpine alone
from feedspine import BronzeStore
store = BronzeStore().ingest(items)

# EntitySpine alone
from entityspine import EntityResolver
entity = EntityResolver().resolve("AAPL")
```

### Level 1: Pairwise Integration

Two packages working together:

```python
# capture-spine + py-sec-edgar
from capture_spine import CaptureService, SEC_PROFILE
from py_sec_edgar.exhibits import Exhibit21Parser

content = CaptureService().fetch(exhibit_url, profile=SEC_PROFILE)
parser = Exhibit21Parser()
data = parser.parse(content.text(), metadata)

# py-sec-edgar + EntitySpine
from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
from entityspine.integration import ingest_filing_facts

facts = exhibit_to_filing_facts(exhibit_data)
result = ingest_filing_facts(store, facts)

# FeedSpine + EntitySpine
from feedspine.adapters.entityspine import feed_record_to_sighting
from entityspine import EntityResolver

sighting = feed_record_to_sighting(record)
entity = resolver.resolve_sighting(sighting)
```

### Level 2: Triple Integration

Three packages working together:

```python
# capture-spine + py-sec-edgar + EntitySpine
from capture_spine import CaptureService, SEC_PROFILE
from py_sec_edgar.exhibits import ExhibitService
from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
from entityspine.integration import ingest_filing_facts

# Capture → Parse → Resolve
content = CaptureService().fetch(url, profile=SEC_PROFILE)
service = ExhibitService()
exhibit = service.parse_exhibit(content.text(), metadata, "21")
facts = exhibit_to_filing_facts(exhibit)
result = ingest_filing_facts(store, facts)
```

### Level 3: With FeedSpine

All four packages in harmony:

```python
# The full pipeline
from capture_spine import CaptureService, SEC_PROFILE
from feedspine import Pipeline
from py_sec_edgar.forms import FormService
from py_sec_edgar.forms.adapters.entityspine import form_to_filing_facts
from entityspine.integration import ingest_filing_facts, SqliteStore

# Initialize
capture = CaptureService(default_profile=SEC_PROFILE)
pipeline = Pipeline(storage=storage)
forms = FormService(capture_service=capture)
store = SqliteStore("entities.db")
store.initialize()

# Full flow
def process_filing(url: str):
    # 1. Capture (capture-spine)
    content = capture.fetch(url)

    # 2. Store in bronze (FeedSpine)
    bronze_item = pipeline.ingest_bronze(content)

    # 3. Parse (py-sec-edgar)
    form = forms.parse_form(content.text(), metadata)

    # 4. Normalize to silver (FeedSpine)
    silver_record = pipeline.promote_to_silver(bronze_item, form)

    # 5. Extract entities (py-sec-edgar adapter)
    facts = form_to_filing_facts(form)

    # 6. Resolve & store (EntitySpine)
    result = ingest_filing_facts(store, facts)

    # 7. Detect changes (FeedSpine)
    changes = pipeline.detect_changes(silver_record)

    return result, changes
```

### Level 4: Full Features (Elasticsearch + Knowledge Graph)

Complete feature set with capture-spine's full application:

```python
# Full features with Elasticsearch and Knowledge Graph
from capture_spine.client import CaptureSpineClient
from capture_spine.knowledge import KnowledgeGraph
from capture_spine.search import SearchService

# Initialize full-featured client
client = CaptureSpineClient("http://localhost:8000")

# Full-text search across all filings
search_results = client.search.query(
    query="risk factors artificial intelligence",
    filters={
        "form_type": ["10-K", "10-Q"],
        "date_range": ("2024-01-01", "2024-12-31"),
    },
    facets=["company", "form_type", "filing_date"],
)

# Knowledge graph queries
kg = client.knowledge
# Find related entities
related = kg.get_related_entities(
    entity_id="AAPL",
    relationship_types=["subsidiary_of", "audited_by"],
)
# Graph traversal
path = kg.find_path("AAPL", "Ernst & Young LLP", max_depth=3)

# Real-time feed monitoring
async for filing in client.stream_filings(form_types=["8-K"]):
    print(f"New filing: {filing.company_name} - {filing.form_type}")

# ML-enriched insights
insights = client.analyze.get_risk_trends(cik="0000320193", years=5)
```

---

## Application Tiers

### capture-spine-basic (Simplified)

For personal/development use with minimal setup:

```bash
# Quick start with Docker (random ports to avoid conflicts)
cd capture-spine-basic
docker compose up -d

# Check assigned ports
docker compose ps
# → API at http://localhost:XXXXX
```

**Features:**
- 6 database tables (vs 40+ in full)
- No authentication (single-user)
- No Elasticsearch
- Simplified UI (NewsfeedPage core features)
- Optional spine package integration

```python
# Optional integration detection
from capture_spine_basic.api.main import (
    FEEDSPINE_AVAILABLE,    # True if feedspine installed
    PYSECEDGAR_AVAILABLE,   # True if py-sec-edgar installed
    ENTITYSPINE_AVAILABLE,  # True if entityspine installed
)
```

**See:** [capture-spine-basic/README.md](capture-spine-basic/README.md)

### capture-spine (Full)

For production/team use with all features:

- 40+ database tables
- Multi-user authentication
- Elasticsearch full-text search
- Knowledge graph with relationships
- Real-time WebSocket updates
- Complex dashboards

---

## Graceful Degradation Matrix

| Scenario | What Works | What's Degraded |
|----------|------------|-----------------|
| Only py-sec-edgar | Parsing, extraction | No entity resolution, no pipelines |
| + EntitySpine | + Entity resolution, graph | No change detection pipelines |
| + FeedSpine | + Data pipelines, dedup | No full-text search, no UI |
| + capture-spine | + Elasticsearch, Knowledge Graph, UI | None - Full Features |

### Degradation Code Pattern

```python
# py-sec-edgar always works
from py_sec_edgar.exhibits import ExhibitService
data = ExhibitService().get_exhibit(cik, "21")

# Try EntitySpine integration
try:
    from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
    from entityspine.integration import ingest_filing_facts
    ENTITYSPINE_AVAILABLE = True
except ImportError:
    ENTITYSPINE_AVAILABLE = False

# Try FeedSpine integration
try:
    from feedspine import FeedPipeline
    FEEDSPINE_AVAILABLE = True
except ImportError:
    FEEDSPINE_AVAILABLE = False

# Use what's available
if ENTITYSPINE_AVAILABLE:
    facts = exhibit_to_filing_facts(data)
    # ... entity resolution

if FEEDSPINE_AVAILABLE:
    pipeline = FeedPipeline()
    # ... pipeline processing
```

---

## Integration Testing Strategy

### Test Categories

| Category | Purpose | Packages Involved |
|----------|---------|-------------------|
| **Unit Tests** | Individual component logic | Single package |
| **Contract Tests** | Contract compliance | Producer + Consumer |
| **Integration Tests** | End-to-end flows | Multiple packages |
| **Random Filing Tests** | Edge case discovery | All parsing packages |
| **Regression Tests** | Known filing consistency | All packages |

### Random Filing Test Framework

```python
# tests/integration/test_random_filings.py
import pytest
from datetime import date, timedelta
from random import choice

from py_sec_edgar.testing import (
    get_random_filings,
    FilingTestResult,
    EdgeCaseReport,
)

class TestRandomFilings:
    """Test parsers against random SEC filings."""

    @pytest.fixture
    def random_10k_filings(self):
        """Get random 10-K filings from last 2 years."""
        return get_random_filings(
            form_type="10-K",
            count=20,
            start_date=date.today() - timedelta(days=730),
        )

    def test_exhibit21_random(self, random_10k_filings):
        """Test Exhibit 21 parser against random filings."""
        from py_sec_edgar.exhibits import ExhibitService

        service = ExhibitService()
        results: list[FilingTestResult] = []

        for filing in random_10k_filings:
            result = service.get_exhibit_with_diagnostics(
                filing.cik,
                exhibit_type="21",
                accession=filing.accession_number,
            )
            results.append(result)

        # Generate edge case report
        report = EdgeCaseReport.from_results(results)

        # Assert minimum success rate
        assert report.success_rate >= 0.8, (
            f"Only {report.success_rate:.0%} success. "
            f"Edge cases: {report.edge_case_summary}"
        )

        # Save report for analysis
        report.save("test_outputs/exhibit21_edge_cases.json")

    def test_form10k_sections_random(self, random_10k_filings):
        """Test 10-K section extraction against random filings."""
        from py_sec_edgar.forms import FormService

        service = FormService()
        results = []

        for filing in random_10k_filings:
            result = service.fetch_and_parse_with_diagnostics(
                filing.document_url,
                filing.metadata,
                "10-K"
            )
            results.append(result)

        # Check section extraction rates
        report = EdgeCaseReport.from_results(results)

        # Key sections should be found most of the time
        assert report.section_found_rate("item1") >= 0.9
        assert report.section_found_rate("item1a") >= 0.85
        assert report.section_found_rate("item7") >= 0.9


class TestFixedFilings:
    """Test against known filings for regression."""

    # Known good filings for regression
    KNOWN_FILINGS = [
        {"cik": "320193", "accession": "0000320193-23-000106"},  # Apple 10-K
        {"cik": "789019", "accession": "0001564590-23-008850"},  # Microsoft 10-K
        {"cik": "1018724", "accession": "0001018724-24-000021"}, # Amazon 10-K
    ]

    @pytest.mark.parametrize("filing", KNOWN_FILINGS)
    def test_exhibit21_known(self, filing):
        """Test Exhibit 21 parser against known filings."""
        from py_sec_edgar.exhibits import ExhibitService

        service = ExhibitService()
        data = service.get_exhibit(
            filing["cik"],
            exhibit_type="21",
            accession=filing["accession"],
        )

        # Known filings should always parse
        assert data is not None
        assert len(data.subsidiaries) > 0

    @pytest.mark.parametrize("filing", KNOWN_FILINGS)
    def test_full_integration_known(self, filing):
        """Test full stack against known filings."""
        pytest.importorskip("entityspine")

        from py_sec_edgar.exhibits import ExhibitService
        from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
        from entityspine.integration import ingest_filing_facts
        from entityspine import MemoryStore

        # Parse
        service = ExhibitService()
        data = service.get_exhibit(filing["cik"], "21", filing["accession"])

        # Convert to FilingFacts
        facts = exhibit_to_filing_facts(data)

        # Ingest to EntitySpine
        store = MemoryStore()
        result = ingest_filing_facts(store, facts)

        # Verify
        assert result.entities_created > 0
        assert result.relationships_created > 0
```

### Edge Case Report Format

```python
@dataclass
class EdgeCaseReport:
    """Report of edge cases found during testing."""

    total_tested: int
    successful: int
    failed: int

    edge_cases: list[EdgeCase]

    @dataclass
    class EdgeCase:
        filing_url: str
        error_type: str
        error_message: str
        warnings: list[str]
        strategy_used: str
        parse_time_ms: int

    @property
    def success_rate(self) -> float:
        return self.successful / self.total_tested if self.total_tested else 0

    def to_json(self) -> dict:
        """Export for analysis."""
        return {
            "summary": {
                "total": self.total_tested,
                "success_rate": self.success_rate,
                "failed": self.failed,
            },
            "edge_cases": [asdict(ec) for ec in self.edge_cases],
            "error_distribution": self._error_distribution(),
        }

    def _error_distribution(self) -> dict[str, int]:
        """Count errors by type."""
        from collections import Counter
        return dict(Counter(ec.error_type for ec in self.edge_cases))
```

---

## Validation Framework

### Contract Validation

```python
# Validate FilingFacts contract
from entityspine.integration import validate_filing_facts

facts = exhibit_to_filing_facts(data)
validation = validate_filing_facts(facts)

assert validation.is_valid, validation.errors
```

### Cross-Package Consistency

```python
# Ensure data flows correctly across packages
def test_data_consistency():
    """Data should be consistent across package boundaries."""

    # Original data
    exhibit = parse_exhibit21(html, metadata)

    # Convert to FilingFacts
    facts = exhibit_to_filing_facts(exhibit)

    # Ingest to EntitySpine
    store = MemoryStore()
    result = ingest_filing_facts(store, facts)

    # Verify consistency
    for subsidiary in exhibit.subsidiaries:
        # Should be able to find each subsidiary in EntitySpine
        entity = store.find_entity_by_name(subsidiary.name)
        assert entity is not None, f"Subsidiary {subsidiary.name} not found"

        # Relationship should exist
        rels = store.get_relationships(entity.id)
        assert any(r.type == "subsidiary_of" for r in rels)
```

---

## CI/CD Integration Test Jobs

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  random-filing-tests:
    name: Random Filing Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install all packages
        run: |
          pip install -e ./py_sec_edgar
          pip install -e ./entityspine
          pip install -e ./feedspine
          pip install -e ./capture-spine

      - name: Run random filing tests
        run: |
          pytest tests/integration/test_random_filings.py \
            --random-count=50 \
            --report-output=test_outputs/

      - name: Upload edge case report
        uses: actions/upload-artifact@v4
        with:
          name: edge-case-report
          path: test_outputs/

      - name: Check success rate
        run: |
          python scripts/check_success_rate.py \
            --report=test_outputs/edge_cases.json \
            --min-rate=0.85

  fixed-filing-tests:
    name: Fixed Filing Regression
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install packages
        run: pip install -e ./py_sec_edgar -e ./entityspine

      - name: Run regression tests
        run: pytest tests/integration/test_fixed_filings.py -v

  contract-tests:
    name: Contract Compliance
    runs-on: ubuntu-latest
    strategy:
      matrix:
        contract:
          - filing-facts
          - feed-record
          - captured-content
    steps:
      - uses: actions/checkout@v4

      - name: Run contract tests
        run: pytest tests/contracts/test_${{ matrix.contract }}.py
```

---

## Success Criteria

### For Each Package Individually

1. **Works standalone** without other packages installed
2. **Clear error messages** when optional dependency missing
3. **100% contract compliance** when integrated

### For Integration

1. **Data consistency** across package boundaries
2. **Graceful degradation** when packages unavailable
3. **Edge case detection** via random testing
4. **<1% regression rate** on known filings
5. **Clear provenance** from capture through resolution

---

## Quick Reference

### Import Patterns

```python
# Always works
from py_sec_edgar.exhibits import ExhibitService

# Check for optional
try:
    from entityspine import EntityResolver
    HAS_ENTITYSPINE = True
except ImportError:
    HAS_ENTITYSPINE = False

# Adapters import their target
from py_sec_edgar.exhibits.adapters.entityspine import exhibit_to_filing_facts
# (this will fail if entityspine not installed - that's expected)
```

### Flow Patterns

```
# Pattern A: Parse Only (standalone)
URL → py-sec-edgar → ExhibitData/FormData

# Pattern B: Parse + Resolve
URL → py-sec-edgar → FilingFacts → EntitySpine → Entity

# Pattern C: Full Pipeline
URL → capture-spine → FeedSpine Bronze → py-sec-edgar →
      FeedSpine Silver → EntitySpine → FeedSpine Gold
```

### Testing Patterns

```python
# Pattern: Test with optional dependencies
def test_with_entityspine():
    entityspine = pytest.importorskip("entityspine")
    # Test code that requires entityspine

# Pattern: Random filing test
def test_random():
    filings = get_random_filings(count=10)
    results = [parse(f) for f in filings]
    assert success_rate(results) >= 0.8

# Pattern: Fixed filing regression
@pytest.mark.parametrize("filing", KNOWN_FILINGS)
def test_known_filing(filing):
    result = parse(filing)
    assert result.matches_expected()
```
