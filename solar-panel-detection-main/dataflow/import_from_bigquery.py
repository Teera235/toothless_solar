#!/usr/bin/env python3
"""
Import buildings from BigQuery to Cloud SQL
This is simpler than Dataflow and works well for millions of rows

USAGE:
1. First load data to BigQuery:
   ./load_to_bigquery.ps1

2. Then run this script:
   python import_from_bigquery.py
"""

import psycopg2
from google.cloud import bigquery
import sys
import time

# Configuration
PROJECT_ID = "trim-descent-452802-t2"
BQ_DATASET = "openbuildings"
BQ_TABLE = "thailand_raw"

import os

# Check if running in Cloud Shell or locally
if os.path.exists('/google/devshell'):
    # Cloud Shell - use public IP
    DB_CONFIG = {
        'host': '34.21.146.214',
        'port': '5432',
        'user': 'postgres',
        'password': 'toothless_solar_2024',
        'database': 'toothless_solar'
    }
else:
    # Local or Cloud Run - use Unix socket
    DB_CONFIG = {
        'host': '/cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db',
        'port': '5432',
        'user': 'postgres',
        'password': 'toothless_solar_2024',
        'database': 'toothless_solar'
    }

BATCH_SIZE = 500  # Insert 500 buildings at a time
FETCH_SIZE = 10000  # Fetch 10K rows from BigQuery at a time

def parse_geometry(geometry_wkt):
    """Parse WKT geometry and calculate centroid"""
    try:
        if not geometry_wkt or not geometry_wkt.startswith('POLYGON'):
            return None
        
        # Extract coordinates
        coords_str = geometry_wkt.replace('POLYGON((', '').replace('))', '')
        coords_pairs = coords_str.split(', ')
        
        lons = []
        lats = []
        for pair in coords_pairs:
            parts = pair.strip().split()
            if len(parts) >= 2:
                try:
                    lons.append(float(parts[0]))
                    lats.append(float(parts[1]))
                except:
                    continue
        
        if not lons or not lats:
            return None
        
        centroid_lon = sum(lons) / len(lons)
        centroid_lat = sum(lats) / len(lats)
        
        return {
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
            'centroid_wkt': f"POINT({centroid_lon} {centroid_lat})"
        }
    except:
        return None

def insert_batch(cur, batch):
    """Insert a batch of buildings"""
    inserted = 0
    
    for building in batch:
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
            """, building)
            
            if cur.rowcount > 0:
                inserted += 1
                
        except Exception as e:
            # Skip errors
            continue
    
    return inserted

def main():
    """Main import function"""
    print("🚀 Starting import from BigQuery to Cloud SQL...")
    print(f"📊 Source: {PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}")
    print(f"🗄️  Target: {DB_CONFIG['database']}")
    print()
    
    # Connect to BigQuery
    print("📊 Connecting to BigQuery...")
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Check row count
    count_query = f"""
        SELECT COUNT(*) as total
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`
        WHERE geometry IS NOT NULL
        AND geometry LIKE 'POLYGON%'
    """
    
    count_result = bq_client.query(count_query).result()
    total_rows = list(count_result)[0]['total']
    print(f"✅ Found {total_rows:,} buildings in BigQuery")
    print()
    
    # Connect to Cloud SQL
    print("🗄️  Connecting to Cloud SQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(autocommit=False)
        cur = conn.cursor()
        print("✅ Connected to Cloud SQL")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Query BigQuery in batches
    query = f"""
        SELECT 
            geometry,
            area_in_meters,
            confidence,
            full_plus_code
        FROM `{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}`
        WHERE geometry IS NOT NULL
        AND geometry LIKE 'POLYGON%'
    """
    
    print(f"📥 Fetching data from BigQuery (batch size: {FETCH_SIZE:,})...")
    print()
    
    query_job = bq_client.query(query)
    
    batch = []
    total_inserted = 0
    total_skipped = 0
    total_processed = 0
    start_time = time.time()
    
    for row in query_job.result():
        total_processed += 1
        
        try:
            geometry_wkt = row['geometry']
            geo_data = parse_geometry(geometry_wkt)
            
            if not geo_data:
                total_skipped += 1
                continue
            
            area_m2 = float(row.get('area_in_meters', 100))
            confidence = float(row.get('confidence', 0.8))
            building_id = row.get('full_plus_code', f"OB_{hash(geometry_wkt) % 10000000}")
            
            batch.append((
                str(building_id),
                geo_data['centroid_lat'],
                geo_data['centroid_lon'],
                area_m2,
                confidence,
                geometry_wkt,
                geo_data['centroid_wkt']
            ))
            
            # Insert batch when full
            if len(batch) >= BATCH_SIZE:
                inserted = insert_batch(cur, batch)
                conn.commit()
                total_inserted += inserted
                batch = []
                
                # Progress update
                if total_processed % 5000 == 0:
                    elapsed = time.time() - start_time
                    rate = total_processed / elapsed
                    remaining = (total_rows - total_processed) / rate if rate > 0 else 0
                    
                    print(f"  📊 Progress: {total_processed:,}/{total_rows:,} "
                          f"({100*total_processed/total_rows:.1f}%) | "
                          f"Inserted: {total_inserted:,} | "
                          f"Rate: {rate:.0f} rows/sec | "
                          f"ETA: {remaining/60:.0f} min")
            
        except Exception as e:
            total_skipped += 1
            continue
    
    # Insert remaining batch
    if batch:
        inserted = insert_batch(cur, batch)
        conn.commit()
        total_inserted += inserted
    
    # Final stats
    cur.execute("SELECT COUNT(*) FROM buildings;")
    db_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    elapsed = time.time() - start_time
    
    print()
    print("="*70)
    print("🎉 Import completed!")
    print(f"⏱️  Duration: {elapsed/60:.1f} minutes")
    print(f"📊 Processed: {total_processed:,} rows")
    print(f"✅ Inserted: {total_inserted:,}")
    print(f"⏭️  Skipped: {total_skipped:,}")
    print(f"🗄️  Total in database: {db_count:,}")
    print(f"⚡ Average rate: {total_processed/elapsed:.0f} rows/sec")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
