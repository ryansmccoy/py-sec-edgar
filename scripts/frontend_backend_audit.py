#!/usr/bin/env python3
"""Frontend-Backend-API-Database Disconnect Audit

Analyzes alignment between:
- Frontend pages/components and API endpoints
- API endpoints and backend services
- Backend services and database models
- All layers and test coverage
"""

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class APIEndpoint:
    """API endpoint definition"""

    method: str
    path: str
    file: str
    function: str
    has_test: bool = False
    used_by_frontend: bool = False


@dataclass
class FrontendPage:
    """Frontend page/component"""

    name: str
    file: str
    api_calls: list[str] = field(default_factory=list)
    missing_endpoints: list[str] = field(default_factory=list)


@dataclass
class BackendService:
    """Backend service/repository"""

    name: str
    file: str
    methods: list[str] = field(default_factory=list)
    used_by_api: bool = False
    has_test: bool = False


@dataclass
class DatabaseModel:
    """Database/Pydantic model"""

    name: str
    file: str
    fields: list[str] = field(default_factory=list)
    used_by_service: bool = False
    has_migration: bool = False


@dataclass
class DisconnectReport:
    """Full disconnect analysis"""

    project: str

    # API Analysis
    api_endpoints: list[APIEndpoint] = field(default_factory=list)
    untested_endpoints: list[str] = field(default_factory=list)
    unused_endpoints: list[str] = field(default_factory=list)

    # Frontend Analysis
    frontend_pages: list[FrontendPage] = field(default_factory=list)
    missing_api_endpoints: list[str] = field(default_factory=list)
    orphaned_frontend: list[str] = field(default_factory=list)

    # Backend Analysis
    backend_services: list[BackendService] = field(default_factory=list)
    unused_services: list[str] = field(default_factory=list)
    untested_services: list[str] = field(default_factory=list)

    # Database Analysis
    db_models: list[DatabaseModel] = field(default_factory=list)
    unused_models: list[str] = field(default_factory=list)
    missing_migrations: list[str] = field(default_factory=list)

    # Cross-layer gaps
    frontend_backend_gaps: list[str] = field(default_factory=list)
    backend_db_gaps: list[str] = field(default_factory=list)
    api_service_gaps: list[str] = field(default_factory=list)

    total_disconnects: int = 0


