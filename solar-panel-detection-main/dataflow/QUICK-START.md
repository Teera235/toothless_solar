# Quick Start: Import Buildings Data

## Current Status

✅ Backend API: Running
✅ Frontend: Running  
✅ Database: Ready
❌ Data: Not imported yet (database is empty)

## Problem

CSV files in GCS are too large (millions of rows):
- Direct import fails with memory errors (even at 8Gi limit)
- Cloud Run Job cannot handle the volume

## Solution: BigQuery + Cloud SQL

Use BigQuery as intermediate staging:
1. Load CSV → BigQuery (fast, handles millions of rows)
2. Import BigQuery → Cloud SQL (batch processing)

## One-Command Import

```powershell
.\import-buildings.ps1
```

This will:
1. Load CSV files to BigQuery (10-30 min)
2. Import from BigQuery to Cloud SQL (20-60 min)
3. Verify the data

**Total time:** 30-90 minutes

## Manual Steps

### Step 1: Load to BigQuery

```powershell
cd dataflow
.\load_to_bigquery.ps1
```

Or manually:

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

### Step 2: Import to Cloud SQL

```powershell
cd dataflow
python import_from_bigquery.py
```

## Check Status

```powershell
.\check-status.ps1
```

## After Import

1. Open frontend: https://toothless-solar-frontend-715107904640.asia-southeast1.run.app
2. Zoom into map to see building polygons
3. Test API: https://buildings-api-715107904640.asia-southeast1.run.app/stats

## Cost

For ~2 million buildings:
- BigQuery load: ~$0.05
- Direct import: Free (runs locally)
- Cloud SQL storage: ~$0.17/GB/month

**Total:** ~$0.05 (one-time) + ~$0.17/GB/month

## Cleanup

After import, you can delete BigQuery dataset to save costs:

```bash
bq rm -r -f trim-descent-452802-t2:openbuildings
```

## Files

- `import-buildings.ps1` - Master script (run this)
- `load_to_bigquery.ps1` - Load CSV to BigQuery
- `import_from_bigquery.py` - Import BigQuery to Cloud SQL (recommended)
- `gcs_to_cloudsql.py` - Dataflow pipeline (alternative for very large datasets)

## Troubleshooting

### BigQuery load fails
```bash
# Check permissions
gcloud projects get-iam-policy trim-descent-452802-t2

# Verify files exist
gsutil ls gs://trim-descent-452802-t2-openbuildings-v3/thailand/
```

### Import is slow
- Increase `BATCH_SIZE` in `import_from_bigquery.py`
- Use Dataflow pipeline instead (distributed processing)

### Connection error
```bash
# Check Cloud SQL is running
gcloud sql instances describe nabha-solar-db

# Test connection
gcloud sql connect nabha-solar-db --user=postgres
```

## Summary

System is deployed and ready. Just need to import the data!

Run `.\import-buildings.ps1` and wait 30-90 minutes. Done! 🎉
