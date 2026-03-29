"""
Buildings API - Query from BigQuery directly
Fast access to 107M+ building footprints
"""

from fastapi import FastAPI, Query
from google.cloud import bigquery
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import os

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
        "version": "2.0.0",
        "source": "BigQuery",
        "buildings": "107M+ in Thailand",
        "endpoints": {
            "/stats": "Get database statistics",
            "/buildings/bbox": "Get buildings in bounding box",
            "/buildings/nearby": "Get buildings near a point"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
