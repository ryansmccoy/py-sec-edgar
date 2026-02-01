"""
Log Management Service for Spine Ecosystem

Features:
- Rotate and archive old logs
- Scan for errors/exceptions
- Generate daily digest
- Optional: Send alerts

Usage:
    python scripts/log_manager.py --scan    # Scan for errors
    python scripts/log_manager.py --rotate  # Rotate old logs
    python scripts/log_manager.py --digest  # Generate digest
    python scripts/log_manager.py --all     # Do everything
    python scripts/log_manager.py --watch   # Watch mode (run every hour)
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import shutil
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ============================================================================
# Configuration
# ============================================================================

# Root of the workspace (adjust if running from different directory)
WORKSPACE_ROOT = Path(__file__).parent.parent

LOG_DIRECTORIES = [
    WORKSPACE_ROOT / "logs",
    WORKSPACE_ROOT / "capture-spine" / "logs",
    WORKSPACE_ROOT / "entityspine",
]

ARCHIVE_DIR = WORKSPACE_ROOT / "logs" / "archive"
RETENTION_DAYS = 7  # Keep uncompressed logs for 7 days
ARCHIVE_RETENTION_DAYS = 90  # Keep compressed archives for 90 days

# Patterns that indicate errors
ERROR_PATTERNS = [
    r"ERROR",
    r"EXCEPTION",
    r"Traceback \(most recent call last\)",
    r"CRITICAL",
    r"FATAL",
    r"UNHANDLED EXCEPTION",
    r"Failed to",
    r"Connection refused",
    r"Timeout",
    r"ConnectionResetError",
    r"OperationalError",
    r"IntegrityError",
    r"KeyError",
    r"ValueError",
    r"TypeError",
    r"AttributeError",
    r"ImportError",
    r"ModuleNotFoundError",
]

# File patterns to skip
SKIP_PATTERNS = [
    r"\.git",
    r"__pycache__",
    r"\.venv",
    r"node_modules",
]


# ============================================================================
# Log Scanning
# ============================================================================


def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    path_str = str(path)
    return any(re.search(pattern, path_str) for pattern in SKIP_PATTERNS)


def scan_for_errors(
    log_dir: Path, max_errors_per_file: int = 50
) -> dict[str, list[dict]]:
    """
    Scan logs for error patterns.

    Returns a dict of {file_path: [{line, content, pattern}, ...]}
    """
    errors: dict[str, list[dict]] = defaultdict(list)
    pattern = re.compile("|".join(ERROR_PATTERNS), re.IGNORECASE)

    log_files = list(log_dir.glob("**/*.log"))
    print(f"  Scanning {len(log_files)} log files in {log_dir}...")

    for log_file in log_files:
        if should_skip_path(log_file):
            continue

        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    match = pattern.search(line)
                    if match:
                        errors[str(log_file.relative_to(WORKSPACE_ROOT))].append(
                            {
                                "line": line_num,
                                "content": line.strip()[:300],
                                "pattern": match.group(),
                            }
                        )
                        if (
                            len(errors[str(log_file.relative_to(WORKSPACE_ROOT))])
                            >= max_errors_per_file
                        ):
                            break
        except Exception as e:
            print(f"  ⚠️  Error reading {log_file}: {e}")

    return dict(errors)


def get_error_summary(errors: dict[str, list[dict]]) -> dict[str, int]:
    """Get a summary of error types."""
    summary: dict[str, int] = defaultdict(int)
    for file_errors in errors.values():
        for error in file_errors:
            summary[error["pattern"]] += 1
    return dict(sorted(summary.items(), key=lambda x: -x[1]))


# ============================================================================
# Log Rotation
# ============================================================================


def rotate_logs() -> tuple[int, int]:
    """
    Move old logs to archive and compress.

    Returns (files_rotated, bytes_saved)
    """
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    month_dir = ARCHIVE_DIR / datetime.now().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    files_rotated = 0
    bytes_saved = 0

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        for log_file in log_dir.glob("*.log"):
            if should_skip_path(log_file):
                continue

            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff:
                    original_size = log_file.stat().st_size
                    archive_name = f"{log_file.stem}_{mtime.strftime('%Y%m%d')}.log.gz"
                    archive_path = month_dir / archive_name

                    # Handle duplicate names
                    counter = 1
                    while archive_path.exists():
                        archive_name = f"{log_file.stem}_{mtime.strftime('%Y%m%d')}_{counter}.log.gz"
                        archive_path = month_dir / archive_name
                        counter += 1

                    print(
                        f"  📦 Archiving: {log_file.name} → {archive_path.relative_to(WORKSPACE_ROOT)}"
                    )

                    with open(log_file, "rb") as f_in:
                        with gzip.open(archive_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    compressed_size = archive_path.stat().st_size
                    bytes_saved += original_size - compressed_size

                    log_file.unlink()
                    files_rotated += 1

            except Exception as e:
                print(f"  ⚠️  Error rotating {log_file}: {e}")

    return files_rotated, bytes_saved


def cleanup_old_archives() -> int:
    """Delete archives older than retention period."""
    cutoff = datetime.now() - timedelta(days=ARCHIVE_RETENTION_DAYS)
    files_deleted = 0

    if not ARCHIVE_DIR.exists():
        return 0

    for archive_file in ARCHIVE_DIR.glob("**/*.gz"):
        try:
            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
            if mtime < cutoff:
                print(
                    f"  🗑️  Deleting old archive: {archive_file.relative_to(WORKSPACE_ROOT)}"
                )
                archive_file.unlink()
                files_deleted += 1
        except Exception as e:
            print(f"  ⚠️  Error deleting {archive_file}: {e}")

    # Clean up empty directories
    for dir_path in sorted(ARCHIVE_DIR.glob("*"), reverse=True):
        if dir_path.is_dir() and not list(dir_path.iterdir()):
            dir_path.rmdir()

    return files_deleted


# ============================================================================
# Digest Generation
# ============================================================================


def generate_digest() -> str:
    """Generate a markdown summary of recent errors."""
    lines = []
    lines.append(f"# Log Digest - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"\n> Generated by `log_manager.py`\n")

    total_errors = 0
    all_errors: dict[str, list[dict]] = {}

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        errors = scan_for_errors(log_dir)
        all_errors.update(errors)
        dir_errors = sum(len(v) for v in errors.values())
        total_errors += dir_errors

    # Summary
    lines.append(f"\n## Summary\n")
    lines.append(f"- **Total Errors Found**: {total_errors}")
    lines.append(f"- **Files with Errors**: {len(all_errors)}")
    lines.append(f"- **Scan Time**: {datetime.now().isoformat()}\n")

    if all_errors:
        # Error type breakdown
        summary = get_error_summary(all_errors)
        lines.append(f"\n## Error Types\n")
        lines.append("| Pattern | Count |")
        lines.append("|---------|-------|")
        for pattern, count in list(summary.items())[:15]:
            lines.append(f"| `{pattern}` | {count} |")

        # Details by file
        lines.append(f"\n## Details by File\n")
        for file_path, file_errors in sorted(
            all_errors.items(), key=lambda x: -len(x[1])
        ):
            lines.append(f"\n### {file_path} ({len(file_errors)} errors)\n")
            lines.append("```")
            for err in file_errors[:10]:  # First 10 errors
                content = err["content"][:150].replace("\n", " ")
                lines.append(f"Line {err['line']}: {content}")
            if len(file_errors) > 10:
                lines.append(f"... and {len(file_errors) - 10} more")
            lines.append("```")
    else:
        lines.append("\n✅ **No errors found!**\n")

    return "\n".join(lines)


def generate_json_report() -> dict[str, Any]:
    """Generate a JSON report for programmatic access."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "directories_scanned": [],
        "total_errors": 0,
        "files_with_errors": 0,
        "error_summary": {},
        "errors_by_file": {},
    }

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        report["directories_scanned"].append(str(log_dir.relative_to(WORKSPACE_ROOT)))
        errors = scan_for_errors(log_dir)
        report["errors_by_file"].update(errors)

    report["total_errors"] = sum(len(v) for v in report["errors_by_file"].values())
    report["files_with_errors"] = len(report["errors_by_file"])
    report["error_summary"] = get_error_summary(report["errors_by_file"])

    return report


