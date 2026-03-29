# Test weather API endpoints after backend is running
Write-Host "🧪 Testing Weather API Endpoints" -ForegroundColor Cyan
Write-Host "Make sure backend is running on http://localhost:8080" -ForegroundColor Yellow
Write-Host ""

$baseUrl = "http://localhost:8080"
$testLocations = @(
    @{ Name = "Bangkok"; Lat = 13.7563; Lon = 100.5018 },
    @{ Name = "Chiang Mai"; Lat = 18.7883; Lon = 98.9853 }
)

foreach ($location in $testLocations) {
    Write-Host "🌍 Testing $($location.Name)" -ForegroundColor Yellow
    
    # Test 1: Weather forecast endpoint
    Write-Host "  📡 Testing /weather/forecast..." -ForegroundColor Gray
    $weatherUrl = "$baseUrl/weather/forecast?lat=$($location.Lat)&lon=$($location.Lon)"
    
    try {
        $response = Invoke-RestMethod -Uri $weatherUrl -Method Get -TimeoutSec 10
        Write-Host "  ✅ Weather forecast: $($response.hourly_count) hours, $($response.daily_count) days" -ForegroundColor Green
        Write-Host "     Impact: $($response.impact_summary.impact_level)" -ForegroundColor White
    }
    catch {
        Write-Host "  ❌ Weather forecast failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 2: Solar forecast endpoint
    Write-Host "  ⚡ Testing /solar/forecast..." -ForegroundColor Gray
    $solarUrl = "$baseUrl/solar/forecast?lat=$($location.Lat)&lon=$($location.Lon)&system_kwp=5"
    
    try {
        $response = Invoke-RestMethod -Uri $solarUrl -Method Get -TimeoutSec 10
        Write-Host "  ✅ Solar forecast: $($response.next_24h_generation_kwh) kWh next 24h" -ForegroundColor Green
        Write-Host "     Weather score: $($response.weather_quality_score)/100" -ForegroundColor White
    }
    catch {
        Write-Host "  ❌ Solar forecast failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 3: Enhanced solar calculation
    Write-Host "  🏠 Testing enhanced /solar/calculate..." -ForegroundColor Gray
    $calcUrl = "$baseUrl/solar/calculate"
    $body = @{
        latitude = $location.Lat
        longitude = $location.Lon
        area_m2 = 100
        confidence = 0.9
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri $calcUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 15
        Write-Host "  ✅ Solar calculation: $($response.system_size_kwp) kWp system" -ForegroundColor Green
        Write-Host "     Annual: $($response.annual_production_kwh) kWh" -ForegroundColor White
        if ($response.weather_forecast) {
            Write-Host "     Weather enhanced: $($response.weather_forecast.next_24h_generation) kWh next 24h" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "  ❌ Solar calculation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "✅ Endpoint testing completed!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Frontend Integration:" -ForegroundColor Cyan
Write-Host "  1. Start frontend: npm start (in frontend folder)" -ForegroundColor Gray
Write-Host "  2. Click weather button on map" -ForegroundColor Gray
Write-Host "  3. Click buildings to see weather-enhanced solar analysis" -ForegroundColor Gray