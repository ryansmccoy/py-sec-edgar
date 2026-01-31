"""Rewrite capability for Message Enrichment support.

This module implements the content rewriting functionality required by
Capture Spine's Message Enrichment feature (02-message-enrichment/).

Reference: capture-spine/docs/features/productivity/02-message-enrichment/PROMPTS.md
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from genai_spine.providers.base import CompletionRequest

if TYPE_CHECKING:
    from genai_spine.providers.base import LLMProvider


class RewriteMode(str, Enum):
    """Available rewrite modes.

    Maps to Capture Spine's enrichment prompts:
    - clean: Fix grammar, spelling, improve clarity
    - format: Add structure with headings, bullets, lists
    - organize: Reorganize into logical sections
    - professional: Business/formal tone
    - casual: Friendly, conversational tone
    - summarize: Condense to key points
    - technical: Technical documentation style
    """

    CLEAN = "clean"
    FORMAT = "format"
    ORGANIZE = "organize"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    SUMMARIZE = "summarize"
    TECHNICAL = "technical"


# System prompts for each mode (from Capture Spine PROMPTS.md)
REWRITE_SYSTEM_PROMPTS = {
    RewriteMode.CLEAN: (
        "You are a professional editor. Your task is to clean up and improve text "
        "while preserving its original meaning and intent. Fix grammar, spelling, "
        "punctuation, and improve readability. Do not add new information or change "
        "the core message."
    ),
    RewriteMode.FORMAT: (
        "You are a document formatting expert. Your task is to restructure and "
        "format text for better readability. Add appropriate headings, bullet "
        "points, numbered lists, and paragraphs. Preserve all information but "
        "present it in a cleaner, more organized way."
    ),
    RewriteMode.ORGANIZE: (
        "You are an expert at organizing information. Your task is to reorganize "
        "text into logical sections with clear flow. Group related ideas together, "
        "create meaningful sections, and ensure the content flows naturally from "
        "one point to the next."
    ),
    RewriteMode.PROFESSIONAL: (
        "You are a professional business writer. Your task is to rewrite text "
        "in a polished, professional tone suitable for business communications. "
        "Maintain clarity and precision while being appropriately formal. Avoid "
        "casual language and slang."
    ),
    RewriteMode.CASUAL: (
        "You are a friendly writer who excels at casual communication. Your task "
        "is to rewrite text in a warm, approachable tone. Make it feel like a "
        "conversation with a friend while keeping the core message intact. Use "
        "simple language and a natural flow."
    ),
    RewriteMode.SUMMARIZE: (
        "You are an expert summarizer. Your task is to condense text to its key "
        "points while maintaining accuracy. Extract the essential information and "
        "present it concisely. Preserve important technical details."
    ),
    RewriteMode.TECHNICAL: (
        "You are a technical writer. Your task is to rewrite text as professional "
        "technical documentation. Use clear, precise language. Add appropriate "
        "formatting, code blocks if needed, and organize into logical sections."
    ),
}

# User prompt templates for each mode
REWRITE_USER_PROMPTS = {
    RewriteMode.CLEAN: "Please clean up and improve the following text:\n\n{content}",
    RewriteMode.FORMAT: "Please reformat the following content with proper structure:\n\n{content}",
    RewriteMode.ORGANIZE: "Please organize the following content into logical sections:\n\n{content}",
    RewriteMode.PROFESSIONAL: "Please rewrite the following in a professional tone:\n\n{content}",
    RewriteMode.CASUAL: "Please rewrite the following in a casual, friendly tone:\n\n{content}",
    RewriteMode.SUMMARIZE: "Please summarize the following content to key points:\n\n{content}",
    RewriteMode.TECHNICAL: "Please rewrite the following as technical documentation:\n\n{content}",
}

# Default temperatures per mode
REWRITE_TEMPERATURES = {
    RewriteMode.CLEAN: 0.3,
    RewriteMode.FORMAT: 0.3,
    RewriteMode.ORGANIZE: 0.3,
    RewriteMode.PROFESSIONAL: 0.4,
    RewriteMode.CASUAL: 0.6,
    RewriteMode.SUMMARIZE: 0.2,
    RewriteMode.TECHNICAL: 0.3,
}


async def rewrite_content(
    provider: LLMProvider,
    content: str,
    mode: RewriteMode = RewriteMode.CLEAN,
    model: str | None = None,
    context: str | None = None,
    preserve_code_blocks: bool = True,
    temperature: float | None = None,
) -> dict:
    """Rewrite content using the specified mode.

    This is the core function for Capture Spine's Message Enrichment feature.

    Args:
        provider: LLM provider to use
        content: The content to rewrite
        mode: Rewrite mode (clean, format, organize, etc.)
        model: Optional model override
        context: Optional context from previous messages
        preserve_code_blocks: Whether to preserve code blocks unchanged
        temperature: Optional temperature override

    Returns:
        Dict with original, rewritten, mode, provider, model, tokens, etc.
    """
    # Build system prompt
    system_prompt = REWRITE_SYSTEM_PROMPTS[mode]
    if preserve_code_blocks:
        system_prompt += "\n\nIMPORTANT: Preserve all code blocks exactly as they appear."
    if context:
        system_prompt += f"\n\nContext from previous messages:\n{context}"

    # Build user prompt
    user_prompt = REWRITE_USER_PROMPTS[mode].format(content=content)

    # Determine temperature
    temp = temperature if temperature is not None else REWRITE_TEMPERATURES[mode]

    # Build request and call the provider
    request = CompletionRequest(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temp,
    )
    response = await provider.complete(request)

    return {
        "original": content,
        "rewritten": response.content,
        "mode": mode.value,
        "provider": response.provider,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "latency_ms": response.latency_ms,
        "cost_usd": response.cost_usd,
    }


# =============================================================================
# Title Inference
# =============================================================================

TITLE_SYSTEM_PROMPT = (
    "You are an expert headline writer. Create compelling, accurate titles "
    "that capture the essence of the content. Be specific and descriptive. "
    "Use technical terms appropriately. Make titles searchable."
)

TITLE_USER_PROMPT = """Generate a concise title ({max_words} words or less) for the following content.

Requirements:
- Be specific and descriptive
- Use technical terms appropriately
- Make it searchable
- Don't start with "How to" unless it's a how-to guide

Content:
{content}

Title:"""


async def infer_title(
    provider: LLMProvider,
    content: str,
    max_words: int = 10,
    model: str | None = None,
) -> dict:
    """Generate a title for content.

    This supports Capture Spine's "Infer Title" feature.

    Args:
        provider: LLM provider to use
        content: The content to generate a title for
        max_words: Maximum words in the title
        model: Optional model override

    Returns:
        Dict with title, provider, model, tokens
    """
    user_prompt = TITLE_USER_PROMPT.format(
        content=content[:2000],  # Limit content length
        max_words=max_words,
    )

    request = CompletionRequest(
        messages=[
            {"role": "system", "content": TITLE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.5,
        max_tokens=50,  # Titles are short
    )
    response = await provider.complete(request)

    # Clean up the response (remove quotes, extra whitespace)
    title = response.content.strip().strip("\"'")

    return {
        "title": title,
        "provider": response.provider,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }
