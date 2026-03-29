# Deploy Weather-Enhanced Solar API to Google Cloud Run
# March 2026 - With WxTech Weather Integration

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"
$SERVICE_NAME = "solar-weather-api"
$IMAGE_NAME = "solar-weather-api"

Write-Host "🌤️ Deploying Weather-Enhanced Solar API" -ForegroundColor Cyan
Write-Host "Project: $PROJECT_ID" -ForegroundColor Gray
Write-Host "Region: $REGION" -ForegroundColor Gray
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "backend/api_weather_only.py")) {
    Write-Host "❌ api_weather_only.py not found! Run from project root." -ForegroundColor Red
    exit 1
}

# Check if .env exists with API key
if (-not (Test-Path "backend/.env")) {
    Write-Host "❌ backend/.env not found!" -ForegroundColor Red
    Write-Host "Create backend/.env with: WXTECH_API_KEY=your_key" -ForegroundColor Yellow
    exit 1
}

$envContent = Get-Content "backend/.env" -Raw
if ($envContent -notmatch "WXTECH_API_KEY=") {
    Write-Host "❌ WXTECH_API_KEY not found in .env!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment configured" -ForegroundColor Green

# Create Cloud Build config for weather API
$cloudbuildConfig = @"
steps:
  # Build the Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'Dockerfile.weather', '-t', 'gcr.io/$PROJECT_ID/$IMAGE_NAME', '.']
    
  # Push the image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/$IMAGE_NAME']

images:
  - 'gcr.io/$PROJECT_ID/$IMAGE_NAME'

options:
  machineType: 'E2_HIGHCPU_8'
  
timeout: '900s'
"@

$cloudbuildConfig | Out-File -FilePath "backend/cloudbuild-weather.yaml" -Encoding UTF8

Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
Set-Location backend

# Enable Kaniko for better caching
gcloud config set builds/use_kaniko True

# Submit build
gcloud builds submit --config=cloudbuild-weather.yaml --timeout=15m

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Cyan

gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 1 `
    --timeout 300 `
    --max-instances 20 `
    --min-instances 1 `
    --set-env-vars "WXTECH_API_KEY=$(Get-Content ..\.env | Select-String 'WXTECH_API_KEY=' | ForEach-Object { $_.ToString().Split('=')[1] })"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Get service URL
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "🎉 Deployment successful!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🌐 API URL: $SERVICE_URL" -ForegroundColor White
Write-Host "📚 API Docs: $SERVICE_URL/docs" -ForegroundColor White
Write-Host ""
Write-Host "🌤️ Weather Endpoints:" -ForegroundColor Green
Write-Host "   GET $SERVICE_URL/weather/forecast?lat=13.7563`&lon=100.5018" -ForegroundColor Gray
Write-Host "   GET $SERVICE_URL/solar/forecast?lat=13.7563`&lon=100.5018`&system_kwp=5" -ForegroundColor Gray
Write-Host "   POST $SERVICE_URL/test/mock-building" -ForegroundColor Gray
Write-Host ""
Write-Host "🧪 Test Commands:" -ForegroundColor Yellow
Write-Host "   curl `"$SERVICE_URL/health`"" -ForegroundColor Gray
Write-Host "   curl `"$SERVICE_URL/weather/forecast?lat=13.7563`&lon=100.5018`"" -ForegroundColor Gray
Write-Host ""

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$SERVICE_URL/health" -TimeoutSec 10
    Write-Host "✅ Health check: $($healthResponse.status)" -ForegroundColor Green
    
    $weatherResponse = Invoke-RestMethod -Uri "$SERVICE_URL/weather/forecast?lat=13.7563`&lon=100.5018" -TimeoutSec 15
    Write-Host "✅ Weather API: $($weatherResponse.impact_summary.impact_level) conditions" -ForegroundColor Green
    Write-Host "   📊 $($weatherResponse.hourly_count) hourly + $($weatherResponse.daily_count) daily forecasts" -ForegroundColor Gray
}
catch {
    Write-Host "⚠️ API test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   The service might still be starting up..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Update frontend API_BASE_URL to: $SERVICE_URL" -ForegroundColor White
Write-Host "2. Deploy frontend with updated config" -ForegroundColor White
Write-Host "3. Test weather integration on live site" -ForegroundColor White

Set-Location ..