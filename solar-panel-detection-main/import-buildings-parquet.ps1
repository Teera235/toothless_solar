# Master script to import using Parquet format
# Parquet is 5-10x smaller and much faster than CSV!

param(
    [switch]$SkipConversion = $false,
    [switch]$SkipBigQuery = $false,
    [switch]$DirectImport = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Building Import Pipeline (Parquet Edition)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ID = "trim-descent-452802-t2"

# Step 0: Convert CSV to Parquet (if needed)
if (-not $SkipConversion) {
    Write-Host "[STEP 0] Converting CSV to Parquet..." -ForegroundColor Yellow
    Write-Host "This will save 80-90% storage and make loading much faster" -ForegroundColor Gray
    Write-Host ""
    
    # Check if dependencies are installed
    $pandasInstalled = python -c "import pandas" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install pandas pyarrow google-cloud-storage
    }
    
    Push-Location dataflow
    try {
        python convert_csv_to_parquet.py
        if ($LASTEXITCODE -ne 0) {
            throw "Conversion failed"
        }
    } finally {
        Pop-Location
    }
    
    Write-Host ""
    Write-Host "[OK] Conversion complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[SKIP] Skipping CSV to Parquet conversion" -ForegroundColor Gray
    Write-Host ""
}

# Step 1: Load to BigQuery (unless using direct import)
if (-not $DirectImport -and -not $SkipBigQuery) {
    Write-Host "[STEP 1] Loading Parquet to BigQuery..." -ForegroundColor Yellow
    Write-Host "Parquet loads 5-10x faster than CSV!" -ForegroundColor Gray
    Write-Host ""
    
    Push-Location dataflow
    try {
        .\load_parquet_to_bigquery.ps1
        if ($LASTEXITCODE -ne 0) {
            throw "BigQuery load failed"
        }
    } finally {
        Pop-Location
    }
    
    Write-Host ""
    Write-Host "[OK] BigQuery load complete!" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Import to Cloud SQL
Write-Host "[STEP 2] Importing to Cloud SQL..." -ForegroundColor Yellow
Write-Host ""

if ($DirectImport) {
    Write-Host "Using direct import from Parquet files..." -ForegroundColor Gray
    Write-Host ""
    
    Push-Location dataflow
    try {
        python import_from_parquet.py
        if ($LASTEXITCODE -ne 0) {
            throw "Import failed"
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Using BigQuery as intermediate..." -ForegroundColor Gray
    Write-Host ""
    
    # Check if dependencies are installed
    $bqInstalled = python -c "from google.cloud import bigquery" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing dependencies..." -ForegroundColor Yellow
        pip install google-cloud-bigquery psycopg2-binary
    }
    
    Push-Location dataflow
    try {
        python import_from_bigquery.py
        if ($LASTEXITCODE -ne 0) {
            throw "Import failed"
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "[OK] Import complete!" -ForegroundColor Green
Write-Host ""

# Step 3: Verify
Write-Host "[STEP 3] Verifying data..." -ForegroundColor Yellow
Write-Host ""

$apiUrl = "https://buildings-api-715107904640.asia-southeast1.run.app/stats"
try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get
    Write-Host "[OK] API Response:" -ForegroundColor Green
    Write-Host "   Total buildings: $($response.total_buildings)" -ForegroundColor White
    Write-Host "   Avg confidence: $($response.confidence.average)" -ForegroundColor White
    Write-Host "   Avg area: $($response.area_m2.average) m2" -ForegroundColor White
} catch {
    Write-Host "[WARNING] Could not reach API" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[SUCCESS] All done!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open frontend: https://toothless-solar-frontend-715107904640.asia-southeast1.run.app"
Write-Host "  2. Check API: https://buildings-api-715107904640.asia-southeast1.run.app/stats"
Write-Host "  3. View buildings on map"
Write-Host ""

Write-Host "Usage examples:" -ForegroundColor Gray
Write-Host "  .\import-buildings-parquet.ps1                    # Full pipeline"
Write-Host "  .\import-buildings-parquet.ps1 -SkipConversion    # Skip CSV conversion"
Write-Host "  .\import-buildings-parquet.ps1 -DirectImport      # Skip BigQuery, import directly"
Write-Host "  .\import-buildings-parquet.ps1 -SkipBigQuery      # Skip BigQuery load"
