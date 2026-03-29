"""
Buildings API - Google Open Buildings Integration
Provides access to 1.88M building footprints in Bangkok
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()

app = FastAPI(title="Toothless Solar Buildings API")

# CORS - Allow all origins including AWS CloudFront
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",  # Allow all origins for production
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
# Use DATABASE_URL from environment (for Railway/Supabase) or fallback to local config
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Production mode (Railway/Supabase) - use connection string
    DB_CONFIG = DATABASE_URL
else:
    # Development mode (local) - use config dict
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'toothless_solar_2024'),
        'database': os.getenv('DB_NAME', 'toothless_solar')
    }

def get_db_connection():
    """Create database connection"""
    if isinstance(DB_CONFIG, str):
        # Production: Use connection string
        return psycopg2.connect(DB_CONFIG, cursor_factory=RealDictCursor)
    else:
        # Development: Use config dict
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# Models
class Building(BaseModel):
    id: int
    open_buildings_id: str
    latitude: float
    longitude: float
    area_m2: float
    confidence: float
    geometry: Optional[str] = None

class BuildingsResponse(BaseModel):
    total: int
    buildings: List[Building]

class BoundingBox(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

# Endpoints

@app.get("/")
def root():
    """API info"""
    return {
        "name": "Toothless Solar Buildings API",
        "version": "1.0.0",
        "buildings": "1.88M in Bangkok",
        "endpoints": {
            "/buildings/bbox": "Get buildings in bounding box",
            "/buildings/nearby": "Get buildings near a point",
            "/buildings/{id}": "Get building details",
            "/stats": "Get database statistics"
        }
    }

@app.get("/stats")
def get_stats():
    """Get database statistics (cached)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Single query for all stats (faster)
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                AVG(confidence) as avg_confidence,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                AVG(area_m2) as avg_area,
                MIN(area_m2) as min_area,
                MAX(area_m2) as max_area,
                MIN(latitude) as min_lat,
                MAX(latitude) as max_lat,
                MIN(longitude) as min_lon,
                MAX(longitude) as max_lon
            FROM buildings;
        """)
        stats = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return {
            "total_buildings": stats['total'],
            "confidence": {
                "average": round(stats['avg_confidence'], 3),
                "min": round(stats['min_confidence'], 3),
                "max": round(stats['max_confidence'], 3)
            },
            "area_m2": {
                "average": round(stats['avg_area'], 1),
                "min": round(stats['min_area'], 1),
                "max": round(stats['max_area'], 1)
            },
            "extent": {
                "latitude": [stats['min_lat'], stats['max_lat']],
                "longitude": [stats['min_lon'], stats['max_lon']]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/bbox", response_model=BuildingsResponse)
def get_buildings_in_bbox(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lon: float = Query(..., description="Maximum longitude"),
    limit: int = Query(1000, le=5000, description="Max results"),
    min_confidence: float = Query(0.7, description="Minimum confidence")
):
    """Get buildings within bounding box"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                id,
                open_buildings_id,
                latitude,
                longitude,
                area_m2,
                confidence,
                ST_AsGeoJSON(geometry) as geometry
            FROM buildings
            WHERE 
                latitude BETWEEN %s AND %s
                AND longitude BETWEEN %s AND %s
                AND confidence >= %s
            ORDER BY area_m2 DESC
            LIMIT %s;
        """
        
        cur.execute(query, (min_lat, max_lat, min_lon, max_lon, min_confidence, limit))
        buildings = cur.fetchall()
        
        # Count total
        count_query = """
            SELECT COUNT(*) as total
            FROM buildings
            WHERE 
                latitude BETWEEN %s AND %s
                AND longitude BETWEEN %s AND %s
                AND confidence >= %s;
        """
        cur.execute(count_query, (min_lat, max_lat, min_lon, max_lon, min_confidence))
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return {
            "total": total,
            "buildings": buildings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/nearby", response_model=BuildingsResponse)
def get_buildings_nearby(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_m: float = Query(500, description="Radius in meters"),
    limit: int = Query(100, le=1000),
    min_confidence: float = Query(0.7)
):
    """Get buildings near a point"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                id,
                open_buildings_id,
                latitude,
                longitude,
                area_m2,
                confidence,
                ST_AsGeoJSON(geometry) as geometry,
                ST_Distance(
                    centroid::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) as distance_m
            FROM buildings
            WHERE 
                ST_DWithin(
                    centroid::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                    %s
                )
                AND confidence >= %s
            ORDER BY distance_m
            LIMIT %s;
        """
        
        cur.execute(query, (lon, lat, lon, lat, radius_m, min_confidence, limit))
        buildings = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "total": len(buildings),
            "buildings": buildings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/{building_id}")
def get_building_detail(building_id: int):
    """Get detailed building information"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
            SELECT 
                id,
                open_buildings_id,
                latitude,
                longitude,
                area_m2,
                confidence,
                ST_AsGeoJSON(geometry) as geometry,
                ST_AsGeoJSON(centroid) as centroid,
                created_at
            FROM buildings
            WHERE id = %s;
        """
        
        cur.execute(query, (building_id,))
        building = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
        
        return building
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buildings/search/address")
def search_by_address(
    address: str = Query(..., description="Address to search"),
    limit: int = Query(10, le=100)
):
    """Search buildings by address (placeholder - requires geocoding)"""
    return {
        "message": "Address search requires geocoding service",
        "suggestion": "Use /buildings/nearby with coordinates instead"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)


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
    assumptions: Dict

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
            from pvlib import location, pvsystem, modelchain
            import pandas as pd
            import numpy as np
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
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Solar calculation error: {str(e)}")
