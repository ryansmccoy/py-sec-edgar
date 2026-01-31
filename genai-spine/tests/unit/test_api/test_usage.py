"""Unit tests for usage API router."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


class TestUsageEndpoints:
    """Tests for /v1/usage, /v1/pricing endpoints."""

    @pytest.mark.asyncio
    async def test_get_pricing_list(self, client: AsyncClient):
        """Test GET /v1/pricing returns model pricing list."""
        response = await client.get("/v1/pricing")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check structure of first item
        first = data[0]
        assert "model" in first
        assert "input_cost_per_1m_tokens" in first
        assert "output_cost_per_1m_tokens" in first
        assert "is_free" in first

    @pytest.mark.asyncio
    async def test_get_pricing_for_model(self, client: AsyncClient):
        """Test GET /v1/pricing/{model} returns specific model pricing."""
        response = await client.get("/v1/pricing/gpt-4o")

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o"
        assert "input_cost_per_1m_tokens" in data
        assert "output_cost_per_1m_tokens" in data

    @pytest.mark.asyncio
    async def test_get_pricing_unknown_model(self, client: AsyncClient):
        """Test GET /v1/pricing/{model} with unknown model returns null."""
        response = await client.get("/v1/pricing/unknown-model-xyz")

        # Returns 200 with null body for unknown models
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_estimate_cost(self, client: AsyncClient):
        """Test POST /v1/estimate-cost returns cost estimation."""
        response = await client.post(
            "/v1/estimate-cost",
            json={
                "model": "gpt-4o",
                "estimated_input_tokens": 1000,
                "estimated_output_tokens": 500,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "gpt-4o"
        assert data["estimated_input_tokens"] == 1000
        assert data["estimated_output_tokens"] == 500
        assert "estimated_cost_usd" in data
        assert data["estimated_cost_usd"] > 0

    @pytest.mark.asyncio
    async def test_estimate_cost_free_model(self, client: AsyncClient):
        """Test cost estimation for free model (Ollama)."""
        response = await client.post(
            "/v1/estimate-cost",
            json={
                "model": "llama3.2:latest",
                "estimated_input_tokens": 10000,
                "estimated_output_tokens": 5000,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["estimated_cost_usd"] == 0

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, client: AsyncClient):
        """Test GET /v1/usage returns usage statistics."""
        response = await client.get("/v1/usage")

        assert response.status_code == 200
        data = response.json()
        # The endpoint should return stats even if empty
        assert "total_requests" in data
        assert "total_input_tokens" in data
        assert "total_output_tokens" in data
        assert "total_cost_usd" in data

    @pytest.mark.asyncio
    async def test_get_usage_stats_with_date_filter(self, client: AsyncClient):
        """Test GET /v1/usage with date filters."""
        response = await client.get(
            "/v1/usage",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
