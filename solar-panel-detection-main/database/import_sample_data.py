#!/usr/bin/env python3
"""
Import sample buildings data (100 buildings) for demo
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import random

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': 'toothless_solar_2024',
    'database': 'toothless_solar'
}

# Bangkok area bounds
BANGKOK_BOUNDS = {
    'min_lat': 13.65,
    'max_lat': 13.85,
    'min_lon': 100.45,
    'max_lon': 100.65
}

def generate_sample_buildings(count=100):
    """Generate sample building data"""
    buildings = []
    
    for i in range(count):
        # Random location in Bangkok
        lat = random.uniform(BANGKOK_BOUNDS['min_lat'], BANGKOK_BOUNDS['max_lat'])
        lon = random.uniform(BANGKOK_BOUNDS['min_lon'], BANGKOK_BOUNDS['max_lon'])
        
        # Random building properties
        area = random.uniform(50, 500)  # 50-500 m²
        confidence = random.uniform(0.7, 0.95)  # 70-95% confidence
        
        # Simple square polygon (offset by ~0.0001 degrees ≈ 10 meters)
        offset = 0.0001
        polygon_wkt = f"POLYGON(({lon} {lat}, {lon+offset} {lat}, {lon+offset} {lat+offset}, {lon} {lat+offset}, {lon} {lat}))"
        point_wkt = f"POINT({lon} {lat})"
        
        buildings.append({
            'open_buildings_id': f'SAMPLE_{i+1:04d}',
            'latitude': lat,
            'longitude': lon,
            'area_m2': area,
            'confidence': confidence,
            'geometry_wkt': polygon_wkt,
            'centroid_wkt': point_wkt
        })
    
    return buildings

def import_buildings():
    """Import buildings into database"""
    print("🚀 Importing sample buildings...")
    
    # Generate sample data
    buildings = generate_sample_buildings(100)
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Insert buildings
    inserted = 0
    for building in buildings:
        try:
            cur.execute("""
                INSERT INTO buildings (
                    open_buildings_id,
                    latitude,
                    longitude,
                    area_m2,
                    confidence,
                    geometry,
                    centroid
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    ST_GeomFromText(%s, 4326),
                    ST_GeomFromText(%s, 4326)
                ) ON CONFLICT (open_buildings_id) DO NOTHING;
            """, (
                building['open_buildings_id'],
                building['latitude'],
                building['longitude'],
                building['area_m2'],
                building['confidence'],
                building['geometry_wkt'],
                building['centroid_wkt']
            ))
            inserted += 1
        except Exception as e:
            print(f"❌ Error inserting building: {e}")
            continue
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) as total FROM buildings;")
    total = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    print(f"✅ Imported {inserted} buildings")
    print(f"📊 Total buildings in database: {total}")

if __name__ == "__main__":
    try:
        import_buildings()
        print("\n🎉 Sample data import completed!")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
