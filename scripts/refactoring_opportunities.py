#!/usr/bin/env python3
"""
Refactoring Opportunities Analyzer
===================================
Identify files that are candidates for refactoring based on:
- File size (lines of code)
- Number of classes/functions
- Class/method complexity
- Code smells (god classes, long methods, etc.)

Outputs detailed structure so AI can suggest refactorings.
"""

import ast
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# Thresholds for refactoring candidates
THRESHOLDS = {
    "large_file": 500,  # Lines of code
    "huge_file": 1000,
    "large_class": 300,  # Lines in a class
    "huge_class": 500,
    "long_method": 50,  # Lines in a method
    "very_long_method": 100,
    "many_methods": 20,  # Methods in a class
    "god_class": 30,
    "complex_function": 10,  # Cyclomatic complexity
}


@dataclass
class MethodInfo:
    """Information about a method/function"""

    name: str
    line_start: int
    line_end: int
    lines: int
    args: list
    returns: str
    is_async: bool
    is_property: bool
    is_classmethod: bool
    is_staticmethod: bool
    complexity: int = 0
    docstring: str = ""
    calls: list = field(default_factory=list)


@dataclass
class ClassInfo:
    """Information about a class"""

    name: str
    line_start: int
    line_end: int
    lines: int
    bases: list
    methods: list = field(default_factory=list)
    properties: list = field(default_factory=list)
    class_vars: list = field(default_factory=list)
    docstring: str = ""
    nested_classes: list = field(default_factory=list)


@dataclass
class FileStructure:
    """Complete file structure"""

    filepath: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    imports: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    functions: list = field(default_factory=list)
    module_docstring: str = ""


@dataclass
class RefactoringOpportunity:
    """A specific refactoring opportunity"""

    filepath: str
    type: str  # "large_file", "god_class", "long_method", etc.
    severity: str  # "high", "medium", "low"
    description: str
    location: str  # e.g., "class MyClass", "function my_func"
    metrics: dict = field(default_factory=dict)
    suggestions: list = field(default_factory=list)


