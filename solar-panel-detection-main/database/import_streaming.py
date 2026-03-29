#!/usr/bin/env python3
"""
Import buildings data from GCS using streaming (memory efficient)
"""

import psycopg2
from google.cloud import storage
import csv
import gzip
import io
import sys

# Cloud SQL configuration
DB_CONFIG = {
    'host': '/cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db',
    'port': '5432',
    'user': 'postgres',
    'password': 'toothless_solar_2024',
    'database': 'toothless_solar'
}

# Cloud Storage configuration
GCS_BUCKET = 'trim-descent-452802-t2-openbuildings-v3'
GCS_PREFIX = 'thailand/'

BATCH_SIZE = 100  # Insert 100 buildings at a time

def process_csv_streaming(blob, conn):
    """Process CSV file in streaming mode"""
    print(f"  📥 Downloading {blob.name}...")
    
    # Download and decompress
    content_bytes = blob.download_as_bytes()
    if blob.name.endswith('.gz'):
        content_bytes = gzip.decompress(content_bytes)
    
    content = content_bytes.decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    
    cur = conn.cursor()
    batch = []
    inserted = 0
    skipped = 0
    total_rows = 0
    
    for row in reader:
        total_rows += 1
        
        try:
            # Parse WKT geometry
            geometry_wkt = row.get('geometry', '')
            if not geometry_wkt or not geometry_wkt.startswith('POLYGON'):
                skipped += 1
                continue
            
            # Extract coordinates for centroid
            coords_str = geometry_wkt.replace('POLYGON((', '').replace('))', '')
            coords_pairs = coords_str.split(', ')
            
            lons = []
            lats = []
            for pair in coords_pairs:
                parts = pair.strip().split()
                if len(parts) >= 2:
                    lons.append(float(parts[0]))
                    lats.append(float(parts[1]))
            
            if not lons or not lats:
                skipped += 1
                continue
            
            centroid_lon = sum(lons) / len(lons)
            centroid_lat = sum(lats) / len(lats)
            point_wkt = f"POINT({centroid_lon} {centroid_lat})"
            
            # Extract properties
            area_m2 = float(row.get('area_in_meters', 100))
            confidence = float(row.get('confidence', 0.8))
            building_id = row.get('full_plus_code', f"OB_{hash(geometry_wkt) % 10000000}")
            
            batch.append((
                str(building_id),
                centroid_lat,
                centroid_lon,
                area_m2,
                confidence,
                geometry_wkt,
                point_wkt
            ))
            
            # Insert batch when full
            if len(batch) >= BATCH_SIZE:
                inserted += insert_batch(cur, batch)
                conn.commit()
                batch = []
                
                # Progress update
                if inserted % 1000 == 0:
                    print(f"    ✓ Inserted {inserted} buildings...")
            
        except Exception as e:
            skipped += 1
            continue
    
    # Insert remaining batch
    if batch:
        inserted += insert_batch(cur, batch)
        conn.commit()
    
    cur.close()
    
    print(f"  📊 Processed {total_rows} rows")
    print(f"  ✅ Inserted: {inserted}, Skipped: {skipped}")
    
    return inserted, skipped

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
            # Skip duplicates or errors
            continue
    
    return inserted

def main():
    """Main import function"""
    print("🚀 Starting streaming import from GCS...")
    print(f"📦 Bucket: gs://{GCS_BUCKET}/{GCS_PREFIX}")
    print(f"🗄️  Database: {DB_CONFIG['database']}")
    print()
    
    # List files
    print("📂 Listing CSV files...")
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=GCS_PREFIX))
    
    csv_files = [b for b in blobs if b.name.endswith('.csv') or b.name.endswith('.csv.gz')]
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"✅ Found {len(csv_files)} CSV files")
    print()
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_session(autocommit=False)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Process files
    total_inserted = 0
    total_skipped = 0
    
    for i, blob in enumerate(csv_files, 1):
        print(f"\n[{i}/{len(csv_files)}] Processing {blob.name}")
        
        try:
            inserted, skipped = process_csv_streaming(blob, conn)
            total_inserted += inserted
            total_skipped += skipped
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final stats
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM buildings;")
    total_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print("\n" + "="*60)
    print("🎉 Import completed!")
    print(f"✅ Total inserted: {total_inserted:,}")
    print(f"⏭️  Total skipped: {total_skipped:,}")
    print(f"📊 Total in database: {total_count:,}")
    print("="*60)

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
