"""
Weather API Only - Test version without BigQuery dependency
Simple FastAPI server for testing weather integration
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
from weather_service import get_weather_service, SolarWeatherAnalyzer

app = FastAPI(title="Solar Weather API (Test Version)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "Solar Weather API",
        "version": "1.0.0",
        "description": "Weather-enhanced solar analysis",
        "endpoints": {
            "/weather/forecast": "Get weather forecast for location",
            "/solar/forecast": "Get weather-enhanced solar forecast",
            "/test/mock-building": "Test with mock building data"
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "weather_api": "available"}

@app.get("/weather/forecast")
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    timezone: str = Query("Asia/Bangkok", description="Timezone")
):
    """Get weather forecast for location"""
    try:
        async with get_weather_service() as weather_client:
            forecast = await weather_client.get_forecast(lat, lon, timezone)
            
            # Get weather impact summary
            impact = SolarWeatherAnalyzer.get_weather_impact_summary(forecast)
            
            return {
                "location": {"lat": lat, "lon": lon, "timezone": timezone},
                "impact_summary": impact,
                "hourly_count": len(forecast.hourly),
                "daily_count": len(forecast.daily),
                "fetched_at": forecast.fetched_at.isoformat(),
                "next_24h_preview": [
                    {
                        "time": h.forecast_time.isoformat(),
                        "weather": h.weather_main,
                        "temp": h.temperature_c,
                        "solar_radiation": h.solar_radiation_wm2,
                        "rain": h.precip_mm_per_hr
                    }
                    for h in forecast.hourly[:24]
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather forecast error: {str(e)}")

@app.get("/solar/forecast")
async def get_solar_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    system_kwp: float = Query(..., description="System size in kWp"),
    timezone: str = Query("Asia/Bangkok", description="Timezone")
):
    """Get weather-enhanced solar generation forecast"""
    try:
        async with get_weather_service() as weather_client:
            forecast = await weather_client.get_forecast(lat, lon, timezone)
            solar_forecast = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_kwp)
            
            return {
                "location": {"lat": lat, "lon": lon},
                "system_kwp": system_kwp,
                **solar_forecast
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar forecast error: {str(e)}")

# Mock building data for testing
class MockBuildingRequest(BaseModel):
    latitude: float = 13.7563
    longitude: float = 100.5018
    area_m2: float = 100.0
    confidence: float = 0.9

@app.post("/test/mock-building")
async def test_mock_building(request: MockBuildingRequest):
    """Test weather-enhanced solar calculation with mock building"""
    try:
        # Constants
        PANEL_EFFICIENCY = 0.20
        USABLE_ROOF_RATIO = 0.50
        COST_PER_WP = 25
        ELECTRICITY_RATE = 4.18
        CO2_FACTOR = 0.40
        
        # Calculate basic solar metrics
        confidence_adjustment = max(request.confidence, 0.7)
        usable_roof_area = request.area_m2 * USABLE_ROOF_RATIO * confidence_adjustment
        system_size_kwp = usable_roof_area * PANEL_EFFICIENCY
        
        # Get weather forecast
        weather_forecast = None
        try:
            async with get_weather_service() as weather_client:
                forecast = await weather_client.get_forecast(request.latitude, request.longitude)
                solar_forecast = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_size_kwp)
                weather_forecast = {
                    "next_24h_generation": solar_forecast["next_24h_generation_kwh"],
                    "weather_quality_score": solar_forecast["weather_quality_score"],
                    "weekly_outlook": solar_forecast["weekly_outlook"][:3]
                }
        except Exception as e:
            print(f"⚠️ Weather forecast failed: {e}")
        
        # Basic calculations (fallback)
        annual_production = system_size_kwp * 5.06 * 365 * 0.80  # Thailand average
        installation_cost = system_size_kwp * 1000 * COST_PER_WP
        annual_savings = annual_production * ELECTRICITY_RATE
        payback_period = installation_cost / annual_savings if annual_savings > 0 else None
        co2_reduction = annual_production * CO2_FACTOR
        
        return {
            "usable_roof_area": round(usable_roof_area),
            "system_size_kwp": round(system_size_kwp, 1),
            "annual_production_kwh": round(annual_production),
            "installation_cost_thb": round(installation_cost),
            "annual_savings_thb": round(annual_savings),
            "payback_period_years": round(payback_period, 1) if payback_period else None,
            "co2_reduction_kg": round(co2_reduction),
            "co2_reduction_ton": round(co2_reduction / 1000, 1),
            "irradiance_source": "Thailand average (5.06 kWh/m²/day)",
            "irradiance_kwh_m2_day": 5.06,
            "weather_forecast": weather_forecast,
            "assumptions": {
                "panel_efficiency": PANEL_EFFICIENCY,
                "usable_roof_ratio": USABLE_ROOF_RATIO,
                "cost_per_wp": COST_PER_WP,
                "electricity_rate": ELECTRICITY_RATE,
                "co2_factor": CO2_FACTOR,
                "calculation_method": "simplified_with_weather"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mock building calculation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)