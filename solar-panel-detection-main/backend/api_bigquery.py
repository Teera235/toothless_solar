"""
Buildings API - Query from BigQuery directly
Fast access to 107M+ building footprints with weather-enhanced solar analysis
"""

from fastapi import FastAPI, Query, HTTPException
from google.cloud import bigquery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
from weather_service import get_weather_service, SolarWeatherAnalyzer

app = FastAPI(title="Toothless Solar Buildings API (BigQuery)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BigQuery client
PROJECT_ID = os.getenv('GCP_PROJECT', 'trim-descent-452802-t2')
DATASET = 'openbuildings'
TABLE = 'thailand_raw'
bq_client = bigquery.Client(project=PROJECT_ID)

@app.get("/")
def root():
    return {
        "name": "Toothless Solar Buildings API",
        "version": "2.1.0",
        "source": "BigQuery + WxTech Weather",
        "buildings": "107M+ in Thailand",
        "endpoints": {
            "/stats": "Get database statistics",
            "/buildings/bbox": "Get buildings in bounding box",
            "/buildings/nearby": "Get buildings near a point",
            "/weather/forecast": "Get weather forecast for location",
            "/solar/calculate": "Calculate solar potential",
            "/solar/forecast": "Get weather-enhanced solar forecast"
        }
    }

@app.get("/stats")
def get_stats():
    """Get database statistics"""
    try:
        query = f"""
            SELECT 
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                AVG(area_in_meters) as avg_area,
                MIN(area_in_meters) as min_area,
                MAX(area_in_meters) as max_area,
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
        """
        
        result = list(bq_client.query(query).result())[0]
        
        return {
            "total_buildings": int(result['total']),
            "confidence": {
                "average": round(float(result['avg_confidence']), 3),
                "min": round(float(result['min_confidence']), 3),
                "max": round(float(result['max_confidence']), 3)
            },
            "area_m2": {
                "average": round(float(result['avg_area']), 1),
                "min": round(float(result['min_area']), 1),
                "max": round(float(result['max_area']), 1)
            },
            "extent": {
                "latitude": [float(result['min_lat']), float(result['max_lat'])],
                "longitude": [float(result['min_lon']), float(result['max_lon'])]
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/buildings/bbox")
def get_buildings_bbox(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lon: float = Query(..., description="Maximum longitude"),
    limit: int = Query(1000, le=5000, description="Max results"),
    min_confidence: float = Query(0.7, description="Minimum confidence")
):
    """Get buildings within bounding box"""
    try:
        query = f"""
            SELECT 
                full_plus_code as open_buildings_id,
                latitude,
                longitude,
                area_in_meters as area_m2,
                confidence,
                ST_ASGEOJSON(ST_GEOGFROMTEXT(geometry)) as geometry
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE latitude BETWEEN {min_lat} AND {max_lat}
            AND longitude BETWEEN {min_lon} AND {max_lon}
            AND confidence >= {min_confidence}
            ORDER BY area_in_meters DESC
            LIMIT {limit}
        """
        
        results = list(bq_client.query(query).result())
        
        # Count total (for pagination)
        count_query = f"""
            SELECT COUNT(*) as total
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE latitude BETWEEN {min_lat} AND {max_lat}
            AND longitude BETWEEN {min_lon} AND {max_lon}
            AND confidence >= {min_confidence}
        """
        total = list(bq_client.query(count_query).result())[0]['total']
        
        buildings = []
        for row in results:
            import json
            buildings.append({
                "id": hash(row['open_buildings_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'] or f"OB_{hash(row['geometry']) % 10000000}",
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence']),
                "geometry": json.loads(row['geometry']) if row['geometry'] else None
            })
        
        return {
            "total": int(total),
            "buildings": buildings
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "buildings": []}

@app.get("/buildings/nearby")
def get_buildings_nearby(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_m: float = Query(500, description="Radius in meters"),
    limit: int = Query(100, le=1000),
    min_confidence: float = Query(0.7)
):
    """Get buildings near a point"""
    try:
        # Simple bbox approximation (1 degree ≈ 111km)
        lat_delta = radius_m / 111000
        lon_delta = radius_m / (111000 * abs(lat))
        
        query = f"""
            SELECT 
                full_plus_code as open_buildings_id,
                latitude,
                longitude,
                area_in_meters as area_m2,
                confidence,
                geometry,
                ST_DISTANCE(
                    ST_GEOGPOINT(longitude, latitude),
                    ST_GEOGPOINT({lon}, {lat})
                ) as distance_m
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            WHERE latitude BETWEEN {lat - lat_delta} AND {lat + lat_delta}
            AND longitude BETWEEN {lon - lon_delta} AND {lon + lon_delta}
            AND confidence >= {min_confidence}
            AND ST_DISTANCE(
                ST_GEOGPOINT(longitude, latitude),
                ST_GEOGPOINT({lon}, {lat})
            ) <= {radius_m}
            ORDER BY distance_m
            LIMIT {limit}
        """
        
        results = list(bq_client.query(query).result())
        
        buildings = []
        for row in results:
            buildings.append({
                "id": hash(row['open_buildings_id']) % 1000000,
                "open_buildings_id": row['open_buildings_id'] or f"OB_{hash(row['geometry']) % 10000000}",
                "latitude": float(row['latitude']),
                "longitude": float(row['longitude']),
                "area_m2": float(row['area_m2']),
                "confidence": float(row['confidence']),
                "geometry": row['geometry'],
                "distance_m": float(row['distance_m'])
            })
        
        return {
            "total": len(buildings),
            "buildings": buildings
        }
    except Exception as e:
        return {"error": str(e), "total": 0, "buildings": []}

# Solar Calculation Models
class SolarCalculationRequest(BaseModel):
    latitude: float
    longitude: float
    area_m2: float
    confidence: float = 0.9
    tilt: Optional[float] = None  # If None, use latitude (optimal for Thailand)
    azimuth: Optional[float] = 180  # 180 = facing south (optimal for Northern hemisphere)

class SolarCalculationResponse(BaseModel):
    usable_roof_area: float
    system_size_kwp: float
    annual_production_kwh: float
    installation_cost_thb: float
    annual_savings_thb: float
    payback_period_years: Optional[float]
    co2_reduction_kg: float
    co2_reduction_ton: float
    irradiance_source: str
    irradiance_kwh_m2_day: float
    assumptions: dict
    weather_forecast: Optional[dict] = None  # New field for weather data

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

@app.post("/solar/calculate", response_model=SolarCalculationResponse)
async def calculate_solar_potential(request: SolarCalculationRequest):
    """
    Calculate solar potential using pvlib-python for accurate modeling
    
    This endpoint uses pvlib to:
    - Get NASA POWER irradiance data
    - Calculate optimal tilt angle
    - Model PV system performance with temperature effects
    - Account for inverter losses and system efficiency
    """
    try:
        # Try to import pvlib
        try:
            import pvlib
            from pvlib import location
            import pandas as pd
            use_pvlib = True
        except ImportError:
            print("⚠️ pvlib not installed, using simplified calculation")
            use_pvlib = False
        
        # Constants (Thailand-specific)
        PANEL_EFFICIENCY = 0.20
        USABLE_ROOF_RATIO = 0.50
        COST_PER_WP = 25  # THB/Wp
        ELECTRICITY_RATE = 4.18  # THB/kWh
        CO2_FACTOR = 0.40  # kgCO₂/kWh
        
        # Adjust for confidence
        confidence_adjustment = max(request.confidence, 0.7)
        usable_roof_area = request.area_m2 * USABLE_ROOF_RATIO * confidence_adjustment
        system_size_kwp = usable_roof_area * PANEL_EFFICIENCY
        
        if use_pvlib:
            # Use pvlib for accurate calculation
            try:
                # Create location
                site = location.Location(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    tz='Asia/Bangkok',
                    altitude=10  # Bangkok average
                )
                
                # Get solar position for typical year
                times = pd.date_range('2024-01-01', '2024-12-31', freq='H', tz=site.tz)
                solar_position = site.get_solarposition(times)
                
                # Get clear sky irradiance (pvlib built-in model)
                clearsky = site.get_clearsky(times)
                
                # Optimal tilt = latitude for Thailand
                tilt = request.tilt if request.tilt is not None else abs(request.latitude)
                azimuth = request.azimuth if request.azimuth is not None else 180
                
                # Calculate POA (Plane of Array) irradiance
                poa_irradiance = pvlib.irradiance.get_total_irradiance(
                    surface_tilt=tilt,
                    surface_azimuth=azimuth,
                    dni=clearsky['dni'],
                    ghi=clearsky['ghi'],
                    dhi=clearsky['dhi'],
                    solar_zenith=solar_position['apparent_zenith'],
                    solar_azimuth=solar_position['azimuth']
                )
                
                # Temperature model (Thailand is hot!)
                temp_model_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
                cell_temperature = pvlib.temperature.sapm_cell(
                    poa_irradiance['poa_global'],
                    temp_air=30,  # Average Thailand temp
                    wind_speed=2,  # Light breeze
                    **temp_model_params
                )
                
                # Module parameters (typical monocrystalline)
                module_params = {
                    'pdc0': system_size_kwp * 1000,  # Wp
                    'gamma_pdc': -0.004,  # Temperature coefficient (%/°C)
                }
                
                # Calculate DC power with temperature effects
                dc_power = pvlib.pvsystem.pvwatts_dc(
                    poa_irradiance['poa_global'],
                    cell_temperature,
                    module_params['pdc0'],
                    module_params['gamma_pdc']
                )
                
                # Inverter efficiency (typical)
                ac_power = dc_power * 0.96  # 96% inverter efficiency
                
                # Annual production (kWh)
                annual_production = (ac_power.sum() / 1000)  # W to kWh
                
                # Average daily irradiance for display
                avg_irradiance = (poa_irradiance['poa_global'].mean() / 1000) * 24  # W/m² to kWh/m²/day
                
                irradiance_source = "pvlib (Clear Sky Model)"
                
            except Exception as e:
                print(f"⚠️ pvlib calculation failed: {e}, falling back to simple model")
                use_pvlib = False
        
        if not use_pvlib:
            # Fallback: Simple calculation
            # Try NASA POWER API
            try:
                import requests
                nasa_url = f"https://power.larc.nasa.gov/api/temporal/monthly/point"
                params = {
                    'parameters': 'ALLSKY_SFC_SW_DWN',
                    'community': 'RE',
                    'longitude': round(request.longitude, 2),
                    'latitude': round(request.latitude, 2),
                    'format': 'JSON'
                }
                response = requests.get(nasa_url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    monthly_data = data.get('properties', {}).get('parameter', {}).get('ALLSKY_SFC_SW_DWN', {})
                    monthly_values = [v for v in monthly_data.values() if isinstance(v, (int, float))]
                    
                    if monthly_values:
                        avg_irradiance = sum(monthly_values) / len(monthly_values)
                        irradiance_source = "NASA POWER"
                    else:
                        avg_irradiance = 5.06
                        irradiance_source = "Default (Thailand avg)"
                else:
                    avg_irradiance = 5.06
                    irradiance_source = "Default (Thailand avg)"
            except:
                avg_irradiance = 5.06
                irradiance_source = "Default (Thailand avg)"
            
            # Simple calculation
            SYSTEM_EFFICIENCY = 0.80
            annual_production = system_size_kwp * avg_irradiance * 365 * SYSTEM_EFFICIENCY
        
        # Financial calculations
        installation_cost = system_size_kwp * 1000 * COST_PER_WP
        annual_savings = annual_production * ELECTRICITY_RATE
        payback_period = installation_cost / annual_savings if annual_savings > 0 else None
        
        # Environmental
        co2_reduction = annual_production * CO2_FACTOR
        
        # Try to get weather forecast for enhanced analysis
        weather_forecast = None
        try:
            if os.getenv("WXTECH_API_KEY"):
                async with get_weather_service() as weather_client:
                    forecast = await weather_client.get_forecast(request.latitude, request.longitude)
                    solar_forecast = SolarWeatherAnalyzer.calculate_solar_forecast(forecast, system_size_kwp)
                    weather_forecast = {
                        "next_24h_generation": solar_forecast["next_24h_generation_kwh"],
                        "weather_quality_score": solar_forecast["weather_quality_score"],
                        "weekly_outlook": solar_forecast["weekly_outlook"][:3]  # First 3 days
                    }
        except Exception as e:
            print(f"⚠️ Weather forecast failed: {e}")
        
        return {
            "usable_roof_area": round(usable_roof_area),
            "system_size_kwp": round(system_size_kwp, 1),
            "annual_production_kwh": round(annual_production),
            "installation_cost_thb": round(installation_cost),
            "annual_savings_thb": round(annual_savings),
            "payback_period_years": round(payback_period, 1) if payback_period else None,
            "co2_reduction_kg": round(co2_reduction),
            "co2_reduction_ton": round(co2_reduction / 1000, 1),
            "irradiance_source": irradiance_source,
            "irradiance_kwh_m2_day": round(avg_irradiance, 2),
            "assumptions": {
                "panel_efficiency": PANEL_EFFICIENCY,
                "usable_roof_ratio": USABLE_ROOF_RATIO,
                "cost_per_wp": COST_PER_WP,
                "electricity_rate": ELECTRICITY_RATE,
                "co2_factor": CO2_FACTOR,
                "calculation_method": "pvlib" if use_pvlib else "simplified"
            },
            "weather_forecast": weather_forecast
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar calculation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
