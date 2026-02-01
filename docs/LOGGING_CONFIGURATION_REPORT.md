# Log File Configuration Report - Spine Ecosystem

## Executive Summary

The spine ecosystem currently has **inconsistent logging** across different applications. Only **capture-spine** is actively saving log files to disk (via uvicorn configuration in development scripts). The other spine projects (genai-spine, entityspine, feedspine, market-spine) either don't have file logging configured or aren't running/generating logs.

## Current State

### Log Files Found

```
Location                                  Files  Size(MB)  Status
─────────────────────────────────────────────────────────────────
capture-spine/logs/                         37   107.09   ACTIVE
capture-spine/scripts/dev/logs/              4    24.10   DEV ONLY
capture-spine/scripts/logs/                  2     0.00   EMPTY
capture-spine/backups/                       1     0.03   BACKUP
─────────────────────────────────────────────────────────────────
genai-spine/                                 0     0.00   NO FILES
entityspine/                                 0     0.00   NO FILES
feedspine/                                   0     0.00   NO FILES
market-spine/                                0     0.00   NO FILES
```

**Total:** 44 files, 131.22 MB

### Where Logs Are Being Saved

#### ✅ capture-spine - CONFIGURED
- **Location**: `./logs/` directory (mounted in Docker)
- **Configuration**: `docker-compose.dev.yml` line 102:
  ```yaml
  volumes:
    - ./logs:/app/logs
  ```
- **How**: Uvicorn FileHandler configured in `scripts/dev/run_api.py`
- **Format**:
  - Filename: `api-YYYY-MM-DD.log`, `frontend-YYYY-MM-DD.log`
  - Format: `timestamp | level | logger | message`
- **Retention**: Manual (no rotation configured in Docker)
- **Size**: 107 MB (last 10 days)

#### ❌ genai-spine - NOT CONFIGURED
- **Current**: Logs only to stdout (Docker logs)
- **Main**: `src/genai_spine/main.py` - uses uvicorn with `log_level` but no file handler
- **Missing**: File logging configuration, log directory mount

#### ❌ entityspine - NOT CONFIGURED
- **Current**: No logging files found
- **Status**: May be using spine-core logging framework but no file output

#### ❌ feedspine - NOT CONFIGURED
- **Current**: No logging files found
- **Config**: Has `log_level` setting in `core/config.py` but no file handler

#### ❌ market-spine - NOT CONFIGURED
- **Current**: No logging files found
- **Framework**: Should use spine-core logging but not generating files

## Issues Identified

### 1. Inconsistent Configuration
- **Problem**: Only capture-spine saves logs to files
- **Impact**: Can't analyze history for other services
- **Root Cause**: Each app configures logging independently

### 2. No Centralized Logging Strategy
- **Problem**: No shared logging configuration
- **Impact**: Different formats, different locations, different retention
- **Solution Needed**: Standardized logging across all spine apps

### 3. Docker Logging Mixed with File Logging
- **Problem**: capture-spine logs to BOTH stdout (Docker) AND files
- **Impact**: Duplication, inconsistency
- **Best Practice**: Should choose one primary method

### 4. No Log Rotation in Docker
- **Problem**: Docker-mounted logs grow indefinitely
- **Impact**: 107 MB accumulated in 10 days (will grow unbounded)
- **Missing**: TimedRotatingFileHandler or external rotation

### 5. Development vs Production Discrepancy
- **Problem**: `scripts/dev/run_api.py` configures file logging, but production might not
- **Impact**: Different logging in dev vs prod
- **Evidence**: Docker compose just runs `uvicorn` without custom log config

## Logging Framework Analysis

### spine-core Framework (Available But Not Used Everywhere)
- **Location**: `spine-core/packages/spine-core/src/spine/framework/logging/`
- **Features**:
  - Structured logging with structlog
  - JSON or console output
  - Execution context tracking
  - Environment-based configuration
- **Usage**: Designed for market-spine, can be adopted by others
- **Gap**: No file handler in the framework (stdout only)

### capture-spine Custom Setup
- **Location**: `scripts/dev/run_api.py`
- **Method**: Uvicorn log_config with FileHandler
- **Format**: Custom formatter
- **Loggers**: uvicorn, fastapi, capture_spine.*

## Recommendations

### Option 1: Unified File Logging (Simple)
**Add FileHandler to all apps consistently**

```python
# Standardized logging config for all spine apps
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

def setup_spine_logging(app_name: str, log_dir: Path = Path("./logs")):
    log_dir.mkdir(exist_ok=True)

    # Rotating file handler (daily rotation, keep 30 days)
    file_handler = TimedRotatingFileHandler(
        log_dir / f"{app_name}.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s"
    ))

    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
```

**Apply to all apps:**
- capture-spine: Use this instead of custom uvicorn config
- genai-spine: Add to `main.py` before uvicorn.run()
- entityspine: Add to startup
- feedspine: Add to startup
- market-spine: Add to startup

### Option 2: Container-Native Logging (Recommended)
**Remove file logging, use Docker/Promtail for everything**

