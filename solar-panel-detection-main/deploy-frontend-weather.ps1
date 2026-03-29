# Deploy Frontend with Weather API Integration
# March 2026 - Updated for Weather Features

$PROJECT_ID = "trim-descent-452802-t2"
$REGION = "asia-southeast1"
$BACKEND_SERVICE = "solar-weather-api"

Write-Host "🌐 Deploying Frontend with Weather Integration" -ForegroundColor Cyan

# Get backend URL
Write-Host "🔍 Getting backend URL..." -ForegroundColor Yellow
try {
    $BACKEND_URL = gcloud run services describe $BACKEND_SERVICE --region $REGION --format="value(status.url)"
    Write-Host "✅ Backend URL: $BACKEND_URL" -ForegroundColor Green
}
catch {
    Write-Host "❌ Could not get backend URL. Deploy backend first!" -ForegroundColor Red
    Write-Host "Run: .\deploy-weather-api.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if frontend exists
if (-not (Test-Path "frontend/package.json")) {
    Write-Host "❌ Frontend not found!" -ForegroundColor Red
    exit 1
}

Set-Location frontend

# Create/update .env for production
Write-Host "⚙️ Configuring frontend environment..." -ForegroundColor Yellow
$frontendEnv = @"
REACT_APP_API_URL=$BACKEND_URL
REACT_APP_BUILDINGS_API_URL=$BACKEND_URL
GENERATE_SOURCEMAP=false
"@

$frontendEnv | Out-File -FilePath ".env.production" -Encoding UTF8
Write-Host "✅ Frontend environment configured" -ForegroundColor Green

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ npm install failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Build for production
Write-Host "🔨 Building for production..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green

# Create app.yaml for App Engine
$appYaml = @"
runtime: nodejs18

handlers:
  # Serve static files
  - url: /static
    static_dir: build/static
    secure: always

  # Serve index.html for all routes (SPA)
  - url: /.*
    static_files: build/index.html
    upload: build/index.html
    secure: always

env_variables:
  REACT_APP_API_URL: "$BACKEND_URL"
  REACT_APP_BUILDINGS_API_URL: "$BACKEND_URL"

automatic_scaling:
  min_instances: 0
  max_instances: 10
"@

$appYaml | Out-File -FilePath "app.yaml" -Encoding UTF8

# Deploy to App Engine
Write-Host "🚀 Deploying to App Engine..." -ForegroundColor Cyan

gcloud app deploy --quiet

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    Set-Location ..
    exit 1
}

# Get frontend URL
$FRONTEND_URL = gcloud app describe --format="value(defaultHostname)"
$FRONTEND_URL = "https://$FRONTEND_URL"

Write-Host ""
Write-Host "🎉 Frontend deployment successful!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🌐 Frontend URL: $FRONTEND_URL" -ForegroundColor White
Write-Host "🔗 Backend API: $BACKEND_URL" -ForegroundColor White
Write-Host ""
Write-Host "🌟 New Features Available:" -ForegroundColor Green
Write-Host "   🌤️ Weather forecast panel" -ForegroundColor Gray
Write-Host "   ⚡ Weather-enhanced solar analysis" -ForegroundColor Gray
Write-Host "   📊 24h/7d generation outlook" -ForegroundColor Gray
Write-Host "   🎯 Weather impact scoring" -ForegroundColor Gray
Write-Host ""

# Test the deployment
Write-Host "🧪 Testing frontend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $FRONTEND_URL -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend is live!" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️ Frontend test failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   The service might still be starting up..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎯 Usage Instructions:" -ForegroundColor Cyan
Write-Host "1. Open: $FRONTEND_URL" -ForegroundColor White
Write-Host "2. Click '🌤️ Weather' button to see forecast" -ForegroundColor White
Write-Host "3. Click any building to see weather-enhanced solar analysis" -ForegroundColor White
Write-Host "4. View 24h generation forecast and weather impact" -ForegroundColor White

Set-Location ..