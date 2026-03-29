#!/usr/bin/env python3
"""
Convert CSV files from GCS to Parquet format
Parquet is 5-10x smaller and much faster to read than CSV

USAGE:
    python convert_csv_to_parquet.py
"""

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from google.cloud import storage
import gzip
import io
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "trim-descent-452802-t2"
SOURCE_BUCKET = "trim-descent-452802-t2-openbuildings-v3"
SOURCE_PREFIX = "thailand/"
DEST_BUCKET = "trim-descent-452802-t2-openbuildings-v3"
DEST_PREFIX = "thailand-parquet/"

# Parquet settings
COMPRESSION = "snappy"  # Fast compression (or use 'gzip' for better compression)
ROW_GROUP_SIZE = 100000  # Rows per row group

def convert_csv_to_parquet(blob, storage_client):
    """Convert a single CSV file to Parquet"""
    print(f"\n📄 Processing: {blob.name}")
    
    try:
        # Download and decompress CSV
        print("  ⬇️  Downloading...")
        content_bytes = blob.download_as_bytes()
        
        if blob.name.endswith('.gz'):
            print("  📦 Decompressing...")
            content_bytes = gzip.decompress(content_bytes)
        
        # Read CSV into DataFrame
        print("  📊 Reading CSV...")
        df = pd.read_csv(io.BytesIO(content_bytes))
        
        print(f"  ✅ Loaded {len(df):,} rows")
        print(f"  📋 Columns: {list(df.columns)}")
        
        # Optimize data types
        print("  🔧 Optimizing data types...")
        if 'latitude' in df.columns:
            df['latitude'] = df['latitude'].astype('float32')
        if 'longitude' in df.columns:
            df['longitude'] = df['longitude'].astype('float32')
        if 'area_in_meters' in df.columns:
            df['area_in_meters'] = df['area_in_meters'].astype('float32')
        if 'confidence' in df.columns:
            df['confidence'] = df['confidence'].astype('float32')
        
        # Convert to Parquet
        print(f"  💾 Converting to Parquet ({COMPRESSION} compression)...")
        parquet_buffer = io.BytesIO()
        
        df.to_parquet(
            parquet_buffer,
            engine='pyarrow',
            compression=COMPRESSION,
            index=False,
            row_group_size=ROW_GROUP_SIZE
        )
        
        # Upload to GCS
        parquet_buffer.seek(0)
        dest_blob_name = blob.name.replace(SOURCE_PREFIX, DEST_PREFIX)
        dest_blob_name = dest_blob_name.replace('.csv.gz', '.parquet')
        dest_blob_name = dest_blob_name.replace('.csv', '.parquet')
        
        print(f"  ⬆️  Uploading to: {dest_blob_name}")
        dest_bucket = storage_client.bucket(DEST_BUCKET)
        dest_blob = dest_bucket.blob(dest_blob_name)
        dest_blob.upload_from_file(parquet_buffer, content_type='application/octet-stream')
        
        # Compare sizes
        csv_size_mb = len(content_bytes) / (1024 * 1024)
        parquet_size_mb = len(parquet_buffer.getvalue()) / (1024 * 1024)
        compression_ratio = csv_size_mb / parquet_size_mb if parquet_size_mb > 0 else 0
        
        print(f"  📊 Size comparison:")
        print(f"     CSV: {csv_size_mb:.2f} MB")
        print(f"     Parquet: {parquet_size_mb:.2f} MB")
        print(f"     Compression: {compression_ratio:.1f}x smaller")
        print(f"  ✅ Done!")
        
        return {
            'file': blob.name,
            'rows': len(df),
            'csv_size_mb': csv_size_mb,
            'parquet_size_mb': parquet_size_mb,
            'compression_ratio': compression_ratio
        }
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main conversion function"""
    print("🚀 CSV to Parquet Converter")
    print("=" * 60)
    print(f"📦 Source: gs://{SOURCE_BUCKET}/{SOURCE_PREFIX}")
    print(f"📦 Destination: gs://{DEST_BUCKET}/{DEST_PREFIX}")
    print(f"🗜️  Compression: {COMPRESSION}")
    print("=" * 60)
    print()
    
    # Initialize GCS client
    storage_client = storage.Client(project=PROJECT_ID)
    
    # List CSV files
    print("📂 Listing CSV files...")
    bucket = storage_client.bucket(SOURCE_BUCKET)
    blobs = list(bucket.list_blobs(prefix=SOURCE_PREFIX))
    
    csv_files = [b for b in blobs if b.name.endswith('.csv') or b.name.endswith('.csv.gz')]
    
    if not csv_files:
        print("❌ No CSV files found")
        return
    
    print(f"✅ Found {len(csv_files)} CSV files")
    print()
    
    # Convert files
    results = []
    start_time = datetime.now()
    
    for i, blob in enumerate(csv_files, 1):
        print(f"\n[{i}/{len(csv_files)}] Converting...")
        result = convert_csv_to_parquet(blob, storage_client)
        if result:
            results.append(result)
    
    # Summary
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("🎉 Conversion Complete!")
    print("=" * 60)
    
    if results:
        total_rows = sum(r['rows'] for r in results)
        total_csv_mb = sum(r['csv_size_mb'] for r in results)
        total_parquet_mb = sum(r['parquet_size_mb'] for r in results)
        avg_compression = total_csv_mb / total_parquet_mb if total_parquet_mb > 0 else 0
        
        print(f"✅ Converted: {len(results)} files")
        print(f"📊 Total rows: {total_rows:,}")
        print(f"💾 CSV size: {total_csv_mb:.2f} MB")
        print(f"💾 Parquet size: {total_parquet_mb:.2f} MB")
        print(f"🗜️  Compression: {avg_compression:.1f}x smaller")
        print(f"💰 Storage savings: {total_csv_mb - total_parquet_mb:.2f} MB ({100 * (1 - total_parquet_mb/total_csv_mb):.1f}%)")
        print(f"⏱️  Time: {elapsed:.1f} seconds")
        print(f"⚡ Rate: {total_rows/elapsed:.0f} rows/sec")
    
    print("\n📦 Parquet files location:")
    print(f"   gs://{DEST_BUCKET}/{DEST_PREFIX}")
    print()
    print("Next steps:")
    print("  1. Load Parquet to BigQuery:")
    print(f"     bq load --source_format=PARQUET \\")
    print(f"       {PROJECT_ID}:openbuildings.thailand_raw \\")
    print(f"       gs://{DEST_BUCKET}/{DEST_PREFIX}*.parquet")
    print()
    print("  2. Or import directly to Cloud SQL:")
    print("     python import_from_parquet.py")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Conversion interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
