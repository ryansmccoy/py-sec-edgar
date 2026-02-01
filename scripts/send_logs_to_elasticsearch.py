#!/usr/bin/env python3
"""
Send application logs to Elasticsearch for searchable log indexing.

This script reads log files from the workspace and sends them to Elasticsearch
for full-text search, analysis, and visualization in Kibana/Grafana.

Usage:
    python scripts/send_logs_to_elasticsearch.py --index spine-logs --days 7
    python scripts/send_logs_to_elasticsearch.py --index capture-spine --pattern "capture-spine/logs/*.log"
"""

import argparse
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    from elasticsearch import Elasticsearch, helpers
except ImportError:
    print("ERROR: elasticsearch package not found")
    print("Install with: pip install elasticsearch")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Workspace root
WORKSPACE = Path(__file__).parent.parent

# Default log patterns
DEFAULT_LOG_PATTERNS = [
    "logs/**/*.log",
    "capture-spine/logs/**/*.log",
    "entityspine/*.log",
]


class ElasticsearchLogShipper:
    """Ships logs from files to Elasticsearch."""

    def __init__(
        self, es_host: str = "http://localhost:9200", index_name: str = "spine-logs"
    ):
        """
        Initialize Elasticsearch connection.

        Args:
            es_host: Elasticsearch host URL
            index_name: Name of the index to store logs
        """
        # For ES 8.x with security disabled
        self.es = Elasticsearch([es_host], verify_certs=False, ssl_show_warn=False)
        self.index_name = index_name

        # Test connection
        try:
            info = self.es.info()
            logger.info(
                f"Connected to Elasticsearch {info['version']['number']} at {es_host}"
            )
            logger.info(f"Cluster: {info['cluster_name']}")
            logger.info(f"Target index: {index_name}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Elasticsearch at {es_host}: {e}")

    def parse_log_line(self, line: str, source_file: Path) -> Optional[Dict]:
        """
        Parse a log line into structured fields.

        Supports common Python logging formats:
        - 2025-01-15 10:30:45,123 - INFO - module - Message
        - [2025-01-15 10:30:45] ERROR: Message
        - INFO:module:Message

        Args:
            line: Raw log line
            source_file: Path to source log file

        Returns:
            Dictionary with parsed fields or None if unparseable
        """
        line = line.strip()
        if not line:
            return None

        # Pattern 1: Full format with timestamp, level, module, message
        # 2025-01-15 10:30:45,123 - INFO - module - Message
        pattern1 = r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+-\s+(\w+)\s+-\s+(\S+)\s+-\s+(.+)$"
        match = re.match(pattern1, line)
        if match:
            timestamp_str, level, module, message = match.groups()
            timestamp = self._parse_timestamp(timestamp_str)
            return {
                "@timestamp": timestamp,
                "level": level.upper(),
                "logger": module,
                "message": message,
                "source_file": str(source_file),
                "service": self._extract_service(source_file),
            }

        # Pattern 2: Bracket format [2025-01-15 10:30:45] ERROR: Message
        pattern2 = r"^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+(\w+):\s+(.+)$"
        match = re.match(pattern2, line)
        if match:
            timestamp_str, level, message = match.groups()
            timestamp = self._parse_timestamp(timestamp_str)
            return {
                "@timestamp": timestamp,
                "level": level.upper(),
                "message": message,
                "source_file": str(source_file),
                "service": self._extract_service(source_file),
            }

        # Pattern 3: Python logging format INFO:module:Message
        pattern3 = r"^(\w+):(\S+):(.+)$"
        match = re.match(pattern3, line)
        if match:
            level, module, message = match.groups()
            if level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                return {
                    "@timestamp": datetime.utcnow().isoformat(),
                    "level": level.upper(),
                    "logger": module,
                    "message": message,
                    "source_file": str(source_file),
                    "service": self._extract_service(source_file),
                }

        # Fallback: Just store the raw line with file metadata
        return {
            "@timestamp": datetime.utcnow().isoformat(),
            "level": "UNKNOWN",
            "message": line,
            "source_file": str(source_file),
            "service": self._extract_service(source_file),
        }

    def _parse_timestamp(self, timestamp_str: str) -> str:
        """Parse timestamp string to ISO format."""
        # Try different formats
        formats = [
            "%Y-%m-%d %H:%M:%S,%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        # Fallback to current time if unparseable
        logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return datetime.utcnow().isoformat()

    def _extract_service(self, file_path: Path) -> str:
        """Extract service name from file path."""
        parts = file_path.parts

        # Look for service indicators in path
        for part in parts:
            if "spine" in part.lower():
                return part

        # Default to parent directory name
        return file_path.parent.name

    def ship_log_file(self, log_file: Path, since_days: Optional[int] = None) -> int:
        """
        Ship a log file to Elasticsearch.

        Args:
            log_file: Path to log file
            since_days: Only ship logs from last N days (None = all)

        Returns:
            Number of log entries shipped
        """
        if not log_file.exists():
            logger.warning(f"Log file not found: {log_file}")
            return 0

        # Calculate cutoff time if filtering by date
        cutoff_time = None
        if since_days is not None:
            cutoff_time = datetime.utcnow() - timedelta(days=since_days)

        logger.info(f"Processing {log_file} ({log_file.stat().st_size / 1024:.1f} KB)")

        # Read and parse log lines
        docs = []
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    doc = self.parse_log_line(line, log_file)
                    if doc:
                        # Filter by date if requested
                        if cutoff_time:
                            log_time = datetime.fromisoformat(
                                doc["@timestamp"].replace("Z", "+00:00")
                            )
                            if log_time < cutoff_time:
                                continue

                        docs.append(doc)

                        # Bulk index every 1000 documents
                        if len(docs) >= 1000:
                            self._bulk_index(docs)
                            docs = []

                except Exception as e:
                    logger.error(f"Error parsing line {line_num} in {log_file}: {e}")

        # Index remaining documents
        if docs:
            self._bulk_index(docs)

        return len(docs)

    def _bulk_index(self, docs: List[Dict]):
        """Bulk index documents to Elasticsearch."""
        actions = [{"_index": self.index_name, "_source": doc} for doc in docs]

        try:
            success, failed = helpers.bulk(self.es, actions, raise_on_error=False)
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents")
            logger.info(f"Indexed {success} documents")
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")

    def ship_logs(
        self, patterns: List[str], since_days: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Ship logs matching patterns to Elasticsearch.

        Args:
            patterns: List of glob patterns to match log files
            since_days: Only ship logs from last N days

        Returns:
            Dictionary mapping file paths to document counts
        """
        results = {}

        for pattern in patterns:
            for log_file in WORKSPACE.glob(pattern):
                if log_file.is_file():
                    count = self.ship_log_file(log_file, since_days)
                    results[str(log_file)] = count

        return results

    def create_index_template(self):
        """Create index template with mappings for log fields."""
        template = {
            "index_patterns": [f"{self.index_name}-*", self.index_name],
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "level": {"type": "keyword"},
                    "logger": {"type": "keyword"},
                    "message": {"type": "text"},
                    "source_file": {"type": "keyword"},
                    "service": {"type": "keyword"},
                }
            },
        }

        try:
            self.es.indices.put_index_template(
                name=f"{self.index_name}-template", body=template
            )
            logger.info(f"Created index template: {self.index_name}-template")
        except Exception as e:
            logger.warning(f"Could not create index template: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ship application logs to Elasticsearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ship all logs from last 7 days
  %(prog)s --days 7

  # Ship capture-spine logs only
  %(prog)s --pattern "capture-spine/logs/**/*.log"

  # Ship to custom Elasticsearch instance
  %(prog)s --host http://es.example.com:9200 --index my-logs

  # Ship all logs (no date filter)
  %(prog)s --all
        """,
    )

    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Elasticsearch host URL (default: http://localhost:9200)",
    )

    parser.add_argument(
        "--index", default="spine-logs", help="Index name (default: spine-logs)"
    )

    parser.add_argument(
        "--pattern",
        action="append",
        help="Log file pattern (can specify multiple times)",
    )

    parser.add_argument("--days", type=int, help="Only ship logs from last N days")

    parser.add_argument(
        "--all", action="store_true", help="Ship all logs regardless of date"
    )

    parser.add_argument(
        "--create-template",
        action="store_true",
        help="Create index template before shipping",
    )

    args = parser.parse_args()

    # Determine patterns
    patterns = args.pattern if args.pattern else DEFAULT_LOG_PATTERNS

    # Determine date filter
    since_days = None if args.all else (args.days or 7)

    # Initialize shipper
    try:
        shipper = ElasticsearchLogShipper(es_host=args.host, index_name=args.index)
    except ConnectionError as e:
        logger.error(str(e))
        logger.error(
            "Make sure Elasticsearch is running (docker compose -f capture-spine/docker-compose.search.yml up -d)"
        )
        return 1

    # Create template if requested
    if args.create_template:
        shipper.create_index_template()

    # Ship logs
    logger.info(f"Shipping logs from patterns: {patterns}")
    if since_days:
        logger.info(f"Filtering to logs from last {since_days} days")

    results = shipper.ship_logs(patterns, since_days)

    # Summary
    total_docs = sum(results.values())
    total_files = len(results)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"SUMMARY: Shipped {total_docs:,} log entries from {total_files} files")
    logger.info("=" * 60)

    for file_path, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            logger.info(f"  {count:6,} entries  {file_path}")

    logger.info("")
    logger.info(f"View in Kibana: http://localhost:5601/app/discover")
    logger.info(
        f"View in Grafana: http://localhost:3100/explore (add Elasticsearch data source)"
    )

    return 0


if __name__ == "__main__":
    exit(main())