class FrontendBackendAuditor:
    """Audit frontend-backend-API-database alignment"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.project_name = project_path.name

    def audit(self) -> DisconnectReport:
        """Run full disconnect audit"""
        report = DisconnectReport(project=self.project_name)

        print(f"\n{'=' * 80}")
        print(f"AUDITING: {self.project_name}")
        print(f"{'=' * 80}\n")

        # 1. Scan API endpoints
        print("[1/6] Scanning API endpoints...")
        report.api_endpoints = self._scan_api_endpoints()

        # 2. Scan frontend
        print("[2/6] Scanning frontend pages/components...")
        report.frontend_pages = self._scan_frontend()

        # 3. Scan backend services
        print("[3/6] Scanning backend services...")
        report.backend_services = self._scan_backend_services()

        # 4. Scan database models
        print("[4/6] Scanning database models...")
        report.db_models = self._scan_db_models()

        # 5. Scan tests
        print("[5/6] Checking test coverage...")
        self._check_test_coverage(report)

        # 6. Analyze disconnects
        print("[6/6] Analyzing disconnects...")
        self._analyze_disconnects(report)

        return report

    def _scan_api_endpoints(self) -> list[APIEndpoint]:
        """Scan all API endpoints"""
        endpoints = []

        # Check common API paths
        api_paths = [
            self.project_path / "src" / self.project_name.replace("-", "_") / "api",
            self.project_path / self.project_name.replace("-", "_") / "api",
            self.project_path / "app" / "api",
            self.project_path / "src" / "api",
        ]

        for api_path in api_paths:
            if not api_path.exists():
                continue

            for py_file in api_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")

                    # FastAPI/Flask route patterns
                    patterns = [
                        r'@(?:router|app|bp)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                        r'@(?:router|app|bp)\.route\s*\(\s*["\']([^"\']+)["\'],?\s*methods\s*=\s*\[([^\]]+)\]',
                    ]

                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            if len(match.groups()) == 2:
                                method, path = match.groups()
                            else:
                                path, methods = match.groups()
                                method = methods.split(",")[0].strip(" \"'")

                            # Find function name
                            func_match = re.search(
                                rf"{re.escape(match.group(0))}\s*\n\s*(?:async\s+)?def\s+(\w+)",
                                content,
                            )
                            func_name = func_match.group(1) if func_match else "unknown"

                            endpoints.append(
                                APIEndpoint(
                                    method=method.upper(),
                                    path=path,
                                    file=str(py_file.relative_to(self.project_path)),
                                    function=func_name,
                                )
                            )
                except Exception as e:
                    pass

        return endpoints

    def _scan_frontend(self) -> list[FrontendPage]:
        """Scan frontend pages and components"""
        pages = []

        frontend_paths = [
            self.project_path / "frontend" / "src",
            self.project_path / "src" / "frontend",
        ]

        for frontend_path in frontend_paths:
            if not frontend_path.exists():
                continue

            # Scan pages
            pages_dir = frontend_path / "pages"
            if pages_dir.exists():
                for tsx_file in pages_dir.glob("*.tsx"):
                    if tsx_file.name.startswith("_"):
                        continue

                    try:
                        content = tsx_file.read_text(encoding="utf-8")
                        api_calls = self._extract_api_calls(content)

                        pages.append(
                            FrontendPage(
                                name=tsx_file.stem,
                                file=str(tsx_file.relative_to(self.project_path)),
                                api_calls=api_calls,
                            )
                        )
                    except Exception:
                        pass

        return pages

    def _extract_api_calls(self, content: str) -> list[str]:
        """Extract API calls from frontend code"""
        api_calls = []

        # Patterns for API calls
        patterns = [
            r'fetch\s*\(\s*[`"\']([^`"\']+)[`"\']',  # fetch('/api/...')
            r'axios\.\w+\s*\(\s*[`"\']([^`"\']+)[`"\']',  # axios.get('/api/...')
            r'api\.\w+\s*\(\s*[`"\']([^`"\']+)[`"\']',  # api.get('/api/...')
            r'[`"\']/api/v\d+/([^`"\']+)[`"\']',  # Direct API paths
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            api_calls.extend(matches)

        # Clean up
        api_calls = [call.replace("${", "{").split("?")[0] for call in api_calls]
        return list(set(api_calls))

    def _scan_backend_services(self) -> list[BackendService]:
        """Scan backend services and repositories"""
        services = []

        backend_paths = [
            self.project_path / "src" / self.project_name.replace("-", "_"),
            self.project_path / self.project_name.replace("-", "_"),
            self.project_path / "app",
        ]

        for backend_path in backend_paths:
            if not backend_path.exists():
                continue

            # Look for service/repository files
            for py_file in backend_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                name = py_file.stem
                if not any(
                    x in name.lower()
                    for x in ["service", "repository", "repo", "handler", "manager"]
                ):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            methods = [
                                m.name
                                for m in node.body
                                if isinstance(m, ast.FunctionDef)
                            ]

                            services.append(
                                BackendService(
                                    name=node.name,
                                    file=str(py_file.relative_to(self.project_path)),
                                    methods=methods,
                                )
                            )
                except Exception:
                    pass

        return services

    def _scan_db_models(self) -> list[DatabaseModel]:
        """Scan database/Pydantic models"""
        models = []

        model_paths = [
            self.project_path / "src" / self.project_name.replace("-", "_") / "models",
            self.project_path / self.project_name.replace("-", "_") / "models",
            self.project_path / "app" / "models",
        ]

        for model_path in model_paths:
            if not model_path.exists():
                continue

            for py_file in model_path.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check if it's a model (SQLAlchemy/Pydantic)
                            if any(
                                base.id in ["BaseModel", "Base", "Model"]
                                for base in node.bases
                                if isinstance(base, ast.Name)
                            ):
                                fields = []
                                for item in node.body:
                                    if isinstance(item, ast.AnnAssign) and isinstance(
                                        item.target, ast.Name
                                    ):
                                        fields.append(item.target.id)

                                models.append(
                                    DatabaseModel(
                                        name=node.name,
                                        file=str(
                                            py_file.relative_to(self.project_path)
                                        ),
                                        fields=fields,
                                    )
                                )
                except Exception:
                    pass

        return models

    def _check_test_coverage(self, report: DisconnectReport):
        """Check test coverage for all layers"""
        tests_path = self.project_path / "tests"
        if not tests_path.exists():
            return

        # Get all test files
        test_files = []
        for test_file in tests_path.rglob("test_*.py"):
            try:
                test_files.append(test_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        all_tests = "\n".join(test_files)

        # Check API endpoint coverage
        for endpoint in report.api_endpoints:
            # Look for test with endpoint path or function name
            if endpoint.path in all_tests or endpoint.function in all_tests:
                endpoint.has_test = True

        # Check service coverage
        for service in report.backend_services:
            if service.name in all_tests:
                service.has_test = True

    def _analyze_disconnects(self, report: DisconnectReport):
        """Analyze all disconnects between layers"""

        # 1. Frontend -> API disconnects
        all_api_paths = {f"{ep.method} {ep.path}" for ep in report.api_endpoints}

        for page in report.frontend_pages:
            for api_call in page.api_calls:
                # Try to match with existing endpoints
                matched = False
                for ep in report.api_endpoints:
                    if ep.path in api_call or api_call in ep.path:
                        ep.used_by_frontend = True
                        matched = True
                        break

                if not matched and api_call:
                    page.missing_endpoints.append(api_call)
                    report.missing_api_endpoints.append(
                        f"{page.name} calls missing: {api_call}"
                    )

        # 2. API -> Backend disconnects
        for endpoint in report.api_endpoints:
            # Check if endpoint uses any service
            try:
                ep_file = self.project_path / endpoint.file
                if ep_file.exists():
                    content = ep_file.read_text(encoding="utf-8")
                    for service in report.backend_services:
                        if service.name in content:
                            service.used_by_api = True
            except Exception:
                pass

        # 3. Backend -> Database disconnects
        for service in report.backend_services:
            try:
                svc_file = self.project_path / service.file
                if svc_file.exists():
                    content = svc_file.read_text(encoding="utf-8")
                    for model in report.db_models:
                        if model.name in content:
                            model.used_by_service = True
            except Exception:
                pass

        # Collect disconnects
        report.untested_endpoints = [
            f"{ep.method} {ep.path}" for ep in report.api_endpoints if not ep.has_test
        ]
        report.unused_endpoints = [
            f"{ep.method} {ep.path}"
            for ep in report.api_endpoints
            if not ep.used_by_frontend
        ]
        report.unused_services = [
            svc.name for svc in report.backend_services if not svc.used_by_api
        ]
        report.untested_services = [
            svc.name for svc in report.backend_services if not svc.has_test
        ]
        report.unused_models = [
            m.name for m in report.db_models if not m.used_by_service
        ]

        # Calculate total
        report.total_disconnects = (
            len(report.missing_api_endpoints)
            + len(report.untested_endpoints)
            + len(report.unused_endpoints)
            + len(report.unused_services)
            + len(report.untested_services)
            + len(report.unused_models)
        )


def print_report(report: DisconnectReport):
    """Print detailed disconnect report"""
    print(f"\n{'=' * 80}")
    print(f"DISCONNECT REPORT: {report.project}")
    print(f"{'=' * 80}\n")

    # Summary
    print(f"Total Disconnects: {report.total_disconnects}")
    print(
        f"  - API Endpoints: {len(report.api_endpoints)} ({len(report.untested_endpoints)} untested, {len(report.unused_endpoints)} unused)"
    )
    print(
        f"  - Frontend Pages: {len(report.frontend_pages)} ({len(report.missing_api_endpoints)} missing APIs)"
    )
    print(
        f"  - Backend Services: {len(report.backend_services)} ({len(report.unused_services)} unused, {len(report.untested_services)} untested)"
    )
    print(
        f"  - Database Models: {len(report.db_models)} ({len(report.unused_models)} unused)"
    )

    # Details
    if report.missing_api_endpoints:
        print(f"\n{'-' * 80}")
        print("MISSING API ENDPOINTS (Frontend calls but doesn't exist)")
        print(f"{'-' * 80}")
        for missing in report.missing_api_endpoints[:10]:
            print(f"  [!] {missing}")
        if len(report.missing_api_endpoints) > 10:
            print(f"  ... and {len(report.missing_api_endpoints) - 10} more")

    if report.untested_endpoints:
        print(f"\n{'-' * 80}")
        print("UNTESTED API ENDPOINTS")
        print(f"{'-' * 80}")
        for endpoint in report.untested_endpoints[:15]:
            print(f"  [ ] {endpoint}")
        if len(report.untested_endpoints) > 15:
            print(f"  ... and {len(report.untested_endpoints) - 15} more")

    if report.unused_endpoints:
        print(f"\n{'-' * 80}")
        print("UNUSED API ENDPOINTS (Not called by frontend)")
        print(f"{'-' * 80}")
        for endpoint in report.unused_endpoints[:10]:
            print(f"  [?] {endpoint}")
        if len(report.unused_endpoints) > 10:
            print(f"  ... and {len(report.unused_endpoints) - 10} more")

    if report.unused_services:
        print(f"\n{'-' * 80}")
        print("UNUSED BACKEND SERVICES (Not used by API)")
        print(f"{'-' * 80}")
        for service in report.unused_services[:10]:
            print(f"  [?] {service}")
        if len(report.unused_services) > 10:
            print(f"  ... and {len(report.unused_services) - 10} more")

    if report.untested_services:
        print(f"\n{'-' * 80}")
        print("UNTESTED BACKEND SERVICES")
        print(f"{'-' * 80}")
        for service in report.untested_services[:10]:
            print(f"  [ ] {service}")
        if len(report.untested_services) > 10:
            print(f"  ... and {len(report.untested_services) - 10} more")

    if report.unused_models:
        print(f"\n{'-' * 80}")
        print("UNUSED DATABASE MODELS (Not used by services)")
        print(f"{'-' * 80}")
        for model in report.unused_models[:10]:
            print(f"  [?] {model}")
        if len(report.unused_models) > 10:
            print(f"  ... and {len(report.unused_models) - 10} more")

    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Frontend-Backend-API-Database Disconnect Audit"
    )
    parser.add_argument(
        "--project", help="Specific project to audit (default: all fullstack projects)"
    )
    parser.add_argument("--json", help="Export to JSON file")
    args = parser.parse_args()

    workspace_root = Path(__file__).parent.parent

    # Projects with frontend
    fullstack_projects = ["capture-spine", "genai-spine"]

    if args.project:
        projects = [args.project]
    else:
        projects = fullstack_projects

    reports = {}
    for project in projects:
        project_path = workspace_root / project
        if not project_path.exists():
            print(f"[SKIP] {project} - not found")
            continue

        auditor = FrontendBackendAuditor(project_path)
        report = auditor.audit()
        reports[project] = report
        print_report(report)

    # Summary across all projects
    if len(reports) > 1:
        print(f"\n{'=' * 80}")
        print("SUMMARY ACROSS ALL PROJECTS")
        print(f"{'=' * 80}\n")

        total_disconnects = sum(r.total_disconnects for r in reports.values())
        print(f"Total Disconnects: {total_disconnects}")

        for name, report in reports.items():
            print(f"  {name}: {report.total_disconnects}")

    if args.json:

        def serialize(obj):
            if hasattr(obj, "__dict__"):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            return obj

        data = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "projects": {name: serialize(report) for name, report in reports.items()},
        }

        Path(args.json).write_text(json.dumps(data, indent=2))
        print(f"\n[EXPORT] Saved to {args.json}")


if __name__ == "__main__":
    main()
