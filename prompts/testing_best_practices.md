# Testing Best Practices Prompt

> **Purpose**: Reusable prompt for GitHub Copilot to audit, create, and enhance tests following industry best practices across backend, frontend, integration, and unit testing.

---

## 🎯 Mission

You are auditing and enhancing tests in this codebase. Apply these best practices to ensure comprehensive, maintainable, and fast test suites.

---

## 📁 Test Organization

### Directory Structure

```
tests/
├── unit/                    # Fast, isolated tests (~80% of tests)
│   ├── domain/              # Mirror source structure
│   │   ├── test_entity.py
│   │   ├── test_claim.py
│   │   └── test_enums.py
│   ├── services/
│   │   └── test_resolver.py
│   └── conftest.py          # Unit test fixtures
│
├── integration/             # Tests with real dependencies (~15%)
│   ├── database/
│   │   └── test_repository.py
│   ├── api/
│   │   └── test_endpoints.py
│   ├── external/
│   │   └── test_sec_client.py
│   └── conftest.py          # Integration fixtures (DB, API clients)
│
├── e2e/                     # End-to-end tests (~5%)
│   ├── playwright/          # Browser automation
│   │   ├── test_login_flow.py
│   │   └── test_search.py
│   └── scenarios/
│       └── test_full_workflow.py
│
├── fixtures/                # Shared test data
│   ├── entities.json
│   ├── filings.json
│   └── factory.py           # Test data factories
│
├── conftest.py              # Root fixtures, markers, plugins
└── pytest.ini               # Test configuration
```

### File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Unit test | `test_{module}.py` | `test_entity.py` |
| Integration | `test_{feature}_integration.py` | `test_api_integration.py` |
| E2E | `test_{workflow}.py` | `test_login_flow.py` |
| Fixtures | `conftest.py` or `fixtures.py` | `conftest.py` |
| Factories | `factory.py` or `factories.py` | `entity_factory.py` |

### Test Function Naming

Use descriptive names that explain the scenario:

```python
# ✅ GOOD - Describes behavior and scenario
def test_entity_merge_combines_identifiers_from_both_sources():
    ...

def test_resolver_returns_none_when_no_match_found():
    ...

def test_api_returns_404_when_entity_not_found():
    ...

# ❌ BAD - Vague or implementation-focused
def test_merge():
    ...

def test_resolver():
    ...

def test_api():
    ...
```

---

## 🧪 Unit Test Best Practices

### The AAA Pattern

Every test should follow **Arrange-Act-Assert**:

```python
def test_entity_add_identifier_creates_new_claim():
    """Adding an identifier creates a new IdentifierClaim."""
    # Arrange - Set up test data and dependencies
    entity = Entity(entity_id="ent_001", entity_type=EntityType.COMPANY, name="Acme Corp")

    # Act - Perform the action being tested
    updated = entity.add_identifier(
        scheme=IdentifierScheme.LEI,
        value="5493001KJTIIGC8Y1R12",
        source="gleif"
    )

    # Assert - Verify the expected outcome
    assert len(updated.identifiers) == 1
    assert updated.identifiers[0].scheme == IdentifierScheme.LEI
    assert updated.identifiers[0].value == "5493001KJTIIGC8Y1R12"
```

### One Assertion Concept Per Test

Test one logical concept, but multiple related assertions are fine:

```python
# ✅ GOOD - One concept (entity creation), multiple related assertions
def test_entity_creation_sets_all_required_fields():
    entity = Entity(
        entity_id="ent_001",
        entity_type=EntityType.COMPANY,
        name="Acme Corp"
    )

    assert entity.entity_id == "ent_001"
    assert entity.entity_type == EntityType.COMPANY
    assert entity.name == "Acme Corp"
    assert entity.status == EntityStatus.ACTIVE  # Default value

# ❌ BAD - Testing multiple unrelated concepts
def test_entity():
    entity = Entity(...)
    assert entity.name == "Acme"

    merged = entity.merge(other)  # Different concept
    assert len(merged.identifiers) == 2

    serialized = entity.to_dict()  # Yet another concept
    assert "name" in serialized
```

