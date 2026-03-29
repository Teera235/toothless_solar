# Import Google Open Buildings to Cloud SQL

This directory contains scripts to import millions of building polygons from Google Open Buildings dataset into Cloud SQL.

## Architecture

```
GCS (CSV files) → BigQuery → Dataflow → Cloud SQL
```

**Why this approach?**
- BigQuery can load millions of CSV rows in minutes (vs hours with other methods)
- Dataflow can process and transform data at scale
- Cloud SQL gets clean, validated data with proper PostGIS geometry

## Prerequisites

1. **Enable APIs**
   ```bash
   gcloud services enable bigquery.googleapis.com
   gcloud services enable dataflow.googleapis.com
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify data exists in GCS**
   ```bash
   gsutil ls gs://trim-descent-452802-t2-openbuildings-v3/thailand/
   ```

## Step 1: Load to BigQuery (Fast!)

BigQuery can load millions of rows from compressed CSV files in 10-30 minutes.

**Windows (PowerShell):**
```powershell
.\load_to_bigquery.ps1
```

**Linux/Mac:**
```bash
chmod +x load_to_bigquery.sh
./load_to_bigquery.sh
```

**Manual command:**
```bash
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  --replace \
  --location=asia-southeast1 \
  trim-descent-452802-t2:openbuildings.thailand_raw \
  gs://trim-descent-452802-t2-openbuildings-v3/thailand/*.csv.gz
```

This will:
- Create `openbuildings` dataset
- Create `thailand_raw` table
- Load all CSV files from GCS
- Auto-detect schema

## Step 2: Run Dataflow Pipeline

The Dataflow pipeline reads from BigQuery, transforms data, and writes to Cloud SQL.

```bash
python gcs_to_cloudsql.py
```

**What it does:**
1. Reads buildings from BigQuery
2. Parses WKT geometry strings
3. Calculates centroids
4. Batches inserts (100-500 per batch)
5. Writes to Cloud SQL with PostGIS geometry

**Pipeline configuration:**
- Runner: DataflowRunner (runs on GCP)
- Workers: Up to 20 (auto-scales)
- Machine: n1-standard-2
- Region: asia-southeast1

**Monitoring:**
- View job: https://console.cloud.google.com/dataflow/jobs
- Check logs: Cloud Logging

## Alternative: Direct Import (Small datasets only)

For testing or small datasets (<100K rows), you can use the streaming import:

```bash
python ../database/import_streaming.py
```

⚠️ **Warning:** This will fail with memory errors for large datasets (millions of rows).

## Troubleshooting

### BigQuery load fails
- Check GCS bucket permissions
- Verify CSV format (should have headers)
- Check quota limits

### Dataflow fails to connect to Cloud SQL
- Verify Cloud SQL instance is running
- Check firewall rules
- Ensure Cloud SQL Admin API is enabled
- Verify credentials

### Slow performance
- Increase `max_num_workers` in pipeline
- Use larger machine type
- Check Cloud SQL instance size (needs enough CPU/memory)

### Out of memory
- Don't use direct CSV import for large datasets
- Use BigQuery → Dataflow approach instead

## Cost Estimation

For ~2 million buildings:

- **BigQuery load:** ~$0.05 (very cheap!)
- **Dataflow:** ~$2-5 (depends on duration)
- **Cloud SQL storage:** ~$0.17/GB/month
- **Total one-time:** ~$2-5

## Verification

After import completes, verify data:

```bash
# Check count
psql -h /cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db \
     -U postgres -d toothless_solar \
     -c "SELECT COUNT(*) FROM buildings;"

# Check sample
psql -h /cloudsql/trim-descent-452802-t2:asia-southeast1:nabha-solar-db \
     -U postgres -d toothless_solar \
     -c "SELECT * FROM buildings LIMIT 5;"

# Check via API
curl https://buildings-api-715107904640.asia-southeast1.run.app/stats
```

## Next Steps

After data is imported:
1. Verify buildings appear on map
2. Test API endpoints
3. Optimize queries if needed
4. Consider adding indexes for common queries

## Files

- `load_to_bigquery.ps1` - Load CSV to BigQuery (Windows)
- `load_to_bigquery.sh` - Load CSV to BigQuery (Linux/Mac)
- `gcs_to_cloudsql.py` - Dataflow pipeline (BigQuery → Cloud SQL)
- `setup.py` - Python dependencies for Dataflow workers
- `requirements.txt` - Local development dependencies
