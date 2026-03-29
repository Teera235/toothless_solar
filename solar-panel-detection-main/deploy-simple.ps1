# Simple deployment script for GCP
param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$CloudSqlInstance = "nabha-solar-db",
    [string]$DbPassword = "toothless_solar_2024",
    [string]$Region = "asia-southeast1"
)

Write-Host "🚀 Deploying Toothless Solar Dashboard to GCP" -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Build and push Docker image
Write-Host "Building and pushing Docker image..." -ForegroundColor Yellow
Set-Location backend
gcloud builds submit --tag gcr.io/$ProjectId/buildings-api
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Docker image built successfully" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
$CloudSqlConnection = "${ProjectId}:${Region}:${CloudSqlInstance}"

gcloud run deploy buildings-api `
    --image gcr.io/$ProjectId/buildings-api `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "DB_HOST=/cloudsql/${ProjectId}:${Region}:${CloudSqlInstance}" `
    --set-env-vars "DB_NAME=toothless_solar" `
    --set-env-vars "DB_USER=postgres" `
    --set-env-vars "DB_PASSWORD=$DbPassword" `
    --set-env-vars "DB_PORT=5432" `
    --add-cloudsql-instances "${ProjectId}:${Region}:${CloudSqlInstance}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Cloud Run deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Backend API deployed successfully" -ForegroundColor Green

# Get API URL
$ApiUrl = gcloud run services describe buildings-api --region $Region --format 'value(status.url)'
Write-Host "Backend API URL: $ApiUrl" -ForegroundColor Green

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Set-Location ../frontend

# Update environment file
"REACT_APP_BUILDINGS_API_URL=$ApiUrl" | Out-File -FilePath .env -Encoding utf8

# Build frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Frontend built successfully" -ForegroundColor Green

Write-Host "`n✅ Deployment complete!" -ForegroundColor Green
Write-Host "Backend URL: $ApiUrl" -ForegroundColor Cyan