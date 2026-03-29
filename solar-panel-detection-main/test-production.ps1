# Test Production Weather-Enhanced Solar System
# March 2026 - Comprehensive Testing

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"

Write-Host "🧪 Testing Production Weather-Enhanced Solar System" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# Get service URLs
Write-Host "🔍 Getting service URLs..." -ForegroundColor Yellow
try {
    $BACKEND_URL = gcloud run services describe "solar-weather-api" --region $REGION --format="value(status.url)"
    $FRONTEND_URL = "https://$(gcloud app describe --format='value(defaultHostname)')"
    
    Write-Host "✅ Backend: $BACKEND_URL" -ForegroundColor Green
    Write-Host "✅ Frontend: $FRONTEND_URL" -ForegroundColor Green
}
catch {
    Write-Host "❌ Could not get service URLs. Are services deployed?" -ForegroundColor Red
    Write-Host "Run: .\deploy-all-weather.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test locations
$testLocations = @(
    @{ Name = "Bangkok"; Lat = 13.7563; Lon = 100.5018 },
    @{ Name = "Chiang Mai"; Lat = 18.7883; Lon = 98.9853 },
    @{ Name = "Phuket"; Lat = 7.8804; Lon = 98.3923 }
)

# Test 1: Backend Health
Write-Host "🏥 Test 1: Backend Health Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/health" -TimeoutSec 10
    Write-Host "✅ Status: $($healthResponse.status)" -ForegroundColor Green
    Write-Host "✅ Weather API: $($healthResponse.weather_api)" -ForegroundColor Green
}
catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 2: Weather Forecasts
Write-Host "🌤️ Test 2: Weather Forecast API" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

foreach ($location in $testLocations) {
    Write-Host "Testing $($location.Name)..." -ForegroundColor Gray
    
    try {
        $weatherUrl = "$BACKEND_URL/weather/forecast?lat=$($location.Lat)&lon=$($location.Lon)"
        $weatherResponse = Invoke-RestMethod -Uri $weatherUrl -TimeoutSec 15
        
        Write-Host "✅ $($location.Name): $($weatherResponse.impact_summary.impact_level) conditions" -ForegroundColor Green
        Write-Host "   📊 $($weatherResponse.hourly_count) hourly + $($weatherResponse.daily_count) daily forecasts" -ForegroundColor Gray
        Write-Host "   🌡️ Avg temp: $($weatherResponse.impact_summary.avg_temperature)°C" -ForegroundColor Gray
        Write-Host "   ☀️ Solar: $($weatherResponse.impact_summary.avg_solar_radiation) W/m²" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ $($location.Name) failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 3: Solar Forecasts
Write-Host "⚡ Test 3: Solar Forecast API" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

foreach ($location in $testLocations) {
    Write-Host "Testing $($location.Name) (5kW system)..." -ForegroundColor Gray
    
    try {
        $solarUrl = "$BACKEND_URL/solar/forecast?lat=$($location.Lat)&lon=$($location.Lon)&system_kwp=5"
        $solarResponse = Invoke-RestMethod -Uri $solarUrl -TimeoutSec 15
        
        Write-Host "✅ $($location.Name): $($solarResponse.next_24h_generation_kwh) kWh next 24h" -ForegroundColor Green
        Write-Host "   🎯 Weather score: $($solarResponse.weather_quality_score)/100" -ForegroundColor Gray
        Write-Host "   📅 Weekly outlook: $($solarResponse.weekly_outlook.Count) days" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ $($location.Name) failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 4: Mock Building Analysis
Write-Host "🏠 Test 4: Mock Building Analysis" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$mockBuildings = @(
    @{ Name = "Small House"; Area = 50; Lat = 13.7563; Lon = 100.5018 },
    @{ Name = "Medium House"; Area = 100; Lat = 18.7883; Lon = 98.9853 },
    @{ Name = "Large Building"; Area = 500; Lat = 7.8804; Lon = 98.3923 }
)

foreach ($building in $mockBuildings) {
    Write-Host "Testing $($building.Name) ($($building.Area) m²)..." -ForegroundColor Gray
    
    try {
        $body = @{
            latitude = $building.Lat
            longitude = $building.Lon
            area_m2 = $building.Area
            confidence = 0.9
        } | ConvertTo-Json
        
        $buildingResponse = Invoke-RestMethod -Uri "$BACKEND_URL/test/mock-building" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 15
        
        Write-Host "✅ $($building.Name): $($buildingResponse.system_size_kwp) kWp system" -ForegroundColor Green
        Write-Host "   💰 Annual savings: ฿$($buildingResponse.annual_savings_thb.ToString('N0'))" -ForegroundColor Gray
        Write-Host "   🌱 CO₂ reduction: $($buildingResponse.co2_reduction_ton) tons/year" -ForegroundColor Gray
        
        if ($buildingResponse.weather_forecast) {
            Write-Host "   🌤️ Weather forecast: $($buildingResponse.weather_forecast.next_24h_generation) kWh next 24h" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ $($building.Name) failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# Test 5: Frontend Accessibility
Write-Host "🌐 Test 5: Frontend Accessibility" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

try {
    $frontendResponse = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 10 -UseBasicParsing
    
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend is accessible" -ForegroundColor Green
        Write-Host "   📄 Content length: $($frontendResponse.Content.Length) bytes" -ForegroundColor Gray
        
        # Check for key content
        if ($frontendResponse.Content -match "Solar Panel Detection" -or $frontendResponse.Content -match "Buildings") {
            Write-Host "✅ Content looks correct" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Content might be incomplete" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "❌ Frontend test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 6: Performance Check
Write-Host "⚡ Test 6: Performance Check" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

$performanceTests = @(
    @{ Name = "Health Check"; Url = "$BACKEND_URL/health" },
    @{ Name = "Weather Forecast"; Url = "$BACKEND_URL/weather/forecast?lat=13.7563&lon=100.5018" },
    @{ Name = "Solar Forecast"; Url = "$BACKEND_URL/solar/forecast?lat=13.7563&lon=100.5018&system_kwp=5" }
)

foreach ($test in $performanceTests) {
    Write-Host "Testing $($test.Name)..." -ForegroundColor Gray
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    
    try {
        $response = Invoke-RestMethod -Uri $test.Url -TimeoutSec 30
        $stopwatch.Stop()
        
        $responseTime = $stopwatch.ElapsedMilliseconds
        $status = if ($responseTime -lt 1000) { "✅" } elseif ($responseTime -lt 3000) { "⚠️" } else { "❌" }
        
        Write-Host "$status $($test.Name): $responseTime ms" -ForegroundColor $(if ($responseTime -lt 1000) { "Green" } elseif ($responseTime -lt 3000) { "Yellow" } else { "Red" })
    }
    catch {
        $stopwatch.Stop()
        Write-Host "❌ $($test.Name): Failed ($($stopwatch.ElapsedMilliseconds) ms)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎉 Production Testing Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Your system is live at:" -ForegroundColor White
Write-Host "   Frontend: $FRONTEND_URL" -ForegroundColor Cyan
Write-Host "   Backend: $BACKEND_URL" -ForegroundColor Cyan
Write-Host "   API Docs: $BACKEND_URL/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Ready for users! Share the frontend URL to start using the weather-enhanced solar analysis." -ForegroundColor Green