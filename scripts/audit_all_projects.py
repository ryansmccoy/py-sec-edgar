#!/usr/bin/env python3
"""Multi-Project Feature Implementation Matrix Audit.

Scans all spine ecosystem projects to identify feature implementation gaps.
"""

import ast
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectAudit:
    """Audit results for a single project."""

    name: str
    path: Path
    api_endpoints: dict[str, list[str]] = field(default_factory=dict)
    cli_commands: dict[str, list[str]] = field(default_factory=dict)
    frontend_pages: list[str] = field(default_factory=list)
    frontend_components: dict[str, list[str]] = field(default_factory=dict)
    backend_services: dict[str, list[str]] = field(default_factory=dict)
    tests: dict[str, list[str]] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)
    db_models: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        """Return summary stats."""
        return {
            "api_routes": sum(len(v) for v in self.api_endpoints.values()),
            "api_files": len(self.api_endpoints),
            "cli_commands": sum(len(v) for v in self.cli_commands.values()),
            "cli_files": len(self.cli_commands),
            "frontend_pages": len(self.frontend_pages),
            "frontend_components": sum(
                len(v) for v in self.frontend_components.values()
            ),
            "backend_services": sum(len(v) for v in self.backend_services.values()),
            "test_files": sum(len(v) for v in self.tests.values()),
            "examples": len(self.examples),
            "db_models": len(self.db_models),
        }


