#!/usr/bin/env python3
"""
Import buildings data from Google Cloud Storage (Google Open Buildings CSV format)
"""

import psycopg2
from google.cloud import storage
import csv
import gzip
import io
import sys

# Cloud SQL configuration (using Cloud SQL Proxy or direct connection)
DB_CONFIG = {
    'host': '/cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db',  # Cloud SQL socket
    'port': '5432',
    'user': 'postgres',
    'password': 'toothless_solar_2024',
    'database': 'toothless_solar'
}

# Cloud Storage configuration
GCS_BUCKET = 'trim-descent-452802-t2-openbuildings-v3'
GCS_PREFIX = 'thailand/'  # Prefix for files in bucket

def list_gcs_files():
    """List all files in GCS bucket"""
    print(f"📂 Listing files in gs://{GCS_BUCKET}/...")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET)
    blobs = list(bucket.list_blobs(prefix=GCS_PREFIX))
    
    print(f"✅ Found {len(blobs)} files")
    return blobs

def parse_csv_file(blob):
    """Parse CSV file from GCS (Google Open Buildings format)"""
    # Download and decompress
    content_bytes = blob.download_as_bytes()
    
    if blob.name.endswith('.gz'):
        content_bytes = gzip.decompress(content_bytes)
    
    content = content_bytes.decode('utf-8')
    
    buildings = []
    reader = csv.DictReader(io.StringIO(content))
    
    for row in reader:
        try:
            # Parse WKT geometry
            geometry_wkt = row.get('geometry', '')
            if not geometry_wkt or not geometry_wkt.startswith('POLYGON'):
                continue
            
            # Extract coordinates from WKT to calculate centroid
            # Format: POLYGON((lon lat, lon lat, ...))
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
                continue
            
            centroid_lon = sum(lons) / len(lons)
            centroid_lat = sum(lats) / len(lats)
            point_wkt = f"POINT({centroid_lon} {centroid_lat})"
            
            # Extract properties
            area_m2 = float(row.get('area_in_meters', 100))
            confidence = float(row.get('confidence', 0.8))
            building_id = row.get('full_plus_code', f"OB_{hash(geometry_wkt) % 1000000}")
            
            buildings.append({
                'open_buildings_id': str(building_id),
                'latitude': centroid_lat,
                'longitude': centroid_lon,
                'area_m2': area_m2,
                'confidence': confidence,
                'geometry_wkt': geometry_wkt,
                'centroid_wkt': point_wkt
            })
            
        except Exception as e:
            # Skip invalid rows
            continue
    
    return buildings

def import_buildings_batch(conn, buildings):
    """Import a batch of buildings"""
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    
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
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
                
        except Exception as e:
            print(f"❌ Error inserting building {building['open_buildings_id']}: {e}")
            skipped += 1
            continue
    
    conn.commit()
    cur.close()
    
    return inserted, skipped

def main():
    """Main import function"""
    print("🚀 Starting import from Google Cloud Storage...")
    print(f"📦 Bucket: gs://{GCS_BUCKET}")
    print(f"🗄️  Database: {DB_CONFIG['database']}")
    print()
    
    # List files
    blobs = list_gcs_files()
    
    if not blobs:
        print("❌ No files found in bucket")
        return
    
    # Filter CSV files
    csv_files = [b for b in blobs if b.name.endswith('.csv') or b.name.endswith('.csv.gz')]
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"📄 Found {len(csv_files)} CSV files")
    print()
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("💡 Make sure Cloud SQL Proxy is running or use direct connection")
        return
    
    # Process each file (limit to first 5 files for testing)
    total_inserted = 0
    total_skipped = 0
    max_files = 5  # Process only 5 files at a time
    
    for i, blob in enumerate(csv_files[:max_files], 1):
        print(f"\n[{i}/{min(max_files, len(csv_files))}] Processing {blob.name}...")
        
        try:
            # Parse file
            buildings = parse_csv_file(blob)
            print(f"  📊 Found {len(buildings)} buildings")
            
            if not buildings:
                continue
            
            # Import batch
            inserted, skipped = import_buildings_batch(conn, buildings)
            total_inserted += inserted
            total_skipped += skipped
            
            print(f"  ✅ Inserted: {inserted}, Skipped: {skipped}")
            print(f"  📊 Total so far: {total_inserted} inserted, {total_skipped} skipped")
            
        except Exception as e:
            print(f"  ❌ Error processing file: {e}")
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
    print(f"✅ Total inserted: {total_inserted}")
    print(f"⏭️  Total skipped: {total_skipped}")
    print(f"📊 Total in database: {total_count}")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Import interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
