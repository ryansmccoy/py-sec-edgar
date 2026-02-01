# EntitySpine Docker Services - Quick Start

Complete guide to running EntitySpine with Docker services.

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **EntitySpine Web** | 3002 | React frontend - search, visualize, manage |
| **EntitySpine API** | 8000 | FastAPI backend - entity resolution service |
| **EntitySpine Docs** | 8001 | MkDocs documentation - guides and API docs |
| **Grafana** | 3100 | Monitoring dashboards |
| **Loki** | 3101 | Log aggregation |
| **Uptime Kuma** | 3001 | Service health monitoring |
| **Dozzle** | 9999 | Real-time Docker logs |

## Quick Start

### Start EntitySpine Services Only

```bash
cd monitoring
docker compose -f docker-compose.monitoring.yml --profile entityspine up -d
```

**Access:**
- Web App: http://localhost:3002
- API: http://localhost:8000
- Docs: http://localhost:8001

### Start Everything (Full Stack)

```bash
cd monitoring
docker compose -f docker-compose.monitoring.yml --profile full up -d
```

**Includes:**
- EntitySpine (Web + API + Docs)
- Monitoring (Grafana + Loki + Promtail)
- Health Checks (Uptime Kuma + Dozzle)

### Start Monitoring Only

```bash
cd monitoring
docker compose -f docker-compose.monitoring.yml up -d
```

**Access:**
- Grafana: http://localhost:3100 (admin/admin)
- Loki: http://localhost:3101

## Usage Examples

### Search for Entities

1. Open http://localhost:3002
2. Click "Search" in sidebar
3. Search for "Apple", "AAPL", or "CIK 0000320193"
4. Click result to view details

### Visualize Knowledge Graph

1. Search for an entity
2. Click "View Knowledge Graph"
3. Explore entity relationships interactively

### Load SEC Data

1. Open http://localhost:3002/database
2. Click "Load SEC Data"
3. Wait for 14,000+ companies to load
4. Start searching!

### View Documentation

1. Open http://localhost:3002/docs for quick links
2. Open http://localhost:8001 for full MkDocs site
3. Browse guides:
   - Core Concepts
   - SEC Data Guide
   - Building Corporate Networks
   - API Reference

## Docker Commands

### View Logs

```bash
# All services
docker compose -f monitoring/docker-compose.monitoring.yml logs -f

# Specific service
docker compose -f monitoring/docker-compose.monitoring.yml logs -f entityspine-web
docker compose -f monitoring/docker-compose.monitoring.yml logs -f entityspine-api
```

### Restart Services

```bash
# Restart all
docker compose -f monitoring/docker-compose.monitoring.yml restart

# Restart specific service
docker compose -f monitoring/docker-compose.monitoring.yml restart entityspine-web
```

### Stop Services

```bash
# Stop all
docker compose -f monitoring/docker-compose.monitoring.yml down

# Stop and remove volumes
docker compose -f monitoring/docker-compose.monitoring.yml down -v
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker compose -f monitoring/docker-compose.monitoring.yml up -d --build entityspine-web
docker compose -f monitoring/docker-compose.monitoring.yml up -d --build entityspine-api
```

## Service Health Checks

### Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.3.3"
}
```

### Check Container Status

```bash
docker ps --filter "name=spine-entityspine"
```

### View Real-Time Logs

Open Dozzle: http://localhost:9999

## Troubleshooting

### EntitySpine API not starting

**Issue:** API container exits immediately

**Solution:**
```bash
# Check logs
docker logs spine-entityspine-api

# Common fixes:
# 1. Missing requirements
cd entityspine
pip install -r requirements/base.txt -r requirements/api.txt

# 2. Port already in use
# Change port in docker-compose.monitoring.yml:
# ports:
#   - "8001:8080"  # Changed from 8000
```

### Frontend can't connect to API

**Issue:** "Failed to load statistics" error

**Solution:**
```bash
# Check API is running
curl http://localhost:8000/health

# Check network connection
docker network inspect spine-monitoring_monitoring-net

# Restart with dependencies
docker compose -f monitoring/docker-compose.monitoring.yml restart entityspine-api
docker compose -f monitoring/docker-compose.monitoring.yml restart entityspine-web
```

### Docs not loading

**Issue:** EntitySpine Docs page is blank

**Solution:**
```bash
# Check mkdocs files exist
ls entityspine/mkdocs.yml
ls entityspine/docs/

# Rebuild docs locally first
cd entityspine
python -m mkdocs build

# Restart docs container
docker compose -f monitoring/docker-compose.monitoring.yml restart entityspine-docs
```

### Database is empty

**Issue:** No entities found

**Solution:**
1. Open http://localhost:3002/database
2. Click "Load SEC Data"
3. Wait 2-5 minutes for download and import
4. Check stats: http://localhost:8000/stats

## Development Workflow

### Working on Frontend

```bash
# Option 1: Docker with hot reload
cd entityspine/web
docker compose -f ../../monitoring/docker-compose.monitoring.yml up entityspine-web --build

# Option 2: Local development
npm install
npm start  # Runs on http://localhost:3000
```

### Working on API

```bash
# Option 1: Docker
docker compose -f monitoring/docker-compose.monitoring.yml up entityspine-api --build

# Option 2: Local development
cd entityspine
pip install -e ".[api]"
uvicorn entityspine.api.app:app --reload
```

### Working on Docs

```bash
# Option 1: Docker
docker compose -f monitoring/docker-compose.monitoring.yml up entityspine-docs

# Option 2: Local development
cd entityspine
python -m mkdocs serve
```

## Environment Variables

### EntitySpine API

```bash
ENTITYSPINE_DB_PATH=/data/entities.db  # Database location
ENTITYSPINE_AUTO_LOAD_SEC=true         # Auto-load SEC data on startup
```

### EntitySpine Web

```bash
REACT_APP_API_URL=http://localhost:8000    # API endpoint
REACT_APP_DOCS_URL=http://localhost:8001   # Docs endpoint
```

## Profiles

The docker-compose.yml uses profiles to control which services run:

| Profile | Services |
|---------|----------|
| `default` | Grafana, Loki, Promtail |
| `entityspine` | + EntitySpine (Web, API, Docs) |
| `full` | + Uptime Kuma, Dozzle |

### Using Profiles

```bash
# Just EntitySpine
docker compose -f monitoring/docker-compose.monitoring.yml --profile entityspine up -d

# EntitySpine + Full monitoring
docker compose -f monitoring/docker-compose.monitoring.yml --profile full up -d

# Default (monitoring only)
docker compose -f monitoring/docker-compose.monitoring.yml up -d
```

## Next Steps

1. **Load Data:** Visit http://localhost:3002/database and load SEC data
2. **Explore:** Search for companies, view knowledge graphs
3. **Read Docs:** Learn about core concepts at http://localhost:8001
4. **Monitor:** Check Grafana dashboards at http://localhost:3100
5. **Customize:** Edit docker-compose.monitoring.yml to change ports or add services

## Links

- **EntitySpine Repository:** https://github.com/ryansmccoy/entity-spine
- **Documentation:** http://localhost:8001
- **API Playground:** http://localhost:8000/docs (FastAPI Swagger UI)
- **Frontend Source:** `entityspine/web/`
- **Backend Source:** `entityspine/src/entityspine/api/`

---

**Need help?** Check the logs with `docker compose logs -f` or open an issue on GitHub.
