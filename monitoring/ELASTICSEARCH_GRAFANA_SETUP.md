# Elasticsearch Integration & Grafana Dashboards - Complete Setup

## 🎉 INTEGRATION COMPLETE

Successfully integrated logs into Elasticsearch and created advanced Grafana dashboards!

## 📊 Summary

### Logs Ingested to Elasticsearch
- **Total Entries**: 118,751 log entries
- **Source Files**: 272 log files
- **Date Range**: Last 7 days
- **Index Name**: `spine-logs`

### Top Log Sources
1. **992 entries** - capture-spine/logs/api_2025-12-28_211038.log
2. **990 entries** - capture-spine/logs/api_2025-12-30_144825.log
3. **907 entries** - capture-spine/logs/api-2026-01-03.log
4. **905 entries** - capture-spine/logs/api_2025-12-29_155322.log
5. **882 entries** - capture-spine/logs/frontend-2026-01-04.log

## 🔗 Access URLs

### Grafana - Advanced Dashboards
- **URL**: http://localhost:3100
- **Username**: `admin`
- **Password**: `admin`
- **Dashboards Available**:
  - "Spine Ecosystem - Log Dashboard" (basic Loki dashboard)
  - "Spine Ecosystem - Advanced Log Analytics" (NEW - 9 panels with sophisticated visualizations)

### Uptime Kuma - Service Monitoring
- **URL**: http://localhost:3001
- **First Time Setup**: Create admin account on first launch
- **Status**: Running and healthy

### Kibana - Elasticsearch UI
- **URL**: http://localhost:5601
- **Status**: Available for Elasticsearch log exploration
- **Index Pattern**: Create `spine-logs*` pattern in Kibana > Stack Management > Index Patterns

### Dozzle - Docker Logs
- **URL**: http://localhost:9999
- **Purpose**: Real-time Docker container log viewing

## 📈 Grafana Dashboard Features

The new "Spine Ecosystem - Advanced Log Analytics" dashboard includes:

### 1. Key Metrics (Top Row)
- **🔴 Total Errors (24h)**: Shows total error count with color thresholds
- **⚠️ Total Warnings (24h)**: Warning count across all services

### 2. Time Series Visualizations
- **📊 Log Volume by Service**: Track log activity per service
- **🔥 Error Rate by Service**: Stacked bar chart showing errors over time
- **📉 Log Level Trends**: Compare ERROR, WARNING, INFO trends

### 3. Distribution Charts
- **📈 Log Level Distribution**: Donut chart showing breakdown by severity
- **📊 Errors by Service**: Horizontal bar chart of total errors per service

### 4. Analysis Tables
- **🔝 Top Error Messages**: Table of most frequent errors

### 5. Live Monitoring
- **🔴 Live Error & Warning Stream**: Real-time log tail showing errors and warnings

## 🛠️ How to Use

### Elasticsearch Log Queries (Kibana)
1. Open http://localhost:5601
2. Go to "Discover"
3. Create index pattern: `spine-logs*`
4. Search examples:
   - Find errors: `level:ERROR`
   - Search message content: `message:"connection refused"`
   - Filter by service: `service:capture-spine`
   - Time range: Use time picker in top-right

### Grafana Dashboard Navigation
1. Open http://localhost:3100
2. Login with admin/admin
3. Go to "Dashboards" (left sidebar, grid icon)
4. Select "Spine Ecosystem - Advanced Log Analytics"
5. Use time range selector (top-right) to change window
6. Click on any graph to drill down
7. Use "Refresh" dropdown to enable auto-refresh (10s, 30s, 1m, etc.)

### Uptime Kuma Setup
1. Open http://localhost:3001
2. Create admin account (first-time setup wizard)
3. Add monitors:
   - **HTTP Monitor**: http://localhost:8000/health (spine-dev-api)
   - **HTTP Monitor**: http://localhost:8001/health (spine-api-qa)
   - **HTTP Monitor**: http://localhost:9200 (Elasticsearch)
   - **Docker Container**: Monitor spine containers

## 🔄 Continuous Log Ingestion

To keep Elasticsearch updated with new logs, run periodically:

