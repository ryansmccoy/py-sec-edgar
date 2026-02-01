# Centralized Logging & Monitoring Options

## 📍 Current State Analysis

### What You Have Now

| Component | Log Location | Persistence | Rotation |
|-----------|-------------|-------------|----------|
| **py-sec-edgar** | `logs/*.log` | ✅ Files | ❌ None (200+ files from Sept 2025!) |
| **capture-spine API** | `capture-spine/logs/api*.log` | ✅ Files | ⚠️ Daily (but fills up) |
| **Celery Workers** | Docker stdout | ❌ Lost on restart | ❌ None |
| **Frontend** | `capture-spine/logs/frontend*.log` | ✅ Files | ⚠️ Daily |
| **entityspine** | `entityspine/load_*.log` | ✅ Files | ❌ None |

### Problems Identified

1. **Log Sprawl**: 200+ log files in `logs/` directory with no cleanup
2. **No Centralized View**: Errors in different places, hard to correlate
3. **Docker Logs Lost**: Container restarts lose Celery worker logs
4. **No Alerting**: Issues discovered manually (like the `TokenInvalidError` you just saw)
5. **No Search**: Can't easily find when an error first started

---

## 🎯 Solution Options (Simplest to Most Complete)

### Option 1: Simple Log Rotation + Aggregation Script (Zero Dependencies)

**Best for**: Quick fix, single developer, local development

```
┌──────────────────────────────────────────────────────────────────┐
│                    Local Log Management                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │py-sec-edgar │    │capture-spine│    │ entityspine │          │
│  │   /logs/    │    │   /logs/    │    │   /*.log    │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                           │                                      │
│                    ┌──────▼──────┐                               │
│                    │ Log Scanner │ (Python script)               │
│                    │   Service   │ - Rotates old logs            │
│                    └──────┬──────┘ - Zips archives               │
│                           │        - Scans for errors            │
│                           │        - Sends alerts                │
│                    ┌──────▼──────┐                               │
│                    │  /archive/  │                               │
│                    │ YYYY-MM-DD/ │                               │
│                    └─────────────┘                               │
└──────────────────────────────────────────────────────────────────┘
```

