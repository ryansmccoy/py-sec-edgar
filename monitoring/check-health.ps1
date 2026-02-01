# Spine Ecosystem Health Check Script
# Checks all services and reports their status

param(
    [switch]$Detailed,
    [switch]$Json,
    [switch]$Watch,
    [int]$WatchInterval = 5
)

$services = @(
    @{ Name = "Capture Spine Web"; Url = "http://localhost:3000"; Container = "spine-dev-frontend"; Critical = $true; Method = "GET" }
    @{ Name = "Capture Spine API"; Url = "http://localhost:8000/docs"; Container = "spine-dev-api"; Critical = $true; Method = "GET" }
    @{ Name = "EntitySpine Web"; Url = "http://localhost:5173"; Container = "spine-entityspine-web"; Critical = $false; Method = "GET" }
    @{ Name = "EntitySpine API"; Url = "http://localhost:8765/health"; Container = "spine-entityspine-api"; Critical = $false; Method = "GET" }
    @{ Name = "EntitySpine Docs"; Url = "http://localhost:8123"; Container = "spine-entityspine-docs"; Critical = $false; Method = "GET" }
    @{ Name = "GenAI Spine Web"; Url = "http://localhost:5173"; Container = "genai-spine-frontend"; Critical = $false; Method = "GET" }
    @{ Name = "GenAI Spine API"; Url = "http://localhost:8100/docs"; Container = "genai-spine-api"; Critical = $false; Method = "GET" }
    @{ Name = "Ollama"; Url = "http://localhost:11434/api/tags"; Container = "spine-ollama"; Critical = $false; Method = "GET" }
    @{ Name = "Grafana"; Url = "http://localhost:3100/api/health"; Container = "spine-grafana"; Critical = $false; Method = "GET" }
    @{ Name = "Uptime Kuma"; Url = "http://localhost:3001"; Container = "uptime-kuma"; Critical = $false; Method = "GET" }
    @{ Name = "Dozzle"; Url = "http://localhost:9999"; Container = "dozzle"; Critical = $false; Method = "GET" }
    @{ Name = "Loki"; Url = "http://localhost:3101/loki/api/v1/status/buildinfo"; Container = "spine-loki"; Critical = $false; Method = "GET" }
    @{ Name = "Elasticsearch"; Url = "http://localhost:9200/_cluster/health"; Container = "spine-elasticsearch"; Critical = $false; Method = "GET" }
    @{ Name = "Kibana"; Url = "http://localhost:5601/api/status"; Container = "spine-kibana"; Critical = $false; Method = "GET" }
)

function Test-ServiceHealth {
    param($Service)

    $result = @{
        Name = $Service.Name
        Url = $Service.Url
        Container = $Service.Container
        Critical = $Service.Critical
        HttpStatus = $null
        ContainerStatus = $null
        Healthy = $false
        ResponseTime = $null
        Error = $null
    }

    # Check container status
    try {
        $containerInfo = docker inspect $Service.Container 2>$null | ConvertFrom-Json
        if ($containerInfo) {
            $result.ContainerStatus = $containerInfo[0].State.Status

            # Check health if defined
            if ($containerInfo[0].State.Health) {
                $healthStatus = $containerInfo[0].State.Health.Status
                $result.ContainerStatus = "$($result.ContainerStatus) ($healthStatus)"
            }
        } else {
            $result.ContainerStatus = "not found"
        }
    } catch {
        $result.ContainerStatus = "error"
        $result.Error = $_.Exception.Message
    }

    # Check HTTP endpoint
    try {
        $method = if ($Service.Method) { $Service.Method } else { "Head" }
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-WebRequest -Uri $Service.Url -Method $method -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $sw.Stop()

        $result.HttpStatus = $response.StatusCode
        $result.ResponseTime = [math]::Round($sw.Elapsed.TotalMilliseconds, 0)
        $result.Healthy = $response.StatusCode -eq 200
    } catch {
        $sw.Stop()
        $result.ResponseTime = [math]::Round($sw.Elapsed.TotalMilliseconds, 0)

        if ($_.Exception.Response) {
            $result.HttpStatus = [int]$_.Exception.Response.StatusCode
        } else {
            $result.HttpStatus = "unreachable"
        }

        $result.Error = $_.Exception.Message
    }

    return $result
}

