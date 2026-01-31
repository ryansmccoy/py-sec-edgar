"""Classification capability."""

from __future__ import annotations

import json
import logging
from typing import Any

from genai_spine.providers.base import CompletionRequest, LLMProvider

logger = logging.getLogger(__name__)


CLASSIFICATION_SYSTEM_PROMPT = """You are an expert content classifier. Your task is to accurately categorize text into the provided categories.

Guidelines:
- Choose the most appropriate category/categories
- Provide confidence scores (0.0 to 1.0)
- Be consistent in your classifications
- Always return valid JSON"""

CLASSIFICATION_USER_TEMPLATE = """Classify the following text into {selection_type} of these categories: {categories}

Return as JSON with format:
{{"classifications": [{{"category": "category_name", "confidence": 0.95}}]}}

{multi_label_instruction}

Text:
{content}

Classification (JSON):"""


async def classify_content(
    provider: LLMProvider,
    model: str,
    content: str,
    categories: list[str],
    multi_label: bool = False,
) -> dict[str, Any]:
    """Classify content into categories.

    Args:
        provider: LLM provider to use
        model: Model identifier
        content: Text to classify
        categories: List of possible categories
        multi_label: Whether to allow multiple labels

    Returns:
        Dict with classifications list and usage info
    """
    selection_type = "one or more" if multi_label else "exactly one"
    multi_label_instruction = (
        "You may assign multiple categories if appropriate."
        if multi_label
        else "Choose only the single best category."
    )

    user_prompt = CLASSIFICATION_USER_TEMPLATE.format(
        selection_type=selection_type,
        categories=", ".join(categories),
        multi_label_instruction=multi_label_instruction,
        content=content,
    )

    request = CompletionRequest(
        messages=[
            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.1,  # Low temperature for consistent classification
        output_schema={"type": "object"},  # Request JSON mode
    )

    response = await provider.complete(request)

    if not response.success:
        raise RuntimeError(f"Classification failed: {response.error}")

    # Parse classifications from response
    classifications = []
    try:
        raw_content = response.content.strip()

        # Handle markdown code blocks
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0]

        parsed = json.loads(raw_content)

        if isinstance(parsed, dict):
            if "classifications" in parsed:
                classifications = parsed["classifications"]
            elif "category" in parsed:
                # Single classification format
                classifications = [parsed]
        elif isinstance(parsed, list):
            classifications = parsed
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse classification JSON: {e}")
        # Try to extract category from text
        for category in categories:
            if category.lower() in response.content.lower():
                classifications.append({"category": category, "confidence": 0.8})
                if not multi_label:
                    break

    # Normalize format
    normalized = []
    for cls in classifications:
        normalized.append(
            {
                "category": cls.get("category", "unknown"),
                "confidence": float(cls.get("confidence", 1.0)),
            }
        )

    # Sort by confidence
    normalized.sort(key=lambda x: x["confidence"], reverse=True)

    # If single label, keep only top result
    if not multi_label and len(normalized) > 1:
        normalized = [normalized[0]]

    return {
        "classifications": normalized,
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": float(response.cost_usd),
            "latency_ms": response.latency_ms,
        },
    }
