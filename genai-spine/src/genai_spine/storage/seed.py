"""Default prompt definitions for seeding the database.

This module contains the built-in prompts that ship with GenAI Spine.
These prompts are marked as is_system=True and cannot be modified by users.

To seed a new database:
    from genai_spine.storage.seed import seed_default_prompts

    async with backend.unit_of_work() as uow:
        await seed_default_prompts(uow)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from genai_spine.storage.schemas import (
    PromptCategory,
    PromptCreate,
    PromptVariable,
)

if TYPE_CHECKING:
    from genai_spine.storage.protocols import UnitOfWork

logger = logging.getLogger(__name__)


# =============================================================================
# Rewrite Prompts (Message Enrichment support)
# =============================================================================

REWRITE_PROMPTS = [
    PromptCreate(
        slug="rewrite-clean",
        name="Clean Rewrite",
        description="Rewrite content cleanly, fixing grammar, spelling, and formatting",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "clean", "grammar", "spelling"],
        system_prompt=(
            "You are a professional editor. Your task is to clean up and improve text "
            "while preserving its original meaning and intent. Fix grammar, spelling, "
            "punctuation, and improve readability. Do not add new information or change "
            "the core message."
        ),
        user_prompt_template="Please clean up and improve the following text:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="The content to clean and rewrite",
                required=True,
            ),
        ],
        temperature=0.3,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="rewrite-format",
        name="Format Content",
        description="Reformat content with proper structure, headings, and lists",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "format", "structure"],
        system_prompt=(
            "You are a document formatting expert. Your task is to restructure and "
            "format text for better readability. Add appropriate headings, bullet "
            "points, numbered lists, and paragraphs. Preserve all information but "
            "present it in a cleaner, more organized way."
        ),
        user_prompt_template="Please reformat the following content with proper structure:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="The content to reformat",
                required=True,
            ),
        ],
        temperature=0.3,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="rewrite-organize",
        name="Organize Content",
        description="Reorganize content logically with clear sections",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "organize", "sections"],
        system_prompt=(
            "You are an expert at organizing information. Your task is to reorganize "
            "text into logical sections with clear flow. Group related ideas together, "
            "create meaningful sections, and ensure the content flows naturally from "
            "one point to the next."
        ),
        user_prompt_template="Please organize the following content into logical sections:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="The content to organize",
                required=True,
            ),
        ],
        temperature=0.3,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="rewrite-professional",
        name="Professional Tone",
        description="Rewrite content in a professional, business tone",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "professional", "business", "tone"],
        system_prompt=(
            "You are a professional business writer. Your task is to rewrite text "
            "in a polished, professional tone suitable for business communications. "
            "Maintain clarity and precision while being appropriately formal. Avoid "
            "casual language and slang."
        ),
        user_prompt_template="Please rewrite the following in a professional tone:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="The content to make professional",
                required=True,
            ),
        ],
        temperature=0.4,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="rewrite-casual",
        name="Casual Tone",
        description="Rewrite content in a friendly, casual tone",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "casual", "friendly", "tone"],
        system_prompt=(
            "You are a friendly writer who excels at casual communication. Your task "
            "is to rewrite text in a warm, approachable tone. Make it feel like a "
            "conversation with a friend while keeping the core message intact. Use "
            "simple language and a natural flow."
        ),
        user_prompt_template="Please rewrite the following in a casual, friendly tone:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="The content to make casual",
                required=True,
            ),
        ],
        temperature=0.6,
        is_system=True,
        is_public=True,
    ),
]


# =============================================================================
# Summarization Prompts
# =============================================================================

SUMMARIZE_PROMPTS = [
    PromptCreate(
        slug="summarize-article",
        name="Summarize Article",
        description="Summarize a news article or document concisely",
        category=PromptCategory.SUMMARIZE,
        tags=["summarize", "news", "article"],
        system_prompt=(
            "You are a helpful assistant that creates concise, accurate summaries. "
            "Extract the key points and present them clearly."
        ),
        user_prompt_template="""Summarize the following text in {{max_sentences}} sentences or less.
{% if focus %}Focus on: {{focus}}{% endif %}

