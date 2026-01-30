#!/usr/bin/env python3
"""
Generate ECOSYSTEM.md from project metadata.

Scans all projects in the py-sec-edgar ecosystem, extracts metadata from
project_meta.yaml files and pyproject.toml/package.json, and generates
a unified ECOSYSTEM.md documentation file.

Usage:
    python scripts/generate_ecosystem_docs.py
    python scripts/generate_ecosystem_docs.py --output ECOSYSTEM.md
    python scripts/generate_ecosystem_docs.py --format json > ecosystem.json

Requirements:
    - Python 3.11+
    - PyYAML (pip install pyyaml)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Try to import yaml, fall back to basic parsing if not available
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import tomllib (Python 3.11+)
try:
    import tomllib

    HAS_TOML = True
except ImportError:
    HAS_TOML = False


@dataclass
class RecentFeature:
    """A recently added feature."""

    date: str
    feature: str
    version: str = ""


@dataclass
class ProjectInfo:
    """Metadata about a project in the ecosystem."""

    name: str
    path: Path
    tagline: str = ""
    version: str = ""
    description: str = ""
    language: str = "Python"
    status: str = "private"
    pypi: str | None = None
    github: str | None = None
    categories: list[str] = field(default_factory=list)
    key_features: list[str] = field(default_factory=list)
    key_docs: list[str] = field(default_factory=list)
    key_models: list[str] = field(default_factory=list)
    integration_points: dict[str, str] = field(default_factory=dict)
    recent_features: list[RecentFeature] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)


# Project definitions with paths relative to workspace root
PROJECTS = [
    ("entityspine", "entityspine/", "Python"),
    ("feedspine", "feedspine/", "Python"),
    ("spine-core", "spine-core/", "Python"),
    ("capture-spine", "capture-spine/", "Python"),
    ("trading-desktop", "spine-core/trading-desktop/trading-desktop/", "TypeScript"),
    ("py-sec-edgar", ".", "Python"),
]


def find_workspace_root() -> Path:
    """Find the workspace root by looking for pyproject.toml or .git."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            # Check if this is the root (has py_sec_edgar or is named py-sec-edgar)
            if (current / "py_sec_edgar").exists() or current.name == "py-sec-edgar":
                return current
        current = current.parent
    return Path.cwd()


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file."""
    if not HAS_YAML:
        print(f"Warning: PyYAML not installed, skipping {path}", file=sys.stderr)
        return {}
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_toml(path: Path) -> dict[str, Any]:
    """Load a TOML file."""
    if not HAS_TOML:
        print(f"Warning: tomllib not available, skipping {path}", file=sys.stderr)
        return {}
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_exports_from_init(init_path: Path) -> list[str]:
    """Extract __all__ exports from an __init__.py file."""
    if not init_path.exists():
        return []

    content = init_path.read_text(encoding="utf-8")

    # Look for __all__ = [...]
    import re

    match = re.search(r"__all__\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if match:
        items_str = match.group(1)
        # Extract quoted strings
        items = re.findall(r'["\']([^"\']+)["\']', items_str)
        return items[:20]  # Limit to first 20

    return []


def scan_project(
    name: str, rel_path: str, language: str, workspace: Path
) -> ProjectInfo:
    """Extract metadata from a project."""
    project_path = workspace / rel_path

    info = ProjectInfo(name=name, path=project_path, language=language)

    # Load project_meta.yaml if exists
    meta_path = project_path / "project_meta.yaml"
    meta = load_yaml(meta_path)

    if meta:
        info.tagline = meta.get("tagline", "")
        info.status = meta.get("status", "private")
        info.pypi = meta.get("pypi")
        info.github = meta.get("github")
        info.categories = meta.get("categories", [])
        info.key_features = meta.get("key_features", [])
        info.key_docs = meta.get("key_docs", [])
        info.key_models = meta.get("key_models", [])
        info.integration_points = meta.get("integration_points", {})

        # Parse recent features
        for feat in meta.get("recent_features", []):
            info.recent_features.append(
                RecentFeature(
                    date=str(feat.get("date", "")),
                    feature=feat.get("feature", ""),
                    version=feat.get("version", ""),
                )
            )

    # Load version from pyproject.toml or package.json
    if language == "Python":
        pyproject = load_toml(project_path / "pyproject.toml")
        if pyproject:
            project_section = pyproject.get("project", {})
            info.version = project_section.get("version", "")
            info.description = project_section.get("description", info.tagline)

        # Try to get exports from __init__.py
        for init_path in [
            project_path / "src" / name / "__init__.py",
            project_path / "src" / name.replace("-", "_") / "__init__.py",
            project_path / name / "__init__.py",
            project_path / "app" / "__init__.py",
        ]:
            exports = extract_exports_from_init(init_path)
            if exports:
                info.exports = exports
                break
    else:
        package_json = load_json(project_path / "package.json")
        if package_json:
            info.version = package_json.get("version", "")
            info.description = package_json.get("description", info.tagline)

    return info


def generate_ecosystem_md(projects: list[ProjectInfo], workspace: Path) -> str:
    """Generate ECOSYSTEM.md content."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# Financial Data Ecosystem",
        "",
        f"> Auto-generated on {now} by `scripts/generate_ecosystem_docs.py`",
        "",
        "---",
        "",
        "## Projects",
        "",
        "| Project | Version | Status | Description |",
        "|---------|---------|--------|-------------|",
    ]

    for p in projects:
        status_badge = "🟢 Public" if p.status == "public" else "🔒 Private"
        pypi_link = f"[PyPI](https://pypi.org/project/{p.pypi}/)" if p.pypi else "-"
        desc = p.tagline or p.description or "-"
        lines.append(f"| **{p.name}** | {p.version or '-'} | {status_badge} | {desc} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Architecture",
            "",
            "```",
            "┌─────────────────────────────────────────────────────────────────────────┐",
            "│                         py-sec-edgar ECOSYSTEM                          │",
            "├─────────────────────────────────────────────────────────────────────────┤",
            "│                                                                         │",
            "│   ┌─────────────────┐                      ┌─────────────────┐         │",
            "│   │   entityspine   │◄────────────────────►│   feedspine     │         │",
            "│   │  Domain Models  │                      │  Feed Capture   │         │",
            "│   │  Entity, Security│                      │  Deduplication  │         │",
            "│   └────────┬────────┘                      └────────┬────────┘         │",
            "│            │                                        │                   │",
            "│            ▼                                        ▼                   │",
            "│   ┌─────────────────────────────────────────────────────────┐          │",
            "│   │                    capture-spine                        │          │",
            "│   │            Point-in-Time Content Capture                │          │",
            "│   │     RSS Feeds • Documents • Knowledge Management        │          │",
            "│   └─────────────────────────┬───────────────────────────────┘          │",
            "│                             │                                           │",
            "│                             ▼                                           │",
            "│   ┌─────────────────────────────────────────────────────────┐          │",
            "│   │                     spine-core                          │          │",
            "│   │           Registry-Driven Pipeline Framework            │          │",
            "│   │              Market Data • Analytics API                │          │",
            "│   └─────────────────────────┬───────────────────────────────┘          │",
            "│                             │                                           │",
            "│                             ▼                                           │",
            "│   ┌─────────────────────────────────────────────────────────┐          │",
            "│   │                   trading-desktop                       │          │",
            "│   │        Bloomberg Terminal-Style React Frontend          │          │",
            "│   └─────────────────────────────────────────────────────────┘          │",
            "│                                                                         │",
            "│   ┌─────────────────┐                                                  │",
            "│   │  py-sec-edgar   │ ◄── SEC Filing Download & Processing             │",
            "│   └─────────────────┘                                                  │",
            "│                                                                         │",
            "└─────────────────────────────────────────────────────────────────────────┘",
            "```",
            "",
            "---",
            "",
            "## Feature Matrix",
            "",
            "| Feature | entityspine | feedspine | capture-spine | spine-core | trading-desktop |",
            "|---------|-------------|-----------|---------------|------------|-----------------|",
            "| Entity Resolution | ✅ | - | uses | uses | uses |",
            "| Feed Deduplication | - | ✅ | ✅ | - | - |",
            "| Knowledge Graph | ✅ | - | - | - | displays |",
            "| Point-in-Time Query | - | ✅ | ✅ | - | - |",
            "| Market Data | - | - | - | ✅ | displays |",
            "| React UI | - | - | - | - | ✅ |",
            "| SEC Filings | - | adapters | captures | - | - |",
            "",
            "---",
            "",
            "## Recent Development",
            "",
        ]
    )

    # Aggregate recent features
    all_features: list[tuple[str, str, RecentFeature]] = []
    for p in projects:
        for feat in p.recent_features:
            all_features.append((p.name, p.version, feat))

    # Sort by date descending
    all_features.sort(key=lambda x: x[2].date, reverse=True)

    for proj_name, proj_version, feat in all_features[:10]:  # Last 10 features
        lines.append(f"### {proj_name} {feat.version} ({feat.date})")
        lines.append(f"- {feat.feature}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Key Documentation",
            "",
            "### Architecture & Design",
            "",
        ]
    )

    for p in projects:
        for doc in p.key_docs[:3]:
            doc_path = (
                f"{p.path.relative_to(workspace)}/{doc}" if p.path != workspace else doc
            )
            lines.append(f"- [{p.name}: {Path(doc).name}]({doc_path})")

    lines.extend(
        [
            "",
            "### Domain Models",
            "",
        ]
    )

    for p in projects:
        for model in p.key_models[:3]:
            model_path = (
                f"{p.path.relative_to(workspace)}/{model}"
                if p.path != workspace
                else model
            )
            lines.append(f"- [{p.name}: {Path(model).name}]({model_path})")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Integration Points",
            "",
        ]
    )

    for p in projects:
        if p.integration_points:
            lines.append(f"### {p.name}")
            lines.append("")
            for target, description in p.integration_points.items():
                lines.append(f"- **→ {target}**: {description}")
            lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Quick Links",
            "",
            "| Project | README | Docs | PyPI |",
            "|---------|--------|------|------|",
        ]
    )

    for p in projects:
        readme = (
            f"[README]({p.path.relative_to(workspace)}/README.md)"
            if p.path != workspace
            else "[README](README.md)"
        )
        docs = (
            f"[docs/]({p.path.relative_to(workspace)}/docs/)"
            if p.path != workspace
            else "[docs/](docs/)"
        )
        pypi = f"[{p.pypi}](https://pypi.org/project/{p.pypi}/)" if p.pypi else "-"
        lines.append(f"| {p.name} | {readme} | {docs} | {pypi} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "*This file is auto-generated. Run `python scripts/generate_ecosystem_docs.py` to update.*",
        ]
    )

    return "\n".join(lines)


def generate_json(projects: list[ProjectInfo]) -> str:
    """Generate JSON output."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "projects": [
            {
                "name": p.name,
                "path": str(p.path),
                "tagline": p.tagline,
                "version": p.version,
                "language": p.language,
                "status": p.status,
                "pypi": p.pypi,
                "github": p.github,
                "categories": p.categories,
                "key_features": p.key_features,
                "key_docs": p.key_docs,
                "integration_points": p.integration_points,
                "exports": p.exports,
            }
            for p in projects
        ],
    }
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Generate ECOSYSTEM.md from project metadata"
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--workspace", "-w", help="Workspace root directory")
    args = parser.parse_args()

    workspace = Path(args.workspace) if args.workspace else find_workspace_root()
    print(f"Workspace: {workspace}", file=sys.stderr)

    # Scan all projects
    projects = []
    for name, rel_path, language in PROJECTS:
        print(f"Scanning {name}...", file=sys.stderr)
        info = scan_project(name, rel_path, language, workspace)
        projects.append(info)

    # Generate output
    if args.format == "json":
        output = generate_json(projects)
    else:
        output = generate_ecosystem_md(projects, workspace)

    # Write output
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