class CodeAnalyzer:
    """Analyze code structure and identify refactoring opportunities"""

    def __init__(self, project_root: Path, src_dirs: list):
        self.project_root = project_root
        self.src_dirs = src_dirs
        self.file_structures = []
        self.opportunities = []

    def analyze_project(self) -> list:
        """Analyze entire project"""
        for src_dir in self.src_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue

            for py_file in src_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                if "/migrations/" in str(py_file) or "\\migrations\\" in str(py_file):
                    continue

                try:
                    structure = self.analyze_file(py_file)
                    self.file_structures.append(structure)
                    self.identify_opportunities(structure)
                except Exception as e:
                    pass

        return self.opportunities

    def analyze_file(self, filepath: Path) -> FileStructure:
        """Analyze a single file's structure"""
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        structure = FileStructure(
            filepath=str(filepath.relative_to(self.project_root)),
            total_lines=len(lines),
            code_lines=0,
            comment_lines=0,
            blank_lines=0,
        )

        # Count line types
        for line in lines:
            stripped = line.strip()
            if not stripped:
                structure.blank_lines += 1
            elif stripped.startswith("#"):
                structure.comment_lines += 1
            else:
                structure.code_lines += 1

        # Parse AST
        try:
            tree = ast.parse(content)
            structure.module_docstring = ast.get_docstring(tree) or ""

            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        structure.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        structure.imports.append(f"{module}.{alias.name}")
                elif isinstance(node, ast.ClassDef):
                    structure.classes.append(self.analyze_class(node, content))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    structure.functions.append(self.analyze_method(node, content))
        except:
            pass

        return structure

    def analyze_class(self, node: ast.ClassDef, content: str) -> ClassInfo:
        """Analyze a class definition"""
        lines = content.split("\n")

        class_info = ClassInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            lines=(node.end_lineno or node.lineno) - node.lineno + 1,
            bases=[self.get_name(base) for base in node.bases],
            docstring=ast.get_docstring(node) or "",
        )

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self.analyze_method(item, content)
                if any(
                    d.id == "property"
                    for d in item.decorator_list
                    if isinstance(d, ast.Name)
                ):
                    class_info.properties.append(method)
                else:
                    class_info.methods.append(method)
            elif isinstance(item, ast.ClassDef):
                class_info.nested_classes.append(item.name)
            elif isinstance(item, ast.AnnAssign) or isinstance(item, ast.Assign):
                # Class variables
                if isinstance(item, ast.AnnAssign) and isinstance(
                    item.target, ast.Name
                ):
                    class_info.class_vars.append(item.target.id)

        return class_info

    def analyze_method(self, node, content: str) -> MethodInfo:
        """Analyze a method/function definition"""
        is_async = isinstance(node, ast.AsyncFunctionDef)

        # Get decorators
        is_property = any(self.get_name(d) == "property" for d in node.decorator_list)
        is_classmethod = any(
            self.get_name(d) == "classmethod" for d in node.decorator_list
        )
        is_staticmethod = any(
            self.get_name(d) == "staticmethod" for d in node.decorator_list
        )

        # Get arguments
        args = [arg.arg for arg in node.args.args]

        # Get return annotation
        returns = self.get_name(node.returns) if node.returns else ""

        # Calculate cyclomatic complexity (simplified)
        complexity = self.calculate_complexity(node)

        # Get function calls
        calls = self.get_function_calls(node)

        method_info = MethodInfo(
            name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            lines=(node.end_lineno or node.lineno) - node.lineno + 1,
            args=args,
            returns=returns,
            is_async=is_async,
            is_property=is_property,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            complexity=complexity,
            docstring=ast.get_docstring(node) or "",
            calls=calls[:20],  # Limit
        )

        return method_info

    def get_name(self, node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return self.get_name(node.value)
        return ""

    def calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity (simplified)"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def get_function_calls(self, node) -> list:
        """Get all function calls in a node"""
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self.get_name(child.func)
                if name:
                    calls.append(name)
        return list(set(calls))

    def identify_opportunities(self, structure: FileStructure):
        """Identify refactoring opportunities in a file"""

        # Large/Huge file
        if structure.code_lines > THRESHOLDS["huge_file"]:
            self.opportunities.append(
                RefactoringOpportunity(
                    filepath=structure.filepath,
                    type="huge_file",
                    severity="high",
                    description=f"File has {structure.code_lines} lines of code",
                    location="entire file",
                    metrics={
                        "lines": structure.code_lines,
                        "classes": len(structure.classes),
                        "functions": len(structure.functions),
                    },
                    suggestions=[
                        "Split into multiple modules by responsibility",
                        "Extract classes into separate files",
                        "Group related functions into classes or modules",
                    ],
                )
            )
        elif structure.code_lines > THRESHOLDS["large_file"]:
            self.opportunities.append(
                RefactoringOpportunity(
                    filepath=structure.filepath,
                    type="large_file",
                    severity="medium",
                    description=f"File has {structure.code_lines} lines of code",
                    location="entire file",
                    metrics={
                        "lines": structure.code_lines,
                        "classes": len(structure.classes),
                        "functions": len(structure.functions),
                    },
                    suggestions=["Consider splitting into smaller modules"],
                )
            )

        # Analyze classes
        for cls in structure.classes:
            # God class (too many methods)
            if len(cls.methods) > THRESHOLDS["god_class"]:
                self.opportunities.append(
                    RefactoringOpportunity(
                        filepath=structure.filepath,
                        type="god_class",
                        severity="high",
                        description=f"Class '{cls.name}' has {len(cls.methods)} methods",
                        location=f"class {cls.name} (lines {cls.line_start}-{cls.line_end})",
                        metrics={
                            "methods": len(cls.methods),
                            "lines": cls.lines,
                            "properties": len(cls.properties),
                        },
                        suggestions=[
                            "Apply Single Responsibility Principle",
                            "Extract related methods into separate classes",
                            "Use composition over inheritance",
                            "Consider facade or strategy patterns",
                        ],
                    )
                )
            elif len(cls.methods) > THRESHOLDS["many_methods"]:
                self.opportunities.append(
                    RefactoringOpportunity(
                        filepath=structure.filepath,
                        type="large_class",
                        severity="medium",
                        description=f"Class '{cls.name}' has {len(cls.methods)} methods",
                        location=f"class {cls.name} (lines {cls.line_start}-{cls.line_end})",
                        metrics={"methods": len(cls.methods), "lines": cls.lines},
                        suggestions=["Consider splitting responsibilities"],
                    )
                )

            # Huge class (by lines)
            if cls.lines > THRESHOLDS["huge_class"]:
                self.opportunities.append(
                    RefactoringOpportunity(
                        filepath=structure.filepath,
                        type="huge_class",
                        severity="high",
                        description=f"Class '{cls.name}' has {cls.lines} lines",
                        location=f"class {cls.name} (lines {cls.line_start}-{cls.line_end})",
                        metrics={"lines": cls.lines, "methods": len(cls.methods)},
                        suggestions=[
                            "Extract helper classes",
                            "Move utility methods to separate modules",
                        ],
                    )
                )

            # Long methods
            for method in cls.methods:
                if method.lines > THRESHOLDS["very_long_method"]:
                    self.opportunities.append(
                        RefactoringOpportunity(
                            filepath=structure.filepath,
                            type="very_long_method",
                            severity="high",
                            description=f"Method '{cls.name}.{method.name}' has {method.lines} lines",
                            location=f"{cls.name}.{method.name} (lines {method.line_start}-{method.line_end})",
                            metrics={
                                "lines": method.lines,
                                "complexity": method.complexity,
                                "args": len(method.args),
                            },
                            suggestions=[
                                "Extract helper methods",
                                "Simplify logic flow",
                                "Consider breaking into multiple methods",
                            ],
                        )
                    )
                elif method.lines > THRESHOLDS["long_method"]:
                    self.opportunities.append(
                        RefactoringOpportunity(
                            filepath=structure.filepath,
                            type="long_method",
                            severity="medium",
                            description=f"Method '{cls.name}.{method.name}' has {method.lines} lines",
                            location=f"{cls.name}.{method.name} (lines {method.line_start}-{method.line_end})",
                            metrics={
                                "lines": method.lines,
                                "complexity": method.complexity,
                            },
                            suggestions=["Consider extracting helper methods"],
                        )
                    )

                # Complex methods
                if method.complexity > THRESHOLDS["complex_function"]:
                    self.opportunities.append(
                        RefactoringOpportunity(
                            filepath=structure.filepath,
                            type="complex_method",
                            severity="medium",
                            description=f"Method '{cls.name}.{method.name}' has complexity {method.complexity}",
                            location=f"{cls.name}.{method.name} (lines {method.line_start}-{method.line_end})",
                            metrics={
                                "complexity": method.complexity,
                                "lines": method.lines,
                            },
                            suggestions=[
                                "Simplify conditional logic",
                                "Extract complex conditions into helper methods",
                                "Consider early returns",
                            ],
                        )
                    )

        # Analyze module-level functions
        for func in structure.functions:
            if func.lines > THRESHOLDS["very_long_method"]:
                self.opportunities.append(
                    RefactoringOpportunity(
                        filepath=structure.filepath,
                        type="very_long_function",
                        severity="high",
                        description=f"Function '{func.name}' has {func.lines} lines",
                        location=f"function {func.name} (lines {func.line_start}-{func.line_end})",
                        metrics={"lines": func.lines, "complexity": func.complexity},
                        suggestions=[
                            "Extract helper functions",
                            "Consider creating a class",
                        ],
                    )
                )


class RefactoringReport:
    """Generate refactoring opportunity reports"""

    def __init__(self, opportunities: list, structures: list):
        self.opportunities = opportunities
        self.structures = structures

    def print_summary(self):
        """Print high-level summary"""
        print(f"\n{'=' * 80}")
        print("REFACTORING OPPORTUNITIES SUMMARY")
        print(f"{'=' * 80}\n")

        # Count by severity
        high = [o for o in self.opportunities if o.severity == "high"]
        medium = [o for o in self.opportunities if o.severity == "medium"]
        low = [o for o in self.opportunities if o.severity == "low"]

        print(f"Total opportunities: {len(self.opportunities)}")
        print(f"  High priority:     {len(high)}")
        print(f"  Medium priority:   {len(medium)}")
        print(f"  Low priority:      {len(low)}")

        # Count by type
        by_type = {}
        for o in self.opportunities:
            by_type[o.type] = by_type.get(o.type, 0) + 1

        print(f"\nBy type:")
        for opp_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {opp_type:20} {count:3}")

    def print_top_opportunities(self, limit: int = 20):
        """Print top refactoring opportunities"""
        print(f"\n{'=' * 80}")
        print(f"TOP {limit} REFACTORING OPPORTUNITIES")
        print(f"{'=' * 80}\n")

        # Sort by severity and metrics
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_opps = sorted(
            self.opportunities,
            key=lambda o: (priority_order[o.severity], o.metrics.get("lines", 0)),
            reverse=True,
        )

        for i, opp in enumerate(sorted_opps[:limit], 1):
            severity_icon = {"high": "[!!!]", "medium": "[!!]", "low": "[!]"}[
                opp.severity
            ]
            print(f"{i}. {severity_icon} {opp.type.upper()}: {opp.filepath}")
            print(f"   Location: {opp.location}")
            print(f"   {opp.description}")
            print(
                f"   Metrics: {', '.join(f'{k}={v}' for k, v in opp.metrics.items())}"
            )
            if opp.suggestions:
                print(f"   Suggestions:")
                for suggestion in opp.suggestions:
                    print(f"     - {suggestion}")
            print()

    def print_file_details(self, filepath: str):
        """Print detailed structure for a specific file"""
        structures = [s for s in self.structures if s.filepath == filepath]
        if not structures:
            print(f"File not found: {filepath}")
            return

        structure = structures[0]

        print(f"\n{'=' * 80}")
        print(f"FILE STRUCTURE: {filepath}")
        print(f"{'=' * 80}\n")

        print(
            f"Lines: {structure.total_lines} (code: {structure.code_lines}, comments: {structure.comment_lines}, blank: {structure.blank_lines})"
        )
        print(f"Imports: {len(structure.imports)}")
        print(f"Classes: {len(structure.classes)}")
        print(f"Functions: {len(structure.functions)}")

        if structure.module_docstring:
            print(f"\nModule docstring:")
            print(f"  {structure.module_docstring[:200]}...")

        # Classes
        for cls in structure.classes:
            print(f"\n{'-' * 80}")
            print(
                f"CLASS: {cls.name} (lines {cls.line_start}-{cls.line_end}, {cls.lines} lines)"
            )
            if cls.bases:
                print(f"  Inherits: {', '.join(cls.bases)}")
            if cls.docstring:
                print(f"  Docstring: {cls.docstring[:100]}...")

            print(f"  Class variables: {len(cls.class_vars)}")
            if cls.class_vars:
                print(f"    {', '.join(cls.class_vars[:10])}")

            print(f"  Properties: {len(cls.properties)}")
            for prop in cls.properties:
                print(
                    f"    @property {prop.name} (lines {prop.line_start}-{prop.line_end}, {prop.lines} lines)"
                )

            print(f"  Methods: {len(cls.methods)}")
            for method in cls.methods[:30]:  # Limit display
                decorators = []
                if method.is_async:
                    decorators.append("async")
                if method.is_classmethod:
                    decorators.append("@classmethod")
                if method.is_staticmethod:
                    decorators.append("@staticmethod")

                deco_str = " ".join(decorators) + " " if decorators else ""
                args_str = f"({', '.join(method.args)})"
                ret_str = f" -> {method.returns}" if method.returns else ""

                complexity_flag = (
                    f" [complex: {method.complexity}]" if method.complexity > 10 else ""
                )
                long_flag = (
                    f" [LONG: {method.lines} lines]" if method.lines > 50 else ""
                )

                print(
                    f"    {deco_str}{method.name}{args_str}{ret_str} (lines {method.line_start}-{method.line_end}){complexity_flag}{long_flag}"
                )

                if method.docstring:
                    print(f"      Doc: {method.docstring[:80]}...")

            if len(cls.methods) > 30:
                print(f"    ... and {len(cls.methods) - 30} more methods")

        # Module-level functions
        if structure.functions:
            print(f"\n{'-' * 80}")
            print(f"MODULE FUNCTIONS: {len(structure.functions)}")
            for func in structure.functions[:20]:
                args_str = f"({', '.join(func.args)})"
                ret_str = f" -> {func.returns}" if func.returns else ""
                print(
                    f"  {func.name}{args_str}{ret_str} (lines {func.line_start}-{func.line_end}, {func.lines} lines)"
                )

    def export_json(self, filepath: str):
        """Export opportunities to JSON for AI analysis"""
        data = {
            "opportunities": [asdict(o) for o in self.opportunities],
            "file_structures": [asdict(s) for s in self.structures],
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)

        print(f"\n[EXPORT] Refactoring analysis saved to {filepath}")

    def export_ai_prompt(self, filepath: str, top_n: int = 10):
        """Export as AI-friendly prompt for refactoring suggestions"""
        priority_order = {"high": 3, "medium": 2, "low": 1}
        sorted_opps = sorted(
            self.opportunities,
            key=lambda o: (priority_order[o.severity], o.metrics.get("lines", 0)),
            reverse=True,
        )[:top_n]

        with open(filepath, "w") as f:
            f.write("# Refactoring Opportunities for AI Analysis\n\n")
            f.write(
                "Below are the top refactoring candidates. For each, please suggest:\n"
            )
            f.write("1. Specific refactoring strategy\n")
            f.write("2. How to split/reorganize the code\n")
            f.write("3. New file/class structure\n")
            f.write("4. Any design patterns to apply\n\n")
            f.write("=" * 80 + "\n\n")

            for i, opp in enumerate(sorted_opps, 1):
                f.write(f"## {i}. {opp.type.upper()}: {opp.filepath}\n\n")
                f.write(f"**Severity:** {opp.severity}\n")
                f.write(f"**Location:** {opp.location}\n")
                f.write(f"**Description:** {opp.description}\n")
                f.write(
                    f"**Metrics:** {', '.join(f'{k}={v}' for k, v in opp.metrics.items())}\n\n"
                )

                # Find the structure
                structures = [s for s in self.structures if s.filepath == opp.filepath]
                if structures:
                    structure = structures[0]
                    f.write(f"**File Structure:**\n")
                    f.write(f"- Total lines: {structure.code_lines}\n")
                    f.write(f"- Classes: {len(structure.classes)}\n")
                    f.write(f"- Functions: {len(structure.functions)}\n\n")

                    # If it's a class issue, show the class details
                    if "class" in opp.location.lower():
                        class_name = opp.location.split()[1].split("(")[0]
                        for cls in structure.classes:
                            if cls.name == class_name:
                                f.write(f"**Class '{cls.name}' Details:**\n")
                                f.write(f"- Lines: {cls.lines}\n")
                                f.write(f"- Methods: {len(cls.methods)}\n")
                                f.write(f"- Properties: {len(cls.properties)}\n")
                                if cls.bases:
                                    f.write(
                                        f"- Inherits from: {', '.join(cls.bases)}\n"
                                    )
                                f.write(f"\n**Methods:**\n")
                                for method in cls.methods:
                                    f.write(
                                        f"- {method.name}({', '.join(method.args)}) - {method.lines} lines, complexity {method.complexity}\n"
                                    )
                                break

                f.write(f"\n**Current Suggestions:**\n")
                for suggestion in opp.suggestions:
                    f.write(f"- {suggestion}\n")

                f.write("\n" + "=" * 80 + "\n\n")

        print(f"[EXPORT] AI-friendly prompt saved to {filepath}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze refactoring opportunities")
    parser.add_argument("--project", help="Project name to analyze")
    parser.add_argument("--json", help="Export to JSON file")
    parser.add_argument("--ai-prompt", help="Export AI-friendly prompt file")
    parser.add_argument("--file", help="Show detailed structure for specific file")
    parser.add_argument(
        "--top", type=int, default=20, help="Number of top opportunities to show"
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).parent.parent

    # Project configurations
    PROJECTS = {
        "capture-spine": {
            "path": "capture-spine",
            "src_dirs": ["src/backend", "src/frontend/src"],
        },
        "entityspine": {
            "path": "entityspine",
            "src_dirs": ["src/entityspine", "entityspine"],
        },
        "feedspine": {"path": "feedspine", "src_dirs": ["src/feedspine", "feedspine"]},
        "genai-spine": {"path": "genai-spine", "src_dirs": ["src", "genai_spine"]},
        "spine-core": {"path": "spine-core", "src_dirs": ["src", "spine_core"]},
        "py_sec_edgar": {"path": "py_sec_edgar", "src_dirs": ["py_sec_edgar"]},
    }

    if args.project:
        if args.project not in PROJECTS:
            print(f"Unknown project: {args.project}")
            print(f"Available: {', '.join(PROJECTS.keys())}")
            return
        projects = {args.project: PROJECTS[args.project]}
    else:
        projects = PROJECTS

    all_opportunities = []
    all_structures = []

    for name, config in projects.items():
        project_path = workspace_root / config["path"]
        if not project_path.exists():
            continue

        print(f"[ANALYZE] {name}...")
        analyzer = CodeAnalyzer(project_path, config["src_dirs"])
        opportunities = analyzer.analyze_project()

        all_opportunities.extend(opportunities)
        all_structures.extend(analyzer.file_structures)

    report = RefactoringReport(all_opportunities, all_structures)

    if args.file:
        report.print_file_details(args.file)
    else:
        report.print_summary()
        report.print_top_opportunities(args.top)

    if args.json:
        report.export_json(args.json)

    if args.ai_prompt:
        report.export_ai_prompt(args.ai_prompt, args.top)


if __name__ == "__main__":
    main()
