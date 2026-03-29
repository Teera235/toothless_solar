# Test WxTech Weather API using PowerShell
# This script tests the API integration without Python dependencies

Write-Host "🧪 Testing WxTech Weather API" -ForegroundColor Cyan
Write-Host "=================================================="

# API Configuration
$apiKey = "pEfaXCQdGHdWpuSbGM0k2CoxnCWToODm26xfs890"
$baseUrl = "https://wxtech.weathernews.com/api/v2/global/wx"

# Test locations
$locations = @(
    @{ Name = "Bangkok"; Lat = 13.7563; Lon = 100.5018 }
    @{ Name = "Chiang Mai"; Lat = 18.7883; Lon = 98.9853 }
)

# Headers
$headers = @{
    "X-API-Key" = $apiKey
    "User-Agent" = "Solar-Panel-Detection/1.0"
}

foreach ($location in $locations) {
    Write-Host ""
    Write-Host "🌍 Testing $($location.Name) ($($location.Lat), $($location.Lon))" -ForegroundColor Yellow
    
    # Build URL with parameters
    $latlon = "$($location.Lat)/$($location.Lon)"
    $url = "$baseUrl" + "?latlon=$latlon&tz=Asia/Bangkok"
    
    Write-Host "📡 Calling: $url" -ForegroundColor Gray
    
    try {
        # Make API call
        $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get -TimeoutSec 10
        
        Write-Host "✅ API call successful!" -ForegroundColor Green
        
        # Check response structure
        if ($response.wxdata) {
            $locationKey = "$($location.Lat)/$($location.Lon)"
            $wxData = $response.wxdata.$locationKey
            
            if ($wxData) {
                # Count forecasts
                $srfCount = if ($wxData.srf) { $wxData.srf.Count } else { 0 }
                $mrfCount = if ($wxData.mrf) { $wxData.mrf.Count } else { 0 }
                
                Write-Host "   📊 Short Range Forecast (SRF): $srfCount hours" -ForegroundColor White
                Write-Host "   📅 Medium Range Forecast (MRF): $mrfCount days" -ForegroundColor White
                
                # Show first hourly forecast
                if ($wxData.srf -and $wxData.srf.Count -gt 0) {
                    $hour = $wxData.srf[0]
                    Write-Host "   🌤️ First hourly forecast:" -ForegroundColor White
                    Write-Host "      Time: $($hour.time)" -ForegroundColor Gray
                    Write-Host "      Weather: $($hour.wx), Temp: $($hour.temp)°C" -ForegroundColor Gray
                    Write-Host "      Solar: $($hour.solrad) W/m², Rain: $($hour.prec) mm/h" -ForegroundColor Gray
                }
                
                # Show first daily forecast
                if ($wxData.mrf -and $wxData.mrf.Count -gt 0) {
                    $day = $wxData.mrf[0]
                    Write-Host "   📅 First daily forecast:" -ForegroundColor White
                    Write-Host "      Date: $($day.date)" -ForegroundColor Gray
                    Write-Host "      Temp: $($day.mintemp)°C - $($day.maxtemp)°C" -ForegroundColor Gray
                    Write-Host "      Solar: $($day.solrad) Wh/m²/day" -ForegroundColor Gray
                    Write-Host "      Rain chance: $($day.pop)%" -ForegroundColor Gray
                }
            }
            else {
                Write-Host "❌ Location key not found in response" -ForegroundColor Red
            }
        }
        else {
            Write-Host "❌ No wxdata in response" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ API Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ Test completed!" -ForegroundColor Green