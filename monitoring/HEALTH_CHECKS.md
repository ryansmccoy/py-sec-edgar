# Health Check System

## Overview

The Spine ecosystem has multiple layers of health checking:

1. **Automated Script** - `check-health.ps1`
2. **Ecosystem Dashboard** - Web UI at http://localhost:3000/monitoring/ecosystem
3. **Uptime Kuma** - Service monitoring at http://localhost:3001
4. **Docker Health Checks** - Built into containers
5. **Grafana** - Metrics and alerting at http://localhost:3100

## Quick Health Check

```powershell
# Basic check
.\monitoring\check-health.ps1

# Detailed with response times
.\monitoring\check-health.ps1 -Detailed

# Watch mode (auto-refresh)
.\monitoring\check-health.ps1 -Watch

# JSON output (for CI/CD)
.\monitoring\check-health.ps1 -Json
```

## Services Monitored

| Service | URL | Container | Critical |
|---------|-----|-----------|----------|
| **Capture Spine Web** | http://localhost:3000 | capture-spine-frontend | ✅ Yes |
| **Capture Spine API** | http://localhost:8080/health | capture-spine-api | ✅ Yes |
| **EntitySpine Web** | http://localhost:5173 | spine-entityspine-web | No |
| **EntitySpine API** | http://localhost:8765/health | spine-entityspine-api | No |
| **EntitySpine Docs** | http://localhost:8123 | spine-entityspine-docs | No |
| **GenAI Spine Web** | http://localhost:3030 | genai-spine-frontend | No |
| **GenAI Spine API** | http://localhost:8090/health | genai-spine-api | No |
| **Ollama** | http://localhost:11434/api/tags | ollama | No |
| **Grafana** | http://localhost:3100/api/health | spine-grafana | No |
| **Uptime Kuma** | http://localhost:3001 | spine-uptime | No |
| **Dozzle** | http://localhost:9999 | spine-dozzle | No |
| **Loki** | http://localhost:3101/ready | spine-loki | No |
| **Elasticsearch** | http://localhost:9200/_cluster/health | spine-elasticsearch | No |
| **Kibana** | http://localhost:5601/api/status | spine-kibana | No |

## Health Check Methods

### 1. PowerShell Script

**Best for**: Quick command-line checks, CI/CD, automation

```powershell
# Run basic health check
cd monitoring
./check-health.ps1

# Example output:
# 🏥 Spine Ecosystem Health Check
# ================================
#
# 📊 Summary: 12/14 services online
#
# 📁 Core Applications
# ────────────────────────────────────────────────────────────
#   ✅ Capture Spine Web       [200]
#   ✅ Capture Spine API       [200]
#
# 📁 EntitySpine
# ────────────────────────────────────────────────────────────
#   ✅ EntitySpine Web         [200]
#   ✅ EntitySpine API         [200]
#   ✅ EntitySpine Docs        [200]
```

**Features**:
- ✅ HTTP endpoint checks
- ✅ Docker container status
- ✅ Response time measurement
- ✅ Critical service flagging
- ✅ Watch mode for continuous monitoring
- ✅ JSON output for automation

### 2. Ecosystem Dashboard (Web UI)

**Best for**: Visual monitoring, quick access, developer workflow

**Access**: http://localhost:3000/monitoring/ecosystem

**Features**:
- ✅ Real-time status indicators
- ✅ One-click access to services
- ✅ Search and filter
- ✅ Auto-refresh every 30 seconds
- ✅ Service descriptions
- ✅ Container information

### 3. Uptime Kuma

**Best for**: Long-term monitoring, alerts, status page

**Access**: http://localhost:3001

**Setup**:
```powershell
# First time: Create account and add monitors
1. Open http://localhost:3001
2. Create admin account
3. Add monitors for each service
4. Configure notifications (email, Slack, Discord, etc.)
```

**Features**:
- ✅ Historical uptime tracking
- ✅ Alert notifications
- ✅ Public status page
- ✅ Response time graphs
- ✅ Certificate monitoring
- ✅ Keyword monitoring

### 4. Docker Health Checks

**Best for**: Container orchestration, automatic restarts

**Check manually**:
```powershell
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Inspect specific service
docker inspect spine-entityspine-api --format='{{.State.Health.Status}}'

# View health check logs
docker inspect spine-entityspine-api --format='{{json .State.Health}}' | ConvertFrom-Json
```

**Services with health checks**:
- EntitySpine API: `curl -f http://localhost:8080/health`
- Loki: Built-in health endpoint
- Grafana: Built-in health endpoint

### 5. Grafana Dashboards

**Best for**: Metrics, trends, alerts

