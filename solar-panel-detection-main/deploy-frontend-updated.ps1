# Deploy Updated Frontend to Firebase
# This script builds and deploys the frontend with new features

Write-Host "🚀 Deploying Updated Solar Panel Detection Frontend" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: frontend directory not found" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Navigate to frontend directory
Set-Location frontend

Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "🔨 Building production bundle..." -ForegroundColor Cyan
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Write-Host ""
Write-Host "🚀 Deploying to Firebase..." -ForegroundColor Cyan
firebase deploy --only hosting

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}

Set-Location ..

Write-Host ""
Write-Host "✅ Deployment successful!" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 New Features Deployed:" -ForegroundColor Cyan
Write-Host "  ✓ Dashboard with statistics and charts" -ForegroundColor White
Write-Host "  ✓ Search and filter functionality" -ForegroundColor White
Write-Host "  ✓ Client-side caching" -ForegroundColor White
Write-Host "  ✓ Responsive design for mobile" -ForegroundColor White
Write-Host "  ✓ Performance optimizations" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Your app is live at:" -ForegroundColor Cyan
Write-Host "   https://toothless-solar-frontend-715107904640.asia-southeast1.run.app" -ForegroundColor Yellow
Write-Host ""
