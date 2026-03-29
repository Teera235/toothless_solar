# Deploy Backend API with pvlib Support
# Updated: March 2026 - Added pvlib for professional solar calculations

Write-Host "🚀 Deploying Backend API with pvlib to Cloud Run..." -ForegroundColor Cyan
Write-Host ""
Write-Host "📦 This build includes:" -ForegroundColor Yellow
Write-Host "   ✓ pvlib-python 0.10.3 (Sandia National Labs)" -ForegroundColor White
Write-Host "   ✓ pandas 2.1.4 (data processing)" -ForegroundColor White
Write-Host "   ✓ numpy 1.26.2 (numerical computing)" -ForegroundColor White
Write-Host "   ✓ Hourly solar position calculation" -ForegroundColor White
Write-Host "   ✓ Temperature effects modeling" -ForegroundColor White
Write-Host "   ✓ Clear sky irradiance model" -ForegroundColor White
Write-Host ""

# Configuration
$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"
$SERVICE_NAME = "buildings-api"
$IMAGE_NAME = "buildings-api-bq"

# Navigate to backend directory
Set-Location backend

Write-Host "⏳ Building Docker image with --no-cache (this may take 3-5 minutes due to pvlib dependencies)..." -ForegroundColor Yellow
$buildStart = Get-Date

gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE_NAME --timeout=15m --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

$buildEnd = Get-Date
$buildDuration = ($buildEnd - $buildStart).TotalSeconds
Write-Host "✅ Build completed in $([math]::Round($buildDuration, 1)) seconds" -ForegroundColor Green
Write-Host ""

Write-Host "☁️ Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 120 `
    --max-instances 10 `
    --min-instances 0

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "✅ Deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 API URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "📚 API Docs: $SERVICE_URL/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 Test pvlib calculation:" -ForegroundColor Yellow
Write-Host "   POST $SERVICE_URL/solar/calculate" -ForegroundColor White
Write-Host '   Body: {"latitude": 13.7563, "longitude": 100.5018, "area_m2": 250, "confidence": 0.95}' -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Expected improvements:" -ForegroundColor Yellow
Write-Host "   • Accuracy: ±5-8% (vs ±15-20% simplified)" -ForegroundColor White
Write-Host "   • Temperature effects: -6% adjustment for Thailand" -ForegroundColor White
Write-Host "   • Hourly simulation: 8,760 data points/year" -ForegroundColor White
Write-Host "   • Clear sky model: Ineichen-Perez standard" -ForegroundColor White
Write-Host ""

# Return to root directory
Set-Location ..
