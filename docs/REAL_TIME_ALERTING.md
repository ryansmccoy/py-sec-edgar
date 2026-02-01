# Real-Time Log Alerting System

This system monitors Docker container logs in Elasticsearch and displays real-time alerts in the capture-spine frontend.

## Architecture

```
Docker Containers → Promtail → Loki → Elasticsearch
                                           ↓
                    Backend API ← Query ← Elasticsearch
                         ↓
                    Frontend (Polling every 30s)
                         ↓
                    AlertNotificationBar (Top banner)
```

## Components

### Backend API (`app/api/routers/monitoring/alerts.py`)

Two endpoints for retrieving log alerts:

1. **`GET /api/v1/monitoring/alerts`** - Recent error/warning logs
   - **Parameters:**
     - `minutes`: Time range to search (default: 30)
     - `limit`: Max alerts to return (default: 50)
     - `min_level`: Minimum severity (WARNING|ERROR|CRITICAL)
   - **Returns:** List of alerts with timestamp, service, level, message
   - **Example:**
     ```bash
     curl 'http://localhost:8000/api/v1/monitoring/alerts?minutes=30&min_level=ERROR'
     ```

2. **`GET /api/v1/monitoring/alerts/summary`** - Aggregated counts by service
   - **Parameters:**
     - `minutes`: Time range (default: 60)
   - **Returns:** Per-service error/warning counts
   - **Example:**
     ```bash
     curl 'http://localhost:8000/api/v1/monitoring/alerts/summary'
     ```

### Frontend Component (`frontend/src/components/monitoring/AlertNotificationBar.tsx`)

**AlertNotificationBar** - Dismissible banner at the top of the app

**Features:**
- ✅ Polls `/api/v1/monitoring/alerts` every 30 seconds
- ✅ Auto-appears when new errors detected
- ✅ Color-coded by severity:
  - 🔴 **CRITICAL** - Red background
  - 🟠 **ERROR** - Orange background
  - 🟡 **WARNING** - Yellow background
- ✅ Dismissible (hides until new alerts arrive)
- ✅ Click "View Logs" → navigates to `/monitoring/logs`
- ✅ Shows most recent alert + count of additional alerts

**Usage:**
```tsx
import { AlertNotificationBar } from './components/monitoring/AlertNotificationBar';

// Already added to App.tsx - renders at top of all pages
<AlertNotificationBar />
```

## How It Works

### 1. Log Collection (Already Set Up)

Promtail collects logs from Docker containers:

```yaml
# monitoring/promtail-config.yml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '^/(spine-.*|genai-.*|.*-spine.*)$'
        action: keep
```

Logs flow: **Docker stdout → Promtail → Loki → Elasticsearch**

### 2. Alert Query (Backend)

Backend queries Elasticsearch for logs matching:
- **Time range**: Last N minutes (default: 30)
- **Level**: WARNING, ERROR, or CRITICAL
- **Excludes**: Health check noise (`GET /health`)

**Elasticsearch Query:**
```python
{
  "bool": {
    "filter": [
      {"range": {"@timestamp": {"gte": "now-30m"}}},
      {"terms": {"level.keyword": ["WARNING", "ERROR", "CRITICAL"]}}
    ],
    "must_not": [
      {"match_phrase": {"message": "GET /health"}}
    ]
  }
}
```

### 3. Frontend Polling

Component polls backend every 30 seconds:

```typescript
useEffect(() => {
  fetchAlerts();
  const interval = setInterval(fetchAlerts, 30000);
  return () => clearInterval(interval);
}, []);
```

### 4. Alert Display

Banner appears when:
- Errors/warnings exist in last 30 minutes
- User hasn't dismissed the current alert

Banner disappears when:
- User clicks "X" (dismiss)
- No errors exist

## Examples

### Example: Backend Error Triggers Alert

1. **Backend logs error:**
   ```python
   logger.error("Failed to connect to database")
   ```

2. **Promtail ships to Elasticsearch** (within seconds)

3. **Frontend polls API** (every 30s)
   ```
   GET /api/v1/monitoring/alerts?minutes=30&min_level=WARNING
   ```

4. **Alert banner appears:**
   ```
   🟠 Error
   1m ago · spine-dev-api
   Failed to connect to database
   +2 more alerts in the last 30 minutes
   [View Logs] [X]
   ```

### Example Response

**GET /api/v1/monitoring/alerts**
```json
{
  "alerts": [
    {
      "timestamp": "2026-01-31T10:15:30.123Z",
      "level": "ERROR",
      "service": "spine-dev-api",
      "logger": "capture_spine.api.feeds",
      "message": "Failed to fetch feed: Connection timeout",
      "exception": null
    },
    {
      "timestamp": "2026-01-31T10:10:15.456Z",
      "level": "WARNING",
      "service": "genai-spine-api",
      "logger": "genai_spine.providers",
      "message": "OpenAI API rate limit reached",
      "exception": null
    }
  ],
  "total_count": 12,
  "time_range_minutes": 30,
  "has_critical": false,
  "has_errors": true
}
```

