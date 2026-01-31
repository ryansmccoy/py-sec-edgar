"""Commit message generation capability.

This module implements the commit message generation functionality required by
Capture Spine's Work Session Tracking feature (08-work-sessions/).

Reference: capture-spine/docs/features/productivity/08-work-sessions/README.md
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from genai_spine.providers.base import CompletionRequest

if TYPE_CHECKING:
    from genai_spine.providers.base import LLMProvider


class CommitStyle(str, Enum):
    """Commit message styles.

    - conventional: feat(scope): description
    - semantic: type: description
    - simple: Just a descriptive message
    """

    CONVENTIONAL = "conventional"
    SEMANTIC = "semantic"
    SIMPLE = "simple"


COMMIT_SYSTEM_PROMPT = """You are an expert at writing clear, meaningful git commit messages.

Your task is to analyze the provided file changes and chat context to generate an organized commit message.

Guidelines:
1. Start with a clear, concise summary line
2. Group related changes by feature or component
3. Use bullet points for individual changes
4. Mention file types affected (docs, tests, src, etc.)
5. Reference any discussed features or decisions from chat context

{style_instructions}"""

STYLE_INSTRUCTIONS = {
    CommitStyle.CONVENTIONAL: """Format: Conventional Commits
- Summary: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
- Example: feat(storage): add PostgreSQL backend support""",
    CommitStyle.SEMANTIC: """Format: Semantic Commit
- Summary: type: description
- Types: feature, bugfix, docs, refactor, test
- Example: feature: add database storage layer""",
    CommitStyle.SIMPLE: """Format: Simple Descriptive
- Write a clear, descriptive summary
- No special prefixes required
- Example: Add PostgreSQL storage backend with connection pooling""",
}

COMMIT_USER_PROMPT = """Generate a commit message for the following changes.

## Files Changed ({file_count} files)
{file_list}

## Chat Context
{chat_context}

{diff_section}

Generate a well-organized commit message:"""


async def generate_commit_message(
    provider: LLMProvider,
    files: list[dict],
    chat_context: list[dict] | None = None,
    style: CommitStyle = CommitStyle.CONVENTIONAL,
    include_scope: bool = True,
    max_length: int = 500,
    model: str | None = None,
) -> dict:
    """Generate a commit message from file changes and chat context.

    This supports Capture Spine's Work Session "Generate Commit" feature.

    Args:
        provider: LLM provider to use
        files: List of file change dicts with path, status, and optional diff
        chat_context: Optional list of chat messages for context
        style: Commit message style
        include_scope: Whether to include scope in conventional commits
        max_length: Maximum message length
        model: Optional model override

    Returns:
        Dict with commit_message, feature_groups, suggested_tags, etc.

    Example files:
        [
            {"path": "src/storage/postgres.py", "status": "modified", "diff": "..."},
            {"path": "docs/README.md", "status": "added"}
        ]
    """
    # Build file list
    file_list = []
    for f in files[:50]:  # Limit to 50 files
        status_icon = {
            "added": "✨",
            "modified": "📝",
            "deleted": "🗑️",
            "renamed": "📋",
        }.get(f.get("status", "modified"), "📝")
        file_list.append(f"{status_icon} {f['path']} ({f.get('status', 'modified')})")

    file_list_str = "\n".join(file_list)

    # Build chat context
    chat_str = "No chat context provided."
    if chat_context:
        chat_messages = []
        for msg in chat_context[-10:]:  # Last 10 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")[:200]  # Truncate
            chat_messages.append(f"[{role}]: {content}")
        chat_str = "\n".join(chat_messages)

    # Build diff section (if any files have diffs)
    diff_section = ""
    diffs = [f for f in files if f.get("diff")]
    if diffs:
        diff_parts = []
        for f in diffs[:5]:  # Limit to 5 diffs
            diff = f["diff"][:500]  # Truncate long diffs
            diff_parts.append(f"### {f['path']}\n```diff\n{diff}\n```")
        diff_section = "## Sample Diffs\n" + "\n".join(diff_parts)

    # Build prompts
    system_prompt = COMMIT_SYSTEM_PROMPT.format(style_instructions=STYLE_INSTRUCTIONS[style])

    user_prompt = COMMIT_USER_PROMPT.format(
        file_count=len(files),
        file_list=file_list_str,
        chat_context=chat_str,
        diff_section=diff_section,
    )

    # Build request and call the provider
    request = CompletionRequest(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=0.4,
        max_tokens=max_length,
    )
    response = await provider.complete(request)

    # Parse response to extract commit message and analyze
    commit_message = response.content.strip()

    # Analyze files to suggest groupings
    feature_groups = _analyze_file_groups(files)
    suggested_tags = _suggest_tags(files, commit_message)

    return {
        "commit_message": commit_message,
        "feature_groups": feature_groups,
        "suggested_tags": suggested_tags,
        "files_analyzed": len(files),
        "provider": response.provider,
        "model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }


def _analyze_file_groups(files: list[dict]) -> list[dict]:
    """Group files by directory/component."""
    groups = {}

    for f in files:
        path = f.get("path", "")
        parts = path.split("/")

        # Determine scope from path
        if len(parts) >= 2:
            scope = parts[0]
            if parts[0] in ("src", "app", "lib"):
                scope = parts[1] if len(parts) > 1 else parts[0]
        else:
            scope = "root"

        if scope not in groups:
            groups[scope] = {
                "scope": scope,
                "description": f"Changes to {scope}",
                "files": [],
            }
        groups[scope]["files"].append(path)

    return list(groups.values())


def _suggest_tags(files: list[dict], commit_message: str) -> list[str]:
    """Suggest tags based on files and commit content."""
    tags = set()

    # Tags from file paths
    for f in files:
        path = f.get("path", "").lower()
        if "test" in path:
            tags.add("tests")
        if "doc" in path or path.endswith(".md"):
            tags.add("documentation")
        if "api" in path:
            tags.add("api")
        if "storage" in path or "database" in path or "db" in path:
            tags.add("database")
        if "config" in path or "settings" in path:
            tags.add("configuration")
        if "frontend" in path or "ui" in path or "component" in path:
            tags.add("frontend")

    # Tags from commit message
    msg_lower = commit_message.lower()
    if "fix" in msg_lower or "bug" in msg_lower:
        tags.add("bugfix")
    if "feat" in msg_lower or "feature" in msg_lower or "add" in msg_lower:
        tags.add("feature")
    if "refactor" in msg_lower:
        tags.add("refactor")

    return sorted(list(tags))[:5]  # Max 5 tags