### Use Fixtures for Reusable Test Data

```python
# conftest.py
import pytest
from datetime import date
from entityspine.domain import Entity, EntityType, IdentifierClaim, IdentifierScheme

@pytest.fixture
def sample_entity():
    """A minimal valid entity for testing."""
    return Entity(
        entity_id="ent_test_001",
        entity_type=EntityType.COMPANY,
        name="Test Corporation"
    )

@pytest.fixture
def entity_with_identifiers(sample_entity):
    """Entity with common identifier types attached."""
    return sample_entity.add_identifier(
        scheme=IdentifierScheme.LEI,
        value="5493001KJTIIGC8Y1R12",
        source="gleif"
    ).add_identifier(
        scheme=IdentifierScheme.CIK,
        value="0001234567",
        source="sec"
    )

@pytest.fixture
def filing_date():
    """Standard filing date for tests."""
    return date(2024, 1, 15)
```

### Parametrize for Multiple Cases

```python
import pytest

@pytest.mark.parametrize("scheme,value,expected_valid", [
    (IdentifierScheme.LEI, "5493001KJTIIGC8Y1R12", True),
    (IdentifierScheme.LEI, "INVALID", False),
    (IdentifierScheme.CIK, "0001234567", True),
    (IdentifierScheme.CIK, "123", False),  # Too short
    (IdentifierScheme.CUSIP, "037833100", True),
    (IdentifierScheme.CUSIP, "INVALID99", False),
])
def test_identifier_validation(scheme, value, expected_valid):
    """Validate identifier formats for various schemes."""
    result = validate_identifier(scheme, value)
    assert result.is_valid == expected_valid
```

### Mock External Dependencies

```python
from unittest.mock import Mock, patch, MagicMock
import pytest

class TestEntityResolver:
    """Tests for entity resolution service."""

    @pytest.fixture
    def mock_repository(self):
        """Mock repository for isolated testing."""
        repo = Mock()
        repo.find_by_identifier.return_value = None
        return repo

    def test_resolve_creates_new_entity_when_not_found(self, mock_repository):
        """Creates new entity when no existing match found."""
        resolver = EntityResolver(repository=mock_repository)

        result = resolver.resolve(
            scheme=IdentifierScheme.LEI,
            value="5493001KJTIIGC8Y1R12"
        )

        assert result.is_new is True
        mock_repository.find_by_identifier.assert_called_once_with(
            IdentifierScheme.LEI, "5493001KJTIIGC8Y1R12"
        )

    @patch("entityspine.services.resolver.datetime")
    def test_resolve_timestamps_with_current_time(self, mock_datetime, mock_repository):
        """Resolution timestamp uses current UTC time."""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 12, 0, 0)
        resolver = EntityResolver(repository=mock_repository)

        result = resolver.resolve(scheme=IdentifierScheme.LEI, value="...")

        assert result.resolved_at == datetime(2024, 1, 15, 12, 0, 0)
```

---

## 🔌 Integration Test Best Practices

### Mark Integration Tests

```python
import pytest

pytestmark = pytest.mark.integration  # Mark entire module

# Or mark individual tests
@pytest.mark.integration
@pytest.mark.database
def test_repository_persists_entity():
    """Entity survives round-trip to database."""
    ...
```

### Use Real Dependencies When Practical

```python
# conftest.py for integration tests
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container():
    """Spin up real PostgreSQL for integration tests."""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture
def db_session(postgres_container):
    """Database session with automatic rollback."""
    engine = create_engine(postgres_container.get_connection_url())
    with engine.connect() as conn:
        trans = conn.begin()
        yield conn
        trans.rollback()  # Clean up after each test
```

### Test Database Transactions

