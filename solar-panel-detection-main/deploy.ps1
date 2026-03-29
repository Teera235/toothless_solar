# Deploy Toothless Solar Dashboard to GCP
# PowerShell script for Windows

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$true)]
    [string]$CloudSqlInstance,
    
    [Parameter(Mandatory=$true)]
    [string]$DbPassword,
    
    [string]$Region = "asia-southeast1"
)

Write-Host "🚀 Deploying Toothless Solar Dashboard to GCP" -ForegroundColor Green
Write-Host "📍 Project: $ProjectId" -ForegroundColor Cyan
Write-Host "📍 Region: $Region" -ForegroundColor Cyan
Write-Host ""

# Set project
Write-Host "⚙️ Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Build and push Docker image
Write-Host "`n🐳 Building Docker image..." -ForegroundColor Yellow
Set-Location backend

Write-Host "Building and pushing Docker image to Container Registry..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$ProjectId/buildings-api

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker image built successfully" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host "`n🚀 Deploying to Cloud Run..." -ForegroundColor Yellow

$CloudSqlConnection = "${ProjectId}:${Region}:${CloudSqlInstance}"

Write-Host "Deploying Cloud Run service..." -ForegroundColor Yellow
gcloud run deploy buildings-api `
    --image gcr.io/$ProjectId/buildings-api `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300 `
    --max-instances 10 `
    --set-env-vars "DB_HOST=/cloudsql/$CloudSqlConnection" `
    --set-env-vars "DB_NAME=toothless_solar" `
    --set-env-vars "DB_USER=postgres" `
    --set-env-vars "DB_PASSWORD=$DbPassword" `
    --set-env-vars "DB_PORT=5432" `
    --add-cloudsql-instances $CloudSqlConnection

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Cloud Run deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Backend API deployed successfully" -ForegroundColor Green

# Get API URL
Write-Host "`n📡 Getting API URL..." -ForegroundColor Yellow
$ApiUrl = gcloud run services describe buildings-api --region $Region --format 'value(status.url)' 2>$null

if (-not $ApiUrl) {
    $ApiUrl = gcloud run services describe buildings-api --region $Region --format 'value(status.url)'
}

Write-Host "`n✅ Backend API URL: $ApiUrl" -ForegroundColor Green

# Test the API
Write-Host "`n🧪 Testing API..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "$ApiUrl/stats" -UseBasicParsing -TimeoutSec 30
    $stats = $response.Content | ConvertFrom-Json
    Write-Host "✅ API is working!" -ForegroundColor Green
    Write-Host "📊 Total buildings: $($stats.total_buildings)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ API test failed, but deployment completed" -ForegroundColor Yellow
    Write-Host "   Please check Cloud Run logs for details" -ForegroundColor Yellow
}

# Deploy frontend
Write-Host "`n🌐 Building frontend..." -ForegroundColor Yellow
Set-Location ../frontend

# Update environment variable
Write-Host "⚙️ Updating frontend configuration..." -ForegroundColor Yellow
"REACT_APP_BUILDINGS_API_URL=$ApiUrl" | Out-File -FilePath .env -Encoding utf8

# Build frontend
Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend built successfully" -ForegroundColor Green

# Check for Firebase
if (Test-Path "firebase.json") {
    Write-Host "🔥 Deploying to Firebase..." -ForegroundColor Yellow
    firebase deploy --only hosting
} else {
    Write-Host "⚠️ Firebase not configured. Build output in build/ folder" -ForegroundColor Yellow
}

# Summary
Write-Host "`n🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "`n📊 Summary:" -ForegroundColor Yellow
Write-Host "  Backend API: $ApiUrl" -ForegroundColor Cyan
Write-Host "  Cloud SQL: $CloudSqlInstance" -ForegroundColor Cyan
Write-Host "  Region: $Region" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test API: $ApiUrl/stats"
Write-Host "  2. Deploy frontend to Firebase or hosting service"
Write-Host "  3. Configure DNS if using custom domain"