#!/usr/bin/env python3
"""
Audit Data Analyzer
====================
Interactive analysis and visualization of comprehensive audit data.
Load JSON exports and slice/dice the data various ways.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional


def load_audit(filepath: str) -> dict:
    """Load audit JSON file"""
    with open(filepath) as f:
        return json.load(f)


def print_table(headers: list, rows: list, col_widths: Optional[list] = None):
    """Print formatted table"""
    if not col_widths:
        col_widths = [
            max(len(str(row[i])) for row in rows + [headers]) + 2
            for i in range(len(headers))
        ]

    header_row = "".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_row)
    print("-" * len(header_row))
    for row in rows:
        print("".join(str(c).ljust(w) for c, w in zip(row, col_widths)))


class AuditAnalyzer:
    """Interactive audit data analyzer"""

    def __init__(self, data: dict):
        self.data = data
        self.projects = data.get("projects", {})
        self.timestamp = data.get("timestamp", "")

    # ============================================================
    # SUMMARY VIEWS
    # ============================================================

    def summary(self):
        """Overall health summary"""
        print(f"\n{'=' * 80}")
        print("ECOSYSTEM HEALTH SUMMARY")
        print(f"Audit timestamp: {self.timestamp}")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            rows.append(
                [
                    name,
                    f"{p['score']:.0f}",
                    p["tests"]["test_functions"],
                    len(p["tests"]["unit_tests"]),
                    len(p["tests"]["integration_tests"]),
                    len(p["tests"]["e2e_tests"]),
                    len(p["coverage_gaps"]),
                    f"{p['docs']['docstring_coverage']:.0f}%",
                    len(p["issues"]),
                ]
            )

        headers = [
            "Project",
            "Score",
            "Tests",
            "Unit",
            "Integ",
            "E2E",
            "Gaps",
            "Docs",
            "Issues",
        ]
        print_table(headers, rows)

    # ============================================================
    # TEST ANALYSIS
    # ============================================================

    def test_breakdown(self):
        """Detailed test breakdown by project"""
        print(f"\n{'=' * 80}")
        print("TEST BREAKDOWN BY PROJECT")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            t = p["tests"]
            rows.append(
                [
                    name,
                    t["test_functions"],
                    t["test_classes"],
                    t["fixtures"],
                    t["parametrized"],
                    t["async_tests"],
                    t["mocked_tests"],
                ]
            )

        headers = [
            "Project",
            "Functions",
            "Classes",
            "Fixtures",
            "Param",
            "Async",
            "Mocked",
        ]
        print_table(headers, rows)

    def test_files_by_type(self):
        """Test file counts by type"""
        print(f"\n{'=' * 80}")
        print("TEST FILES BY TYPE")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            t = p["tests"]
            total = (
                len(t["unit_tests"])
                + len(t["integration_tests"])
                + len(t["e2e_tests"])
                + len(t["other_tests"])
            )
            rows.append(
                [
                    name,
                    len(t["unit_tests"]),
                    len(t["integration_tests"]),
                    len(t["e2e_tests"]),
                    len(t["other_tests"]),
                    total,
                ]
            )

        headers = ["Project", "Unit", "Integration", "E2E", "Other", "Total"]
        print_table(headers, rows)

    def tests_needing_categorization(self):
        """Tests in 'other' that should be categorized"""
        print(f"\n{'=' * 80}")
        print("TESTS NEEDING CATEGORIZATION (in 'other' bucket)")
        print(f"{'=' * 80}")

        for name, p in self.projects.items():
            other = p["tests"]["other_tests"]
            if other:
                print(f"\n{name}: {len(other)} files")
                for f in other[:15]:
                    print(f"  - {f}")
                if len(other) > 15:
                    print(f"  ... and {len(other) - 15} more")

    # ============================================================
    # COVERAGE GAP ANALYSIS
    # ============================================================

    def coverage_gaps_summary(self):
        """Summary of test coverage gaps"""
        print(f"\n{'=' * 80}")
        print("TEST COVERAGE GAPS SUMMARY")
        print(f"{'=' * 80}\n")

        rows = []
        total_gaps = 0
        total_functions = 0
        total_classes = 0
        total_lines = 0

        for name, p in self.projects.items():
            gaps = p["coverage_gaps"]
            if gaps:
                funcs = sum(len(g.get("functions", [])) for g in gaps)
                classes = sum(len(g.get("classes", [])) for g in gaps)
                lines = sum(g.get("lines", 0) for g in gaps)
                rows.append([name, len(gaps), funcs, classes, lines])
                total_gaps += len(gaps)
                total_functions += funcs
                total_classes += classes
                total_lines += lines
            else:
                rows.append([name, 0, 0, 0, 0])

        rows.append(["TOTAL", total_gaps, total_functions, total_classes, total_lines])

        headers = ["Project", "Files", "Functions", "Classes", "Lines"]
        print_table(headers, rows)

    def coverage_gaps_by_module(self, project: str):
        """Detailed coverage gaps for a project, grouped by module"""
        print(f"\n{'=' * 80}")
        print(f"COVERAGE GAPS FOR {project}")
        print(f"{'=' * 80}\n")

        if project not in self.projects:
            print(f"Project '{project}' not found")
            return

        gaps = self.projects[project]["coverage_gaps"]
        if not gaps:
            print("No coverage gaps! All files have tests.")
            return

        # Group by top-level directory
        by_module = defaultdict(list)
        for gap in gaps:
            parts = gap["source_file"].replace("\\", "/").split("/")
            module = parts[1] if len(parts) > 1 else parts[0]
            by_module[module].append(gap)

        for module, module_gaps in sorted(by_module.items()):
            total_funcs = sum(len(g.get("functions", [])) for g in module_gaps)
            total_lines = sum(g.get("lines", 0) for g in module_gaps)
            print(
                f"\n{module}/ ({len(module_gaps)} files, {total_funcs} functions, {total_lines} lines)"
            )
            for g in module_gaps[:10]:
                print(f"  - {g['source_file']} ({g['lines']} lines)")
            if len(module_gaps) > 10:
                print(f"  ... and {len(module_gaps) - 10} more")

    def largest_untested_files(self, limit: int = 20):
        """Largest source files without tests"""
        print(f"\n{'=' * 80}")
        print(f"TOP {limit} LARGEST UNTESTED FILES")
        print(f"{'=' * 80}\n")

        all_gaps = []
        for name, p in self.projects.items():
            for gap in p["coverage_gaps"]:
                all_gaps.append(
                    {
                        "project": name,
                        "file": gap["source_file"],
                        "lines": gap.get("lines", 0),
                        "functions": len(gap.get("functions", [])),
                        "classes": len(gap.get("classes", [])),
                    }
                )

        # Sort by lines
        all_gaps.sort(key=lambda x: x["lines"], reverse=True)

        rows = [
            [g["project"], g["file"], g["lines"], g["functions"], g["classes"]]
            for g in all_gaps[:limit]
        ]

        headers = ["Project", "File", "Lines", "Funcs", "Classes"]
        print_table(headers, rows)

    # ============================================================
    # CODE QUALITY ANALYSIS
    # ============================================================

    def code_quality_summary(self):
        """Code quality metrics summary"""
        print(f"\n{'=' * 80}")
        print("CODE QUALITY METRICS")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            q = p.get("quality", {})
            rows.append(
                [
                    name,
                    q.get("total_lines", 0),
                    q.get("code_lines", 0),
                    q.get("comment_lines", 0),
                    f"{q.get('avg_function_length', 0):.1f}",
                    q.get("max_function_length", 0),
                    f"{q.get('type_hints_usage', 0):.0f}%",
                    len(q.get("complex_functions", [])),
                    len(q.get("long_files", [])),
                ]
            )

        headers = [
            "Project",
            "Total",
            "Code",
            "Comments",
            "AvgFunc",
            "MaxFunc",
            "TypeHints",
            "Complex",
            "LongFiles",
        ]
        print_table(headers, rows)

    def complex_functions(self, project: Optional[str] = None):
        """List complex functions (>50 lines)"""
        print(f"\n{'=' * 80}")
        print("COMPLEX FUNCTIONS (>50 lines)")
        print(f"{'=' * 80}")

        projects = {project: self.projects[project]} if project else self.projects

        for name, p in projects.items():
            funcs = p.get("quality", {}).get("complex_functions", [])
            if funcs:
                print(f"\n{name}: {len(funcs)} complex functions")
                for f in funcs[:20]:
                    print(f"  - {f}")
                if len(funcs) > 20:
                    print(f"  ... and {len(funcs) - 20} more")

    # ============================================================
    # GIT ANALYSIS
    # ============================================================

    def git_summary(self):
        """Git status summary"""
        print(f"\n{'=' * 80}")
        print("GIT STATUS SUMMARY")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            g = p.get("git", {})
            rows.append(
                [
                    name,
                    len(g.get("uncommitted_files", [])),
                    len(g.get("staged_files", [])),
                    g.get("total_commits_30d", 0),
                    g.get("days_since_last_commit", "N/A"),
                    g.get("last_commit_date", "N/A")[:10]
                    if g.get("last_commit_date")
                    else "N/A",
                ]
            )

        headers = [
            "Project",
            "Uncommitted",
            "Staged",
            "Commits(30d)",
            "DaysAgo",
            "LastCommit",
        ]
        print_table(headers, rows)

    def uncommitted_files(self, project: Optional[str] = None):
        """List uncommitted files"""
        print(f"\n{'=' * 80}")
        print("UNCOMMITTED FILES")
        print(f"{'=' * 80}")

        projects = {project: self.projects[project]} if project else self.projects

        for name, p in projects.items():
            files = p.get("git", {}).get("uncommitted_files", [])
            if files:
                print(f"\n{name}: {len(files)} uncommitted files")
                for f in files:
                    print(f"  - {f}")

    # ============================================================
    # DOCUMENTATION ANALYSIS
    # ============================================================

    def docs_summary(self):
        """Documentation coverage summary"""
        print(f"\n{'=' * 80}")
        print("DOCUMENTATION COVERAGE")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            d = p.get("docs", {})
            rows.append(
                [
                    name,
                    "Y" if d.get("readme_exists") else "N",
                    len(d.get("readme_sections", [])),
                    len(d.get("api_docs", [])),
                    len(d.get("guides", [])),
                    f"{d.get('docstring_coverage', 0):.0f}%",
                    len(d.get("undocumented_functions", [])),
                    len(d.get("undocumented_classes", [])),
                ]
            )

        headers = [
            "Project",
            "README",
            "Sections",
            "APIDocs",
            "Guides",
            "Docstrings",
            "NoDocFuncs",
            "NoDocClasses",
        ]
        print_table(headers, rows)

    def undocumented_items(self, project: str):
        """List undocumented functions and classes"""
        print(f"\n{'=' * 80}")
        print(f"UNDOCUMENTED ITEMS IN {project}")
        print(f"{'=' * 80}")

        if project not in self.projects:
            print(f"Project '{project}' not found")
            return

        d = self.projects[project].get("docs", {})

        funcs = d.get("undocumented_functions", [])
        if funcs:
            print(f"\nFunctions without docstrings: {len(funcs)}")
            for f in funcs[:20]:
                print(f"  - {f}")

        classes = d.get("undocumented_classes", [])
        if classes:
            print(f"\nClasses without docstrings: {len(classes)}")
            for c in classes[:20]:
                print(f"  - {c}")

    # ============================================================
    # DEAD CODE ANALYSIS
    # ============================================================

    def dead_code_summary(self):
        """Dead code analysis summary"""
        print(f"\n{'=' * 80}")
        print("DEAD CODE / TECHNICAL DEBT")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            dc = p.get("dead_code", {})
            rows.append(
                [
                    name,
                    len(dc.get("unused_imports", [])),
                    len(dc.get("empty_files", [])),
                    len(dc.get("todo_fixme", [])),
                ]
            )

        headers = ["Project", "UnusedImports", "EmptyFiles", "TODOs"]
        print_table(headers, rows)

    def todos(self, project: Optional[str] = None):
        """List TODO/FIXME comments"""
        print(f"\n{'=' * 80}")
        print("TODO/FIXME COMMENTS")
        print(f"{'=' * 80}")

        projects = {project: self.projects[project]} if project else self.projects

        for name, p in projects.items():
            todos = p.get("dead_code", {}).get("todo_fixme", [])
            if todos:
                print(f"\n{name}: {len(todos)} TODOs")
                for t in todos[:15]:
                    print(f"  - {t}")
                if len(todos) > 15:
                    print(f"  ... and {len(todos) - 15} more")

    # ============================================================
    # CONFIGURATION ANALYSIS
    # ============================================================

    def config_matrix(self):
        """Configuration comparison matrix"""
        print(f"\n{'=' * 80}")
        print("CONFIGURATION MATRIX")
        print(f"{'=' * 80}\n")

        rows = []
        for name, p in self.projects.items():
            c = p.get("config", {})
            rows.append(
                [
                    name,
                    "Y" if c.get("has_pyproject") else "-",
                    "Y" if c.get("has_dockerfile") else "-",
                    "Y" if c.get("has_docker_compose") else "-",
                    "Y" if c.get("has_ci_config") else "-",
                    "Y" if c.get("has_pre_commit") else "-",
                    "Y" if c.get("has_mkdocs") else "-",
                    c.get("python_version", "-")[:8],
                    c.get("linter_config", "-"),
                    c.get("formatter_config", "-"),
                ]
            )

        headers = [
            "Project",
            "pyproj",
            "docker",
            "compose",
            "CI",
            "precommit",
            "mkdocs",
            "python",
            "linter",
            "fmt",
        ]
        print_table(headers, rows)

    def config_missing(self):
        """List missing configurations"""
        print(f"\n{'=' * 80}")
        print("MISSING CONFIGURATIONS")
        print(f"{'=' * 80}")

        for name, p in self.projects.items():
            c = p.get("config", {})
            missing = []
            if not c.get("has_pyproject"):
                missing.append("pyproject.toml")
            if not c.get("has_ci_config"):
                missing.append("CI/CD")
            if not c.get("has_pre_commit"):
                missing.append("pre-commit")
            if not c.get("has_mkdocs"):
                missing.append("mkdocs")

            if missing:
                print(f"\n{name}: Missing {', '.join(missing)}")

    # ============================================================
    # ISSUE ANALYSIS
    # ============================================================

    def all_issues(self):
        """All issues by severity"""
        print(f"\n{'=' * 80}")
        print("ALL ISSUES BY PROJECT")
        print(f"{'=' * 80}")

        for name, p in self.projects.items():
            issues = p.get("issues", [])
            if issues:
                print(f"\n{name}: ({len(issues)} issues)")
                for severity, message in issues:
                    icon = {"CRITICAL": "[!!]", "WARNING": "[!]", "INFO": "[i]"}.get(
                        severity, "[ ]"
                    )
                    print(f"  {icon} {severity}: {message}")

    def critical_issues(self):
        """List only critical and warning issues"""
        print(f"\n{'=' * 80}")
        print("CRITICAL AND WARNING ISSUES ONLY")
        print(f"{'=' * 80}")

        for name, p in self.projects.items():
            issues = [
                (s, m) for s, m in p.get("issues", []) if s in ("CRITICAL", "WARNING")
            ]
            if issues:
                print(f"\n{name}:")
                for severity, message in issues:
                    icon = {"CRITICAL": "[!!]", "WARNING": "[!]"}.get(severity, "[ ]")
                    print(f"  {icon} {message}")

    # ============================================================
    # CROSS-PROJECT ANALYSIS
    # ============================================================

    def compare_projects(self, *project_names):
        """Side-by-side comparison of specific projects"""
        print(f"\n{'=' * 80}")
        print(f"PROJECT COMPARISON: {', '.join(project_names)}")
        print(f"{'=' * 80}\n")

        metrics = [
            ("Score", lambda p: f"{p['score']:.0f}"),
            ("Test Functions", lambda p: p["tests"]["test_functions"]),
            ("Unit Tests", lambda p: len(p["tests"]["unit_tests"])),
            ("Integration Tests", lambda p: len(p["tests"]["integration_tests"])),
            ("Coverage Gaps", lambda p: len(p["coverage_gaps"])),
            ("Docstring Coverage", lambda p: f"{p['docs']['docstring_coverage']:.0f}%"),
            (
                "Type Hints",
                lambda p: f"{p.get('quality', {}).get('type_hints_usage', 0):.0f}%",
            ),
            ("Total Lines", lambda p: p.get("quality", {}).get("total_lines", 0)),
            ("Commits (30d)", lambda p: p.get("git", {}).get("total_commits_30d", 0)),
            ("Issues", lambda p: len(p["issues"])),
        ]

        headers = ["Metric"] + list(project_names)
        rows = []
        for metric_name, extractor in metrics:
            row = [metric_name]
            for pname in project_names:
                if pname in self.projects:
                    row.append(extractor(self.projects[pname]))
                else:
                    row.append("N/A")
            rows.append(row)

        print_table(headers, rows)

    def ranking(self, metric: str = "score"):
        """Rank projects by various metrics"""
        print(f"\n{'=' * 80}")
        print(f"PROJECT RANKING BY: {metric.upper()}")
        print(f"{'=' * 80}\n")

        extractors = {
            "score": lambda p: p["score"],
            "tests": lambda p: p["tests"]["test_functions"],
            "docstrings": lambda p: p["docs"]["docstring_coverage"],
            "typehints": lambda p: p.get("quality", {}).get("type_hints_usage", 0),
            "gaps": lambda p: -len(p["coverage_gaps"]),  # Negative so fewer is better
            "issues": lambda p: -len(p["issues"]),  # Negative so fewer is better
            "lines": lambda p: p.get("quality", {}).get("total_lines", 0),
        }

        if metric not in extractors:
            print(f"Unknown metric. Available: {', '.join(extractors.keys())}")
            return

        extractor = extractors[metric]
        ranked = sorted(
            self.projects.items(), key=lambda x: extractor(x[1]), reverse=True
        )

        for i, (name, p) in enumerate(ranked, 1):
            value = extractor(p)
            if metric in ("gaps", "issues"):
                value = -value  # Convert back to positive
            print(f"  {i}. {name}: {value}")

    # ============================================================
    # INTERACTIVE MENU
    # ============================================================

    def interactive(self):
        """Interactive menu"""
        commands = {
            "summary": ("Overall health summary", self.summary),
            "tests": ("Test breakdown by project", self.test_breakdown),
            "test-files": ("Test files by type", self.test_files_by_type),
            "test-other": (
                "Tests needing categorization",
                self.tests_needing_categorization,
            ),
            "gaps": ("Coverage gaps summary", self.coverage_gaps_summary),
            "gaps-top": (
                "Largest untested files",
                lambda: self.largest_untested_files(20),
            ),
            "quality": ("Code quality metrics", self.code_quality_summary),
            "complex": ("Complex functions", self.complex_functions),
            "git": ("Git status summary", self.git_summary),
            "uncommitted": ("Uncommitted files", self.uncommitted_files),
            "docs": ("Documentation coverage", self.docs_summary),
            "dead": ("Dead code summary", self.dead_code_summary),
            "todos": ("TODO/FIXME comments", self.todos),
            "config": ("Configuration matrix", self.config_matrix),
            "config-missing": ("Missing configurations", self.config_missing),
            "issues": ("All issues", self.all_issues),
            "critical": ("Critical issues only", self.critical_issues),
            "rank": ("Ranking by score", lambda: self.ranking("score")),
            "help": ("Show this menu", lambda: None),
            "quit": ("Exit", lambda: sys.exit(0)),
        }

        print("\n" + "=" * 60)
        print("AUDIT DATA ANALYZER - Interactive Mode")
        print("=" * 60)
        print("\nAvailable commands:")
        for cmd, (desc, _) in commands.items():
            print(f"  {cmd:15} - {desc}")
        print("\nProject-specific:")
        print("  gaps <project>    - Coverage gaps for specific project")
        print("  undoc <project>   - Undocumented items in project")
        print("  compare p1 p2     - Compare two projects")
        print(
            "  rank <metric>     - Rank by: score, tests, docstrings, typehints, gaps, issues"
        )

        while True:
            try:
                cmd = input("\n> ").strip().lower()
                parts = cmd.split()

                if not parts:
                    continue

                if parts[0] in commands:
                    commands[parts[0]][1]()
                elif parts[0] == "gaps" and len(parts) > 1:
                    self.coverage_gaps_by_module(parts[1])
                elif parts[0] == "undoc" and len(parts) > 1:
                    self.undocumented_items(parts[1])
                elif parts[0] == "compare" and len(parts) > 2:
                    self.compare_projects(*parts[1:])
                elif parts[0] == "rank" and len(parts) > 1:
                    self.ranking(parts[1])
                else:
                    print("Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except EOFError:
                break


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze audit data")
    parser.add_argument(
        "audit_file",
        nargs="?",
        default="exports/comprehensive_audit.json",
        help="Path to audit JSON file",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Interactive mode"
    )
    parser.add_argument("--summary", action="store_true", help="Show summary")
    parser.add_argument("--tests", action="store_true", help="Show test breakdown")
    parser.add_argument("--gaps", action="store_true", help="Show coverage gaps")
    parser.add_argument("--quality", action="store_true", help="Show code quality")
    parser.add_argument("--git", action="store_true", help="Show git status")
    parser.add_argument("--docs", action="store_true", help="Show documentation")
    parser.add_argument("--config", action="store_true", help="Show configuration")
    parser.add_argument("--issues", action="store_true", help="Show all issues")
    parser.add_argument("--all", action="store_true", help="Show all reports")
    args = parser.parse_args()

    # Find audit file
    audit_path = Path(args.audit_file)
    if not audit_path.is_absolute():
        audit_path = Path(__file__).parent.parent / audit_path

    if not audit_path.exists():
        print(f"Audit file not found: {audit_path}")
        print("Run comprehensive_ecosystem_audit.py --json first")
        sys.exit(1)

    data = load_audit(audit_path)
    analyzer = AuditAnalyzer(data)

    if args.interactive:
        analyzer.interactive()
    elif args.all:
        analyzer.summary()
        analyzer.test_breakdown()
        analyzer.coverage_gaps_summary()
        analyzer.code_quality_summary()
        analyzer.git_summary()
        analyzer.docs_summary()
        analyzer.dead_code_summary()
        analyzer.config_matrix()
        analyzer.all_issues()
    else:
        # Default or specific reports
        if args.summary or not any(
            [
                args.tests,
                args.gaps,
                args.quality,
                args.git,
                args.docs,
                args.config,
                args.issues,
            ]
        ):
            analyzer.summary()
        if args.tests:
            analyzer.test_breakdown()
            analyzer.test_files_by_type()
        if args.gaps:
            analyzer.coverage_gaps_summary()
            analyzer.largest_untested_files()
        if args.quality:
            analyzer.code_quality_summary()
        if args.git:
            analyzer.git_summary()
        if args.docs:
            analyzer.docs_summary()
        if args.config:
            analyzer.config_matrix()
        if args.issues:
            analyzer.all_issues()


if __name__ == "__main__":
    main()
