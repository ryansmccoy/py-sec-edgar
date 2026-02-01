# EntitySpine Auto-Launch Configuration

## Summary

✅ **EntitySpine services now auto-launch by default** with the monitoring stack.
✅ **All services are on the `monitoring-net` network** and accessible to all containers.
✅ **No profile flags needed** - just run `docker compose up -d`.

## What Changed

### 1. Removed Profile Restrictions
Previously, EntitySpine services required `--profile entityspine` or `--profile full`. Now they start automatically with the default monitoring stack.

**Before:**
```bash
docker compose -f monitoring/docker-compose.monitoring.yml --profile entityspine up -d
```

**Now:**
```bash
docker compose -f monitoring/docker-compose.monitoring.yml up -d
# EntitySpine API, Web, and Docs start automatically!
```

### 2. Network Configuration
All EntitySpine services are on the `monitoring-net` network:

| Service | Container Name | Internal Port | External Port | Networks |
|---------|---------------|---------------|---------------|----------|
| **API** | `spine-entityspine-api` | 8080 | 8000 | monitoring-net, capture-spine_search-net |
| **Web** | `spine-entityspine-web` | 3000 | 3002 | monitoring-net |
| **Docs** | `spine-entityspine-docs` | 8000 | 8001 | monitoring-net |

### 3. Inter-Container Access

Other containers on `monitoring-net` can access EntitySpine services using internal hostnames:

```yaml
# Example: From Grafana, Promtail, or any other container
services:
  my-service:
    networks:
      - monitoring-net
    environment:
      # Use internal container names
      - API_URL=http://spine-entityspine-api:8080
      - WEB_URL=http://spine-entityspine-web:3000
      - DOCS_URL=http://spine-entityspine-docs:8000
```

### 4. Dependencies & Health Checks

The web frontend waits for the API to be healthy before starting:

```yaml
entityspine-frontend:
  depends_on:
    entityspine-api:
      condition: service_healthy
```

The API includes health checks:
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Usage

### Start Everything

```powershell
# Using the startup script
cd monitoring
./start-entityspine.ps1

# Or manually
docker compose -f monitoring/docker-compose.monitoring.yml up -d
```

### Access Services

From your browser (host machine):
- **EntitySpine Web**: http://localhost:3002
- **EntitySpine API**: http://localhost:8000
- **EntitySpine Docs**: http://localhost:8001
- **Grafana**: http://localhost:3100
- **Uptime Kuma**: http://localhost:3001 (requires `--profile full`)
- **Dozzle**: http://localhost:9999 (requires `--profile full`)

From other Docker containers on `monitoring-net`:
- **EntitySpine API**: http://spine-entityspine-api:8080
- **EntitySpine Web**: http://spine-entityspine-web:3000
- **EntitySpine Docs**: http://spine-entityspine-docs:8000

### Start with Additional Services

If you want Uptime Kuma and Dozzle for health monitoring:

```bash
docker compose -f monitoring/docker-compose.monitoring.yml --profile full up -d
```

## Integration Examples

### Grafana Dashboard

Add EntitySpine metrics to Grafana:

```yaml
# Grafana already on monitoring-net, so it can query:
# http://spine-entityspine-api:8080/stats
```

### Promtail Log Collection

Promtail can collect EntitySpine container logs:

```yaml
scrape_configs:
  - job_name: entityspine-api
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        filters:
          - name: name
            values: [spine-entityspine-api]
```

### Uptime Kuma Health Checks

Add monitors for EntitySpine services:
- HTTP(s) monitor: http://spine-entityspine-api:8080/health
- HTTP(s) monitor: http://spine-entityspine-web:3000
- HTTP(s) monitor: http://spine-entityspine-docs:8000

## File Locations

- **Docker Config**: `monitoring/docker-compose.monitoring.yml`
- **Web Source**: `entityspine/web/`
- **API Source**: `entityspine/src/`
- **Docs Source**: `entityspine/docs/`
- **Startup Script**: `monitoring/start-entityspine.ps1`
- **Docker Guide**: `entityspine/web/DOCKER.md`

## Troubleshooting

### Web UI not loading?
```bash
# Check if API is healthy
docker inspect spine-entityspine-api --format='{{.State.Health.Status}}'

# Should output: healthy

# View frontend logs
docker logs spine-entityspine-web
```

### API not responding?
```bash
# Check health endpoint
curl http://localhost:8000/health

# View API logs
docker logs spine-entityspine-api

# Restart API
docker compose -f monitoring/docker-compose.monitoring.yml restart entityspine-api
```

### Network issues?
```bash
# Verify network exists
docker network ls | grep monitoring-net

# Check which containers are on the network
docker network inspect monitoring-net --format='{{range .Containers}}{{.Name}} {{end}}'
```

## Next Steps

1. **Load Data**: Visit http://localhost:3002/database and click "Load SEC Data"
2. **Search Entities**: Go to http://localhost:3002/search
3. **View Graphs**: Explore http://localhost:3002/graph
4. **Monitor**: Check Grafana at http://localhost:3100
5. **Read Docs**: Browse http://localhost:8001

## Summary of Auto-Launch Benefits

✅ **Simplified startup** - No need to remember profile flags
✅ **Always available** - EntitySpine services start with monitoring stack
✅ **Network ready** - All containers can communicate via monitoring-net
✅ **Health checks** - Web waits for API to be healthy
✅ **Persistent data** - Database survives container restarts
✅ **Auto-load SEC data** - API loads 14K+ companies on first start
✅ **Production ready** - Nginx serves optimized React build
