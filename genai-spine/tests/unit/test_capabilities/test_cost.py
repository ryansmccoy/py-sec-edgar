"""Unit tests for cost tracking module."""

from __future__ import annotations

from decimal import Decimal

import pytest

from genai_spine.capabilities.cost import (
    MODEL_COSTS,
    calculate_cost,
    estimate_cost,
    get_model_pricing,
    list_model_pricing,
)


class TestModelCosts:
    """Tests for MODEL_COSTS dictionary."""

    def test_has_openai_models(self):
        """OpenAI models are defined."""
        assert "gpt-4o" in MODEL_COSTS
        assert "gpt-4o-mini" in MODEL_COSTS
        assert "gpt-4-turbo" in MODEL_COSTS

    def test_has_anthropic_models(self):
        """Anthropic models are defined."""
        assert "claude-sonnet-4-20250514" in MODEL_COSTS
        assert "claude-3-5-sonnet-20241022" in MODEL_COSTS
        assert "claude-3-5-haiku-20241022" in MODEL_COSTS

    def test_has_ollama_models(self):
        """Ollama (free) models are defined."""
        assert "llama3.2:latest" in MODEL_COSTS
        assert "llama3:latest" in MODEL_COSTS
        # Ollama models should be free (tuple format)
        assert MODEL_COSTS["llama3.2:latest"][0] == 0.0
        assert MODEL_COSTS["llama3.2:latest"][1] == 0.0

    def test_model_cost_structure(self):
        """Each model cost is a (input, output) tuple."""
        for model, costs in MODEL_COSTS.items():
            assert isinstance(costs, tuple), f"Model {model} costs not tuple"
            assert len(costs) == 2, f"Model {model} costs should have 2 elements"
            assert isinstance(costs[0], (int, float)), f"Model {model} input not numeric"
            assert isinstance(costs[1], (int, float)), f"Model {model} output not numeric"


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_zero_tokens_is_zero_cost(self):
        """Zero tokens should have zero cost."""
        result = calculate_cost("gpt-4o", 0, 0)
        assert result == Decimal("0")

    def test_input_only_tokens(self):
        """Calculate cost with only input tokens."""
        # gpt-4o: $2.50 / 1M tokens input
        result = calculate_cost("gpt-4o", 1_000_000, 0)
        assert result == Decimal("2.50")

    def test_output_only_tokens(self):
        """Calculate cost with only output tokens."""
        # gpt-4o: $10.00 / 1M tokens output
        result = calculate_cost("gpt-4o", 0, 1_000_000)
        assert result == Decimal("10.00")

    def test_combined_tokens(self):
        """Calculate cost with both input and output tokens."""
        # 1K input tokens at $2.50/M = $0.0025
        # 500 output tokens at $10.00/M = $0.005
        result = calculate_cost("gpt-4o", 1000, 500)
        expected = Decimal("0.0025") + Decimal("0.005")
        assert result == expected

    def test_unknown_model_is_zero(self):
        """Unknown models should return zero cost."""
        result = calculate_cost("unknown-model-xyz", 1000, 1000)
        assert result == Decimal("0")

    def test_ollama_is_free(self):
        """Ollama models should be free."""
        result = calculate_cost("llama3.2:latest", 10000, 10000)
        assert result == Decimal("0")


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_estimate_basic(self):
        """Basic cost estimation."""
        result = estimate_cost("gpt-4o", 1000, 500)
        assert "model" in result
        assert "estimated_cost_usd" in result
        assert "estimated_input_tokens" in result
        assert "estimated_output_tokens" in result
        assert result["model"] == "gpt-4o"
        assert result["estimated_input_tokens"] == 1000
        assert result["estimated_output_tokens"] == 500

    def test_estimate_includes_pricing(self):
        """Estimation includes pricing details."""
        result = estimate_cost("gpt-4o", 1000, 500)
        assert "input_cost_per_1m" in result
        assert "output_cost_per_1m" in result
        assert "is_free" in result


class TestGetModelPricing:
    """Tests for get_model_pricing function."""

    def test_known_model(self):
        """Get pricing for a known model."""
        result = get_model_pricing("gpt-4o")
        assert result is not None
        assert result["model"] == "gpt-4o"
        assert "input_cost_per_1m_tokens" in result
        assert "output_cost_per_1m_tokens" in result

    def test_unknown_model_returns_none(self):
        """Unknown model returns None."""
        result = get_model_pricing("unknown-model")
        assert result is None


class TestListModelPricing:
    """Tests for list_model_pricing function."""

    def test_returns_all_models(self):
        """Returns pricing for all models."""
        result = list_model_pricing()
        assert len(result) == len(MODEL_COSTS)

    def test_each_entry_has_required_fields(self):
        """Each entry has model, input, output pricing."""
        result = list_model_pricing()
        for item in result:
            assert "model" in item
            assert "input_cost_per_1m_tokens" in item
            assert "output_cost_per_1m_tokens" in item
