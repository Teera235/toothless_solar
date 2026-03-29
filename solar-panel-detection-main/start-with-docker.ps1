# Start the weather-enhanced backend using Docker
Write-Host "🐳 Starting Solar Panel Detection with Weather API (Docker)" -ForegroundColor Cyan

# Check if Docker is available
try {
    docker --version | Out-Null
    Write-Host "✅ Docker is available" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker not found! Please install Docker Desktop" -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
Set-Location backend

try {
    docker build -f Dockerfile.bigquery -t solar-weather-api .
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
    exit 1
}

# Stop any existing container
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Gray
docker stop solar-weather-api-container 2>$null
docker rm solar-weather-api-container 2>$null

# Run the container
Write-Host "🚀 Starting container..." -ForegroundColor Cyan
Write-Host "Backend will be available at: http://localhost:8080" -ForegroundColor White
Write-Host "API docs at: http://localhost:8080/docs" -ForegroundColor White
Write-Host ""
Write-Host "Weather endpoints:" -ForegroundColor Green
Write-Host "  GET /weather/forecast?lat=13.7563&lon=100.5018" -ForegroundColor Gray
Write-Host "  GET /solar/forecast?lat=13.7563&lon=100.5018&system_kwp=5" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    docker run --name solar-weather-api-container -p 8080:8080 solar-weather-api
}
catch {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
}