```python
@pytest.mark.integration
@pytest.mark.database
class TestEntityRepository:
    """Integration tests for EntityRepository with real database."""

    def test_save_and_retrieve_entity(self, db_session):
        """Entity can be saved and retrieved by ID."""
        repo = EntityRepository(db_session)
        entity = Entity(
            entity_id="ent_001",
            entity_type=EntityType.COMPANY,
            name="Integration Test Corp"
        )

        repo.save(entity)
        retrieved = repo.get_by_id("ent_001")

        assert retrieved is not None
        assert retrieved.name == "Integration Test Corp"

    def test_find_by_identifier_with_index(self, db_session):
        """Identifier lookup uses database index efficiently."""
        repo = EntityRepository(db_session)
        # ... setup entities with identifiers

        with db_session.begin():
            result = repo.find_by_identifier(IdentifierScheme.LEI, "...")

        assert result is not None
        # Optionally: verify query plan uses index
```

---

## 🌐 API Test Best Practices

### Use Test Client

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Sync tests with FastAPI
@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app)

# Async tests
@pytest.fixture
async def async_client(app):
    """Async test client for async endpoints."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### Test HTTP Status Codes and Response Structure

```python
@pytest.mark.api
class TestEntityEndpoints:
    """API endpoint tests for /api/v1/entities."""

    def test_get_entity_returns_200_with_valid_id(self, client, sample_entity):
        """GET /entities/{id} returns 200 for existing entity."""
        response = client.get(f"/api/v1/entities/{sample_entity.entity_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == sample_entity.entity_id
        assert data["name"] == sample_entity.name
        assert "identifiers" in data

    def test_get_entity_returns_404_when_not_found(self, client):
        """GET /entities/{id} returns 404 for non-existent entity."""
        response = client.get("/api/v1/entities/ent_nonexistent")

        assert response.status_code == 404
        assert response.json()["detail"] == "Entity not found"

    def test_create_entity_returns_201_with_location_header(self, client):
        """POST /entities returns 201 with Location header."""
        payload = {
            "entity_type": "COMPANY",
            "name": "New Corporation"
        }

        response = client.post("/api/v1/entities", json=payload)

        assert response.status_code == 201
        assert "Location" in response.headers
        assert response.json()["name"] == "New Corporation"

    @pytest.mark.parametrize("invalid_payload,expected_error", [
        ({}, "entity_type is required"),
        ({"entity_type": "INVALID"}, "Invalid entity type"),
        ({"entity_type": "COMPANY"}, "name is required"),
    ])
    def test_create_entity_validates_payload(self, client, invalid_payload, expected_error):
        """POST /entities returns 422 for invalid payloads."""
        response = client.post("/api/v1/entities", json=invalid_payload)

        assert response.status_code == 422
        assert expected_error in response.text
```

### Test Authentication and Authorization

```python
@pytest.mark.api
@pytest.mark.auth
class TestEntityEndpointsSecurity:
    """Security tests for entity endpoints."""

    def test_get_entity_requires_authentication(self, client):
        """Unauthenticated requests return 401."""
        response = client.get("/api/v1/entities/ent_001")
        assert response.status_code == 401

    def test_get_entity_with_valid_token(self, client, auth_headers):
        """Authenticated requests succeed."""
        response = client.get("/api/v1/entities/ent_001", headers=auth_headers)
        assert response.status_code in (200, 404)  # Auth passed

    def test_delete_entity_requires_admin_role(self, client, user_auth_headers):
        """Non-admin users cannot delete entities."""
        response = client.delete(
            "/api/v1/entities/ent_001",
            headers=user_auth_headers
        )
        assert response.status_code == 403
```

---

## 🎭 Playwright E2E Test Best Practices

### Page Object Model

```python
# tests/e2e/pages/search_page.py
from playwright.sync_api import Page, expect

class SearchPage:
    """Page object for entity search functionality."""

    def __init__(self, page: Page):
        self.page = page
        self.search_input = page.locator("[data-testid='search-input']")
        self.search_button = page.locator("[data-testid='search-button']")
        self.results_list = page.locator("[data-testid='search-results']")
        self.result_items = page.locator("[data-testid='result-item']")
        self.no_results_message = page.locator("[data-testid='no-results']")

    def navigate(self):
        """Navigate to the search page."""
        self.page.goto("/search")
        return self

    def search_for(self, query: str):
        """Perform a search."""
        self.search_input.fill(query)
        self.search_button.click()
        return self

    def get_result_count(self) -> int:
        """Get number of search results."""
        return self.result_items.count()

    def click_result(self, index: int):
        """Click a specific result by index."""
        self.result_items.nth(index).click()
        return self

    def expect_results_visible(self):
        """Assert results are displayed."""
        expect(self.results_list).to_be_visible()
        return self

    def expect_no_results(self):
        """Assert no results message is shown."""
        expect(self.no_results_message).to_be_visible()
        return self
```

### E2E Test Structure

```python
# tests/e2e/playwright/test_search.py
import pytest
from playwright.sync_api import Page, expect

from tests.e2e.pages.search_page import SearchPage
from tests.e2e.pages.entity_detail_page import EntityDetailPage

@pytest.mark.e2e
@pytest.mark.playwright
class TestSearchFlow:
    """End-to-end tests for search functionality."""

    @pytest.fixture
    def search_page(self, page: Page) -> SearchPage:
        return SearchPage(page)

    def test_search_displays_matching_results(self, search_page: SearchPage):
        """Search returns and displays matching entities."""
        search_page.navigate()
        search_page.search_for("Apple Inc")

        search_page.expect_results_visible()
        assert search_page.get_result_count() > 0

    def test_search_shows_no_results_message(self, search_page: SearchPage):
        """Search for non-existent entity shows appropriate message."""
        search_page.navigate()
        search_page.search_for("xyznonexistent12345")

        search_page.expect_no_results()

    def test_clicking_result_navigates_to_detail(
        self, search_page: SearchPage, page: Page
    ):
        """Clicking a search result navigates to entity detail page."""
        search_page.navigate()
        search_page.search_for("Apple Inc")
        search_page.click_result(0)

        detail_page = EntityDetailPage(page)
        detail_page.expect_header_contains("Apple")
```

### Playwright Fixtures

```python
# tests/e2e/conftest.py
import pytest
from playwright.sync_api import Page, Browser, BrowserContext

@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context configuration."""
    return {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

@pytest.fixture
def authenticated_page(page: Page, test_user) -> Page:
    """Page with authenticated session."""
    page.goto("/login")
    page.fill("[data-testid='email']", test_user.email)
    page.fill("[data-testid='password']", test_user.password)
    page.click("[data-testid='login-button']")
    page.wait_for_url("**/dashboard")
    return page

@pytest.fixture
def api_seeded_data(api_client):
    """Seed test data via API before E2E tests."""
    entities = [
        {"name": "Apple Inc", "type": "COMPANY"},
        {"name": "Microsoft Corp", "type": "COMPANY"},
    ]
    created_ids = []
    for entity in entities:
        resp = api_client.post("/api/v1/entities", json=entity)
        created_ids.append(resp.json()["entity_id"])

    yield created_ids

    # Cleanup
    for entity_id in created_ids:
        api_client.delete(f"/api/v1/entities/{entity_id}")
```

---

## ⚡ Performance and Speed

### Mark Slow Tests

```python
@pytest.mark.slow
def test_bulk_import_10000_entities():
    """Importing 10K entities completes within timeout."""
    ...

# pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks integration tests
    e2e: marks end-to-end tests
    api: marks API tests
```

### Use pytest-xdist for Parallelization

```bash
# Run tests in parallel
pytest -n auto tests/unit/

# Run specific marks in parallel
pytest -n 4 -m "not slow and not e2e" tests/
```

### Scope Fixtures Appropriately

```python
# Session scope - once per test session
@pytest.fixture(scope="session")
def database_schema():
    """Create database schema once for all tests."""
    ...

# Module scope - once per test module
@pytest.fixture(scope="module")
def api_client():
    """Shared API client for module."""
    ...

# Function scope (default) - once per test
@pytest.fixture
def sample_entity():
    """Fresh entity for each test."""
    ...
```

---

## 📊 Coverage Requirements

### Minimum Coverage Targets

| Test Type | Coverage Target | Notes |
|-----------|-----------------|-------|
| Unit | 90%+ | Core domain logic |
| Integration | 80%+ | Critical paths |
| E2E | Key flows | Happy paths + error states |

### Coverage Configuration

```ini
# pytest.ini
[pytest]
addopts = --cov=src --cov-report=term-missing --cov-fail-under=85

# .coveragerc
[run]
branch = True
source = src/

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if TYPE_CHECKING:
```

---

## ✅ Test Quality Checklist

Use this checklist when reviewing tests:

### Structure
- [ ] Tests are in appropriate directory (unit/integration/e2e)
- [ ] Test file name matches module being tested
- [ ] Test function names describe the scenario
- [ ] Uses AAA pattern (Arrange-Act-Assert)

### Isolation
- [ ] Unit tests don't hit real databases/APIs/filesystem
- [ ] External dependencies are mocked
- [ ] Tests don't depend on execution order
- [ ] Each test can run independently

### Assertions
- [ ] Tests have meaningful assertions
- [ ] Error messages would help debug failures
- [ ] Edge cases are covered
- [ ] Both happy path and error paths tested

### Maintainability
- [ ] Uses fixtures for common setup
- [ ] Parametrized for multiple cases
- [ ] No magic numbers/strings without explanation
- [ ] DRY - common logic extracted

### Performance
- [ ] Unit tests run in < 100ms each
- [ ] Slow tests are marked appropriately
- [ ] Integration tests use transactions/rollback
- [ ] E2E tests use page objects

---

## 🚫 Anti-Patterns to Avoid

### ❌ Testing Implementation Details

```python
# BAD - Tests internal state
def test_resolver_internal_cache():
    resolver = EntityResolver()
    resolver.resolve(...)
    assert len(resolver._cache) == 1  # Testing private attribute
    assert resolver._last_query == "..."  # Implementation detail

# GOOD - Tests behavior
def test_resolver_returns_cached_result_on_second_call():
    resolver = EntityResolver()
    result1 = resolver.resolve(scheme=IdentifierScheme.LEI, value="...")
    result2 = resolver.resolve(scheme=IdentifierScheme.LEI, value="...")

    assert result1.entity_id == result2.entity_id
    # Optionally verify no additional API call was made
```

### ❌ Overly Complex Setup

```python
# BAD - 50 lines of setup
def test_entity_merge():
    entity1 = Entity(...)
    entity1 = entity1.add_identifier(...)
    entity1 = entity1.add_identifier(...)
    entity1 = entity1.add_alias(...)
    entity2 = Entity(...)
    entity2 = entity2.add_identifier(...)
    # ... 40 more lines

    result = entity1.merge(entity2)
    assert ...

# GOOD - Use fixtures and factories
def test_entity_merge(entity_with_identifiers, entity_factory):
    other = entity_factory.create(identifiers=["LEI", "CUSIP"])

    result = entity_with_identifiers.merge(other)

    assert len(result.identifiers) == 4
```

### ❌ Sleeping in Tests

```python
# BAD - Arbitrary sleep
def test_async_job_completes():
    start_job()
    time.sleep(5)  # Hope it's done by now
    assert job_is_complete()

# GOOD - Poll with timeout
def test_async_job_completes():
    job_id = start_job()

    # Wait for completion with timeout
    completed = wait_for(
        lambda: get_job_status(job_id) == "COMPLETE",
        timeout=10,
        poll_interval=0.5
    )

    assert completed, f"Job {job_id} did not complete in time"
```

### ❌ Ignoring Test Failures

```python
# BAD - Skipping without reason
@pytest.mark.skip
def test_flaky_integration():
    ...

# BAD - Catching and ignoring
def test_might_fail():
    try:
        result = risky_operation()
        assert result is not None
    except:
        pass  # Silently passes

# GOOD - Skip with reason and ticket
@pytest.mark.skip(reason="Flaky due to external API - see ISSUE-123")
def test_external_api_integration():
    ...
```

---

## 🏭 Test Data Factories

### Factory Pattern

```python
# tests/fixtures/factory.py
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date
import uuid

from entityspine.domain import Entity, EntityType, IdentifierClaim, IdentifierScheme

@dataclass
class EntityFactory:
    """Factory for creating test entities with sensible defaults."""

    _counter: int = field(default=0, repr=False)

    def create(
        self,
        *,
        entity_id: Optional[str] = None,
        entity_type: EntityType = EntityType.COMPANY,
        name: Optional[str] = None,
        identifiers: Optional[List[str]] = None,
    ) -> Entity:
        """Create a test entity with optional overrides.

        Args:
            entity_id: Custom ID or auto-generated
            entity_type: Type of entity
            name: Display name or auto-generated
            identifiers: List of identifier schemes to add (e.g., ["LEI", "CIK"])

        Returns:
            Configured Entity instance
        """
        self._counter += 1

        entity = Entity(
            entity_id=entity_id or f"ent_test_{self._counter:04d}",
            entity_type=entity_type,
            name=name or f"Test {entity_type.value.title()} {self._counter}",
        )

        if identifiers:
            for scheme_name in identifiers:
                scheme = IdentifierScheme[scheme_name]
                entity = entity.add_identifier(
                    scheme=scheme,
                    value=self._generate_identifier(scheme),
                    source="test_factory"
                )

        return entity

    def _generate_identifier(self, scheme: IdentifierScheme) -> str:
        """Generate a valid-format identifier for the scheme."""
        if scheme == IdentifierScheme.LEI:
            return f"5493{self._counter:016d}"[:20]
        elif scheme == IdentifierScheme.CIK:
            return f"{self._counter:010d}"
        elif scheme == IdentifierScheme.CUSIP:
            return f"{self._counter:09d}"[:9]
        else:
            return f"TEST_{scheme.value}_{self._counter}"


# Usage in conftest.py
@pytest.fixture
def entity_factory():
    """Factory for creating test entities."""
    return EntityFactory()
```

---

## 🔧 pytest.ini Template

```ini
[pytest]
# Paths
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Markers
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (with real dependencies)
    e2e: End-to-end tests (full stack)
    api: API endpoint tests
    database: Tests requiring database
    slow: Slow-running tests
    playwright: Playwright browser tests

# Output
addopts =
    -v
    --tb=short
    --strict-markers
    -ra

# Coverage (optional, or use in CI)
# addopts = --cov=src --cov-report=term-missing

# Async
asyncio_mode = auto

# Timeouts
timeout = 30
timeout_method = thread
```

---

## 🚀 CI/CD Test Stages

```yaml
# Example GitHub Actions workflow
test:
  stages:
    - name: Unit Tests
      run: pytest tests/unit/ -n auto --cov=src

    - name: Integration Tests
      run: pytest tests/integration/ -m "not slow"
      services:
        - postgres

    - name: E2E Tests
      run: pytest tests/e2e/ --browser chromium

    - name: Full Suite (nightly)
      run: pytest --run-slow
      schedule: "0 2 * * *"
```

---

## 📋 Quick Reference Commands

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific marker
pytest -m "integration and not slow"

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v --tb=long

# Run specific test
pytest tests/unit/test_entity.py::test_entity_merge_combines_identifiers

# Run Playwright tests
pytest tests/e2e/playwright/ --browser chromium --headed

# Generate coverage report
pytest --cov=src --cov-report=html && open htmlcov/index.html
```