## Configuration

### Backend

**Environment Variables:**
```bash
# Elasticsearch URL (default: http://localhost:9200)
ELASTICSEARCH_URL=http://localhost:9200

# Index pattern for log queries (default: logs-*)
ES_LOG_INDEX_PATTERN=logs-*
```

### Frontend

**Polling Interval:**
Edit `AlertNotificationBar.tsx`:
```typescript
const interval = setInterval(fetchAlerts, 30000); // 30 seconds
```

**Alert Threshold:**
Change minimum level in API call:
```typescript
'/api/v1/monitoring/alerts?minutes=30&limit=10&min_level=ERROR'
```

## Testing

### 1. Generate Test Error

**Python (in capture-spine container):**
```python
import logging
logger = logging.getLogger("test")
logger.error("This is a test error for alert system")
```

**Bash:**
```bash
docker exec spine-dev-api python -c "import logging; logging.error('Test alert')"
```

### 2. Check Elasticsearch

```bash
curl -X GET "http://localhost:9200/logs-*/_search?q=level:ERROR&size=5&pretty"
```

### 3. Check API

```bash
curl "http://localhost:8000/api/v1/monitoring/alerts?minutes=5&min_level=ERROR"
```

### 4. Check Frontend

1. Open capture-spine: http://localhost:5173
2. Wait up to 30 seconds for poll
3. Alert banner should appear at top

## Troubleshooting

### No alerts appear

**Check Elasticsearch is running:**
```bash
docker ps | grep elasticsearch
curl http://localhost:9200/_cluster/health
```

**Check logs exist:**
```bash
curl "http://localhost:9200/logs-*/_count"
```

**Check API returns data:**
```bash
curl "http://localhost:8000/api/v1/monitoring/alerts?minutes=60&min_level=WARNING"
```

**Check browser console:**
```
Open DevTools → Console → Look for fetch errors
```

### Alerts don't refresh

**Frontend polling disabled?**
- Check if component mounted: `<AlertNotificationBar />`
- Check browser console for errors
- Verify API endpoint accessible: `curl http://localhost:8000/api/v1/monitoring/alerts`

### Elasticsearch connection fails

**Backend logs show:**
```
Failed to query Elasticsearch for alerts: ConnectionError
```

**Fix:**
- Ensure Elasticsearch running: `docker ps | grep elasticsearch`
- Check network: `docker network inspect capture-spine_search-net`
- Verify URL: `curl http://localhost:9200`

## Advanced Usage

### Custom Alert Rules

Create custom filters in backend:

```python
# Only show critical errors from specific service
exclude_filter = {
    "bool": {
        "must": [
            {"term": {"service.keyword": "spine-dev-api"}},
            {"term": {"level.keyword": "CRITICAL"}}
        ]
    }
}
```

### WebSocket Alternative

For real-time updates without polling:

```python
# Backend (FastAPI)
@router.websocket("/monitoring/alerts/stream")
async def alert_stream(websocket: WebSocket):
    await websocket.accept()
    while True:
        alerts = await get_recent_alerts()
        await websocket.send_json(alerts)
        await asyncio.sleep(5)
```

```typescript
// Frontend
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/api/v1/monitoring/alerts/stream');
  ws.onmessage = (event) => {
    setAlerts(JSON.parse(event.data));
  };
  return () => ws.close();
}, []);
```

## Related Files

- Backend API: [app/api/routers/monitoring/alerts.py](../capture-spine/app/api/routers/monitoring/alerts.py)
- Frontend Component: [frontend/src/components/monitoring/AlertNotificationBar.tsx](../capture-spine/frontend/src/components/monitoring/AlertNotificationBar.tsx)
- Elasticsearch Config: [monitoring/docker-compose.monitoring.yml](../monitoring/docker-compose.monitoring.yml)
- Promtail Config: [monitoring/promtail-config.yml](../monitoring/promtail-config.yml)
- Logging Report: [LOGGING_CONFIGURATION_REPORT.md](LOGGING_CONFIGURATION_REPORT.md)

## Next Steps

1. ✅ **Already done** - Backend alert endpoint created
2. ✅ **Already done** - Frontend banner component added
3. ✅ **Already done** - Polling mechanism implemented
4. 🔄 **Test** - Generate errors and verify alerts appear
5. 🔜 **Enhance** - Add alert history page at `/monitoring/logs`
6. 🔜 **Optimize** - Add alert aggregation by service
7. 🔜 **Extend** - Add Slack/email notifications for critical errors