Text:
{{content}}

Summary:""",
        variables=[
            PromptVariable(
                name="content",
                description="The content to summarize",
                required=True,
            ),
            PromptVariable(
                name="max_sentences",
                description="Maximum number of sentences",
                type="integer",
                required=False,
                default="3",
            ),
            PromptVariable(
                name="focus",
                description="Optional focus area for the summary",
                required=False,
            ),
        ],
        temperature=0.3,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="summarize-bullet",
        name="Bullet Point Summary",
        description="Summarize content as bullet points",
        category=PromptCategory.SUMMARIZE,
        tags=["summarize", "bullets", "key-points"],
        system_prompt=(
            "You are an expert at distilling information into clear, actionable "
            "bullet points. Extract the most important facts and present them concisely."
        ),
        user_prompt_template="""Extract the key points from the following text as {{max_bullets}} bullet points:

{{content}}

Key Points:""",
        variables=[
            PromptVariable(
                name="content",
                description="The content to summarize",
                required=True,
            ),
            PromptVariable(
                name="max_bullets",
                description="Maximum number of bullet points",
                type="integer",
                required=False,
                default="5",
            ),
        ],
        temperature=0.3,
        is_system=True,
        is_public=True,
    ),
]


# =============================================================================
# Extraction Prompts
# =============================================================================

EXTRACTION_PROMPTS = [
    PromptCreate(
        slug="extract-entities",
        name="Extract Entities",
        description="Extract named entities from text",
        category=PromptCategory.EXTRACT,
        tags=["extract", "ner", "entities"],
        system_prompt=(
            "You are an expert at named entity recognition. Extract entities "
            "accurately and classify them correctly."
        ),
        user_prompt_template="""Extract all {{entity_types}} from the following text.

Return as JSON array with format:
[{"text": "entity text", "type": "ENTITY_TYPE"}]

Text:
{{content}}

Entities (JSON):""",
        variables=[
            PromptVariable(
                name="content",
                description="Text to extract entities from",
                required=True,
            ),
            PromptVariable(
                name="entity_types",
                description="Types of entities to extract",
                required=False,
                default="PERSON, ORG, LOCATION",
            ),
        ],
        output_schema={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string"},
                },
            },
        },
        temperature=0.1,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="extract-keywords",
        name="Extract Keywords",
        description="Extract key topics and keywords from text",
        category=PromptCategory.EXTRACT,
        tags=["extract", "keywords", "topics"],
        system_prompt=(
            "You are an expert at keyword extraction and topic modeling. "
            "Identify the most relevant and important terms."
        ),
        user_prompt_template="""Extract the {{max_keywords}} most important keywords from the following text.

Return as JSON array: ["keyword1", "keyword2", ...]

Text:
{{content}}

Keywords (JSON):""",
        variables=[
            PromptVariable(
                name="content",
                description="Text to extract keywords from",
                required=True,
            ),
            PromptVariable(
                name="max_keywords",
                description="Maximum number of keywords",
                type="integer",
                required=False,
                default="10",
            ),
        ],
        output_schema={"type": "array", "items": {"type": "string"}},
        temperature=0.1,
        is_system=True,
        is_public=True,
    ),
]


# =============================================================================
# Classification Prompts
# =============================================================================

CLASSIFICATION_PROMPTS = [
    PromptCreate(
        slug="classify-content",
        name="Classify Content",
        description="Classify content into categories",
        category=PromptCategory.CLASSIFY,
        tags=["classify", "category", "categorize"],
        system_prompt="You are a content classification expert.",
        user_prompt_template="""Classify the following text into one of these categories: {{categories}}

Return as JSON: {"category": "chosen_category", "confidence": 0.0-1.0}

Text:
{{content}}

