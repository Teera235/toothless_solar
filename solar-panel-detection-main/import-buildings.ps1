# Master script to import Google Open Buildings data
# This orchestrates the entire import process

param(
    [switch]$SkipBigQuery = $false,
    [switch]$UseDataflow = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🏗️  Google Open Buildings Import Pipeline" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"

# Step 1: Load to BigQuery (unless skipped)
if (-not $SkipBigQuery) {
    Write-Host "📊 STEP 1: Loading CSV files to BigQuery..." -ForegroundColor Yellow
    Write-Host "This will take 10-30 minutes for millions of rows" -ForegroundColor Gray
    Write-Host ""
    
    Push-Location dataflow
    try {
        .\load_to_bigquery.ps1
        if ($LASTEXITCODE -ne 0) {
            throw "BigQuery load failed"
        }
    } finally {
        Pop-Location
    }
    
    Write-Host ""
    Write-Host "✅ BigQuery load complete!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "⏭️  Skipping BigQuery load (--SkipBigQuery flag set)" -ForegroundColor Gray
    Write-Host ""
}

# Step 2: Import to Cloud SQL
Write-Host "🗄️  STEP 2: Importing from BigQuery to Cloud SQL..." -ForegroundColor Yellow
Write-Host ""

if ($UseDataflow) {
    Write-Host "Using Dataflow (distributed processing)..." -ForegroundColor Gray
    Write-Host ""
    
    # Check if Apache Beam is installed
    $beamInstalled = python -c "import apache_beam" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
        pip install -r dataflow/requirements.txt
    }
    
    # Run Dataflow pipeline
    Push-Location dataflow
    try {
        python gcs_to_cloudsql.py
        if ($LASTEXITCODE -ne 0) {
            throw "Dataflow pipeline failed"
        }
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Using direct import (simpler, works for millions of rows)..." -ForegroundColor Gray
    Write-Host ""
    
    # Check if dependencies are installed
    $bqInstalled = python -c "from google.cloud import bigquery" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
        pip install google-cloud-bigquery psycopg2-binary
    }
    
    # Run import script
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
Write-Host "✅ Import complete!" -ForegroundColor Green
Write-Host ""

# Step 3: Verify
Write-Host "🔍 STEP 3: Verifying data..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Checking API stats..." -ForegroundColor Gray
$apiUrl = "https://buildings-api-715107904640.asia-southeast1.run.app/stats"
try {
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get
    Write-Host "✅ API Response:" -ForegroundColor Green
    Write-Host "   Total buildings: $($response.total_buildings)" -ForegroundColor White
    Write-Host "   Avg confidence: $($response.confidence.average)" -ForegroundColor White
    Write-Host "   Avg area: $($response.area_m2.average) m²" -ForegroundColor White
} catch {
    Write-Host "⚠️  Could not reach API (may need to wait for Cloud Run to start)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 All done!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Open frontend: https://toothless-solar-frontend-715107904640.asia-southeast1.run.app"
Write-Host "  2. Check API: https://buildings-api-715107904640.asia-southeast1.run.app/stats"
Write-Host "  3. View buildings on map (zoom in to see polygons)"
Write-Host ""

# Usage examples
Write-Host "Usage examples:" -ForegroundColor Gray
Write-Host "  .\import-buildings.ps1                    # Full import (BigQuery + Cloud SQL)"
Write-Host "  .\import-buildings.ps1 -SkipBigQuery      # Skip BigQuery load (if already done)"
Write-Host "  .\import-buildings.ps1 -UseDataflow       # Use Dataflow instead of direct import"
