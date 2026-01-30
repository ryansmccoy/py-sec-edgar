# Integration Improvements Backlog

**Created:** January 26, 2026
**Status:** Backlog for future improvements
**Priority:** After Phase 5 completion

---

## Overview

These are integration improvements identified during the Phase 3/4 refactoring. They are not blockers for Phase 5 but would improve code quality and consistency.

---

## HIGH Priority

### 1. CIK Normalization Duplication (8+ places)

**Issue:** CIK normalization (`str(cik).lstrip("0").zfill(10)`) is duplicated in 8+ places.

**Locations:**
- `entityspine/src/entityspine/services/symbology_refresh.py:305`
- `entityspine/src/entityspine/sources/sec.py:106`
- `entityspine/src/entityspine/adapters/feedspine_adapter.py:198, 269`
- `feedspine/src/feedspine/enricher/entity_enricher.py:244`
- `py_sec_edgar/src/py_sec_edgar/services/entity_service.py:249, 294`
- `py_sec_edgar/src/py_sec_edgar/services/filing_facts_generator.py:219`
- `py_sec_edgar/src/py_sec_edgar/integrations/entityspine.py:175, 188, 254`

**Solution:** Add `normalize_cik()` to `py_sec_edgar/integrations/` and use everywhere.

```python
def normalize_cik(cik: str | int) -> str:
    """Normalize CIK to 10-digit zero-padded string."""
    return str(cik).lstrip("0").zfill(10)
```

---

### 2. FilingFacts Ingestion Not Wired

**Issue:** `FilingFactsGenerator` creates FilingFacts but `ingest_filing_facts()` is never called.

**Location:** `py_sec_edgar/src/py_sec_edgar/services/filing_facts_generator.py`

**Solution:** Add pipeline to call `ingest_filing_facts(store, facts)` after generation.

---

### 3. Duplicate Company Services

**Issue:** Two parallel implementations for ticker/CIK lookup:
- `py_sec_edgar/core/company_service.py` (local tickers.json)
- `py_sec_edgar/services/entity_service.py` (EntitySpine)

Both download SEC company_tickers.json independently.

**Solution:** Consolidate into `entity_service.py` only. Use EntitySpine when available, fall back to in-memory index.

---

## MEDIUM Priority

### 4. FeedSpine Underutilization

**Issue:** FeedSpine is used for RSS/index collection but not for:
- Filing document download tracking
- Download deduplication
- Scheduling/rate limiting

**Solution:** Create `create_sec_document_record()` with natural_key for document downloads.

---

### 5. Evidence Fields Not Populated

**Issue:** `FilingFacts.evidence.section` and `evidence.page` are always None.

**Location:** `py_sec_edgar/src/py_sec_edgar/services/filing_facts_generator.py`

**Solution:** Populate section (e.g., "Item 1A") and page when generating FilingFacts.

---

### 6. EntityEnricher Not Auto-Registered

**Issue:** FeedSpine's `EntityEnricher` exists but isn't registered by default in py-sec-edgar collectors.

**Solution:** Auto-register when both EntitySpine and FeedSpine are available.

---

## LOW Priority

### 7. HTTP Client Consolidation

**Issue:** Some places use raw `httpx.get()` bypassing the centralized HTTP client.

**Locations:**
- `py_sec_edgar/utils/ticker_lookup.py`
- Some test files

**Solution:** Use centralized client for consistent rate limiting.

---

### 8. Shared Extraction Patterns

**Issue:** Company name extraction patterns could be shared between EntitySpine and py-sec-edgar.

**Solution:** Move patterns to EntitySpine's integration module for reuse.

---

## Notes

- These improvements are OPTIONAL for Phase 5
- Phase 5 (Section Extraction + Entity Resolution) is the priority
- Address these after Phase 5 is complete and working