# ============================================================================
# Statistics
# ============================================================================


def get_log_stats() -> dict[str, Any]:
    """Get statistics about log files."""
    stats = {
        "total_files": 0,
        "total_size_mb": 0,
        "oldest_log": None,
        "newest_log": None,
        "by_directory": {},
    }

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        dir_stats = {"files": 0, "size_mb": 0}
        dir_name = str(log_dir.relative_to(WORKSPACE_ROOT))

        for log_file in log_dir.glob("**/*.log"):
            if should_skip_path(log_file):
                continue

            try:
                file_stat = log_file.stat()
                dir_stats["files"] += 1
                dir_stats["size_mb"] += file_stat.st_size / (1024 * 1024)

                mtime = datetime.fromtimestamp(file_stat.st_mtime)
                if stats["oldest_log"] is None or mtime < stats["oldest_log"]:
                    stats["oldest_log"] = mtime
                if stats["newest_log"] is None or mtime > stats["newest_log"]:
                    stats["newest_log"] = mtime

            except Exception:
                pass

        stats["by_directory"][dir_name] = dir_stats
        stats["total_files"] += dir_stats["files"]
        stats["total_size_mb"] += dir_stats["size_mb"]

    # Format dates
    if stats["oldest_log"]:
        stats["oldest_log"] = stats["oldest_log"].isoformat()
    if stats["newest_log"]:
        stats["newest_log"] = stats["newest_log"].isoformat()

    return stats


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Log Management Service for Spine Ecosystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/log_manager.py --scan           # Scan for errors
  python scripts/log_manager.py --rotate         # Rotate old logs
  python scripts/log_manager.py --digest         # Generate digest
  python scripts/log_manager.py --stats          # Show log statistics
  python scripts/log_manager.py --all            # Do everything
  python scripts/log_manager.py --watch          # Watch mode (hourly)
  python scripts/log_manager.py --json           # Output as JSON
        """,
    )
    parser.add_argument("--scan", action="store_true", help="Scan for errors")
    parser.add_argument("--rotate", action="store_true", help="Rotate old logs")
    parser.add_argument("--digest", action="store_true", help="Generate digest")
    parser.add_argument("--stats", action="store_true", help="Show log statistics")
    parser.add_argument("--all", action="store_true", help="Do everything")
    parser.add_argument(
        "--watch", action="store_true", help="Watch mode (run every hour)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", type=str, help="Output file path")

    args = parser.parse_args()

    # Default to showing stats if no args
    if not any([args.scan, args.rotate, args.digest, args.stats, args.all, args.watch]):
        args.stats = True

    def run_once():
        results = {}

        if args.stats or args.all:
            print("\n📊 Log Statistics")
            print("=" * 50)
            stats = get_log_stats()
            results["stats"] = stats

            if args.json:
                print(json.dumps(stats, indent=2))
            else:
                print(f"  Total files: {stats['total_files']}")
                print(f"  Total size: {stats['total_size_mb']:.2f} MB")
                print(f"  Oldest log: {stats['oldest_log']}")
                print(f"  Newest log: {stats['newest_log']}")
                print("\n  By directory:")
                for dir_name, dir_stats in stats["by_directory"].items():
                    print(
                        f"    {dir_name}: {dir_stats['files']} files, {dir_stats['size_mb']:.2f} MB"
                    )

        if args.scan or args.all:
            print("\n🔍 Scanning for Errors")
            print("=" * 50)

            if args.json:
                report = generate_json_report()
                results["scan"] = report
                print(json.dumps(report, indent=2))
            else:
                for log_dir in LOG_DIRECTORIES:
                    if log_dir.exists():
                        errors = scan_for_errors(log_dir)
                        error_count = sum(len(v) for v in errors.values())
                        print(
                            f"\n  {log_dir.relative_to(WORKSPACE_ROOT)}: {error_count} errors in {len(errors)} files"
                        )
                        if errors:
                            summary = get_error_summary(errors)
                            print("  Top error types:")
                            for pattern, count in list(summary.items())[:5]:
                                print(f"    - {pattern}: {count}")

        if args.rotate or args.all:
            print("\n📦 Rotating Logs")
            print("=" * 50)
            files_rotated, bytes_saved = rotate_logs()
            files_deleted = cleanup_old_archives()
            results["rotate"] = {
                "files_rotated": files_rotated,
                "bytes_saved": bytes_saved,
                "archives_deleted": files_deleted,
            }
            print(f"  Files rotated: {files_rotated}")
            print(f"  Space saved: {bytes_saved / (1024 * 1024):.2f} MB")
            print(f"  Old archives deleted: {files_deleted}")

        if args.digest or args.all:
            print("\n📝 Generating Digest")
            print("=" * 50)
            digest = generate_digest()
            results["digest"] = digest

            # Save digest
            output_path = (
                Path(args.output)
                if args.output
                else WORKSPACE_ROOT / "logs" / "digest.md"
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(digest, encoding="utf-8")
            print(f"  Saved to: {output_path}")

            if not args.json:
                print("\n" + "=" * 50)
                print(digest[:1000])
                if len(digest) > 1000:
                    print(f"\n... (truncated, see {output_path})")

        return results

    if args.watch:
        print("👀 Watch mode enabled. Press Ctrl+C to stop.")
        print("   Running every hour...")
        while True:
            try:
                run_once()
                print(
                    f"\n💤 Next run at {(datetime.now() + timedelta(hours=1)).strftime('%H:%M')}"
                )
                time.sleep(3600)  # 1 hour
            except KeyboardInterrupt:
                print("\n👋 Stopped.")
                break
    else:
        run_once()


if __name__ == "__main__":
    main()
