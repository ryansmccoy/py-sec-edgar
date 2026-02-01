"""Cost tracking and calculation for LLM providers.

Provides model pricing and cost calculation functions for
tracking LLM usage costs across all providers.
"""

from __future__ import annotations

from decimal import Decimal

# =============================================================================
# Model Pricing (per 1M tokens)
# =============================================================================

# Format: (input_cost_per_1m, output_cost_per_1m)
MODEL_COSTS: dict[str, tuple[float, float]] = {
    # OpenAI models
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1-preview": (15.00, 60.00),
    "o1-mini": (3.00, 12.00),
    "o3-mini": (1.10, 4.40),
    # Anthropic models
    "claude-sonnet-4-20250514": (3.00, 15.00),
    "claude-3-5-sonnet-20241022": (3.00, 15.00),
    "claude-3-5-haiku-20241022": (0.80, 4.00),
    "claude-3-opus-20240229": (15.00, 75.00),
    "claude-3-sonnet-20240229": (3.00, 15.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
    # AWS Bedrock models
    "amazon.nova-lite-v1:0": (0.06, 0.24),
    "amazon.nova-micro-v1:0": (0.035, 0.14),
    "amazon.nova-pro-v1:0": (0.80, 3.20),
    "anthropic.claude-3-sonnet-20240229-v1:0": (3.00, 15.00),
    "anthropic.claude-3-haiku-20240307-v1:0": (0.25, 1.25),
    # Ollama models (local, free)
    "llama3.2:latest": (0.0, 0.0),
    "llama3.2:3b": (0.0, 0.0),
    "llama3.2:1b": (0.0, 0.0),
    "llama3.1:latest": (0.0, 0.0),
    "llama3.1:8b": (0.0, 0.0),
    "llama3.1:70b": (0.0, 0.0),
    "llama3:latest": (0.0, 0.0),
    "mistral:latest": (0.0, 0.0),
    "mixtral:latest": (0.0, 0.0),
    "codellama:latest": (0.0, 0.0),
    "qwen2.5:latest": (0.0, 0.0),
    "deepseek-coder:latest": (0.0, 0.0),
    "phi3:latest": (0.0, 0.0),
    "gemma2:latest": (0.0, 0.0),
}

# Provider to model prefix mapping (for fuzzy matching)
PROVIDER_PREFIXES = {
    "openai": ["gpt-", "o1-", "o3-"],
    "anthropic": ["claude-"],
    "bedrock": ["amazon.", "anthropic."],
    "ollama": [],  # Local models, varies
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """Calculate the cost for an LLM call.

    Args:
        model: The model name/identifier
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Cost in USD as a Decimal
    """
    # Look up exact model first
    costs = MODEL_COSTS.get(model)

    # Try fuzzy matching if not found
    if costs is None:
        for known_model in MODEL_COSTS:
            if model.startswith(known_model.split(":")[0]):
                costs = MODEL_COSTS[known_model]
                break

    # Default to free if unknown (local model assumed)
    if costs is None:
        costs = (0.0, 0.0)

    input_cost, output_cost = costs

    # Calculate cost (costs are per 1M tokens)
    total = (input_tokens / 1_000_000) * input_cost + (output_tokens / 1_000_000) * output_cost

    return Decimal(str(round(total, 6)))


def estimate_cost(
    model: str,
    estimated_input_tokens: int,
    estimated_output_tokens: int,
) -> dict:
    """Estimate cost before making an LLM call.

    Args:
        model: The model to use
        estimated_input_tokens: Estimated input tokens
        estimated_output_tokens: Estimated output tokens

    Returns:
        Dict with estimated costs and model info
    """
    cost = calculate_cost(model, estimated_input_tokens, estimated_output_tokens)
    costs = MODEL_COSTS.get(model, (0.0, 0.0))

    return {
        "model": model,
        "estimated_input_tokens": estimated_input_tokens,
        "estimated_output_tokens": estimated_output_tokens,
        "estimated_cost_usd": float(cost),
        "input_cost_per_1m": costs[0],
        "output_cost_per_1m": costs[1],
        "is_free": costs[0] == 0.0 and costs[1] == 0.0,
    }


def get_model_pricing(model: str) -> dict | None:
    """Get pricing info for a specific model.

    Args:
        model: The model name

    Returns:
        Pricing dict or None if not found
    """
    costs = MODEL_COSTS.get(model)
    if costs is None:
        return None

    return {
        "model": model,
        "input_cost_per_1m_tokens": costs[0],
        "output_cost_per_1m_tokens": costs[1],
        "is_free": costs[0] == 0.0 and costs[1] == 0.0,
    }


def list_model_pricing() -> list[dict]:
    """Get pricing for all known models.

    Returns:
        List of pricing dicts for all models
    """
    return [
        {
            "model": model,
            "input_cost_per_1m_tokens": costs[0],
            "output_cost_per_1m_tokens": costs[1],
            "is_free": costs[0] == 0.0 and costs[1] == 0.0,
        }
        for model, costs in sorted(MODEL_COSTS.items())
    ]


def get_provider_for_model(model: str) -> str | None:
    """Determine the provider for a model based on naming patterns.

    Args:
        model: The model name

    Returns:
        Provider name or None if unknown
    """
    for provider, prefixes in PROVIDER_PREFIXES.items():
        for prefix in prefixes:
            if model.startswith(prefix):
                return provider

    # Check if it's a known local model
    if model in MODEL_COSTS and MODEL_COSTS[model] == (0.0, 0.0):
        return "ollama"

    return None
