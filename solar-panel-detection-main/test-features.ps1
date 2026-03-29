# Test New Features
# This script tests all new features to ensure they work correctly

Write-Host "🧪 Testing Solar Panel Detection Features" -ForegroundColor Green
Write-Host ""

$API_URL = "https://buildings-api-715107904640.asia-southeast1.run.app"
$FRONTEND_URL = "https://toothless-solar-frontend-715107904640.asia-southeast1.run.app"

# Test 1: API Health Check
Write-Host "1️⃣ Testing API Health..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$API_URL/" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ API is healthy" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ API health check failed: $_" -ForegroundColor Red
}

# Test 2: Stats Endpoint
Write-Host ""
Write-Host "2️⃣ Testing Stats Endpoint..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$API_URL/stats" -UseBasicParsing
    $stats = $response.Content | ConvertFrom-Json
    Write-Host "   ✅ Total buildings: $($stats.total_buildings.ToString('N0'))" -ForegroundColor Green
    Write-Host "   ✅ Average confidence: $($stats.confidence.average)" -ForegroundColor Green
    Write-Host "   ✅ Average area: $($stats.area_m2.average) m²" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Stats endpoint failed: $_" -ForegroundColor Red
}

# Test 3: Buildings BBox Endpoint
Write-Host ""
Write-Host "3️⃣ Testing Buildings BBox Endpoint..." -ForegroundColor Cyan
try {
    $bbox = "min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"
    $response = Invoke-WebRequest -Uri "$API_URL/buildings/bbox?$bbox" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "   ✅ Total in area: $($data.total.ToString('N0'))" -ForegroundColor Green
    Write-Host "   ✅ Buildings returned: $($data.buildings.Count)" -ForegroundColor Green
    
    if ($data.buildings.Count -gt 0) {
        $building = $data.buildings[0]
        Write-Host "   ✅ Sample building:" -ForegroundColor Green
        Write-Host "      - ID: $($building.id)" -ForegroundColor White
        Write-Host "      - Area: $($building.area_m2) m²" -ForegroundColor White
        Write-Host "      - Confidence: $($building.confidence * 100)%" -ForegroundColor White
        Write-Host "      - Has geometry: $($null -ne $building.geometry)" -ForegroundColor White
    }
} catch {
    Write-Host "   ❌ Buildings bbox endpoint failed: $_" -ForegroundColor Red
}

# Test 4: Frontend Accessibility
Write-Host ""
Write-Host "4️⃣ Testing Frontend Accessibility..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri $FRONTEND_URL -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Frontend is accessible" -ForegroundColor Green
        Write-Host "   ✅ Status: $($response.StatusCode)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Frontend accessibility failed: $_" -ForegroundColor Red
}

# Test 5: CORS Configuration
Write-Host ""
Write-Host "5️⃣ Testing CORS Configuration..." -ForegroundColor Cyan
try {
    $headers = @{
        "Origin" = $FRONTEND_URL
    }
    $response = Invoke-WebRequest -Uri "$API_URL/stats" -Headers $headers -UseBasicParsing
    $corsHeader = $response.Headers["Access-Control-Allow-Origin"]
    if ($corsHeader) {
        Write-Host "   ✅ CORS is configured: $corsHeader" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  CORS header not found (may still work)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ CORS test failed: $_" -ForegroundColor Red
}

# Test 6: Performance Test
Write-Host ""
Write-Host "6️⃣ Testing API Performance..." -ForegroundColor Cyan
try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri "$API_URL/stats" -UseBasicParsing
    $stopwatch.Stop()
    $elapsed = $stopwatch.ElapsedMilliseconds
    
    if ($elapsed -lt 1000) {
        Write-Host "   ✅ Response time: ${elapsed}ms (Excellent)" -ForegroundColor Green
    } elseif ($elapsed -lt 3000) {
        Write-Host "   ✅ Response time: ${elapsed}ms (Good)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Response time: ${elapsed}ms (Slow)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Performance test failed: $_" -ForegroundColor Red
}

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📊 Test Summary" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ All critical features tested" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: $FRONTEND_URL" -ForegroundColor White
Write-Host "   API: $API_URL" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open frontend in browser" -ForegroundColor White
Write-Host "   2. Test dashboard visibility" -ForegroundColor White
Write-Host "   3. Test search and filter" -ForegroundColor White
Write-Host "   4. Test building selection" -ForegroundColor White
Write-Host "   5. Test responsive design on mobile" -ForegroundColor White
Write-Host ""
