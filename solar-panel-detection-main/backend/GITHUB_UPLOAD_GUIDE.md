# GitHub Upload Guide

This guide provides step-by-step instructions for uploading the backend to the GitHub repository.

## Repository Information

- **Repository**: https://github.com/RIFFAI-org/solar-potential-product
- **Previous Name**: solar-panel-detection
- **Current Name**: solar-potential-product

## Pre-Upload Checklist

### 1. Verify Sensitive Data Protection

Ensure `.gitignore` is properly configured:

```bash
# Check .gitignore exists
cat .gitignore

# Verify .env is ignored
git check-ignore .env
```

Expected output: `.env` (confirms it will be ignored)

### 2. Files to Upload

**Core API Files**:
- `api_bigquery.py` - Main API with BigQuery + weather integration
- `weather_service.py` - Weather service module
- `requirements.txt` - Python dependencies

**Docker Configuration**:
- `Dockerfile.bigquery` - Production Docker configuration
- `cloudbuild-bigquery.yaml` - Cloud Build configuration

**Documentation**:
- `README.md` - Backend overview and quick start
- `BACKEND.md` - Comprehensive API documentation
- `DEPLOYMENT.md` - Deployment guide

**Configuration Templates**:
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules

### 3. Files NOT to Upload

These files contain sensitive data and are already in `.gitignore`:

- `.env` - Contains API keys and database credentials
- `__pycache__/` - Python cache files
- `*.pyc` - Compiled Python files

## Upload Methods

### Method 1: Using Git Command Line (Recommended)

```bash
# Navigate to backend directory
cd solar-panel-detection-main/backend

# Initialize git if not already done
git init

# Add remote (if not already added)
git remote add origin https://github.com/RIFFAI-org/solar-potential-product.git

# Check current branch
git branch

# Create backend branch (optional, for organized upload)
git checkout -b backend-upload

# Add files
git add api_bigquery.py
git add weather_service.py
git add requirements.txt
git add Dockerfile.bigquery
git add cloudbuild-bigquery.yaml
git add README.md
git add BACKEND.md
git add DEPLOYMENT.md
git add .env.example
git add .gitignore

# Verify what will be committed (ensure .env is NOT listed)
git status

# Commit
git commit -m "Add backend API with BigQuery and weather integration

- Main API with 107M+ building footprints from BigQuery
- Weather forecasting integration (WxTech)
- Physics-based solar modeling (pvlib-python)
- Comprehensive API documentation
- Deployment guides for Google Cloud Run"

# Push to GitHub
git push origin backend-upload

# Or push to main branch
git checkout main
git merge backend-upload
git push origin main
```

### Method 2: Using GitHub Desktop

1. Open GitHub Desktop
2. Add repository: `https://github.com/RIFFAI-org/solar-potential-product`
3. Navigate to backend folder
4. Review changes (ensure `.env` is NOT listed)
5. Write commit message
6. Commit and push

### Method 3: Using GitHub Web Interface

1. Go to: https://github.com/RIFFAI-org/solar-potential-product
2. Click "Add file" > "Upload files"
3. Drag and drop files (DO NOT include `.env`)
4. Write commit message
5. Click "Commit changes"

## Verification Steps

### 1. Check Repository

Visit: https://github.com/RIFFAI-org/solar-potential-product

Verify these files are present:
- `backend/api_bigquery.py`
- `backend/weather_service.py`
- `backend/requirements.txt`
- `backend/Dockerfile.bigquery`
- `backend/cloudbuild-bigquery.yaml`
- `backend/README.md`
- `backend/BACKEND.md`
- `backend/DEPLOYMENT.md`
- `backend/.env.example`
- `backend/.gitignore`

### 2. Verify Sensitive Data NOT Uploaded

Check that these are NOT in the repository:
- `backend/.env` (should be blocked by .gitignore)
- `backend/__pycache__/`

### 3. Test Clone

```bash
# Clone repository
git clone https://github.com/RIFFAI-org/solar-potential-product.git
cd solar-potential-product/backend

# Verify files
ls -la

# Check .env does not exist (good!)
# Check .env.example exists (good!)
```

## Post-Upload Tasks

### 1. Update Repository Description

On GitHub repository page, add description:
```
Solar photovoltaic potential analysis API for Thailand's 107M+ buildings with real-time weather integration
```

### 2. Add Topics/Tags

Add these topics to the repository:
- `solar-energy`
- `photovoltaic`
- `thailand`
- `bigquery`
- `fastapi`
- `weather-api`
- `cloud-run`
- `pvlib`

### 3. Create README.md in Root

If not already present, create a root README.md that links to backend:

```markdown
# Solar Potential Product

Solar photovoltaic potential analysis for Thailand.

## Components

- [Backend API](./backend/README.md) - RESTful API with 107M+ building footprints
- [Documentation](./backend/BACKEND.md) - Comprehensive API reference

## Quick Links

- **API Endpoint**: https://solar-weather-api-715107904640.asia-southeast1.run.app
- **API Docs**: https://solar-weather-api-715107904640.asia-southeast1.run.app/docs
```

### 4. Set Up Branch Protection (Optional)

For production repositories:
1. Go to Settings > Branches
2. Add rule for `main` branch
3. Enable "Require pull request reviews before merging"

## Common Issues

### Issue: .env File Accidentally Uploaded

**Solution**:
```bash
# Remove from git history
git rm --cached .env
git commit -m "Remove .env from repository"
git push origin main

# Immediately rotate all credentials in .env
# Update WXTECH_API_KEY
# Update database passwords
```

### Issue: Large Files Rejected

**Error**: `file exceeds GitHub's file size limit of 100 MB`

**Solution**: Backend files are all small (<1 MB), this should not occur. If it does, check for accidentally included data files.

### Issue: Permission Denied

**Error**: `Permission denied (publickey)`

**Solution**: Set up SSH key or use HTTPS with personal access token:
```bash
git remote set-url origin https://github.com/RIFFAI-org/solar-potential-product.git
```

## Security Best Practices

### 1. Never Commit Secrets

- API keys
- Database passwords
- Service account keys
- Private keys

### 2. Use Environment Variables

All sensitive data should be in `.env` file (which is gitignored) and accessed via:
```python
import os
api_key = os.getenv("WXTECH_API_KEY")
```

### 3. Provide Templates

Always include `.env.example` with placeholder values:
```env
WXTECH_API_KEY=your_wxtech_api_key_here
```

### 4. Review Before Push

Always run before pushing:
```bash
git status
git diff --cached
```

Verify no sensitive files are included.

## Collaboration

### For Team Members

1. Clone repository
2. Copy `.env.example` to `.env`
3. Request credentials from team lead
4. Fill in `.env` with actual values
5. Never commit `.env`

### For Contributors

1. Fork repository
2. Create feature branch
3. Make changes
4. Submit pull request
5. Reference issues in PR description

## Maintenance

### Updating Documentation

When API changes:
1. Update `BACKEND.md` with new endpoints
2. Update `README.md` if architecture changes
3. Update `DEPLOYMENT.md` if deployment process changes
4. Commit with descriptive message

### Version Tagging

When releasing new version:
```bash
git tag -a v2.1.0 -m "Version 2.1.0 - BigQuery integration"
git push origin v2.1.0
```

## Support

For upload issues:
- Check GitHub status: https://www.githubstatus.com/
- Review GitHub documentation: https://docs.github.com/
- Contact repository administrator

---

**Last Updated**: March 30, 2026
