# Load Parquet files from GCS to BigQuery
# Parquet is much faster to load than CSV!

$PROJECT_ID = "trim-descent-452802-t2"
$DATASET = "openbuildings"
$TABLE = "thailand_raw"
$GCS_PATH = "gs://trim-descent-452802-t2-openbuildings-v3/thailand-parquet/*.parquet"

Write-Host "Loading Parquet files to BigQuery..." -ForegroundColor Green
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Dataset: $DATASET" -ForegroundColor Gray
Write-Host "Table: $TABLE" -ForegroundColor Gray
Write-Host "Source: $GCS_PATH" -ForegroundColor Gray
Write-Host ""

# Create dataset if not exists
Write-Host "Creating dataset..." -ForegroundColor Yellow
bq mk --dataset --location=asia-southeast1 "$PROJECT_ID`:$DATASET" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Dataset already exists or created" -ForegroundColor Gray
}

# Load Parquet data
Write-Host "Loading Parquet files (this is MUCH faster than CSV)..." -ForegroundColor Yellow
bq load `
  --source_format=PARQUET `
  --replace `
  --location=asia-southeast1 `
  "$PROJECT_ID`:$DATASET.$TABLE" `
  "$GCS_PATH"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to load data" -ForegroundColor Red
    exit 1
}

# Check row count
Write-Host ""
Write-Host "[OK] Data loaded! Checking row count..." -ForegroundColor Green
bq query --use_legacy_sql=false `
  "SELECT COUNT(*) as total_rows FROM ``$PROJECT_ID.$DATASET.$TABLE``"

Write-Host ""
Write-Host "[SUCCESS] BigQuery load complete!" -ForegroundColor Green
Write-Host "Next step: Import to Cloud SQL" -ForegroundColor Cyan
Write-Host "  python import_from_bigquery.py" -ForegroundColor White
