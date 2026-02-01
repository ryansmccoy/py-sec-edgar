"""Capabilities package for GenAI Spine.

Core capabilities for LLM-powered content processing.
Supports Capture Spine's productivity features.

Reference: capture-spine/docs/features/productivity/
"""

from genai_spine.capabilities.classification import classify_content

# Work Session support (08-work-sessions/)
from genai_spine.capabilities.commit import (
    CommitStyle,
    generate_commit_message,
)
from genai_spine.capabilities.extraction import extract_entities

# Message Enrichment support (02-message-enrichment/)
from genai_spine.capabilities.rewrite import (
    RewriteMode,
    infer_title,
    rewrite_content,
)
from genai_spine.capabilities.summarization import summarize_text

__all__ = [
    # Core capabilities
    "classify_content",
    "extract_entities",
    "summarize_text",
    # Message Enrichment (Capture Spine)
    "RewriteMode",
    "rewrite_content",
    "infer_title",
    # Work Sessions (Capture Spine)
    "CommitStyle",
    "generate_commit_message",
]
