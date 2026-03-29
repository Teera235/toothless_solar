# Check deployment and data import status

Write-Host "Checking Solar Panel Detection System Status..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$BACKEND_URL = "https://buildings-api-715107904640.asia-southeast1.run.app"
$FRONTEND_URL = "https://toothless-solar-frontend-715107904640.asia-southeast1.run.app"

# Check Backend API
Write-Host "[Backend API]" -ForegroundColor Yellow
Write-Host "URL: $BACKEND_URL"
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/stats" -Method Get -TimeoutSec 10
    Write-Host "[OK] Status: Online" -ForegroundColor Green
    Write-Host "   Total buildings: $($response.total_buildings)" -ForegroundColor White
    
    if ($response.total_buildings -eq 0) {
        Write-Host "   [WARNING] No buildings imported yet!" -ForegroundColor Yellow
        Write-Host "   Run: .\import-buildings.ps1" -ForegroundColor Gray
    } else {
        Write-Host "   Avg confidence: $($response.confidence.average)" -ForegroundColor Gray
        Write-Host "   Avg area: $($response.area_m2.average) m2" -ForegroundColor Gray
    }
} catch {
    Write-Host "[ERROR] Status: Offline or Error" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
}
Write-Host ""

# Check Frontend
Write-Host "[Frontend]" -ForegroundColor Yellow
Write-Host "URL: $FRONTEND_URL"
try {
    $response = Invoke-WebRequest -Uri $FRONTEND_URL -Method Get -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] Status: Online" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Status: HTTP $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[ERROR] Status: Offline or Error" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "[Summary]" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    $stats = Invoke-RestMethod -Uri "$BACKEND_URL/stats" -Method Get -TimeoutSec 5
    if ($stats.total_buildings -gt 0) {
        Write-Host "[SUCCESS] System is fully operational!" -ForegroundColor Green
        Write-Host "   Buildings imported: $($stats.total_buildings)" -ForegroundColor White
        Write-Host ""
        Write-Host "Ready to use!" -ForegroundColor Green
        Write-Host "   Frontend: $FRONTEND_URL" -ForegroundColor White
        Write-Host "   API: $BACKEND_URL" -ForegroundColor White
    } else {
        Write-Host "[WARNING] System is deployed but no data imported" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Next step: Import buildings data" -ForegroundColor Cyan
        Write-Host "   .\import-buildings.ps1" -ForegroundColor White
    }
} catch {
    Write-Host "[ERROR] System has issues" -ForegroundColor Red
    Write-Host "   Check logs with: gcloud logging read" -ForegroundColor Gray
}

Write-Host ""
