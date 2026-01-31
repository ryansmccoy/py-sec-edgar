"""Entity extraction capability."""

from __future__ import annotations

import json
import logging
from typing import Any

from genai_spine.providers.base import CompletionRequest, LLMProvider

logger = logging.getLogger(__name__)


EXTRACTION_SYSTEM_PROMPT = """You are an expert at named entity recognition (NER). Extract entities accurately from the provided text.

Entity types you may extract:
- PERSON: Names of people
- ORG: Organizations, companies, institutions
- LOCATION: Places, cities, countries
- DATE: Dates, time periods
- MONEY: Monetary amounts
- PERCENT: Percentages
- EVENT: Named events
- PRODUCT: Product names
- INSTRUMENT: Financial instruments (stocks, bonds, etc.)

Always return valid JSON."""

EXTRACTION_USER_TEMPLATE = """Extract all entities of types [{entity_types}] from the following text.

Return as a JSON array with this format:
[{{"text": "entity text", "type": "ENTITY_TYPE", "start": 0, "end": 10}}]

Include character positions (start/end) if possible.
{context_instruction}

Text:
{content}

Entities (JSON array):"""


async def extract_entities(
    provider: LLMProvider,
    model: str,
    content: str,
    entity_types: list[str] | None = None,
    include_context: bool = False,
) -> dict[str, Any]:
    """Extract named entities from text.

    Args:
        provider: LLM provider to use
        model: Model identifier
        content: Text to analyze
        entity_types: Types to extract (PERSON, ORG, LOCATION, etc.)
        include_context: Whether to include surrounding context

    Returns:
        Dict with entities list and usage info
    """
    if entity_types is None:
        entity_types = ["PERSON", "ORG", "LOCATION", "DATE", "MONEY"]

    context_instruction = (
        "Also include a 'context' field with the surrounding sentence for each entity."
        if include_context
        else ""
    )

    user_prompt = EXTRACTION_USER_TEMPLATE.format(
        entity_types=", ".join(entity_types),
        context_instruction=context_instruction,
        content=content,
    )

    request = CompletionRequest(
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.1,  # Very low temperature for extraction
        output_schema={"type": "array"},  # Request JSON mode
    )

    response = await provider.complete(request)

    if not response.success:
        raise RuntimeError(f"Extraction failed: {response.error}")

    # Parse entities from response
    entities = []
    try:
        # Try to parse as JSON
        raw_content = response.content.strip()

        # Handle markdown code blocks
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0]
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0]

        parsed = json.loads(raw_content)

        if isinstance(parsed, list):
            entities = parsed
        elif isinstance(parsed, dict) and "entities" in parsed:
            entities = parsed["entities"]
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse entities JSON: {e}")
        # Try to extract any JSON array from the response
        import re

        match = re.search(r"\[.*\]", response.content, re.DOTALL)
        if match:
            try:
                entities = json.loads(match.group())
            except json.JSONDecodeError:
                pass

    # Normalize entity format
    normalized_entities = []
    for entity in entities:
        normalized = {
            "text": entity.get("text", ""),
            "type": entity.get("type", "UNKNOWN"),
            "start": entity.get("start"),
            "end": entity.get("end"),
            "confidence": entity.get("confidence", 1.0),
        }
        if include_context and "context" in entity:
            normalized["context"] = entity["context"]
        normalized_entities.append(normalized)

    return {
        "entities": normalized_entities,
        "usage": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "cost_usd": float(response.cost_usd),
            "latency_ms": response.latency_ms,
        },
    }
