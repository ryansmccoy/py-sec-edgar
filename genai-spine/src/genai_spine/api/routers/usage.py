"""Usage statistics and cost tracking endpoints."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from genai_spine.api.deps import UnitOfWorkDep
from genai_spine.capabilities.cost import get_model_pricing, list_model_pricing

router = APIRouter()


# =============================================================================
# Response Models
# =============================================================================


class ProviderStats(BaseModel):
    """Stats for a single provider."""

    provider: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float


class ModelStats(BaseModel):
    """Stats for a single model."""

    model: str
    provider: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float


class DailyStats(BaseModel):
    """Stats for a single day."""

    date: str
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float


class UsageResponse(BaseModel):
    """Complete usage statistics response."""

    # Summary
    period_start: str
    period_end: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    avg_latency_ms: float

    # Breakdowns
    by_provider: list[ProviderStats]
    by_model: list[ModelStats]
    daily_breakdown: list[DailyStats]


class ModelPricing(BaseModel):
    """Model pricing information."""

    model: str
    input_cost_per_1m_tokens: float
    output_cost_per_1m_tokens: float
    is_free: bool


class CostEstimateRequest(BaseModel):
    """Request to estimate cost."""

    model: str = Field(..., description="Model to estimate cost for")
    estimated_input_tokens: int = Field(..., ge=0)
    estimated_output_tokens: int = Field(..., ge=0)


class CostEstimateResponse(BaseModel):
    """Cost estimate response."""

    model: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    input_cost_per_1m: float
    output_cost_per_1m: float
    is_free: bool


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats(
    uow: UnitOfWorkDep,
    start_date: date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="End date (YYYY-MM-DD)"),
) -> UsageResponse:
    """Get usage statistics for a date range.

    Returns aggregated statistics including:
    - Total requests, tokens, and costs
    - Breakdown by provider
    - Breakdown by model
    - Daily breakdown

    Defaults to the last 30 days if no dates provided.
    """
    # Default to last 30 days
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    since = datetime.combine(start_date, datetime.min.time())
    until = datetime.combine(end_date, datetime.max.time())

    # Get all executions in date range
    executions, total = await uow.executions.list(
        since=since,
        until=until,
        limit=10000,  # Get all for aggregation
    )

    # Aggregate stats
    total_requests = len(executions)
    successful = [e for e in executions if e.success]
    failed = [e for e in executions if not e.success]

    total_input_tokens = sum(e.input_tokens for e in executions)
    total_output_tokens = sum(e.output_tokens for e in executions)
    total_cost = sum(float(e.cost_usd) for e in executions)

    avg_latency = (
        sum(e.latency_ms for e in executions) / total_requests if total_requests > 0 else 0.0
    )

    # Group by provider
    providers: dict[str, dict] = {}
    for e in executions:
        if e.provider not in providers:
            providers[e.provider] = {
                "provider": e.provider,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "total_latency_ms": 0,
            }
        p = providers[e.provider]
        p["total_requests"] += 1
        if e.success:
            p["successful_requests"] += 1
        else:
            p["failed_requests"] += 1
        p["total_input_tokens"] += e.input_tokens
        p["total_output_tokens"] += e.output_tokens
        p["total_cost_usd"] += float(e.cost_usd)
        p["total_latency_ms"] += e.latency_ms

    by_provider = [
        ProviderStats(
            provider=p["provider"],
            total_requests=p["total_requests"],
            successful_requests=p["successful_requests"],
            failed_requests=p["failed_requests"],
            total_input_tokens=p["total_input_tokens"],
            total_output_tokens=p["total_output_tokens"],
            total_cost_usd=round(p["total_cost_usd"], 4),
            avg_latency_ms=round(p["total_latency_ms"] / p["total_requests"], 1)
            if p["total_requests"] > 0
            else 0.0,
        )
        for p in providers.values()
    ]

    # Group by model
    models: dict[str, dict] = {}
    for e in executions:
        key = f"{e.provider}:{e.model}"
        if key not in models:
            models[key] = {
                "model": e.model,
                "provider": e.provider,
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
                "total_latency_ms": 0,
            }
        m = models[key]
        m["total_requests"] += 1
        m["total_input_tokens"] += e.input_tokens
        m["total_output_tokens"] += e.output_tokens
        m["total_cost_usd"] += float(e.cost_usd)
        m["total_latency_ms"] += e.latency_ms

    by_model = [
        ModelStats(
            model=m["model"],
            provider=m["provider"],
            total_requests=m["total_requests"],
            total_input_tokens=m["total_input_tokens"],
            total_output_tokens=m["total_output_tokens"],
            total_cost_usd=round(m["total_cost_usd"], 4),
            avg_latency_ms=round(m["total_latency_ms"] / m["total_requests"], 1)
            if m["total_requests"] > 0
            else 0.0,
        )
        for m in models.values()
    ]

    # Group by day
    days: dict[str, dict] = {}
    for e in executions:
        day = e.created_at.strftime("%Y-%m-%d")
        if day not in days:
            days[day] = {
                "date": day,
                "total_requests": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cost_usd": 0.0,
            }
        d = days[day]
        d["total_requests"] += 1
        d["total_input_tokens"] += e.input_tokens
        d["total_output_tokens"] += e.output_tokens
        d["total_cost_usd"] += float(e.cost_usd)

    daily_breakdown = [
        DailyStats(
            date=d["date"],
            total_requests=d["total_requests"],
            total_input_tokens=d["total_input_tokens"],
            total_output_tokens=d["total_output_tokens"],
            total_cost_usd=round(d["total_cost_usd"], 4),
        )
        for d in sorted(days.values(), key=lambda x: x["date"])
    ]

    return UsageResponse(
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        total_requests=total_requests,
        successful_requests=len(successful),
        failed_requests=len(failed),
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_cost_usd=round(total_cost, 4),
        avg_latency_ms=round(avg_latency, 1),
        by_provider=by_provider,
        by_model=by_model,
        daily_breakdown=daily_breakdown,
    )


@router.get("/pricing", response_model=list[ModelPricing])
async def get_all_pricing() -> list[ModelPricing]:
    """Get pricing information for all known models.

    Returns cost per 1M tokens for input and output.
    """
    return [ModelPricing(**p) for p in list_model_pricing()]


@router.get("/pricing/{model}", response_model=ModelPricing | None)
async def get_model_price(model: str) -> ModelPricing | None:
    """Get pricing information for a specific model.

    Returns None if model is not in the pricing database.
    """
    pricing = get_model_pricing(model)
    if pricing is None:
        return None
    return ModelPricing(**pricing)


@router.post("/estimate-cost", response_model=CostEstimateResponse)
async def estimate_cost(request: CostEstimateRequest) -> CostEstimateResponse:
    """Estimate cost for an LLM call before execution.

    Useful for budgeting and cost warnings.
    """
    from genai_spine.capabilities.cost import estimate_cost as calc_estimate

    estimate = calc_estimate(
        request.model,
        request.estimated_input_tokens,
        request.estimated_output_tokens,
    )

    return CostEstimateResponse(**estimate)