class MultiProjectAuditor:
    """Audit multiple projects in the ecosystem."""

    # Project configurations
    PROJECTS = {
        "capture-spine": {
            "api_path": "app/api/routers",
            "cli_path": "app/cli/commands",
            "backend_path": "app/features",
            "frontend_path": "frontend/src",
            "tests_path": "tests",
            "has_frontend": True,
        },
        "entityspine": {
            "api_path": "src/entityspine/api",
            "cli_path": "src/entityspine/cli",
            "backend_path": "src/entityspine",
            "tests_path": "tests",
            "examples_path": "examples",
            "has_frontend": False,
        },
        "feedspine": {
            "api_path": "src/feedspine/api",
            "cli_path": "src/feedspine/cli",
            "backend_path": "src/feedspine",
            "tests_path": "tests",
            "examples_path": "examples",
            "has_frontend": False,
        },
        "genai-spine": {
            "api_path": "src/genai_spine/api",
            "cli_path": "src/genai_spine/cli",
            "backend_path": "src/genai_spine",
            "frontend_path": "frontend/src",
            "tests_path": "tests",
            "examples_path": "examples",
            "has_frontend": True,
        },
        "spine-core": {
            "api_path": "src/spine_core/api",
            "cli_path": "src/spine_core/cli",
            "backend_path": "src/spine_core",
            "tests_path": "tests",
            "examples_path": "examples",
            "has_frontend": False,
        },
        "py_sec_edgar": {
            "api_path": "py_sec_edgar/api",
            "cli_path": "py_sec_edgar/cli",
            "backend_path": "py_sec_edgar",
            "tests_path": "tests",
            "examples_path": "examples",
            "has_frontend": False,
        },
    }

    def __init__(self, root_path: Path):
        self.root = root_path
        self.results: dict[str, ProjectAudit] = {}

    def audit_all(self) -> dict[str, ProjectAudit]:
        """Audit all projects."""
        print("=" * 80)
        print("MULTI-PROJECT FEATURE IMPLEMENTATION AUDIT")
        print("=" * 80)
        print()

        for project_name, config in self.PROJECTS.items():
            project_path = self.root / project_name
            if not project_path.exists():
                print(f"[SKIP] {project_name} - not found at {project_path}")
                continue

            print(f"[SCAN] {project_name}...")
            audit = self._audit_project(project_name, project_path, config)
            self.results[project_name] = audit

        return self.results

    def _audit_project(self, name: str, path: Path, config: dict) -> ProjectAudit:
        """Audit a single project."""
        audit = ProjectAudit(name=name, path=path)

        # Scan API
        api_path = path / config.get("api_path", "")
        if api_path.exists():
            audit.api_endpoints = self._scan_api(api_path)

        # Scan CLI
        cli_path = path / config.get("cli_path", "")
        if cli_path.exists():
            audit.cli_commands = self._scan_cli(cli_path)

        # Scan backend services
        backend_path = path / config.get("backend_path", "")
        if backend_path.exists():
            audit.backend_services = self._scan_backend(backend_path)

        # Scan frontend (if applicable)
        if config.get("has_frontend"):
            frontend_path = path / config.get("frontend_path", "")
            if frontend_path.exists():
                audit.frontend_pages = self._scan_frontend_pages(
                    frontend_path / "pages"
                )
                audit.frontend_components = self._scan_frontend_components(
                    frontend_path / "components"
                )

        # Scan tests
        tests_path = path / config.get("tests_path", "")
        if tests_path.exists():
            audit.tests = self._scan_tests(tests_path)

        # Scan examples
        examples_path = path / config.get("examples_path", "")
        if examples_path.exists():
            audit.examples = self._scan_examples(examples_path)

        return audit

    def _scan_api(self, api_path: Path) -> dict[str, list[str]]:
        """Scan API endpoints."""
        endpoints = {}
        for py_file in api_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # FastAPI style
                routes = re.findall(
                    r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
                    content,
                )
                if routes:
                    endpoints[py_file.stem] = [f"{m.upper()} {p}" for m, p in routes]
            except Exception:
                pass
        return endpoints

    def _scan_cli(self, cli_path: Path) -> dict[str, list[str]]:
        """Scan CLI commands."""
        commands = {}
        for py_file in cli_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # Typer/Click style
                cmds = re.findall(
                    r'@(?:app|cli)\.command\s*\(\s*["\']?([^"\')\s,]+)?', content
                )
                # Also function defs that look like commands
                cmds += re.findall(r"def\s+([a-z_]+)\s*\([^)]*\)\s*:", content)
                cmds = [c for c in cmds if c and not c.startswith("_")]
                if cmds:
                    commands[py_file.stem] = list(set(cmds))
            except Exception:
                pass
        return commands

    def _scan_backend(self, backend_path: Path) -> dict[str, list[str]]:
        """Scan backend services/modules."""
        services = {}
        # Look for service/repository patterns
        for py_file in backend_path.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            name = py_file.stem
            if any(
                x in name
                for x in ["service", "repository", "handler", "processor", "manager"]
            ):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    # Find class definitions
                    classes = re.findall(r"class\s+(\w+)\s*[:\(]", content)
                    if classes:
                        services[name] = classes
                except Exception:
                    pass
        return services

    def _scan_frontend_pages(self, pages_path: Path) -> list[str]:
        """Scan frontend pages."""
        if not pages_path.exists():
            return []
        return [f.stem for f in pages_path.glob("*.tsx") if not f.name.startswith("_")]

    def _scan_frontend_components(self, components_path: Path) -> dict[str, list[str]]:
        """Scan frontend components."""
        if not components_path.exists():
            return {}
        components = {}
        for comp_dir in components_path.iterdir():
            if comp_dir.is_dir() and not comp_dir.name.startswith("."):
                files = [
                    f.stem
                    for f in comp_dir.glob("*.tsx")
                    if not f.name.startswith("index")
                ]
                if files:
                    components[comp_dir.name] = files
        return components

    def _scan_tests(self, tests_path: Path) -> dict[str, list[str]]:
        """Scan test files."""
        tests = {"unit": [], "integration": [], "e2e": [], "other": []}
        for test_file in tests_path.rglob("test_*.py"):
            rel = test_file.relative_to(tests_path)
            parts = rel.parts
            if "unit" in parts:
                tests["unit"].append(test_file.name)
            elif "integration" in parts:
                tests["integration"].append(test_file.name)
            else:
                tests["other"].append(test_file.name)

        # Playwright e2e tests
        for spec_file in tests_path.rglob("*.spec.ts"):
            tests["e2e"].append(spec_file.name)

        # Also check frontend e2e
        e2e_path = tests_path.parent / "frontend" / "e2e"
        if e2e_path.exists():
            for spec_file in e2e_path.glob("*.spec.ts"):
                tests["e2e"].append(spec_file.name)

        return tests

    def _scan_examples(self, examples_path: Path) -> list[str]:
        """Scan example files."""
        if not examples_path.exists():
            return []
        return [
            f.name for f in examples_path.glob("*.py") if not f.name.startswith("_")
        ]

    def print_summary(self):
        """Print summary table."""
        print()
        print("=" * 100)
        print("SUMMARY BY PROJECT")
        print("=" * 100)
        print()
        print(
            f"{'Project':<20} {'API':>8} {'CLI':>8} {'Backend':>10} {'Frontend':>10} {'Tests':>8} {'Examples':>10}"
        )
        print("-" * 100)

        totals = defaultdict(int)

        for name, audit in sorted(self.results.items()):
            s = audit.summary()
            api = f"{s['api_routes']}r/{s['api_files']}f" if s["api_files"] else "-"
            cli = f"{s['cli_commands']}c/{s['cli_files']}f" if s["cli_files"] else "-"
            backend = str(s["backend_services"]) if s["backend_services"] else "-"
            frontend = (
                f"{s['frontend_pages']}p/{s['frontend_components']}c"
                if s["frontend_pages"] or s["frontend_components"]
                else "-"
            )
            tests = str(s["test_files"]) if s["test_files"] else "-"
            examples = str(s["examples"]) if s["examples"] else "-"

            print(
                f"{name:<20} {api:>8} {cli:>8} {backend:>10} {frontend:>10} {tests:>8} {examples:>10}"
            )

            for k, v in s.items():
                totals[k] += v

        print("-" * 100)
        print(
            f"{'TOTAL':<20} {totals['api_routes']:>8} {totals['cli_commands']:>8} {totals['backend_services']:>10} {totals['frontend_pages'] + totals['frontend_components']:>10} {totals['test_files']:>8} {totals['examples']:>10}"
        )
        print()

    def print_gaps(self):
        """Print gap analysis."""
        print()
        print("=" * 80)
        print("GAP ANALYSIS")
        print("=" * 80)

        for name, audit in sorted(self.results.items()):
            s = audit.summary()
            issues = []

            # Check for common issues
            if s["api_routes"] > 0 and s["test_files"] == 0:
                issues.append("API but no tests")
            if s["backend_services"] > 0 and s["test_files"] == 0:
                issues.append("Backend services but no tests")
            if (
                s["api_routes"] == 0
                and s["cli_commands"] == 0
                and s["backend_services"] > 5
            ):
                issues.append("Backend with no API/CLI exposure")
            if audit.frontend_pages and not audit.api_endpoints:
                issues.append("Frontend pages but no API")
            if s["examples"] == 0 and (s["api_routes"] > 0 or s["cli_commands"] > 0):
                issues.append("No examples")

            if issues:
                print(f"\n{name}:")
                for issue in issues:
                    print(f"  [!] {issue}")

        print()

    def print_detailed(self):
        """Print detailed breakdown per project."""
        for name, audit in sorted(self.results.items()):
            print()
            print("=" * 80)
            print(f"PROJECT: {name}")
            print("=" * 80)

            if audit.api_endpoints:
                print(
                    f"\nAPI Endpoints ({sum(len(v) for v in audit.api_endpoints.values())} routes):"
                )
                for file, routes in sorted(audit.api_endpoints.items()):
                    print(f"  {file}: {len(routes)} routes")

            if audit.cli_commands:
                print(
                    f"\nCLI Commands ({sum(len(v) for v in audit.cli_commands.values())} commands):"
                )
                for file, cmds in sorted(audit.cli_commands.items()):
                    print(
                        f"  {file}: {', '.join(cmds[:5])}{'...' if len(cmds) > 5 else ''}"
                    )

            if audit.backend_services:
                print(
                    f"\nBackend Services ({sum(len(v) for v in audit.backend_services.values())} classes):"
                )
                for file, classes in sorted(audit.backend_services.items())[:10]:
                    print(
                        f"  {file}: {', '.join(classes[:3])}{'...' if len(classes) > 3 else ''}"
                    )

            if audit.frontend_pages:
                print(f"\nFrontend Pages ({len(audit.frontend_pages)}):")
                print(
                    f"  {', '.join(audit.frontend_pages[:10])}{'...' if len(audit.frontend_pages) > 10 else ''}"
                )

            if audit.tests:
                print(f"\nTests:")
                for test_type, files in audit.tests.items():
                    if files:
                        print(f"  {test_type}: {len(files)} files")

            if audit.examples:
                print(f"\nExamples ({len(audit.examples)}):")
                print(
                    f"  {', '.join(audit.examples[:5])}{'...' if len(audit.examples) > 5 else ''}"
                )


def main():
    """Run multi-project audit."""
    import argparse

    parser = argparse.ArgumentParser(description="Audit all spine ecosystem projects")
    parser.add_argument(
        "--detailed", action="store_true", help="Show detailed breakdown"
    )
    parser.add_argument("--json", type=str, help="Export to JSON file")
    args = parser.parse_args()

    # Find root (parent of capture-spine)
    script_path = Path(__file__).resolve()
    root = script_path.parent.parent

    auditor = MultiProjectAuditor(root)
    results = auditor.audit_all()

    auditor.print_summary()
    auditor.print_gaps()

    if args.detailed:
        auditor.print_detailed()

    if args.json:
        export_data = {}
        for name, audit in results.items():
            export_data[name] = {
                "summary": audit.summary(),
                "api_endpoints": audit.api_endpoints,
                "cli_commands": audit.cli_commands,
                "backend_services": audit.backend_services,
                "frontend_pages": audit.frontend_pages,
                "frontend_components": audit.frontend_components,
                "tests": audit.tests,
                "examples": audit.examples,
            }
        Path(args.json).write_text(json.dumps(export_data, indent=2))
        print(f"[EXPORT] Saved to {args.json}")


if __name__ == "__main__":
    main()
