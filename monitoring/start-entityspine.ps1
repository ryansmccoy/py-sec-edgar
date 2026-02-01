# EntitySpine Docker Stack - Start Script
# Starts all EntitySpine services with monitoring

Write-Host "🚀 Starting EntitySpine Docker Stack..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Navigate to monitoring directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Start services
Write-Host "📦 Starting all services (EntitySpine + Monitoring + Health Checks)" -ForegroundColor Yellow
docker compose -f docker-compose.monitoring.yml --profile full up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ EntitySpine stack started successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Access your services:" -ForegroundColor Cyan
    Write-Host "  EntitySpine Web:  http://localhost:5173" -ForegroundColor White
    Write-Host "  EntitySpine API:  http://localhost:8765" -ForegroundColor White
    Write-Host "  EntitySpine Docs: http://localhost:8123" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor Cyan
    Write-Host "  Grafana:     http://localhost:3100 (admin/admin)" -ForegroundColor White
    Write-Host "  Uptime Kuma: http://localhost:3001" -ForegroundColor White
    Write-Host "  Dozzle Logs: http://localhost:9999" -ForegroundColor White
    Write-Host ""
    Write-Host "📝 View logs:" -ForegroundColor Cyan
    Write-Host "  docker compose -f docker-compose.monitoring.yml logs -f" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🛑 Stop services:" -ForegroundColor Cyan
    Write-Host "  docker compose -f docker-compose.monitoring.yml down" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "❌ Failed to start services. Check logs for details." -ForegroundColor Red
    Write-Host "Run: docker compose -f docker-compose.monitoring.yml logs" -ForegroundColor Gray
    exit 1
}
