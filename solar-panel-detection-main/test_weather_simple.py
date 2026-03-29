#!/usr/bin/env python3
"""
Simple test for WxTech Weather API using requests
"""

import requests
import json
from datetime import datetime

def test_wxtech_api():
    """Test WxTech API with direct HTTP calls"""
    
    # API configuration
    api_key = "pEfaXCQdGHdWpuSbGM0k2CoxnCWToODm26xfs890"
    base_url = "https://wxtech.weathernews.com/api/v2/global/wx"
    
    # Test locations
    test_locations = [
        {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018},
        {"name": "Chiang Mai", "lat": 18.7883, "lon": 98.9853}
    ]
    
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Solar-Panel-Detection/1.0"
    }
    
    print("🧪 Testing WxTech Weather API")
    print("=" * 50)
    
    for location in test_locations:
        print(f"\n🌍 Testing {location['name']} ({location['lat']}, {location['lon']})")
        
        # Prepare request
        params = {
            "latlon": f"{location['lat']}/{location['lon']}",
            "tz": "Asia/Bangkok"
        }
        
        try:
            # Make API call
            print(f"📡 Calling: {base_url}")
            print(f"📍 Params: {params}")
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📏 Response Size: {len(response.content)} bytes")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API call successful!")
                
                # Parse response structure
                if "wxdata" in data:
                    location_key = f"{location['lat']}/{location['lon']}"
                    if location_key in data["wxdata"]:
                        wx_data = data["wxdata"][location_key]
                        
                        # Count forecasts
                        srf_count = len(wx_data.get("srf", []))
                        mrf_count = len(wx_data.get("mrf", []))
                        
                        print(f"   📊 Short Range Forecast (SRF): {srf_count} hours")
                        print(f"   📅 Medium Range Forecast (MRF): {mrf_count} days")
                        
                        # Show first few SRF entries
                        if wx_data.get("srf"):
                            print("   🌤️ First 3 hourly forecasts:")
                            for i, hour in enumerate(wx_data["srf"][:3]):
                                time_str = hour.get("time", "N/A")
                                temp = hour.get("temp", "N/A")
                                wx_code = hour.get("wx", "N/A")
                                solrad = hour.get("solrad", "N/A")
                                prec = hour.get("prec", "N/A")
                                
                                print(f"      {i+1}. {time_str}")
                                print(f"         Weather: {wx_code}, Temp: {temp}°C")
                                print(f"         Solar: {solrad} W/m², Rain: {prec} mm/h")
                        
                        # Show first MRF entry
                        if wx_data.get("mrf"):
                            print("   📅 First daily forecast:")
                            day = wx_data["mrf"][0]
                            date = day.get("date", "N/A")
                            max_temp = day.get("maxtemp", "N/A")
                            min_temp = day.get("mintemp", "N/A")
                            daily_solrad = day.get("solrad", "N/A")
                            pop = day.get("pop", "N/A")
                            
                            print(f"      Date: {date}")
                            print(f"      Temp: {min_temp}°C - {max_temp}°C")
                            print(f"      Solar: {daily_solrad} Wh/m²/day")
                            print(f"      Rain chance: {pop}%")
                        
                        # Calculate simple solar estimate
                        if wx_data.get("srf"):
                            total_24h_solrad = sum(h.get("solrad", 0) for h in wx_data["srf"][:24])
                            avg_solrad = total_24h_solrad / 24 if wx_data["srf"] else 0
                            
                            # Simple solar calculation for 5kW system
                            system_kwp = 5.0
                            estimated_24h_kwh = (avg_solrad / 1000) * system_kwp * 24 * 0.8  # 80% efficiency
                            
                            print(f"   ⚡ Solar Estimate (5kW system):")
                            print(f"      Avg solar radiation: {avg_solrad:.0f} W/m²")
                            print(f"      Est. 24h generation: {estimated_24h_kwh:.1f} kWh")
                    else:
                        print(f"❌ Location key '{location_key}' not found in response")
                else:
                    print("❌ No 'wxdata' in response")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")

def test_weather_codes():
    """Test weather code mapping"""
    print("\n🔍 Weather Code Reference:")
    codes = {
        100: "Sunny",
        200: "Cloudy", 
        300: "Rain",
        400: "Snow",
        430: "Sleet",
        500: "Clear",
        999: "No Data"
    }
    
    for code, desc in codes.items():
        print(f"   {code}: {desc}")

if __name__ == "__main__":
    test_wxtech_api()
    test_weather_codes()
    print("\n✅ Test completed!")