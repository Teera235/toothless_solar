#!/bin/bash
# Load CSV files from GCS to BigQuery
# This is MUCH faster than trying to process CSVs directly in Dataflow

set -e

PROJECT_ID="trim-descent-452802-t2"
DATASET="openbuildings"
TABLE="thailand_raw"
GCS_PATH="gs://trim-descent-452802-t2-openbuildings-v3/thailand/*.csv.gz"

echo "🚀 Loading Google Open Buildings data to BigQuery..."
echo "📦 Project: $PROJECT_ID"
echo "📊 Dataset: $DATASET"
echo "📋 Table: $TABLE"
echo "📂 Source: $GCS_PATH"
echo ""

# Create dataset if not exists
echo "📊 Creating dataset..."
bq mk --dataset --location=asia-southeast1 "$PROJECT_ID:$DATASET" 2>/dev/null || echo "Dataset already exists"

# Load data
echo "📥 Loading data (this may take 10-30 minutes for millions of rows)..."
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  --replace \
  --location=asia-southeast1 \
  "$PROJECT_ID:$DATASET.$TABLE" \
  "$GCS_PATH"

# Check row count
echo ""
echo "✅ Data loaded! Checking row count..."
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as total_rows FROM \`$PROJECT_ID.$DATASET.$TABLE\`"

echo ""
echo "🎉 BigQuery load complete!"
echo "Next step: Run the Dataflow pipeline to import to Cloud SQL"
echo "  python gcs_to_cloudsql.py"