function Show-HealthReport {
    param($Results)

    Write-Host ""
    Write-Host "Spine Ecosystem Health Check" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""

    $online = @($Results | Where-Object { $_.Healthy }).Count
    $total = $Results.Count
    $critical = @($Results | Where-Object { $_.Critical -and -not $_.Healthy }).Count

    # Summary
    Write-Host "Summary: " -NoNewline
    if ($critical -eq 0) {
        Write-Host "$online/$total services online" -ForegroundColor Green
    } else {
        Write-Host "$online/$total services online " -NoNewline -ForegroundColor Yellow
        Write-Host "- $critical critical services down!" -ForegroundColor Red
    }
    Write-Host ""

    # Group by category
    $categories = @{
        "Core Applications" = @("Capture Spine Web", "Capture Spine API")
        "EntitySpine" = @("EntitySpine Web", "EntitySpine API", "EntitySpine Docs")
        "GenAI Spine" = @("GenAI Spine Web", "GenAI Spine API", "Ollama")
        "Monitoring" = @("Grafana", "Uptime Kuma", "Dozzle", "Loki")
        "Search" = @("Elasticsearch", "Kibana")
    }

    foreach ($category in $categories.Keys) {
        $categoryServices = $Results | Where-Object { $categories[$category] -contains $_.Name }

        if ($categoryServices) {
            Write-Host ""
            Write-Host "$category" -ForegroundColor Yellow
            Write-Host ("-" * 60) -ForegroundColor DarkGray

            foreach ($svc in $categoryServices) {
                $icon = if ($svc.Healthy) { "[OK]" } else { "[!!]" }
                $color = if ($svc.Healthy) { "Green" } elseif ($svc.Critical) { "Red" } else { "Yellow" }

                Write-Host "  $icon " -NoNewline -ForegroundColor $color
                Write-Host $svc.Name.PadRight(25) -NoNewline -ForegroundColor $color

                if ($Detailed) {
                    Write-Host " | " -NoNewline -ForegroundColor DarkGray
                    Write-Host "HTTP: " -NoNewline -ForegroundColor DarkGray
                    Write-Host ($svc.HttpStatus -as [string]).PadRight(12) -NoNewline -ForegroundColor $color
                    Write-Host " | " -NoNewline -ForegroundColor DarkGray
                    Write-Host "Container: " -NoNewline -ForegroundColor DarkGray
                    Write-Host $svc.ContainerStatus.PadRight(20) -NoNewline -ForegroundColor $color

                    if ($svc.ResponseTime) {
                        Write-Host " | " -NoNewline -ForegroundColor DarkGray
                        Write-Host "$($svc.ResponseTime)ms" -ForegroundColor Cyan
                    } else {
                        Write-Host ""
                    }

                    if ($svc.Error -and -not $svc.Healthy) {
                        Write-Host "       Error: " -NoNewline -ForegroundColor DarkGray
                        Write-Host $svc.Error -ForegroundColor Red
                    }
                } else {
                    Write-Host " [$($svc.HttpStatus)]" -ForegroundColor $color
                }
            }
            Write-Host ""
        }
    }

    # Recommendations
    if ($critical -gt 0) {
        Write-Host "WARNING: CRITICAL ISSUES DETECTED" -ForegroundColor Red
        Write-Host ""
        Write-Host "Critical services are down. Try:" -ForegroundColor Yellow
        Write-Host "  1. Check logs: docker logs <container-name>" -ForegroundColor White
        Write-Host "  2. Restart: docker compose -f monitoring/docker-compose.monitoring.yml restart" -ForegroundColor White
        Write-Host "  3. Rebuild: docker compose -f monitoring/docker-compose.monitoring.yml up -d --build" -ForegroundColor White
        Write-Host ""
    }

    # Quick actions
    Write-Host "Quick Links:" -ForegroundColor Cyan
    Write-Host "  Dashboard: http://localhost:3000/monitoring/ecosystem" -ForegroundColor White
    Write-Host "  Logs:      http://localhost:9999 (Dozzle)" -ForegroundColor White
    Write-Host "  Grafana:   http://localhost:3100" -ForegroundColor White
    Write-Host "  Health:    http://localhost:3001 (Uptime Kuma)" -ForegroundColor White
    Write-Host ""
}

function Show-JsonReport {
    param($Results)

    $report = @{
        timestamp = (Get-Date).ToString("o")
        summary = @{
            total = $Results.Count
            healthy = @($Results | Where-Object { $_.Healthy }).Count
            unhealthy = @($Results | Where-Object { -not $_.Healthy }).Count
            critical_down = @($Results | Where-Object { $_.Critical -and -not $_.Healthy }).Count
        }
        services = $Results
    }

    $report | ConvertTo-Json -Depth 10
}

# Main execution
do {
    if ($Watch) {
        Clear-Host
    }

    Write-Host "Checking services..." -ForegroundColor Cyan
    $results = @()

    foreach ($service in $services) {
        $results += Test-ServiceHealth -Service $service
    }

    if ($Json) {
        Show-JsonReport -Results $results
    } else {
        Show-HealthReport -Results $results
    }

    if ($Watch) {
        Write-Host "Refreshing in $WatchInterval seconds... (Ctrl+C to stop)" -ForegroundColor DarkGray
        Start-Sleep -Seconds $WatchInterval
    }
} while ($Watch)
