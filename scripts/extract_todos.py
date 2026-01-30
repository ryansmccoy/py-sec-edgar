#!/usr/bin/env python3
"""
Extract TODOs from source code and generate docs/TODO.md.

Scans Python and TypeScript source files for TODO, FIXME, XXX, and HACK
comments, categorizes them by priority, and generates a Markdown file.

Usage:
    python scripts/extract_todos.py
    python scripts/extract_todos.py --project entityspine
    python scripts/extract_todos.py --output docs/TODO.md

Requirements:
    - Python 3.11+
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator

# Patterns for different languages
PYTHON_TODO_PATTERN = re.compile(
    r"#\s*(TODO|FIXME|XXX|HACK|NOTE|OPTIMIZE)[\s:]+(.+?)(?:\s*$)", re.IGNORECASE
)

TS_TODO_PATTERN = re.compile(
    r"(?://|/\*)\s*(TODO|FIXME|XXX|HACK|NOTE|OPTIMIZE)[\s:]+(.+?)(?:\s*\*/|\s*$)",
    re.IGNORECASE,
)

# Priority mapping
PRIORITY_MAP = {
    "FIXME": "High",
    "XXX": "High",
    "HACK": "High",
    "TODO": "Normal",
    "OPTIMIZE": "Low",
    "NOTE": "Low",
}


@dataclass
class TodoItem:
    """A TODO item extracted from source code."""

    type: str
    text: str
    file: str
    line: int
    priority: str

    @property
    def location(self) -> str:
        return f"{self.file}:{self.line}"


def find_workspace_root() -> Path:
    """Find the workspace root by looking for pyproject.toml or .git."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            if (current / "py_sec_edgar").exists() or current.name == "py-sec-edgar":
                return current
        current = current.parent
    return Path.cwd()


def extract_todos_from_file(file_path: Path, base_path: Path) -> Iterator[TodoItem]:
    """Extract TODO items from a single file."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return

    rel_path = str(file_path.relative_to(base_path))

    # Choose pattern based on file extension
    suffix = file_path.suffix.lower()
    if suffix in (".py", ".pyx"):
        pattern = PYTHON_TODO_PATTERN
    elif suffix in (".ts", ".tsx", ".js", ".jsx"):
        pattern = TS_TODO_PATTERN
    else:
        return

    for i, line in enumerate(content.splitlines(), 1):
        match = pattern.search(line)
        if match:
            todo_type = match.group(1).upper()
            text = match.group(2).strip()
            priority = PRIORITY_MAP.get(todo_type, "Normal")

            yield TodoItem(
                type=todo_type,
                text=text,
                file=rel_path,
                line=i,
                priority=priority,
            )


def scan_directory(src_dir: Path, base_path: Path) -> list[TodoItem]:
    """Scan a directory for TODO items."""
    todos: list[TodoItem] = []

    # File extensions to scan
    extensions = {".py", ".pyx", ".ts", ".tsx", ".js", ".jsx"}

    # Directories to skip
    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        ".tox",
        "htmlcov",
        "archive",
        ".hypothesis",
    }

    for path in src_dir.rglob("*"):
        # Skip ignored directories
        if any(part in skip_dirs for part in path.parts):
            continue

        if path.is_file() and path.suffix.lower() in extensions:
            todos.extend(extract_todos_from_file(path, base_path))

    return todos


def generate_todo_md(todos: list[TodoItem], project_name: str = "") -> str:
    """Generate TODO.md content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Group by priority
    high = [t for t in todos if t.priority == "High"]
    normal = [t for t in todos if t.priority == "Normal"]
    low = [t for t in todos if t.priority == "Low"]

    title = f"# TODOs - {project_name}" if project_name else "# TODOs"

    lines = [
        title,
        "",
        f"> Auto-generated on {now} by `scripts/extract_todos.py`",
        "",
        f"**Total: {len(todos)}** (🔴 High: {len(high)}, 🟡 Normal: {len(normal)}, 🟢 Low: {len(low)})",
        "",
        "---",
        "",
    ]

    def add_section(items: list[TodoItem], title: str, emoji: str):
        if not items:
            return
        lines.append(f"## {emoji} {title} ({len(items)})")
        lines.append("")
        for item in items:
            lines.append(f"- **[{item.type}]** {item.text}")
            lines.append(f"  - 📍 [{item.location}]({item.file}#L{item.line})")
            lines.append("")

    add_section(high, "High Priority", "🔴")
    add_section(normal, "Normal Priority", "🟡")
    add_section(low, "Low Priority", "🟢")

    if not todos:
        lines.append("*No TODOs found! 🎉*")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "*This file is auto-generated. Run `python scripts/extract_todos.py` to update.*",
        ]
    )

    return "\n".join(lines)


def get_project_paths(workspace: Path) -> dict[str, Path]:
    """Get paths for all projects."""
    return {
        "entityspine": workspace / "entityspine",
        "feedspine": workspace / "feedspine",
        "spine-core": workspace / "spine-core",
        "capture-spine": workspace / "capture-spine",
        "trading-desktop": workspace
        / "spine-core"
        / "trading-desktop"
        / "trading-desktop",
        "py-sec-edgar": workspace,
    }


def main():
    parser = argparse.ArgumentParser(description="Extract TODOs from source code")
    parser.add_argument(
        "--project", "-p", help="Specific project to scan (default: all)"
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--workspace", "-w", help="Workspace root directory")
    parser.add_argument(
        "--write-all",
        "-a",
        action="store_true",
        help="Write TODO.md to each project's docs/ folder",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else find_workspace_root()
    print(f"Workspace: {workspace}", file=sys.stderr)

    project_paths = get_project_paths(workspace)

    if args.write_all:
        # Write TODO.md to each project
        for name, path in project_paths.items():
            if not path.exists():
                print(f"Skipping {name}: path does not exist", file=sys.stderr)
                continue

            print(f"Scanning {name}...", file=sys.stderr)

            # Determine source directory
            if name == "py-sec-edgar":
                src_dir = path / "py_sec_edgar"
            elif name == "trading-desktop":
                src_dir = path / "src"
            elif name == "capture-spine":
                src_dir = path / "app"
            else:
                src_dir = path / "src"

            if not src_dir.exists():
                src_dir = path

            todos = scan_directory(src_dir, path)
            output = generate_todo_md(todos, name)

            # Write to docs/TODO.md
            docs_dir = path / "docs"
            docs_dir.mkdir(exist_ok=True)
            output_path = docs_dir / "TODO.md"
            output_path.write_text(output, encoding="utf-8")
            print(f"  Written {len(todos)} TODOs to {output_path}", file=sys.stderr)

        return

    if args.project:
        # Scan specific project
        if args.project not in project_paths:
            print(f"Unknown project: {args.project}", file=sys.stderr)
            print(f"Available: {', '.join(project_paths.keys())}", file=sys.stderr)
            sys.exit(1)

        path = project_paths[args.project]

        # Determine source directory
        if args.project == "py-sec-edgar":
            src_dir = path / "py_sec_edgar"
        elif args.project == "trading-desktop":
            src_dir = path / "src"
        elif args.project == "capture-spine":
            src_dir = path / "app"
        else:
            src_dir = path / "src"

        if not src_dir.exists():
            src_dir = path

        todos = scan_directory(src_dir, path)
        output = generate_todo_md(todos, args.project)
    else:
        # Scan entire workspace
        todos = scan_directory(workspace, workspace)
        output = generate_todo_md(todos, "Ecosystem")

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written {len(todos)} TODOs to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
