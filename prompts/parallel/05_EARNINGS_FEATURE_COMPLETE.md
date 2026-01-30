# Prompt 05: Earnings Feature - Complete Implementation

## Context
You are implementing the **Earnings Estimates vs Actuals** feature across multiple packages.

**CRITICAL**: This feature spans ALL projects:
```
py-sec-edgar (8-K fetching)
    → feedspine (observations, comparison engine)
    → entityspine (domain enums)
    → spine-core (pipelines, workflows)
    → capture-spine (UI, alerts)
```

## Existing Documentation
Read these files for full context:
- `feedspine/docs/features/estimates-vs-actuals/01_DESIGN.md` (861 lines)
- `feedspine/docs/features/estimates-vs-actuals/02_IMPLEMENTATION_PLAN.md` (592 lines)
- `feedspine/docs/features/estimates-vs-actuals/05_SPINE_CORE_INTEGRATION.md` (761 lines)
- `feedspine/docs/features/estimates-vs-actuals/06_CAPTURE_SPINE_INTEGRATION.md` (255 lines)

## Key Design Decisions (from docs)

### Two-Timestamp Pattern
```python
class EstimateActualComparison:
    """Critical: separate estimate_as_of from actual_date"""
    symbol: str
    fiscal_quarter: str
    fiscal_year: int

    # Estimate context
    estimate_as_of: datetime      # When we captured the estimate
    consensus_eps: Decimal

    # Actual context
    actual_date: datetime         # When actual was announced
    actual_eps: Decimal

    # Derived
    surprise_percent: Decimal
    beat_miss: Literal["BEAT", "MISS", "MEET"]
```

### Pre-Announcement Estimate Problem
**SOLVED BY**: `get_pre_announcement_estimate(symbol, actual_date)`
- Returns the estimate that was in effect BEFORE the announcement
- Not the post-revision estimate

## Implementation Phases

### Phase 1: Core Comparison Engine (feedspine)
Location: `feedspine/earnings/`

1. **ComparisonResult dataclass** - Already designed, verify implementation
2. **EarningsCalendarService** - Mostly exists, add comparison methods
3. **Historical tracking** - Store estimate snapshots over time

Files to check/create:
- `feedspine/earnings/service.py` - Main service
- `feedspine/earnings/comparison.py` - Comparison logic
- `feedspine/earnings/models.py` - Data models

### Phase 2: Connectors (feedspine + py-sec-edgar)

**Polygon Connector** (for estimates):
```python
# feedspine/connectors/polygon/earnings.py
class PolygonEarningsConnector:
    async def get_earnings_calendar(self, date_from, date_to) -> List[EarningsEvent]
    async def get_estimates(self, symbol) -> List[EstimateSnapshot]
```

**8-K Connector** (for actuals via py-sec-edgar):
```python
# Link to existing py-sec-edgar 8-K fetching
# Detect earnings announcements from 8-K Item 2.02
```

### Phase 3: Spine-Core Pipelines

Location: `spine-core/spine_domains/earnings/`

```python
# Pipeline definition
class IngestCalendarPipeline(Pipeline):
    """Ingest earnings calendar from Polygon."""
    steps = [
        Step.fetch("fetch_calendar", fetch_polygon_calendar),
        Step.transform("parse_events", parse_calendar_events),
        Step.store("store_events", store_to_feedspine),
    ]

class EnrichEstimatesPipeline(Pipeline):
    """Enrich with estimate data."""
    steps = [
        Step.fetch("fetch_estimates", fetch_estimates),
        Step.transform("compare", compare_to_actuals),
        Step.observe("create_observations", create_surprise_observations),
    ]
```

### Phase 4: Capture-Spine UI

Location: `capture-spine/frontend/`

1. **Earnings Calendar View** - Upcoming earnings with estimates
2. **Comparison Table** - Symbol | Q | Est EPS | Act EPS | Surprise | Beat/Miss
3. **Alerts** - Configure alerts for portfolio symbols
4. **Historical Chart** - Show estimate revisions over time

## Your Task (Pick One Phase)

### Option A: Verify Phase 1 (feedspine core)
1. Read existing `feedspine/earnings/service.py`
2. Check if `ComparisonResult` class exists and matches design
3. Verify `compare_estimate_to_actual()` method works
4. Add missing methods if needed
5. Add tests

### Option B: Implement Polygon Connector
1. Create `feedspine/connectors/polygon/earnings.py`
2. Implement calendar and estimates fetching
3. Add tests with mocked responses

### Option C: Implement Spine-Core Pipelines
1. Create `spine-core/spine_domains/earnings/` if not exists
2. Implement `IngestCalendarPipeline`
3. Register with Pipeline registry
4. Add workflow definition

### Option D: Start Capture-Spine UI
1. Create earnings calendar component
2. Create comparison table component
3. Add API endpoints if missing
4. Wire up to frontend

## Success Criteria (by phase)

### Phase 1
- [ ] `EarningsCalendarService.compare_estimate_to_actual(symbol, quarter)` works
- [ ] `get_pre_announcement_estimate(symbol, actual_date)` returns correct estimate
- [ ] Historical estimates are preserved
- [ ] Tests cover edge cases

### Phase 2
- [ ] Polygon connector fetches real data
- [ ] 8-K item detection works
- [ ] Connectors have retry/error handling

### Phase 3
- [ ] Pipelines registered with spine-core
- [ ] Can run: `spine run earnings:ingest-calendar`
- [ ] Workflow tracking works

### Phase 4
- [ ] Calendar view shows upcoming earnings
- [ ] Comparison table displays correctly
- [ ] Alerts can be configured
- [ ] UI matches capture-spine design

## Notes
- Start with Phase 1 to verify core logic
- Each phase builds on previous
- Use existing patterns from each project
- Check `feedspine/examples/earnings/` for example usage
