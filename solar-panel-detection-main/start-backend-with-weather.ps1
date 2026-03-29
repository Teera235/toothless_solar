# Start backend with weather API support
Write-Host "🚀 Starting Solar Panel Detection Backend with Weather API" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "❌ backend\.env file not found!" -ForegroundColor Red
    Write-Host "Please create backend\.env with:" -ForegroundColor Yellow
    Write-Host "WXTECH_API_KEY=your_api_key_here" -ForegroundColor Gray
    exit 1
}

# Check if API key is set
$envContent = Get-Content "backend\.env" -Raw
if ($envContent -notmatch "WXTECH_API_KEY=") {
    Write-Host "❌ WXTECH_API_KEY not found in .env file!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Environment configured" -ForegroundColor Green

# Install dependencies if needed
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
try {
    Set-Location backend
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}
catch {
    Write-Host "⚠️ Could not install dependencies automatically" -ForegroundColor Yellow
    Write-Host "Please run: pip install -r backend/requirements.txt" -ForegroundColor Gray
}

# Start the server
Write-Host "🌐 Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:8080" -ForegroundColor White
Write-Host "API docs at: http://localhost:8080/docs" -ForegroundColor White
Write-Host ""
Write-Host "New weather endpoints:" -ForegroundColor Green
Write-Host "  GET /weather/forecast?lat=13.7563`&lon=100.5018" -ForegroundColor Gray
Write-Host "  GET /solar/forecast?lat=13.7563`&lon=100.5018`&system_kwp=5" -ForegroundColor Gray
Write-Host ""

try {
    uvicorn api_bigquery:app --host 0.0.0.0 --port 8080 --reload
}
catch {
    Write-Host "❌ Failed to start server" -ForegroundColor Red
    Write-Host "Make sure uvicorn is installed: pip install uvicorn" -ForegroundColor Gray
}