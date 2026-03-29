#!/usr/bin/env python3
"""
Import buildings directly from Parquet files to Cloud SQL
This is faster than CSV because Parquet is columnar and compressed

USAGE:
    python import_from_parquet.py
"""

import psycopg2
from google.cloud import storage
import pyarrow.parquet as pq
import io
import sys
import time

# Configuration
PROJECT_ID = "trim-descent-452802-t2"
GCS_BUCKET = "trim-descent-452802-t2-openbuildings-v3"
GCS_PREFIX = "thailand-parquet/"

DB_CONFIG = {
    'host': '/cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db',
    'port': '5432',
    'user': 'postgres',
    'password': 'toothless_solar_2024',
    'database': 'toothless_solar'
}

BATCH_SIZE = 1000  # Parquet is faster, can use larger batches

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
            continue
    
    return inserted

def process_parquet_file(blob, conn):
    """Process a single Parquet file"""
    print(f"\n📄 Processing: {blob.name}")
    
    try:
        # Download Parquet file
        print("  ⬇️  Downloading...")
        content_bytes = blob.download_as_bytes()
        
        # Read Parquet
        print("  📊 Reading Parquet...")
        parquet_file = pq.read_table(io.BytesIO(content_bytes))
        df = parquet_file.to_pandas()
        
        print(f"  ✅ Loaded {len(df):,} rows")
        
        cur = conn.cursor()
        batch = []
        total_inserted = 0
        total_skipped = 0
        
        for idx, row in df.iterrows():
            try:
                geometry_wkt = row.get('geometry', '')
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
                    
                    if total_inserted % 5000 == 0:
                        print(f"    ✓ Inserted {total_inserted:,} buildings...")
                
            except Exception as e:
                total_skipped += 1
                continue
        
        # Insert remaining batch
        if batch:
            inserted = insert_batch(cur, batch)
            conn.commit()
            total_inserted += inserted
        
        cur.close()
        
        print(f"  ✅ Inserted: {total_inserted:,}")
        print(f"  ⏭️  Skipped: {total_skipped:,}")
        
        return total_inserted, total_skipped
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

def main():
    """Main import function"""
    print("🚀 Importing from Parquet to Cloud SQL...")
    print(f"📦 Source: gs://{GCS_BUCKET}/{GCS_PREFIX}")
    print(f"🗄️  Target: {DB_CONFIG['database']}")
    print()
    
    # List Parquet files
    print("📂 Listing Parquet files...")
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=GCS_PREFIX))
    
    parquet_files = [b for b in blobs if b.name.endswith('.parquet')]
    
    if not parquet_files:
        print("❌ No Parquet files found")
        print("Run: python convert_csv_to_parquet.py")
        return
    
    print(f"✅ Found {len(parquet_files)} Parquet files")
    print()
    
    # Connect to Cloud SQL
    print("🗄️  Connecting to Cloud SQL...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(autocommit=False)
        print("✅ Connected")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Process files
    total_inserted = 0
    total_skipped = 0
    start_time = time.time()
    
    for i, blob in enumerate(parquet_files, 1):
        print(f"\n[{i}/{len(parquet_files)}]")
        inserted, skipped = process_parquet_file(blob, conn)
        total_inserted += inserted
        total_skipped += skipped
    
    # Final stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM buildings;")
    db_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("🎉 Import completed!")
    print(f"⏱️  Duration: {elapsed/60:.1f} minutes")
    print(f"✅ Inserted: {total_inserted:,}")
    print(f"⏭️  Skipped: {total_skipped:,}")
    print(f"🗄️  Total in database: {db_count:,}")
    print(f"⚡ Average rate: {total_inserted/elapsed:.0f} rows/sec")
    print("=" * 70)

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
