# Deploy Frontend to Firebase Hosting
# One-click deployment script

param(
    [string]$ProjectId = "trim-descent-452802-t2",
    [string]$ApiUrl = "https://buildings-api-715107904640.asia-southeast1.run.app"
)

Write-Host "🚀 Deploying Frontend to Firebase Hosting" -ForegroundColor Green
Write-Host "=" * 60

# Check if in correct directory
if (-not (Test-Path "frontend")) {
    Write-Host "❌ Error: Must run from sushi/ directory" -ForegroundColor Red
    exit 1
}

# Check if Firebase CLI is installed
Write-Host "`n📦 Checking Firebase CLI..."
$firebaseInstalled = Get-Command firebase -ErrorAction SilentlyContinue
if (-not $firebaseInstalled) {
    Write-Host "⚠️  Firebase CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g firebase-tools
}

# Update .env with API URL
Write-Host "`n🔧 Updating API URL..."
$envContent = "REACT_APP_BUILDINGS_API_URL=$ApiUrl"
Set-Content -Path "frontend/.env" -Value $envContent
Write-Host "✅ API URL: $ApiUrl"

# Install dependencies
Write-Host "`n📦 Installing dependencies..."
Set-Location frontend
npm install

# Build
Write-Host "`n🔨 Building frontend..."
npm run build

if (-not (Test-Path "build")) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build completed"

# Check if Firebase is initialized
if (-not (Test-Path "firebase.json")) {
    Write-Host "`n🔧 Initializing Firebase..."
    Write-Host "⚠️  Please follow the prompts:" -ForegroundColor Yellow
    Write-Host "   - Select: Use existing project"
    Write-Host "   - Project: $ProjectId"
    Write-Host "   - Public directory: build"
    Write-Host "   - Single-page app: Yes"
    Write-Host "   - GitHub deploys: No"
    
    firebase init hosting
}

# Deploy
Write-Host "`n🚀 Deploying to Firebase..."
firebase deploy --only hosting --project $ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n" + ("=" * 60)
    Write-Host "🎉 Deployment completed!" -ForegroundColor Green
    Write-Host ("=" * 60)
    
    # Get hosting URL
    Write-Host "`n📝 Getting hosting URL..."
    $hostingUrl = "https://$ProjectId.web.app"
    
    Write-Host "`n✅ Frontend deployed successfully!"
    Write-Host "🌐 URL: $hostingUrl" -ForegroundColor Cyan
    Write-Host "`n📊 Next steps:"
    Write-Host "   1. Open: $hostingUrl"
    Write-Host "   2. Test the map and building data"
    Write-Host "   3. Check browser console for errors"
    
    # Open in browser
    Write-Host "`n🌐 Opening in browser..."
    Start-Process $hostingUrl
    
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    Write-Host "💡 Troubleshooting:"
    Write-Host "   1. Check if you're logged in: firebase login"
    Write-Host "   2. Check project access: firebase projects:list"
    Write-Host "   3. Try manual deploy: firebase deploy --only hosting"
}

Set-Location ..
