# Deploy Backend API with pvlib Support
# Updated: March 2026

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"
$SERVICE_NAME = "buildings-api"
$IMAGE_NAME = "buildings-api-bq"

Write-Host "Building Docker image with pvlib (no cache)..." -ForegroundColor Cyan

Set-Location backend

# Enable Kaniko for --no-cache support
gcloud config set builds/use_kaniko True

gcloud builds submit --config=cloudbuild.yaml --timeout=15m

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Cyan

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
    Write-Host "Deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host ""
Write-Host "Deployment successful!" -ForegroundColor Green
Write-Host "API URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "API Docs: $SERVICE_URL/docs" -ForegroundColor Cyan
Write-Host ""

Set-Location ..
