# Load CSV files from GCS to BigQuery
# This is MUCH faster than trying to process CSVs directly in Dataflow

$PROJECT_ID = "trim-descent-452802-t2"
$DATASET = "openbuildings"
$TABLE = "thailand_raw"
$GCS_PATH = "gs://trim-descent-452802-t2-openbuildings-v3/thailand/*.csv.gz"

Write-Host "🚀 Loading Google Open Buildings data to BigQuery..." -ForegroundColor Green
Write-Host "📦 Project: $PROJECT_ID"
Write-Host "📊 Dataset: $DATASET"
Write-Host "📋 Table: $TABLE"
Write-Host "📂 Source: $GCS_PATH"
Write-Host ""

# Create dataset if not exists
Write-Host "📊 Creating dataset..." -ForegroundColor Yellow
bq mk --dataset --location=asia-southeast1 "$PROJECT_ID`:$DATASET" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dataset already exists or created" -ForegroundColor Gray
}

# Load data
Write-Host "📥 Loading data (this may take 10-30 minutes for millions of rows)..." -ForegroundColor Yellow
bq load `
  --source_format=CSV `
  --skip_leading_rows=1 `
  --autodetect `
  --replace `
  --location=asia-southeast1 `
  "$PROJECT_ID`:$DATASET.$TABLE" `
  "$GCS_PATH"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to load data" -ForegroundColor Red
    exit 1
}

# Check row count
Write-Host ""
Write-Host "✅ Data loaded! Checking row count..." -ForegroundColor Green
bq query --use_legacy_sql=false `
  "SELECT COUNT(*) as total_rows FROM ``$PROJECT_ID.$DATASET.$TABLE``"

Write-Host ""
Write-Host "🎉 BigQuery load complete!" -ForegroundColor Green
Write-Host "Next step: Run the Dataflow pipeline to import to Cloud SQL"
Write-Host "  python gcs_to_cloudsql.py"
