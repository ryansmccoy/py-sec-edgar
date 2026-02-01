#!/usr/bin/env python3
"""
Comprehensive Ecosystem Audit Tool
===================================
Multi-dimensional analysis of all spine projects including:
- Test coverage structure analysis (unit vs integration vs e2e)
- Git status and recent activity
- Source-to-test file mapping gaps
- Documentation coverage
- Dead code detection
- Code quality metrics
- Dependency analysis
- Configuration consistency
"""

import ast
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Project configurations with more detailed paths
PROJECTS = {
    "capture-spine": {
        "path": "capture-spine",
        "src_dirs": ["src/backend", "src/frontend/src"],
        "test_dirs": ["tests"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml", "package.json", "docker-compose.yml"],
        "type": "fullstack",
    },
    "entityspine": {
        "path": "entityspine",
        "src_dirs": ["src/entityspine", "entityspine"],
        "test_dirs": ["tests"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml", "mkdocs.yml"],
        "type": "backend",
    },
    "feedspine": {
        "path": "feedspine",
        "src_dirs": ["src/feedspine", "feedspine"],
        "test_dirs": ["tests"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml"],
        "type": "backend",
    },
    "genai-spine": {
        "path": "genai-spine",
        "src_dirs": ["src", "genai_spine", "frontend/src"],
        "test_dirs": ["tests", "frontend/e2e"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml", "frontend/package.json"],
        "type": "fullstack",
    },
    "spine-core": {
        "path": "spine-core",
        "src_dirs": ["src", "spine_core"],
        "test_dirs": ["tests"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml"],
        "type": "library",
    },
    "py_sec_edgar": {
        "path": "py_sec_edgar",
        "src_dirs": ["py_sec_edgar"],
        "test_dirs": ["tests"],
        "docs_dir": "docs",
        "config_files": ["pyproject.toml"],
        "type": "library",
    },
}


@dataclass
class TestAnalysis:
    """Detailed test file analysis"""

    unit_tests: list = field(default_factory=list)
    integration_tests: list = field(default_factory=list)
    e2e_tests: list = field(default_factory=list)
    other_tests: list = field(default_factory=list)
    test_functions: int = 0
    test_classes: int = 0
    fixtures: int = 0
    parametrized: int = 0
    async_tests: int = 0
    mocked_tests: int = 0


@dataclass
class GitAnalysis:
    """Git repository analysis"""

    uncommitted_files: list = field(default_factory=list)
    staged_files: list = field(default_factory=list)
    recent_commits: list = field(default_factory=list)
    contributors: list = field(default_factory=list)
    last_commit_date: str = ""
    days_since_last_commit: int = 0
    total_commits_30d: int = 0
    files_changed_30d: int = 0


@dataclass
class CoverageGap:
    """Source file without corresponding test"""

    source_file: str
    expected_test: str
    module: str
    functions: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    lines: int = 0


@dataclass
class DocAnalysis:
    """Documentation analysis"""

    readme_exists: bool = False
    readme_sections: list = field(default_factory=list)
    api_docs: list = field(default_factory=list)
    guides: list = field(default_factory=list)
    examples_documented: int = 0
    docstring_coverage: float = 0.0
    undocumented_functions: list = field(default_factory=list)
    undocumented_classes: list = field(default_factory=list)


@dataclass
class DeadCodeAnalysis:
    """Dead code detection results"""

    unused_imports: list = field(default_factory=list)
    unused_variables: list = field(default_factory=list)
    unused_functions: list = field(default_factory=list)
    unused_classes: list = field(default_factory=list)
    empty_files: list = field(default_factory=list)
    todo_fixme: list = field(default_factory=list)


@dataclass
class DependencyAnalysis:
    """Dependency analysis"""

    dependencies: list = field(default_factory=list)
    dev_dependencies: list = field(default_factory=list)
    missing_from_requirements: list = field(default_factory=list)
    unused_dependencies: list = field(default_factory=list)
    version_conflicts: list = field(default_factory=list)
    internal_deps: list = field(default_factory=list)


@dataclass
class ConfigAnalysis:
    """Configuration consistency"""

    has_pyproject: bool = False
    has_setup_py: bool = False
    has_requirements: bool = False
    has_dockerfile: bool = False
    has_docker_compose: bool = False
    has_ci_config: bool = False
    has_pre_commit: bool = False
    has_mkdocs: bool = False
    python_version: str = ""
    linter_config: str = ""
    formatter_config: str = ""


@dataclass
class CodeQuality:
    """Code quality metrics"""

    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    complex_functions: list = field(default_factory=list)  # cyclomatic > 10
    long_files: list = field(default_factory=list)  # > 500 lines
    type_hints_usage: float = 0.0


@dataclass
class ProjectAudit:
    """Complete project audit"""

    name: str
    path: str
    project_type: str
    tests: TestAnalysis = field(default_factory=TestAnalysis)
    git: GitAnalysis = field(default_factory=GitAnalysis)
    coverage_gaps: list = field(default_factory=list)
    docs: DocAnalysis = field(default_factory=DocAnalysis)
    dead_code: DeadCodeAnalysis = field(default_factory=DeadCodeAnalysis)
    dependencies: DependencyAnalysis = field(default_factory=DependencyAnalysis)
    config: ConfigAnalysis = field(default_factory=ConfigAnalysis)
    quality: CodeQuality = field(default_factory=CodeQuality)
    issues: list = field(default_factory=list)
    score: float = 0.0


class ComprehensiveAuditor:
    """Main auditor class"""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.audits: dict[str, ProjectAudit] = {}

    def audit_all(self) -> dict[str, ProjectAudit]:
        """Run full audit on all projects"""
        for name, config in PROJECTS.items():
            project_path = self.workspace_root / config["path"]
            if project_path.exists():
                print(f"[AUDIT] {name}...")
                self.audits[name] = self.audit_project(name, config)
            else:
                print(f"[SKIP] {name} - path not found")
        return self.audits

    def audit_project(self, name: str, config: dict) -> ProjectAudit:
        """Run complete audit on a single project"""
        project_path = self.workspace_root / config["path"]
        audit = ProjectAudit(
            name=name, path=str(project_path), project_type=config["type"]
        )

        # Run all analysis modules
        audit.tests = self.analyze_tests(project_path, config)
        audit.git = self.analyze_git(project_path)
        audit.coverage_gaps = self.analyze_coverage_gaps(project_path, config)
        audit.docs = self.analyze_docs(project_path, config)
        audit.dead_code = self.analyze_dead_code(project_path, config)
        audit.dependencies = self.analyze_dependencies(project_path)
        audit.config = self.analyze_config(project_path)
        audit.quality = self.analyze_code_quality(project_path, config)

        # Calculate issues and score
        audit.issues = self.calculate_issues(audit)
        audit.score = self.calculate_score(audit)

        return audit

    def analyze_tests(self, project_path: Path, config: dict) -> TestAnalysis:
        """Analyze test structure and patterns"""
        analysis = TestAnalysis()

        for test_dir in config.get("test_dirs", ["tests"]):
            test_path = project_path / test_dir
            if not test_path.exists():
                continue

            for py_file in test_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                rel_path = str(py_file.relative_to(project_path))

                # Categorize by directory structure
                if "/unit/" in rel_path or "\\unit\\" in rel_path:
                    analysis.unit_tests.append(rel_path)
                elif "/integration/" in rel_path or "\\integration\\" in rel_path:
                    analysis.integration_tests.append(rel_path)
                elif (
                    "/e2e/" in rel_path
                    or "\\e2e\\" in rel_path
                    or "/playwright/" in rel_path
                ):
                    analysis.e2e_tests.append(rel_path)
                elif py_file.name.startswith("test_") or py_file.name.endswith(
                    "_test.py"
                ):
                    # Categorize by name patterns
                    if "integration" in py_file.name:
                        analysis.integration_tests.append(rel_path)
                    elif "e2e" in py_file.name:
                        analysis.e2e_tests.append(rel_path)
                    else:
                        analysis.other_tests.append(rel_path)
                else:
                    analysis.other_tests.append(rel_path)

                # Analyze test file content
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")

                    # Count test patterns
                    analysis.test_functions += len(
                        re.findall(r"\bdef test_\w+", content)
                    )
                    analysis.test_classes += len(
                        re.findall(r"\bclass Test\w+", content)
                    )
                    analysis.fixtures += len(re.findall(r"@pytest\.fixture", content))
                    analysis.parametrized += len(
                        re.findall(r"@pytest\.mark\.parametrize", content)
                    )
                    analysis.async_tests += len(
                        re.findall(r"\basync def test_", content)
                    )
                    analysis.mocked_tests += len(
                        re.findall(r"@patch|@mock|Mock\(|MagicMock", content)
                    )
                except:
                    pass

        return analysis

    def analyze_git(self, project_path: Path) -> GitAnalysis:
        """Analyze git status and history"""
        analysis = GitAnalysis()

        try:
            # Check if it's a git repo (might be in parent)
            git_root = self.workspace_root

            # Get uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", str(project_path)],
                capture_output=True,
                text=True,
                cwd=git_root,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        status = line[:2]
                        filepath = line[3:].strip()
                        if status[0] in "MADRCU":
                            analysis.staged_files.append(filepath)
                        if status[1] in "MADRCU?":
                            analysis.uncommitted_files.append(filepath)

            # Get recent commits (last 30 days)
            since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    "--since",
                    since_date,
                    "--",
                    str(project_path),
                ],
                capture_output=True,
                text=True,
                cwd=git_root,
            )
            if result.returncode == 0:
                commits = [c for c in result.stdout.strip().split("\n") if c.strip()]
                analysis.recent_commits = commits[:20]  # Limit to 20
                analysis.total_commits_30d = len(commits)

            # Get last commit date
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci", "--", str(project_path)],
                capture_output=True,
                text=True,
                cwd=git_root,
            )
            if result.returncode == 0 and result.stdout.strip():
                analysis.last_commit_date = result.stdout.strip()[:10]
                try:
                    last_date = datetime.strptime(analysis.last_commit_date, "%Y-%m-%d")
                    analysis.days_since_last_commit = (datetime.now() - last_date).days
                except:
                    pass

            # Get contributors
            result = subprocess.run(
                [
                    "git",
                    "shortlog",
                    "-sn",
                    "--since",
                    since_date,
                    "--",
                    str(project_path),
                ],
                capture_output=True,
                text=True,
                cwd=git_root,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n")[:10]:
                    if line.strip():
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            analysis.contributors.append(
                                {"commits": parts[0].strip(), "name": parts[1]}
                            )

        except Exception as e:
            pass

        return analysis

    def analyze_coverage_gaps(self, project_path: Path, config: dict) -> list:
        """Find source files without corresponding tests"""
        gaps = []

        for src_dir in config.get("src_dirs", []):
            src_path = project_path / src_dir
            if not src_path.exists():
                continue

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                if "/migrations/" in str(py_file) or "\\migrations\\" in str(py_file):
                    continue

                rel_path = py_file.relative_to(src_path)

                # Expected test file name
                expected_test = f"test_{py_file.stem}.py"

                # Check if test exists in various locations
                test_found = False
                for test_dir in config.get("test_dirs", ["tests"]):
                    test_base = project_path / test_dir

                    # Check direct match
                    if (test_base / "unit" / expected_test).exists():
                        test_found = True
                        break
                    if (test_base / expected_test).exists():
                        test_found = True
                        break

                    # Check with module path
                    test_with_path = (
                        test_base / "unit" / rel_path.parent / expected_test
                    )
                    if test_with_path.exists():
                        test_found = True
                        break

                if not test_found:
                    try:
                        content = py_file.read_text(encoding="utf-8", errors="ignore")
                        tree = ast.parse(content)

                        functions = [
                            node.name
                            for node in ast.walk(tree)
                            if isinstance(node, ast.FunctionDef)
                            and not node.name.startswith("_")
                        ]
                        classes = [
                            node.name
                            for node in ast.walk(tree)
                            if isinstance(node, ast.ClassDef)
                        ]

                        if (
                            functions or classes
                        ):  # Only report if there's something to test
                            gaps.append(
                                CoverageGap(
                                    source_file=str(py_file.relative_to(project_path)),
                                    expected_test=expected_test,
                                    module=py_file.stem,
                                    functions=functions[:10],  # Limit
                                    classes=classes[:10],
                                    lines=len(content.split("\n")),
                                )
                            )
                    except:
                        pass

        return gaps

    def analyze_docs(self, project_path: Path, config: dict) -> DocAnalysis:
        """Analyze documentation coverage"""
        analysis = DocAnalysis()

        # Check README
        readme = project_path / "README.md"
        if readme.exists():
            analysis.readme_exists = True
            try:
                content = readme.read_text(encoding="utf-8", errors="ignore")
                # Extract H2 sections
                analysis.readme_sections = re.findall(
                    r"^##\s+(.+)$", content, re.MULTILINE
                )
            except:
                pass

        # Check docs directory
        docs_dir = project_path / config.get("docs_dir", "docs")
        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                rel_path = str(md_file.relative_to(docs_dir))
                if "api" in rel_path.lower():
                    analysis.api_docs.append(rel_path)
                elif "guide" in rel_path.lower() or "tutorial" in rel_path.lower():
                    analysis.guides.append(rel_path)

        # Analyze docstring coverage in source
        total_items = 0
        documented_items = 0

        for src_dir in config.get("src_dirs", []):
            src_path = project_path / src_dir
            if not src_path.exists():
                continue

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name.startswith("_"):
                                continue
                            total_items += 1
                            docstring = ast.get_docstring(node)
                            if docstring:
                                documented_items += 1
                            else:
                                analysis.undocumented_functions.append(
                                    f"{py_file.relative_to(project_path)}:{node.name}"
                                )
                        elif isinstance(node, ast.ClassDef):
                            total_items += 1
                            docstring = ast.get_docstring(node)
                            if docstring:
                                documented_items += 1
                            else:
                                analysis.undocumented_classes.append(
                                    f"{py_file.relative_to(project_path)}:{node.name}"
                                )
                except:
                    pass

        if total_items > 0:
            analysis.docstring_coverage = round(documented_items / total_items * 100, 1)

        # Limit lists for output
        analysis.undocumented_functions = analysis.undocumented_functions[:20]
        analysis.undocumented_classes = analysis.undocumented_classes[:20]

        return analysis

    def analyze_dead_code(self, project_path: Path, config: dict) -> DeadCodeAnalysis:
        """Detect potential dead code"""
        analysis = DeadCodeAnalysis()

        for src_dir in config.get("src_dirs", []):
            src_path = project_path / src_dir
            if not src_path.exists():
                continue

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    rel_path = str(py_file.relative_to(project_path))

                    # Check for empty files
                    lines = [
                        l
                        for l in content.split("\n")
                        if l.strip() and not l.strip().startswith("#")
                    ]
                    if len(lines) < 3:
                        analysis.empty_files.append(rel_path)
                        continue

                    # Find TODO/FIXME comments
                    for i, line in enumerate(content.split("\n"), 1):
                        if re.search(
                            r"#.*\b(TODO|FIXME|XXX|HACK)\b", line, re.IGNORECASE
                        ):
                            analysis.todo_fixme.append(
                                f"{rel_path}:{i}: {line.strip()[:80]}"
                            )

                    # Basic unused import detection (simplified)
                    tree = ast.parse(content)
                    imports = set()
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.asname or alias.name.split(".")[0])
                        elif isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                if alias.name != "*":
                                    imports.add(alias.asname or alias.name)

                    # Check if imports are used (simplified check)
                    for imp in imports:
                        # Count occurrences (excluding the import line itself)
                        pattern = r"\b" + re.escape(imp) + r"\b"
                        matches = re.findall(pattern, content)
                        if len(matches) <= 1:  # Only appears in import
                            analysis.unused_imports.append(f"{rel_path}: {imp}")

                except:
                    pass

        # Limit lists
        analysis.unused_imports = analysis.unused_imports[:30]
        analysis.todo_fixme = analysis.todo_fixme[:30]

        return analysis

    def analyze_dependencies(self, project_path: Path) -> DependencyAnalysis:
        """Analyze project dependencies"""
        analysis = DependencyAnalysis()

        # Parse pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")

                # Extract dependencies (simplified parsing)
                in_deps = False
                in_dev_deps = False
                for line in content.split("\n"):
                    if "[project.dependencies]" in line or "dependencies = [" in line:
                        in_deps = True
                        in_dev_deps = False
                    elif "[project.optional-dependencies]" in line or "dev = [" in line:
                        in_dev_deps = True
                        in_deps = False
                    elif line.strip().startswith("[") and not line.strip().startswith(
                        "[["
                    ):
                        in_deps = False
                        in_dev_deps = False
                    elif in_deps or in_dev_deps:
                        # Extract package name
                        match = re.search(r'"([a-zA-Z0-9_-]+)', line)
                        if match:
                            pkg = match.group(1)
                            if in_deps:
                                analysis.dependencies.append(pkg)
                            else:
                                analysis.dev_dependencies.append(pkg)

                # Check for internal dependencies
                for dep in analysis.dependencies:
                    if dep in [
                        "entityspine",
                        "feedspine",
                        "genai-spine",
                        "spine-core",
                        "py-sec-edgar",
                    ]:
                        analysis.internal_deps.append(dep)

            except:
                pass

        return analysis

    def analyze_config(self, project_path: Path) -> ConfigAnalysis:
        """Analyze project configuration"""
        analysis = ConfigAnalysis()

        analysis.has_pyproject = (project_path / "pyproject.toml").exists()
        analysis.has_setup_py = (project_path / "setup.py").exists()
        analysis.has_requirements = (project_path / "requirements.txt").exists() or (
            project_path / "requirements"
        ).is_dir()
        analysis.has_dockerfile = (project_path / "Dockerfile").exists()
        analysis.has_docker_compose = any(project_path.glob("docker-compose*.yml"))
        analysis.has_ci_config = (project_path / ".github" / "workflows").is_dir() or (
            project_path / ".gitlab-ci.yml"
        ).exists()
        analysis.has_pre_commit = (project_path / ".pre-commit-config.yaml").exists()
        analysis.has_mkdocs = (project_path / "mkdocs.yml").exists()

        # Extract Python version from pyproject.toml
        pyproject = project_path / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8")
                match = re.search(r'requires-python\s*=\s*["\']([^"\']+)', content)
                if match:
                    analysis.python_version = match.group(1)

                if "ruff" in content:
                    analysis.linter_config = "ruff"
                elif "flake8" in content:
                    analysis.linter_config = "flake8"
                elif "pylint" in content:
                    analysis.linter_config = "pylint"

                if "black" in content:
                    analysis.formatter_config = "black"
                elif "ruff" in content and "format" in content:
                    analysis.formatter_config = "ruff"
            except:
                pass

        return analysis

    def analyze_code_quality(self, project_path: Path, config: dict) -> CodeQuality:
        """Analyze code quality metrics"""
        quality = CodeQuality()

        function_lengths = []
        type_hint_count = 0
        total_functions = 0

        for src_dir in config.get("src_dirs", []):
            src_path = project_path / src_dir
            if not src_path.exists():
                continue

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    lines = content.split("\n")

                    quality.total_lines += len(lines)
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            quality.blank_lines += 1
                        elif stripped.startswith("#"):
                            quality.comment_lines += 1
                        else:
                            quality.code_lines += 1

                    # Track long files
                    if len(lines) > 500:
                        quality.long_files.append(
                            f"{py_file.relative_to(project_path)} ({len(lines)} lines)"
                        )

                    # Analyze functions
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            total_functions += 1

                            # Calculate function length
                            func_length = (
                                node.end_lineno - node.lineno
                                if hasattr(node, "end_lineno")
                                else 0
                            )
                            function_lengths.append(func_length)

                            if func_length > quality.max_function_length:
                                quality.max_function_length = func_length

                            if func_length > 50:
                                quality.complex_functions.append(
                                    f"{py_file.relative_to(project_path)}:{node.name} ({func_length} lines)"
                                )

                            # Check for type hints
                            if node.returns or any(
                                arg.annotation for arg in node.args.args
                            ):
                                type_hint_count += 1

                except:
                    pass

        if function_lengths:
            quality.avg_function_length = round(
                sum(function_lengths) / len(function_lengths), 1
            )

        if total_functions:
            quality.type_hints_usage = round(type_hint_count / total_functions * 100, 1)

        quality.complex_functions = quality.complex_functions[:20]
        quality.long_files = quality.long_files[:10]

        return quality

    def calculate_issues(self, audit: ProjectAudit) -> list:
        """Calculate issues based on audit results"""
        issues = []

        # Test issues
        if audit.tests.test_functions == 0:
            issues.append(("CRITICAL", "No test functions found"))
        elif audit.tests.test_functions < 10:
            issues.append(
                ("WARNING", f"Low test count: {audit.tests.test_functions} tests")
            )

        if not audit.tests.integration_tests:
            issues.append(("WARNING", "No integration tests found"))

        # Coverage gaps
        if len(audit.coverage_gaps) > 10:
            issues.append(
                ("WARNING", f"{len(audit.coverage_gaps)} source files without tests")
            )

        # Git issues
        if audit.git.uncommitted_files:
            issues.append(
                ("INFO", f"{len(audit.git.uncommitted_files)} uncommitted files")
            )
        if audit.git.days_since_last_commit > 30:
            issues.append(
                ("WARNING", f"No commits in {audit.git.days_since_last_commit} days")
            )

        # Doc issues
        if not audit.docs.readme_exists:
            issues.append(("CRITICAL", "No README.md found"))
        if audit.docs.docstring_coverage < 30:
            issues.append(
                ("WARNING", f"Low docstring coverage: {audit.docs.docstring_coverage}%")
            )

        # Dead code
        if len(audit.dead_code.todo_fixme) > 20:
            issues.append(
                ("INFO", f"{len(audit.dead_code.todo_fixme)}+ TODO/FIXME comments")
            )
        if audit.dead_code.empty_files:
            issues.append(
                ("INFO", f"{len(audit.dead_code.empty_files)} empty/stub files")
            )

        # Config issues
        if not audit.config.has_pyproject:
            issues.append(("WARNING", "No pyproject.toml found"))
        if not audit.config.has_ci_config:
            issues.append(("INFO", "No CI/CD configuration found"))

        # Quality issues
        if audit.quality.type_hints_usage < 50:
            issues.append(
                ("INFO", f"Low type hint usage: {audit.quality.type_hints_usage}%")
            )
        if audit.quality.complex_functions:
            issues.append(
                (
                    "INFO",
                    f"{len(audit.quality.complex_functions)} complex functions (>50 lines)",
                )
            )

        return issues

    def calculate_score(self, audit: ProjectAudit) -> float:
        """Calculate overall project health score (0-100)"""
        score = 100.0

        # Deductions
        for severity, _ in audit.issues:
            if severity == "CRITICAL":
                score -= 20
            elif severity == "WARNING":
                score -= 10
            elif severity == "INFO":
                score -= 2

        # Bonuses
        if audit.tests.test_functions > 50:
            score += 5
        if audit.tests.integration_tests:
            score += 5
        if audit.docs.docstring_coverage > 70:
            score += 5
        if audit.config.has_ci_config:
            score += 5
        if audit.quality.type_hints_usage > 80:
            score += 5

        return max(0, min(100, round(score, 1)))


def print_summary(audits: dict[str, ProjectAudit]):
    """Print summary table"""
    print("\n" + "=" * 100)
    print("ECOSYSTEM HEALTH SUMMARY")
    print("=" * 100)

    headers = [
        "Project",
        "Score",
        "Tests",
        "Unit",
        "Integ",
        "E2E",
        "Gaps",
        "Docs%",
        "Issues",
    ]
    print(
        f"\n{headers[0]:<20} {headers[1]:>6} {headers[2]:>6} {headers[3]:>6} {headers[4]:>6} {headers[5]:>6} {headers[6]:>6} {headers[7]:>6} {headers[8]:>8}"
    )
    print("-" * 100)

    for name, audit in audits.items():
        tests = audit.tests.test_functions
        unit = len(audit.tests.unit_tests)
        integ = len(audit.tests.integration_tests)
        e2e = len(audit.tests.e2e_tests)
        gaps = len(audit.coverage_gaps)
        docs = f"{audit.docs.docstring_coverage:.0f}%"
        issues = len(audit.issues)

        score_str = f"{audit.score:.0f}"
        if audit.score >= 80:
            score_str = f"{audit.score:.0f} [OK]"
        elif audit.score >= 60:
            score_str = f"{audit.score:.0f} [!]"
        else:
            score_str = f"{audit.score:.0f} [!!]"

        print(
            f"{name:<20} {score_str:>8} {tests:>6} {unit:>6} {integ:>6} {e2e:>6} {gaps:>6} {docs:>6} {issues:>8}"
        )

    print("-" * 100)


def print_git_summary(audits: dict[str, ProjectAudit]):
    """Print git status summary"""
    print("\n" + "=" * 100)
    print("GIT STATUS SUMMARY")
    print("=" * 100)

    for name, audit in audits.items():
        uncommitted = len(audit.git.uncommitted_files)
        staged = len(audit.git.staged_files)
        commits_30d = audit.git.total_commits_30d
        last_commit = audit.git.last_commit_date or "N/A"

        status = (
            "clean"
            if uncommitted == 0 and staged == 0
            else f"{uncommitted} uncommitted, {staged} staged"
        )
        print(f"\n{name}:")
        print(
            f"  Last commit: {last_commit} ({audit.git.days_since_last_commit} days ago)"
        )
        print(f"  Commits (30d): {commits_30d}")
        print(f"  Status: {status}")

        if audit.git.uncommitted_files[:5]:
            print(f"  Uncommitted files:")
            for f in audit.git.uncommitted_files[:5]:
                print(f"    - {f}")
            if len(audit.git.uncommitted_files) > 5:
                print(f"    ... and {len(audit.git.uncommitted_files) - 5} more")


def print_coverage_gaps(audits: dict[str, ProjectAudit]):
    """Print test coverage gap summary"""
    print("\n" + "=" * 100)
    print("TEST COVERAGE GAPS (Source files without tests)")
    print("=" * 100)

    for name, audit in audits.items():
        if not audit.coverage_gaps:
            print(f"\n{name}: All source files have tests! [OK]")
            continue

        print(f"\n{name}: {len(audit.coverage_gaps)} files without tests")
        for gap in audit.coverage_gaps[:10]:
            funcs = len(gap.functions)
            classes = len(gap.classes)
            print(
                f"  - {gap.source_file} ({gap.lines} lines, {funcs} functions, {classes} classes)"
            )
        if len(audit.coverage_gaps) > 10:
            print(f"  ... and {len(audit.coverage_gaps) - 10} more")


def print_issues(audits: dict[str, ProjectAudit]):
    """Print all issues by project"""
    print("\n" + "=" * 100)
    print("ALL ISSUES BY PROJECT")
    print("=" * 100)

    for name, audit in audits.items():
        if not audit.issues:
            print(f"\n{name}: No issues found! [OK]")
            continue

        print(f"\n{name}:")
        for severity, message in audit.issues:
            icon = {"CRITICAL": "[!!]", "WARNING": "[!]", "INFO": "[i]"}.get(
                severity, "[ ]"
            )
            print(f"  {icon} {severity}: {message}")


def print_dead_code(audits: dict[str, ProjectAudit]):
    """Print dead code analysis"""
    print("\n" + "=" * 100)
    print("DEAD CODE / TODO ANALYSIS")
    print("=" * 100)

    for name, audit in audits.items():
        dc = audit.dead_code
        if not dc.todo_fixme and not dc.empty_files and not dc.unused_imports:
            continue

        print(f"\n{name}:")
        if dc.empty_files:
            print(f"  Empty/stub files: {len(dc.empty_files)}")
        if dc.unused_imports:
            print(f"  Potentially unused imports: {len(dc.unused_imports)}")
            for imp in dc.unused_imports[:5]:
                print(f"    - {imp}")
        if dc.todo_fixme:
            print(f"  TODO/FIXME comments: {len(dc.todo_fixme)}")
            for todo in dc.todo_fixme[:5]:
                print(f"    - {todo[:80]}")


def print_config_comparison(audits: dict[str, ProjectAudit]):
    """Print configuration comparison matrix"""
    print("\n" + "=" * 100)
    print("CONFIGURATION COMPARISON MATRIX")
    print("=" * 100)

    configs = ["pyproject", "dockerfile", "compose", "ci", "pre-commit", "mkdocs"]

    print(f"\n{'Project':<20}", end="")
    for cfg in configs:
        print(f"{cfg:>12}", end="")
    print(f"{'python':>12}{'linter':>10}{'formatter':>12}")
    print("-" * 100)

    for name, audit in audits.items():
        c = audit.config
        vals = [
            "Y" if c.has_pyproject else "-",
            "Y" if c.has_dockerfile else "-",
            "Y" if c.has_docker_compose else "-",
            "Y" if c.has_ci_config else "-",
            "Y" if c.has_pre_commit else "-",
            "Y" if c.has_mkdocs else "-",
        ]
        print(f"{name:<20}", end="")
        for v in vals:
            print(f"{v:>12}", end="")
        print(
            f"{c.python_version or '-':>12}{c.linter_config or '-':>10}{c.formatter_config or '-':>12}"
        )


def export_json(audits: dict[str, ProjectAudit], filepath: str):
    """Export full audit to JSON"""

    def serialize(obj):
        if hasattr(obj, "__dict__"):
            return {k: serialize(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [serialize(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        return obj

    data = {
        "timestamp": datetime.now().isoformat(),
        "projects": {name: serialize(audit) for name, audit in audits.items()},
    }

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n[EXPORT] Full audit saved to {filepath}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Ecosystem Audit")
    parser.add_argument("--json", help="Export to JSON file")
    parser.add_argument("--git", action="store_true", help="Show detailed git status")
    parser.add_argument("--gaps", action="store_true", help="Show test coverage gaps")
    parser.add_argument("--issues", action="store_true", help="Show all issues")
    parser.add_argument("--dead", action="store_true", help="Show dead code analysis")
    parser.add_argument("--config", action="store_true", help="Show config comparison")
    parser.add_argument("--all", action="store_true", help="Show all detailed reports")
    parser.add_argument("--project", help="Audit single project")
    args = parser.parse_args()

    workspace_root = Path(__file__).parent.parent
    print(f"Workspace: {workspace_root}")

    auditor = ComprehensiveAuditor(workspace_root)
    audits = auditor.audit_all()

    if args.project:
        audits = {k: v for k, v in audits.items() if k == args.project}

    # Always show summary
    print_summary(audits)

    # Detailed reports
    if args.git or args.all:
        print_git_summary(audits)
    if args.gaps or args.all:
        print_coverage_gaps(audits)
    if args.issues or args.all:
        print_issues(audits)
    if args.dead or args.all:
        print_dead_code(audits)
    if args.config or args.all:
        print_config_comparison(audits)

    if args.json:
        export_json(audits, args.json)


if __name__ == "__main__":
    main()
