#!/usr/bin/env python3
"""
Test script for WxTech Weather API
Test the integration with real API calls
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append('backend')

from weather_service import WxTechClient, SolarWeatherAnalyzer
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

async def test_weather_api():
    """Test WxTech API with real calls"""
    
    api_key = os.getenv('WXTECH_API_KEY')
    if not api_key:
        print("❌ WXTECH_API_KEY not found in environment")
        return
    
    print(f"🔑 Using API Key: {api_key[:8]}...")
    
    # Test locations
    test_locations = [
        {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018},
        {"name": "Chiang Mai", "lat": 18.7883, "lon": 98.9853},
        {"name": "Phuket", "lat": 7.8804, "lon": 98.3923}
    ]
    
    async with WxTechClient(api_key) as client:
        for location in test_locations:
            print(f"\n🌍 Testing {location['name']} ({location['lat']}, {location['lon']})")
            
            try:
                # Get weather forecast
                forecast = await client.get_forecast(
                    location['lat'], 
                    location['lon'], 
                    "Asia/Bangkok"
                )
                
                print(f"✅ Weather data received:")
                print(f"   📊 Hourly forecasts: {len(forecast.hourly)}")
                print(f"   📅 Daily forecasts: {len(forecast.daily)}")
                print(f"   🕐 Fetched at: {forecast.fetched_at}")
                
                # Show first few hourly forecasts
                if forecast.hourly:
                    print(f"   🌤️ Next 6 hours:")
                    for i, hour in enumerate(forecast.hourly[:6]):
                        print(f"      {hour.forecast_time.strftime('%H:%M')} - "
                              f"{hour.weather_main} {hour.temperature_c}°C "
                              f"☀️{hour.solar_radiation_wm2}W/m² "
                              f"🌧️{hour.precip_mm_per_hr}mm/h")
                
                # Test solar analysis
                system_kwp = 5.0  # 5kW system
                solar_analysis = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_kwp)
                
                print(f"   ⚡ Solar Forecast (5kW system):")
                print(f"      Next 24h generation: {solar_analysis['next_24h_generation_kwh']} kWh")
                print(f"      Weather quality score: {solar_analysis['weather_quality_score']}/100")
                print(f"      Avg solar radiation: {solar_analysis['avg_solar_radiation_24h']} W/m²")
                
                # Weather impact summary
                impact = SolarWeatherAnalyzer.get_weather_impact_summary(forecast)
                print(f"   🎯 Weather Impact: {impact['impact_level'].upper()}")
                print(f"      Rain 24h: {impact['total_rain_24h']} mm")
                print(f"      Avg temp: {impact['avg_temperature']}°C")
                
            except Exception as e:
                print(f"❌ Error for {location['name']}: {str(e)}")
                import traceback
                traceback.print_exc()

async def test_api_endpoints():
    """Test the actual API endpoints"""
    print("\n🚀 Testing API endpoints...")
    
    # This would normally be done with HTTP requests
    # For now, just test the service functions directly
    
    try:
        from weather_service import get_weather_service
        
        # Test service initialization
        service = get_weather_service()
        print("✅ Weather service initialized")
        
        # Test with Bangkok coordinates
        async with service as client:
            forecast = await client.get_forecast(13.7563, 100.5018)
            print(f"✅ Direct service call successful: {len(forecast.hourly)} hourly forecasts")
            
    except Exception as e:
        print(f"❌ Service test error: {str(e)}")

def test_data_parsing():
    """Test data parsing with mock response"""
    print("\n🧪 Testing data parsing...")
    
    # Mock WxTech response structure
    mock_response = {
        "requestId": "test-123",
        "wxdata": {
            "13.7563/100.5018": {
                "latlon": "13.7563/100.5018",
                "srf": [
                    {
                        "time": "2026-03-30T14:00:00+07:00",
                        "wx": 100,
                        "temp": 32,
                        "prec": 0.0,
                        "arpress": 1013,
                        "wnddir": 8,
                        "wndspd": 3,
                        "rhum": 65,
                        "solrad": 850
                    }
                ],
                "mrf": [
                    {
                        "date": "2026-03-30",
                        "wx": 100,
                        "maxtemp": 35,
                        "mintemp": 26,
                        "prec": 0.5,
                        "pop": 20,
                        "wnddir": 8,
                        "wndspd": 4,
                        "rhum": 70,
                        "solrad": 6500
                    }
                ]
            }
        }
    }
    
    try:
        client = WxTechClient("dummy-key")
        forecast = client._parse_response(mock_response, 13.7563, 100.5018, "Asia/Bangkok")
        
        print(f"✅ Parsing successful:")
        print(f"   Hourly: {len(forecast.hourly)} items")
        print(f"   Daily: {len(forecast.daily)} items")
        
        if forecast.hourly:
            h = forecast.hourly[0]
            print(f"   First hour: {h.weather_main} {h.temperature_c}°C {h.solar_radiation_wm2}W/m²")
            
        if forecast.daily:
            d = forecast.daily[0]
            print(f"   First day: {d.max_temp_c}°C max, {d.precip_probability_pct}% rain chance")
            
    except Exception as e:
        print(f"❌ Parsing error: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🧪 WxTech Weather API Test Suite")
    print("=" * 50)
    
    # Test 1: Data parsing (no API call)
    test_data_parsing()
    
    # Test 2: Real API calls
    await test_weather_api()
    
    # Test 3: Service endpoints
    await test_api_endpoints()
    
    print("\n✅ Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())