Classification (JSON):""",
        variables=[
            PromptVariable(
                name="content",
                description="Content to classify",
                required=True,
            ),
            PromptVariable(
                name="categories",
                description="Comma-separated list of valid categories",
                required=True,
            ),
        ],
        output_schema={
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "confidence": {"type": "number"},
            },
        },
        temperature=0.1,
        is_system=True,
        is_public=True,
    ),
    PromptCreate(
        slug="classify-sentiment",
        name="Sentiment Analysis",
        description="Analyze the sentiment of text",
        category=PromptCategory.CLASSIFY,
        tags=["classify", "sentiment", "analysis"],
        system_prompt=(
            "You are an expert at sentiment analysis. Analyze text for emotional "
            "tone and sentiment accurately."
        ),
        user_prompt_template="""Analyze the sentiment of the following text.

Return as JSON: {"sentiment": "positive|negative|neutral", "confidence": 0.0-1.0, "explanation": "brief reason"}

Text:
{{content}}

Sentiment (JSON):""",
        variables=[
            PromptVariable(
                name="content",
                description="Content to analyze",
                required=True,
            ),
        ],
        output_schema={
            "type": "object",
            "properties": {
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "confidence": {"type": "number"},
                "explanation": {"type": "string"},
            },
        },
        temperature=0.1,
        is_system=True,
        is_public=True,
    ),
]


# =============================================================================
# Title/Headline Prompts
# =============================================================================

TITLE_PROMPTS = [
    PromptCreate(
        slug="generate-title",
        name="Generate Title",
        description="Generate a title for content",
        category=PromptCategory.CUSTOM,
        tags=["title", "headline", "generate"],
        system_prompt=(
            "You are an expert headline writer. Create compelling, accurate titles "
            "that capture the essence of the content."
        ),
        user_prompt_template="""Generate a concise title (max {{max_words}} words) for the following content:

{{content}}

Title:""",
        variables=[
            PromptVariable(
                name="content",
                description="Content to title",
                required=True,
            ),
            PromptVariable(
                name="max_words",
                description="Maximum words in title",
                type="integer",
                required=False,
                default="10",
            ),
        ],
        temperature=0.5,
        is_system=True,
        is_public=True,
    ),
]


# =============================================================================
# All Default Prompts
# =============================================================================

DEFAULT_PROMPTS = (
    REWRITE_PROMPTS
    + SUMMARIZE_PROMPTS
    + EXTRACTION_PROMPTS
    + CLASSIFICATION_PROMPTS
    + TITLE_PROMPTS
)


# =============================================================================
# Seeding Function
# =============================================================================


async def seed_default_prompts(
    uow: UnitOfWork,
    force: bool = False,
) -> tuple[int, int]:
    """Seed the database with default prompts.

    Args:
        uow: Unit of work for database operations
        force: If True, recreate prompts even if they exist

    Returns:
        Tuple of (created_count, skipped_count)
    """
    created = 0
    skipped = 0

    for prompt in DEFAULT_PROMPTS:
        existing = await uow.prompts.get_by_slug(prompt.slug)

        if existing:
            if force:
                # Update existing prompt
                logger.info(f"Updating existing prompt: {prompt.slug}")
                # Note: We can't actually update system prompts via the API
                # This is intentional - use migrations for schema changes
                skipped += 1
            else:
                logger.debug(f"Skipping existing prompt: {prompt.slug}")
                skipped += 1
        else:
            logger.info(f"Creating prompt: {prompt.slug}")
            await uow.prompts.create(prompt)
            created += 1

    return created, skipped


async def seed_if_empty(uow: UnitOfWork) -> bool:
    """Seed prompts only if database is empty.

    Args:
        uow: Unit of work for database operations

    Returns:
        True if seeding was performed, False if skipped
    """
    prompts, total = await uow.prompts.list(limit=1)

    if total == 0:
        logger.info("Database is empty, seeding default prompts...")
        created, _ = await seed_default_prompts(uow)
        logger.info(f"Created {created} default prompts")
        return True
    else:
        logger.debug(f"Database has {total} prompts, skipping seed")
        return False