1. **Remove file mounts** from all docker-compose files
2. **Log to stdout only** (Docker native)
3. **Promtail collects** from Docker (already configured!)
4. **Loki stores** logs centrally
5. **Grafana/Kibana query** logs

**Benefits:**
- No disk management needed
- Automatic collection via Promtail
- Already ingesting into Elasticsearch
- Centralized search/visualization
- No rotation needed
- Works in Kubernetes/cloud

### Option 3: Hybrid (File + Docker)
**Keep files for local debugging, Docker for production**

- Development: File logging (easy to grep, tail -f)
- Docker: stdout only
- Promtail: Collects from Docker containers
- Elasticsearch: Central search

## Standardized Configuration Proposal

### Create: `spine_logging.py` (shared package)

```python
"""
Standardized logging for Spine ecosystem.

Usage:
    from spine_logging import configure_spine_logging

    # In main.py or app startup
    configure_spine_logging(
        app_name="capture-spine-api",
        log_level="INFO",
        log_to_file=True,  # False in Docker
        log_dir="/app/logs"
    )
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Literal

def configure_spine_logging(
    app_name: str,
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO",
    log_to_file: bool = True,
    log_dir: Path | str = "./logs",
    log_format: Literal["json", "text"] = "text",
    rotation_days: int = 30,
) -> None:
    """Configure standardized logging for Spine applications."""

    handlers = []

    # Console handler (always enabled for Docker)
    console_handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        import json
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
    handlers.append(console_handler)

    # File handler (optional, for local dev)
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_handler = TimedRotatingFileHandler(
            log_path / f"{app_name}.log",
            when="midnight",
            interval=1,
            backupCount=rotation_days,
            encoding="utf-8"
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers,
        force=True
    )

    # Suppress noisy third-party loggers
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("asyncpg").setLevel(logging.INFO)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        import json
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)
```

### Environment Variables (All Apps)

```bash
# Common across all spine apps
SPINE_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
SPINE_LOG_FORMAT=text         # text or json
SPINE_LOG_TO_FILE=false       # true for local dev, false in Docker
SPINE_LOG_DIR=/app/logs       # Where to save logs if enabled
SPINE_LOG_ROTATION_DAYS=30    # How many days to keep
```

## Migration Plan

### Phase 1: Immediate (Capture-Spine)
1. ✅ Already logging to files
2. ⚠️ Remove duplicate stdout logging (choose one)
3. ⚠️ Add log rotation (currently unlimited growth)

### Phase 2: Standardize (All Apps)
1. Create `spine-core/logging/standardized.py`
2. Update capture-spine to use standard config
3. Add logging to genai-spine
4. Add logging to entityspine
5. Add logging to feedspine
6. Add logging to market-spine

### Phase 3: Centralize (Production Ready)
1. Remove file logging from Docker containers
2. Configure Promtail to collect from all containers
3. Verify Elasticsearch ingestion works
4. Create Grafana dashboards per service
5. Set up retention policies

## Docker Compose Updates Needed

### All docker-compose files should have:

```yaml
services:
  app-name:
    environment:
      SPINE_LOG_LEVEL: ${LOG_LEVEL:-INFO}
      SPINE_LOG_FORMAT: text  # or json for production
      SPINE_LOG_TO_FILE: "false"  # Let Docker handle logs

    # Optionally mount for local dev debugging
    # volumes:
    #   - ./logs:/app/logs  # Only for development
```

### Promtail should collect from Docker:

```yaml
# monitoring/promtail-config.yml (already configured!)
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '^/(spine-.*|genai-.*|.*-spine.*)$'
        action: keep
```

## Current Elasticsearch Integration

✅ **Already working:**
- Promtail collects logs from Docker containers
- Loki stores logs (30 day retention)
- Created script to ship to Elasticsearch
- 1.8M+ log entries indexed

❌ **Not automatic:**
- Manual script execution needed
- Should run on schedule or use Filebeat

## Next Steps

1. **Decide**: File-based vs Container-native logging?
2. **Standardize**: Create shared logging module
3. **Migrate**: Update all apps to use standard config
4. **Test**: Verify logs flow to Loki/Elasticsearch
5. **Monitor**: Set up Grafana alerts

## Files to Update

### If Choosing Container-Native (Recommended):

```
capture-spine/docker-compose.dev.yml    - Remove ./logs mount
capture-spine/docker-compose.qa.yml     - Remove ./logs mount
capture-spine/scripts/dev/run_api.py    - Remove FileHandler
genai-spine/src/genai_spine/main.py     - No changes (already stdout)
monitoring/promtail-config.yml          - Already configured ✓
```

### If Choosing Standardized Files:

```
spine-core/packages/spine-core/src/spine/framework/logging/files.py  - NEW
capture-spine/docker-compose.dev.yml    - Add SPINE_LOG_* env vars
genai-spine/docker-compose.yml          - Add logging config
genai-spine/src/genai_spine/main.py     - Import configure_spine_logging()
entityspine/                            - Add logging
feedspine/                              - Add logging
market-spine/                           - Add logging
```

---

**Generated:** 2026-01-31
**Log Files Analyzed:** 44 files across 4 directories
**Total Size:** 131.22 MB