**Implementation**: See [log_scanner.py](#option-1-implementation) below

---

### Option 2: Loki + Grafana Stack (Open Source, Modern)

**Best for**: Small team, Docker environment, want dashboards

```
┌──────────────────────────────────────────────────────────────────┐
│                    Grafana + Loki Stack                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Apps with Structured Logging                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │capture-spine│  │ Celery      │  │ feedspine   │              │
│  │    API      │  │ Workers     │  │   CLI       │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │ (JSON logs)                           │
│                   ┌──────▼──────┐                                │
│                   │   Promtail  │ (Log shipper)                  │
│                   └──────┬──────┘                                │
│                          │                                       │
│                   ┌──────▼──────┐                                │
│                   │    Loki     │ (Log database)                 │
│                   │  Port 3100  │ - Stores logs                  │
│                   └──────┬──────┘ - Label indexing               │
│                          │        - LogQL queries                │
│                   ┌──────▼──────┐                                │
│                   │   Grafana   │                                │
│                   │  Port 3000  │ - Dashboards                   │
│                   └─────────────┘ - Alerts                       │
│                                   - Explore logs                 │
└──────────────────────────────────────────────────────────────────┘
```

**Pros**:
- ✅ Purpose-built for logs (unlike Elasticsearch)
- ✅ Much lighter than ELK (~100MB RAM vs 1GB+)
- ✅ Grafana dashboards are beautiful
- ✅ Easy Docker Compose setup
- ✅ Free and open source

**Cons**:
- ❌ Need to add JSON logging to apps
- ❌ Another service to maintain

---

### Option 3: ELK Stack (You Already Have It Partially!)

**Best for**: Enterprise, need full-text search, want Kibana

```
┌──────────────────────────────────────────────────────────────────┐
│                ELK Stack (Elasticsearch + Kibana)                │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Apps                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │capture-spine│  │ Celery      │  │ feedspine   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│  ┌───────────────────────┼───────────────────────┐              │
│  │              Log Shippers                      │              │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │              │
│  │  │ Filebeat │  │ Logstash │  │ Python-      │ │              │
│  │  │ (files)  │  │(transform)│  │ elasticsearch│ │              │
│  │  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │              │
│  └───────┼─────────────┼───────────────┼─────────┘              │
│          └─────────────┼───────────────┘                         │
│                        │                                         │
│                 ┌──────▼──────┐                                  │
│                 │Elasticsearch│ (from docker-compose.search.yml) │
│                 │  Port 9200  │                                  │
│                 └──────┬──────┘                                  │
│                        │                                         │
│                 ┌──────▼──────┐                                  │
│                 │   Kibana    │                                  │
│                 │  Port 5601  │ - Log explorer                   │
│                 └─────────────┘ - Dashboards                     │
│                                 - ML anomaly detection           │
└──────────────────────────────────────────────────────────────────┘
```

**You Already Have**:
- `docker-compose.search.yml` with Elasticsearch + Kibana
- Just need to add Filebeat to ship logs

---

### Option 4: Unified Dashboard (Use Your Existing Infrastructure!)

**Best for**: Leverage what you have, minimal new dependencies

Your `capture-spine` already has:
- System dashboard endpoint (`/api/v1/system/dashboard`)
- Health checks for all services
- Observability module scaffolding (`app/observability/`)

```
┌──────────────────────────────────────────────────────────────────┐
│              Extend Existing Dashboard                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  capture-spine Frontend                                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  System Dashboard                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ Services │ │  Feeds   │ │  Queue   │ │    NEW!      │  │ │
│  │  │  Health  │ │  Status  │ │  Stats   │ │ Error Log    │  │ │
│  │  │  ✅ ❌   │ │  📊      │ │  📈      │ │ Aggregator   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                       ┌──────▼──────┐                           │
│                       │  New API    │                           │
│                       │ /api/v1/    │                           │
│                       │ logs/errors │                           │
│                       └──────┬──────┘                           │
│                              │                                   │
│                       ┌──────▼──────┐                           │
│                       │   Log DB    │ (new table in Postgres)   │
│                       │error_events │                           │
│                       └─────────────┘                           │
└──────────────────────────────────────────────────────────────────┘
```

---

### Option 5: Pre-Built Open Source Solutions

#### 5a. Dozzle (Docker Log Viewer)
**Best for**: Quick Docker log viewing, zero config

```bash
docker run -d --name dozzle \
  --volume=/var/run/docker.sock:/var/run/docker.sock \
  -p 9999:8080 \
  amir20/dozzle:latest
```

- Real-time Docker container logs
- No database, no setup
- Web UI at http://localhost:9999

#### 5b. Seq (Structured Logging Server)
**Best for**: .NET background but works with any JSON logs

```yaml
# docker-compose.monitoring.yml
services:
  seq:
    image: datalust/seq:latest
    ports:
      - "5341:80"  # UI
      - "5342:5341"  # Ingest
    environment:
      ACCEPT_EULA: "Y"
    volumes:
      - seq-data:/data
```

- Free for single user
- Beautiful log viewer
- SQL-like query language

#### 5c. Graylog (Open Source SIEM)
**Best for**: Security-focused, need alerting

```yaml
services:
  graylog:
    image: graylog/graylog:5.2
    ports:
      - "9000:9000"    # Web UI
      - "12201:12201"  # GELF UDP
      - "1514:1514"    # Syslog
```

#### 5d. Uptime Kuma (Status Page + Monitoring)
**Best for**: Service health monitoring, status page

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    ports:
      - "3001:3001"
    volumes:
      - uptime-kuma:/app/data
```

- Beautiful status dashboard
- Ping, HTTP, DNS, Docker checks
- Notifications (Slack, Discord, Email)

---

## 🏆 Recommended Solution: Hybrid Approach

For your ecosystem, I recommend a **layered approach**:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    Spine Ecosystem Monitoring Stack                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  LAYER 1: Log Collection (Choose One)                                      │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Option A: Loki Stack        Option B: Use Existing ES             │   │
│  │  ┌──────────┐                ┌──────────┐                          │   │
│  │  │ Promtail │                │ Filebeat │ → docker-compose.search  │   │
│  │  │    ↓     │                │    ↓     │                          │   │
│  │  │   Loki   │                │   ES     │                          │   │
│  │  │    ↓     │                │    ↓     │                          │   │
│  │  │ Grafana  │                │ Kibana   │                          │   │
│  │  └──────────┘                └──────────┘                          │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  LAYER 2: Service Health (Lightweight)                                     │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  ┌─────────────────┐         ┌─────────────────┐                   │   │
│  │  │   Uptime Kuma   │  ─or─   │ capture-spine   │ (extend existing) │   │
│  │  │  Status Page    │         │    Dashboard    │                   │   │
│  │  └─────────────────┘         └─────────────────┘                   │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
│  LAYER 3: Log Rotation (Simple Script)                                     │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                                                                    │   │
│  │  Windows Task Scheduler / cron                                     │   │
│  │      ↓                                                             │   │
│  │  log_manager.py                                                    │   │
│  │      - Rotate logs > 7 days                                        │   │
│  │      - Compress to archive/YYYY-MM/                                │   │
│  │      - Delete archives > 90 days                                   │   │
│  │      - Scan for ERROR/EXCEPTION patterns                           │   │
│  │      - Send daily digest                                           │   │
│  │                                                                    │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Implementation Files

### Option 1 Implementation: Log Scanner Service

```python
# scripts/log_manager.py
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
"""

import gzip
import re
import shutil
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
LOG_DIRECTORIES = [
    Path("logs"),
    Path("capture-spine/logs"),
    Path("entityspine"),
]

ARCHIVE_DIR = Path("logs/archive")
RETENTION_DAYS = 7  # Keep uncompressed logs for 7 days
ARCHIVE_RETENTION_DAYS = 90  # Keep compressed archives for 90 days

ERROR_PATTERNS = [
    r"ERROR",
    r"EXCEPTION",
    r"Traceback",
    r"CRITICAL",
    r"FATAL",
    r"UNHANDLED",
    r"Failed to",
    r"Connection refused",
    r"Timeout",
]


def scan_for_errors(log_dir: Path) -> dict:
    """Scan logs for error patterns."""
    errors = defaultdict(list)
    pattern = re.compile("|".join(ERROR_PATTERNS), re.IGNORECASE)

    for log_file in log_dir.glob("**/*.log"):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    if pattern.search(line):
                        errors[str(log_file)].append({
                            "line": line_num,
                            "content": line.strip()[:200],
                        })
        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    return dict(errors)


def rotate_logs():
    """Move old logs to archive and compress."""
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    month_dir = ARCHIVE_DIR / datetime.now().strftime("%Y-%m")
    month_dir.mkdir(parents=True, exist_ok=True)

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        for log_file in log_dir.glob("*.log"):
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                archive_path = month_dir / f"{log_file.name}.gz"
                print(f"Archiving: {log_file} → {archive_path}")

                with open(log_file, "rb") as f_in:
                    with gzip.open(archive_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                log_file.unlink()


def cleanup_old_archives():
    """Delete archives older than retention period."""
    cutoff = datetime.now() - timedelta(days=ARCHIVE_RETENTION_DAYS)

    for archive_file in ARCHIVE_DIR.glob("**/*.gz"):
        mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
        if mtime < cutoff:
            print(f"Deleting old archive: {archive_file}")
            archive_file.unlink()


def generate_digest() -> str:
    """Generate a summary of recent errors."""
    digest = []
    digest.append(f"# Log Digest - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    for log_dir in LOG_DIRECTORIES:
        if not log_dir.exists():
            continue

        errors = scan_for_errors(log_dir)
        if errors:
            digest.append(f"\n## {log_dir}\n")
            for file_path, file_errors in errors.items():
                digest.append(f"\n### {file_path} ({len(file_errors)} errors)\n")
                for err in file_errors[:5]:  # First 5 errors
                    digest.append(f"- Line {err['line']}: `{err['content'][:100]}...`\n")

    return "".join(digest)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Log Management Service")
    parser.add_argument("--scan", action="store_true", help="Scan for errors")
    parser.add_argument("--rotate", action="store_true", help="Rotate old logs")
    parser.add_argument("--digest", action="store_true", help="Generate digest")
    parser.add_argument("--all", action="store_true", help="Do everything")

    args = parser.parse_args()

    if args.scan or args.all:
        print("Scanning for errors...")
        for log_dir in LOG_DIRECTORIES:
            if log_dir.exists():
                errors = scan_for_errors(log_dir)
                print(f"\n{log_dir}: {sum(len(v) for v in errors.values())} errors found")

    if args.rotate or args.all:
        print("\nRotating old logs...")
        rotate_logs()
        cleanup_old_archives()

    if args.digest or args.all:
        print("\nGenerating digest...")
        digest = generate_digest()
        print(digest)

        # Save digest
        digest_file = Path("logs/digest.md")
        digest_file.write_text(digest)
        print(f"Saved to {digest_file}")
```

---

### Docker Compose: Loki + Grafana Stack

```yaml
# docker-compose.monitoring.yml
#
# Usage:
#   docker compose -f docker-compose.monitoring.yml up -d
#
# Access:
#   Grafana: http://localhost:3100 (admin/admin)
#   Loki:    http://localhost:3101 (internal)

name: spine-monitoring

networks:
  monitoring-net:
    driver: bridge

volumes:
  loki-data:
  grafana-data:

services:
  # ============================================
  # Loki - Log Aggregation
  # ============================================
  loki:
    image: grafana/loki:2.9.0
    container_name: spine-loki
    ports:
      - "3101:3100"
    volumes:
      - loki-data:/loki
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring-net
    restart: unless-stopped

  # ============================================
  # Promtail - Log Shipper
  # ============================================
  promtail:
    image: grafana/promtail:2.9.0
    container_name: spine-promtail
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - ./logs:/var/log/spine:ro
      - ./capture-spine/logs:/var/log/capture-spine:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring-net
    depends_on:
      - loki
    restart: unless-stopped

  # ============================================
  # Grafana - Dashboards
  # ============================================
  grafana:
    image: grafana/grafana:10.2.0
    container_name: spine-grafana
    ports:
      - "3100:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - monitoring-net
    depends_on:
      - loki
    restart: unless-stopped

  # ============================================
  # Uptime Kuma - Service Health
  # ============================================
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: spine-uptime
    ports:
      - "3001:3001"
    volumes:
      - ./monitoring/uptime-kuma:/app/data
    networks:
      - monitoring-net
    restart: unless-stopped
```

### Loki Configuration

```yaml
# monitoring/loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  retention_period: 720h  # 30 days
```

### Promtail Configuration

```yaml
# monitoring/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Spine main logs
  - job_name: spine-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: spine
          __path__: /var/log/spine/*.log

  # Capture-spine API logs
  - job_name: capture-spine-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: capture-spine
          __path__: /var/log/capture-spine/*.log

  # Docker container logs
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'stream'
```

---

### Add Filebeat to Existing Elasticsearch

```yaml
# Add to docker-compose.search.yml

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.12.0
    container_name: spine-filebeat
    user: root
    volumes:
      - ./monitoring/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - ./logs:/var/log/spine:ro
      - ./capture-spine/logs:/var/log/capture-spine:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - search-net
    depends_on:
      elasticsearch:
        condition: service_healthy
```

```yaml
# monitoring/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/spine/*.log
      - /var/log/capture-spine/*.log
    multiline:
      pattern: '^\d{4}-\d{2}-\d{2}|^INFO|^ERROR|^WARNING'
      negate: true
      match: after

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "spine-logs-%{+yyyy.MM.dd}"

setup.template.name: "spine-logs"
setup.template.pattern: "spine-logs-*"

processors:
  - add_docker_metadata: ~
```

---

## 📊 Quick Comparison Table

| Solution | Setup Time | RAM Usage | Search | Dashboards | Alerts | Cost |
|----------|------------|-----------|--------|------------|--------|------|
| **Log Scanner (Python)** | 5 min | 0 | ❌ | ❌ | Email | Free |
| **Dozzle** | 1 min | 50MB | ❌ | Basic | ❌ | Free |
| **Loki + Grafana** | 30 min | 200MB | LogQL | ✅ Beautiful | ✅ | Free |
| **ELK Stack** | 1 hr | 2GB+ | Full-text | ✅ Kibana | ✅ | Free |
| **Uptime Kuma** | 5 min | 100MB | ❌ | Status | ✅ | Free |
| **Seq** | 10 min | 500MB | SQL-like | ✅ | ✅ | Free* |
| **Graylog** | 1 hr | 1GB+ | Full-text | ✅ | ✅ | Free |

---

## 🚀 Quick Start Recommendation

### For Immediate Relief (Today):

```powershell
# 1. Install Dozzle for instant Docker log viewing
docker run -d --name dozzle -p 9999:8080 -v //var/run/docker.sock:/var/run/docker.sock amir20/dozzle:latest

# 2. Clean up old logs
python scripts/log_manager.py --rotate

# 3. View Docker logs in browser
start http://localhost:9999
```

### For Next Week (Production Ready):

```powershell
# 1. Create monitoring config directory
mkdir -p monitoring/grafana/provisioning/datasources

# 2. Start Loki + Grafana stack
docker compose -f docker-compose.monitoring.yml up -d

# 3. Add Uptime Kuma monitors for your services
start http://localhost:3001

# 4. Import Grafana dashboard
start http://localhost:3100
```

---

## 📁 Suggested Directory Structure

```
py-sec-edgar/
├── monitoring/
│   ├── docker-compose.monitoring.yml
│   ├── loki-config.yml
│   ├── promtail-config.yml
│   ├── filebeat.yml
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── loki.yml
│           └── dashboards/
│               └── spine-logs.json
├── scripts/
│   └── log_manager.py
└── logs/
    └── archive/
        ├── 2025-09/
        └── 2026-01/
```

---

## 🔗 Related Documentation

- [Observability Module](capture-spine/app/observability/) - Existing scaffolding
- [System Dashboard](capture-spine/app/api/routers/system/dashboard/) - Extend this
- [docker-compose.search.yml](capture-spine/docker-compose.search.yml) - Elasticsearch already here
- [DevOps Monitoring Example](feedspine/examples/04_DEVOPS_MONITORING_EXAMPLE.md) - FeedSpine approach

---

## Next Steps

1. **Decide** which option fits your needs (see comparison table)
2. **Start Simple**: Try Dozzle + log_manager.py for immediate relief
3. **Graduate**: Move to Loki + Grafana when you need search/dashboards
4. **Integrate**: Hook into existing capture-spine dashboard for unified view
