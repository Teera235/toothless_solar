# Prepare Backend for GitHub Upload
# This script helps verify files are ready for upload

Write-Host "=== Preparing Backend for GitHub Upload ===" -ForegroundColor Cyan
Write-Host ""

# Check if .gitignore exists
if (Test-Path ".gitignore") {
    Write-Host "[OK] .gitignore exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] .gitignore missing!" -ForegroundColor Red
    exit 1
}

# Check if .env.example exists
if (Test-Path ".env.example") {
    Write-Host "[OK] .env.example exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] .env.example missing!" -ForegroundColor Red
    exit 1
}

# Verify .env is in .gitignore
$gitignoreContent = Get-Content ".gitignore" -Raw
if ($gitignoreContent -match "\.env") {
    Write-Host "[OK] .env is in .gitignore" -ForegroundColor Green
} else {
    Write-Host "[WARNING] .env not found in .gitignore!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Files to Upload ===" -ForegroundColor Cyan

$filesToUpload = @(
    "api_bigquery.py",
    "weather_service.py",
    "requirements.txt",
    "Dockerfile.bigquery",
    "cloudbuild-bigquery.yaml",
    "README.md",
    "BACKEND.md",
    "DEPLOYMENT.md",
    ".env.example",
    ".gitignore"
)

foreach ($file in $filesToUpload) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "[OK] $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $file" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Files to EXCLUDE ===" -ForegroundColor Cyan

$filesToExclude = @(
    ".env",
    "__pycache__"
)

foreach ($file in $filesToExclude) {
    if (Test-Path $file) {
        Write-Host "[WARNING] $file exists (will be ignored by git)" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] $file not present" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Security Check ===" -ForegroundColor Cyan

# Check for hardcoded API keys in Python files
$pythonFiles = Get-ChildItem -Filter "*.py"
$foundSecrets = $false

foreach ($file in $pythonFiles) {
    $content = Get-Content $file.FullName -Raw
    
    # Check for potential hardcoded API keys (simplified check)
    if ($content -match 'WXTECH_API_KEY\s*=\s*"[A-Za-z0-9]{30,}"') {
        Write-Host "[WARNING] Potential hardcoded API key in $($file.Name)" -ForegroundColor Red
        $foundSecrets = $true
    }
    
    # Check for hardcoded passwords
    if ($content -match 'DB_PASSWORD\s*=\s*"[A-Za-z0-9_]{8,}"') {
        Write-Host "[WARNING] Potential hardcoded password in $($file.Name)" -ForegroundColor Red
        $foundSecrets = $true
    }
}

if (-not $foundSecrets) {
    Write-Host "[OK] No hardcoded secrets detected" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Ready to upload to: https://github.com/RIFFAI-org/solar-potential-product" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Review GITHUB_UPLOAD_GUIDE.md for detailed instructions" -ForegroundColor White
Write-Host "2. Use git commands to add and commit files" -ForegroundColor White
Write-Host "3. Push to GitHub repository" -ForegroundColor White
Write-Host ""
Write-Host "Quick upload commands:" -ForegroundColor Yellow
Write-Host "  git add api_bigquery.py weather_service.py requirements.txt" -ForegroundColor Gray
Write-Host "  git add Dockerfile.bigquery cloudbuild-bigquery.yaml" -ForegroundColor Gray
Write-Host "  git add README.md BACKEND.md DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "  git add .env.example .gitignore" -ForegroundColor Gray
Write-Host "  git commit -m `"Add backend API with BigQuery and weather integration`"" -ForegroundColor Gray
Write-Host "  git push origin main" -ForegroundColor Gray
Write-Host ""