**Access**: http://localhost:3100 (admin/admin)

**Available Dashboards**:
- Container metrics (CPU, memory, network)
- Log aggregation from Loki
- Custom service metrics
- Alert rules

## Health Check API Endpoints

Most services expose health endpoints:

| Service | Endpoint | Response |
|---------|----------|----------|
| Capture Spine API | `/health` | `{"status": "healthy"}` |
| EntitySpine API | `/health` | `{"status": "healthy"}` |
| GenAI Spine API | `/health` | `{"status": "healthy"}` |
| Grafana | `/api/health` | `{"database": "ok"}` |
| Loki | `/ready` | HTTP 200 |
| Elasticsearch | `/_cluster/health` | Cluster status JSON |
| Kibana | `/api/status` | Status JSON |

## Troubleshooting

### Service shows as down

1. **Check container status**:
   ```powershell
   docker ps -a | Select-String <container-name>
   ```

2. **View logs**:
   ```powershell
   docker logs <container-name> --tail 50
   ```

3. **Restart service**:
   ```powershell
   docker restart <container-name>
   # or
   cd monitoring
   docker compose -f docker-compose.monitoring.yml restart <service-name>
   ```

### All services down

1. **Check Docker is running**:
   ```powershell
   docker ps
   ```

2. **Start monitoring stack**:
   ```powershell
   cd monitoring
   ./start-entityspine.ps1
   ```

### Slow response times

1. **Check container resources**:
   ```powershell
   docker stats --no-stream
   ```

2. **View Grafana dashboards** at http://localhost:3100

3. **Check logs** for errors:
   ```powershell
   # Use Dozzle for real-time logs
   # Open http://localhost:9999
   ```

## CI/CD Integration

Use JSON output for automation:

```powershell
# Get JSON report
$health = .\monitoring\check-health.ps1 -Json | ConvertFrom-Json

# Check if critical services are down
if ($health.summary.critical_down -gt 0) {
    Write-Error "Critical services are down!"
    exit 1
}

# Check overall health
$healthyPercent = ($health.summary.healthy / $health.summary.total) * 100
if ($healthyPercent -lt 80) {
    Write-Warning "Only $healthyPercent% of services are healthy"
}
```

## Automated Monitoring

Set up continuous monitoring:

```powershell
# Option 1: Use watch mode
.\monitoring\check-health.ps1 -Watch -WatchInterval 10

# Option 2: Schedule with Task Scheduler
# Create a task that runs check-health.ps1 every 5 minutes

# Option 3: Use Uptime Kuma
# Configure monitors and get notifications
```

## Health Check Frequency

| Method | Frequency | Use Case |
|--------|-----------|----------|
| Script (manual) | On-demand | Quick checks, troubleshooting |
| Script (watch) | 5-30 seconds | Active monitoring session |
| Ecosystem Dashboard | 30 seconds | Developer workflow |
| Uptime Kuma | 60 seconds | Production monitoring |
| Docker health | 30 seconds | Container orchestration |
| Grafana | Real-time | Metrics and trends |

## Best Practices

1. **Start monitoring stack first**: Ensures Grafana, Loki, Uptime Kuma are ready
   ```powershell
   cd monitoring
   ./start-entityspine.ps1
   ```

2. **Check health after deployments**:
   ```powershell
   docker compose up -d --build
   sleep 30
   ./monitoring/check-health.ps1 -Detailed
   ```

3. **Monitor logs during development**:
   - Use Dozzle: http://localhost:9999
   - Or: `docker compose logs -f <service>`

4. **Set up Uptime Kuma for important services**:
   - Configure email/Slack notifications
   - Create a status page for team visibility

5. **Use Grafana for trends**:
   - Create dashboards for key metrics
   - Set up alert rules for anomalies

## Quick Reference

```powershell
# Check all services
.\monitoring\check-health.ps1

# Continuous monitoring
.\monitoring\check-health.ps1 -Watch

# View in browser
start http://localhost:3000/monitoring/ecosystem

# Check Docker
docker ps --format "table {{.Names}}\t{{.Status}}"

# Restart everything
cd monitoring
docker compose -f docker-compose.monitoring.yml restart

# View logs
start http://localhost:9999

# Check metrics
start http://localhost:3100
```

## Summary

✅ **Multiple health check methods available**
✅ **Automated and manual options**
✅ **Real-time and historical monitoring**
✅ **Alerts and notifications (Uptime Kuma)**
✅ **Visual dashboards (Grafana, Ecosystem Dashboard)**
✅ **CI/CD integration (JSON output)**

Use `check-health.ps1` for quick checks and the Ecosystem Dashboard for daily monitoring!