```powershell
# Ship logs from last 24 hours
B:/github/py-sec-edgar/.venv/Scripts/python.exe scripts/send_logs_to_elasticsearch.py --days 1

# Ship all capture-spine logs
B:/github/py-sec-edgar/.venv/Scripts/python.exe scripts/send_logs_to_elasticsearch.py --pattern "capture-spine/logs/**/*.log"

# Ship everything without date filter
B:/github/py-sec-edgar/.venv/Scripts/python.exe scripts/send_logs_to_elasticsearch.py --all
```

### Automated Ingestion (Optional)
Create a Windows Task Scheduler job to run the script hourly:
```powershell
# Schedule task to run every hour
$action = New-ScheduledTaskAction -Execute 'B:/github/py-sec-edgar/.venv/Scripts/python.exe' `
    -Argument 'scripts/send_logs_to_elasticsearch.py --days 1' `
    -WorkingDirectory 'B:\github\py-sec-edgar'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName "Spine Log Ingestion" -Action $action -Trigger $trigger -Description "Ingest spine logs to Elasticsearch"
```

## 📁 Files Created

### Python Scripts
- **scripts/send_logs_to_elasticsearch.py**: Log ingestion tool
  - Parses Python log formats
  - Handles bulk indexing
  - Creates index templates
  - Supports date filtering

### Grafana Configurations
- **monitoring/grafana/provisioning/datasources/elasticsearch.yml**: Elasticsearch data source
  - Auto-configured for Grafana
  - Points to Elasticsearch container
  - Index pattern: `spine-logs*`

- **monitoring/grafana/provisioning/dashboards/spine-advanced-logs.json**: Advanced dashboard
  - 9 sophisticated panels
  - Live refresh capability
  - Color-coded severity levels
  - Interactive drill-down

### Docker Compose Updates
- **monitoring/docker-compose.monitoring.yml**:
  - Added external network connection to `capture-spine_search-net`
  - Grafana now has access to Elasticsearch container

## 🔍 Query Examples

### Loki Queries (in Grafana)
```logql
# All errors
{job=~".+"} |~ "(?i)(error|exception|fatal)"

# Errors from specific service
{job="spine-main"} |~ "ERROR"

# Warning count over time
sum by (job) (count_over_time({job=~".+"} |~ "(?i)warning" [5m]))

# Top error messages
topk(10, sum by (msg) (count_over_time({job=~".+"} |~ "ERROR" | pattern `<_> - ERROR - <_> - <msg>` [1h])))
```

### Elasticsearch Queries (in Kibana)
```json
# Find connection errors
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" }},
        { "match": { "message": "connection" }}
      ]
    }
  }
}

# Errors in last hour from capture-spine
{
  "query": {
    "bool": {
      "must": [
        { "match": { "service": "capture-spine" }},
        { "match": { "level": "ERROR" }},
        { "range": { "@timestamp": { "gte": "now-1h" }}}
      ]
    }
  }
}
```

## 🎯 Next Steps

1. **Explore Dashboards**: Open Grafana and explore the pre-built dashboards
2. **Set Up Alerts**: Configure Grafana alerts for error thresholds
3. **Add Monitors**: Set up Uptime Kuma monitors for all services
4. **Create Kibana Visualizations**: Build custom Elasticsearch dashboards
5. **Schedule Log Ingestion**: Automate periodic log shipping to ES

## 🐛 Troubleshooting

### Grafana Not Loading
```powershell
# Check Grafana status
docker logs spine-grafana --tail 50

# Restart Grafana
docker restart spine-grafana

# Verify port mapping
docker port spine-grafana
```

### Elasticsearch Connection Issues
```powershell
# Check Elasticsearch health
docker exec spine-elasticsearch curl http://localhost:9200/_cluster/health

# View Elasticsearch logs
docker logs spine-elasticsearch --tail 50
```

### Missing Logs in Elasticsearch
```powershell
# Check index exists
docker exec spine-elasticsearch curl http://localhost:9200/_cat/indices?v

# Verify document count
docker exec spine-elasticsearch curl http://localhost:9200/spine-logs/_count
```

## 📚 Resources

- **Grafana Documentation**: https://grafana.com/docs/grafana/latest/
- **Loki Query Language**: https://grafana.com/docs/loki/latest/logql/
- **Elasticsearch Query DSL**: https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html
- **Uptime Kuma**: https://github.com/louislam/uptime-kuma

---

**Status**: ✅ All monitoring services running and integrated
**Last Updated**: 2026-01-31
**Log Entries in ES**: 118,751 entries across 272 files
