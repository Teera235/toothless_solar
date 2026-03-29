# Simple Deploy - Weather API Backend Only
Write-Host "🚀 Deploying Weather API Backend" -ForegroundColor Cyan

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"
$SERVICE_NAME = "solar-weather-api"

# Check environment
if (-not (Test-Path "backend/.env")) {
    Write-Host "❌ backend/.env not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment OK" -ForegroundColor Green

# Build and deploy
Set-Location backend

Write-Host "🔨 Building..." -ForegroundColor Yellow
gcloud builds submit --config=cloudbuild-weather.yaml --timeout=15m

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Deploying..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/solar-weather-api --platform managed --region $REGION --allow-unauthenticated --memory 1Gi --timeout 300

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deploy failed!" -ForegroundColor Red
    exit 1
}

$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "✅ Deployed!" -ForegroundColor Green
Write-Host "URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "Docs: $SERVICE_URL/docs" -ForegroundColor Gray

Set-Location ..