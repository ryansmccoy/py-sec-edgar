"""Summarization capability."""

from __future__ import annotations

import json
import logging
from typing import Any

from genai_spine.providers.base import CompletionRequest, LLMProvider

logger = logging.getLogger(__name__)


SUMMARIZATION_SYSTEM_PROMPT = """You are an expert summarizer. Your task is to create concise, accurate summaries that capture the key information from the provided text.

Guidelines:
- Be accurate and factual
- Maintain the original tone
- Focus on the most important information
- Use clear, professional language
"""

SUMMARIZATION_USER_TEMPLATE = """Summarize the following text in {max_sentences} sentences or less.
{focus_instruction}
{format_instruction}

Text:
{content}

Summary:"""


async def summarize_text(
    provider: LLMProvider,
    model: str,
    content: str,
    max_sentences: int = 3,
    focus: str | None = None,
    output_format: str = "paragraph",
) -> dict[str, Any]:
    """Summarize text content.

    Args:
        provider: LLM provider to use
        model: Model identifier
        content: Text to summarize
        max_sentences: Maximum number of sentences
        focus: Optional focus area (e.g., "financial metrics")
        output_format: "paragraph" or "bullet_points"

    Returns:
        Dict with summary, key_points, word_count, compression_ratio, usage
    """
    focus_instruction = f"Focus on: {focus}" if focus else ""
    format_instruction = (
        "Format as bullet points, one per line starting with •"
        if output_format == "bullet_points"
        else ""
    )

    user_prompt = SUMMARIZATION_USER_TEMPLATE.format(
        max_sentences=max_sentences,
        focus_instruction=focus_instruction,
        format_instruction=format_instruction,
        content=content,
    )

    request = CompletionRequest(
        messages=[
            {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.3,  # Lower temperature for factual summarization
    )

    response = await provider.complete(request)

    if not response.success:
        raise RuntimeError(f"Summarization failed: {response.error}")

    summary = response.content.strip()

    # Extract key points if bullet format
    key_points = []
    if output_format == "bullet_points" and "•" in summary:
        key_points = [
            line.strip().lstrip("•").strip()
            for line in summary.split("\n")
            if line.strip().startswith("•")
        ]

    # Calculate metrics
    original_words = len(content.split())
    summary_words = len(summary.split())
    compression_ratio = 1 - (summary_words / original_words) if original_words > 0 else 0

    return {
        "summary": summary,
        "key_points": key_points,
        "word_count": summary_words,
        "compression_ratio": round(compression_ratio, 3),
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": float(response.cost_usd),
            "latency_ms": response.latency_ms,
        },
    }
