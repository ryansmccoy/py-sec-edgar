# SEC Entity Refactoring Plan

## Goal

Make `entityspine` the single source of truth for base Entity models while `py-sec-edgar` provides SEC-specific convenience extensions.

## Current State

### EntitySpine (v0.3.3)
- **Entity**: Immutable stdlib dataclass, ULID-based, NO identifier shortcuts
- **IdentifierClaim**: Separate records for identifiers with provenance
- **EntityType**: ORGANIZATION, PERSON, FUND, TRUST, GOVERNMENT, etc.
- **EntityStatus**: ACTIVE, INACTIVE, MERGED, PROVISIONAL

### Py-Sec-Edgar (current)
- **Entity**: Mutable dataclass, UUID-based, HAS identifier shortcuts (`.cik`, `.lei`)
- **Identifier**: Embedded in Entity as list
- **EntityType**: COMPANY, FUND, PERSON, GOVERNMENT, SECURITY, UNKNOWN
- **EntityStatus**: ACTIVE, INACTIVE, UNVERIFIED, MERGED

## Key Differences

| Aspect | EntitySpine | Py-Sec-Edgar |
|--------|-------------|--------------|
| Immutability | Frozen dataclass | Mutable dataclass |
| ID Type | ULID | UUID |
| Identifiers | Separate IdentifierClaim table | Embedded list |
| Shortcuts | None (use IdentifierClaim) | `.cik`, `.lei`, `.ticker` |
| EntityType | 10 values (ORGANIZATION-based) | 7 values (COMPANY-based) |

## Proposed Solution

### Phase 1: Add EntitySpine Dependency

```toml
# py_sec_edgar/pyproject.toml
dependencies = [
    "entityspine>=0.3.3",  # Add this
    ...
]
```

### Phase 2: Create SEC Adapter Module

Create `py_sec_edgar/core/identity/adapters.py`:

```python
"""Adapters between entityspine domain models and py-sec-edgar convenience wrappers."""

from entityspine.domain.entity import Entity as BaseEntity
from entityspine.domain.enums import EntityType as BaseEntityType, EntityStatus as BaseEntityStatus
from entityspine.domain.claim import IdentifierClaim
from entityspine.domain.enums import IdentifierScheme

# Re-export base types for backwards compatibility
Entity = BaseEntity
EntityType = BaseEntityType
EntityStatus = BaseEntityStatus

def entity_with_cik(entity: BaseEntity, cik: str) -> tuple[BaseEntity, IdentifierClaim]:
    """Create entity with CIK identifier claim."""
    claim = IdentifierClaim(
        scheme=IdentifierScheme.CIK,
        value=cik,
        entity_id=entity.entity_id,
    )
    return entity, claim

def get_cik(entity: BaseEntity, claims: list[IdentifierClaim]) -> str | None:
    """Get CIK from entity's identifier claims."""
    for claim in claims:
        if claim.entity_id == entity.entity_id and claim.scheme == IdentifierScheme.CIK:
            return claim.value
    return None
```

### Phase 3: Backwards Compatibility Wrapper (Optional)

If needed for migration, create `SECEntity` wrapper with old convenience API:

```python
@dataclass
class SECEntity:
    """SEC-specific entity wrapper with convenience identifier access."""

    entity: BaseEntity
    claims: list[IdentifierClaim] = field(default_factory=list)

    @property
    def cik(self) -> str | None:
        return get_cik(self.entity, self.claims)

    @property
    def lei(self) -> str | None:
        return get_identifier(self.entity, self.claims, IdentifierScheme.LEI)

    @property
    def ticker(self) -> str | None:
        return get_identifier(self.entity, self.claims, IdentifierScheme.TICKER)
```

### Phase 4: Update Imports

Update all py-sec-edgar files to import from entityspine:

```python
# Before
from py_sec_edgar.core.identity.entity import Entity, EntityType, EntityStatus

# After
from entityspine.domain.entity import Entity
from entityspine.domain.enums import EntityType, EntityStatus

# Or via adapter
from py_sec_edgar.core.identity.adapters import Entity, EntityType, EntityStatus
```

## Migration Strategy

1. **Add dependency** - No code changes yet
2. **Create adapters** - Parallel implementation
3. **Deprecation warnings** - Warn on old imports
4. **Update callers** - One module at a time
5. **Remove duplicates** - After all callers updated

## Files to Update

### Keep (SEC-specific)
- `filing.py` - SEC Filing model (uses CIK, AccessionNumber)
- `cik.py` - CIK validation/normalization
- `accession.py` - AccessionNumber parsing
- `registry.py` - EntityRegistry (may need adapter)
- `store.py` - EntityStore (may need adapter)

### Remove/Replace
- `entity.py` - Replace with entityspine Entity + adapters
- `identifiers.py` - Replace with entityspine IdentifierClaim

## Testing Strategy

1. Run existing tests with adapters
2. Verify backwards compatibility
3. Add integration tests for entityspine → py-sec-edgar flow
