# Build All Components
# This script builds both frontend and backend

Write-Host "🔨 Building Solar Panel Detection System" -ForegroundColor Green
Write-Host ""

$ErrorActionPreference = "Stop"

# Build Frontend
Write-Host "📦 Building Frontend..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Set-Location frontend

Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "Building production bundle..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ Frontend built successfully" -ForegroundColor Green
Set-Location ..

# Build Backend
Write-Host ""
Write-Host "🐍 Building Backend..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

Set-Location backend

# Copy BigQuery Dockerfile
Write-Host "Preparing Dockerfile..." -ForegroundColor Yellow
Copy-Item Dockerfile.bigquery Dockerfile -Force

Write-Host "Building Docker image..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/trim-descent-452802-t2/buildings-api-bq --timeout=10m

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host "✅ Backend built successfully" -ForegroundColor Green
Set-Location ..

# Summary
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ Build Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Built Components:" -ForegroundColor Cyan
Write-Host "   ✓ Frontend (React app)" -ForegroundColor White
Write-Host "   ✓ Backend (Docker image)" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Test locally: cd frontend && npm start" -ForegroundColor White
Write-Host "   2. Deploy frontend: .\deploy-frontend-updated.ps1" -ForegroundColor White
Write-Host "   3. Deploy backend: cd backend && gcloud run deploy..." -ForegroundColor White
Write-Host "   4. Run tests: .\test-features.ps1" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   - Quick Start: QUICK-START.md" -ForegroundColor White
Write-Host "   - Features: FEATURES.md" -ForegroundColor White
Write-Host "   - Deployment: DEPLOYMENT.md" -ForegroundColor White
Write-Host ""
