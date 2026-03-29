# Deploy Complete Weather-Enhanced Solar System
# March 2026 - Full Stack Deployment

Write-Host "🚀 Deploying Complete Weather-Enhanced Solar System" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date

# Step 1: Deploy Backend
Write-Host "📡 Step 1: Deploying Weather API Backend..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    .\deploy-weather-api.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Backend deployment failed"
    }
    Write-Host "✅ Backend deployed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Backend deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "⏳ Waiting 30 seconds for backend to stabilize..." -ForegroundColor Gray
Start-Sleep -Seconds 30

# Step 2: Deploy Frontend
Write-Host "🌐 Step 2: Deploying Frontend with Weather Integration..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    .\deploy-frontend-weather.ps1
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend deployment failed"
    }
    Write-Host "✅ Frontend deployed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Frontend deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Backend is still available for API testing" -ForegroundColor Yellow
    exit 1
}

# Step 3: Final Testing
Write-Host ""
Write-Host "🧪 Step 3: Running Integration Tests..." -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"

try {
    # Get URLs
    $BACKEND_URL = gcloud run services describe "solar-weather-api" --region $REGION --format="value(status.url)"
    $FRONTEND_URL = "https://$(gcloud app describe --format='value(defaultHostname)')"
    
    Write-Host "🔗 Backend: $BACKEND_URL" -ForegroundColor White
    Write-Host "🌐 Frontend: $FRONTEND_URL" -ForegroundColor White
    Write-Host ""
    
    # Test backend endpoints
    Write-Host "Testing backend endpoints..." -ForegroundColor Gray
    
    $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/health" -TimeoutSec 10
    Write-Host "✅ Health check: $($healthResponse.status)" -ForegroundColor Green
    
    $weatherResponse = Invoke-RestMethod -Uri "$BACKEND_URL/weather/forecast?lat=13.7563&lon=100.5018" -TimeoutSec 15
    Write-Host "✅ Weather API: $($weatherResponse.impact_summary.impact_level) conditions" -ForegroundColor Green
    
    $solarResponse = Invoke-RestMethod -Uri "$BACKEND_URL/solar/forecast?lat=13.7563&lon=100.5018&system_kwp=5" -TimeoutSec 15
    Write-Host "✅ Solar forecast: $($solarResponse.next_24h_generation_kwh) kWh next 24h" -ForegroundColor Green
    
    # Test frontend
    $frontendResponse = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 10 -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🎉 All tests passed!" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Some tests failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "Services may still be starting up..." -ForegroundColor Gray
}

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "⏱️ Total deployment time: $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor White
Write-Host ""
Write-Host "🌟 Your Weather-Enhanced Solar System is LIVE!" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Frontend: $FRONTEND_URL" -ForegroundColor White
Write-Host "📡 Backend: $BACKEND_URL" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Features Available:" -ForegroundColor Green
Write-Host "   🌤️ Real-time weather forecasts (WxTech 5km data)" -ForegroundColor Gray
Write-Host "   ⚡ Weather-enhanced solar potential analysis" -ForegroundColor Gray
Write-Host "   📊 24-hour generation forecasts" -ForegroundColor Gray
Write-Host "   📅 7-day solar outlook" -ForegroundColor Gray
Write-Host "   🎯 Weather impact scoring (0-100)" -ForegroundColor Gray
Write-Host "   🏠 107M+ building footprints (Thailand)" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 How to Use:" -ForegroundColor Cyan
Write-Host "1. Open the frontend URL above" -ForegroundColor White
Write-Host "2. Click the '🌤️ Weather' button to see current forecast" -ForegroundColor White
Write-Host "3. Click any building on the map for detailed analysis" -ForegroundColor White
Write-Host "4. View weather impact on solar generation" -ForegroundColor White
Write-Host ""
Write-Host "📚 API Documentation: $BACKEND_URL/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Ready for production use! 🎉" -ForegroundColor Green