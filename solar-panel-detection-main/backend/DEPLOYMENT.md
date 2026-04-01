# Deployment Guide

This guide covers deploying the Solar Potential API to Google Cloud Run.

## Prerequisites

1. **Google Cloud SDK** installed and configured
   ```bash
   gcloud --version
   ```

2. **GCP Project** with the following APIs enabled:
   - Cloud Run API
   - Cloud Build API
   - BigQuery API
   - Container Registry API

3. **BigQuery Dataset** with Google Open Buildings data:
   - Dataset: `openbuildings`
   - Table: `thailand_raw`
   - Records: 107,682,789 building footprints

4. **WxTech API Key** (optional, for weather features)
   - Sign up at: https://wxtech.weathernews.com/

## Configuration

### 1. Set GCP Project

```bash
gcloud config set project YOUR_PROJECT_ID
```

### 2. Update Cloud Build Configuration

Edit `cloudbuild-bigquery.yaml` and replace project ID:

```yaml
- 'gcr.io/YOUR_PROJECT_ID/solar-bigquery-api'
```

### 3. Configure Environment Variables

The API requires these environment variables:

- `GCP_PROJECT`: Your Google Cloud project ID
- `WXTECH_API_KEY`: WxTech API key (optional)

## Deployment Methods

### Method 1: Using Cloud Build (Recommended)

This method builds the Docker image and deploys to Cloud Run in one step.

```bash
# Build the container image
gcloud builds submit --config=cloudbuild-bigquery.yaml

# Deploy to Cloud Run
gcloud run deploy solar-weather-api \
  --image gcr.io/YOUR_PROJECT_ID/solar-bigquery-api \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars GCP_PROJECT=YOUR_PROJECT_ID,WXTECH_API_KEY=YOUR_KEY
```

### Method 2: Using PowerShell Script

For Windows users, use the provided deployment script:

```powershell
# Edit deploy-bigquery-api.ps1 with your project ID
./deploy-bigquery-api.ps1
```

### Method 3: Manual Docker Build

```bash
# Build Docker image
docker build -f Dockerfile.bigquery -t gcr.io/YOUR_PROJECT_ID/solar-bigquery-api .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/solar-bigquery-api

# Deploy to Cloud Run
gcloud run deploy solar-weather-api \
  --image gcr.io/YOUR_PROJECT_ID/solar-bigquery-api \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=YOUR_PROJECT_ID,WXTECH_API_KEY=YOUR_KEY
```

## Post-Deployment

### 1. Verify Deployment

```bash
# Get service URL
gcloud run services describe solar-weather-api \
  --region asia-southeast1 \
  --format 'value(status.url)'
```

### 2. Test API

```bash
# Test root endpoint
curl https://YOUR_SERVICE_URL/

# Test database connection
curl https://YOUR_SERVICE_URL/stats

# Test building query
curl "https://YOUR_SERVICE_URL/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"
```

### 3. Access API Documentation

Visit: `https://YOUR_SERVICE_URL/docs`

## Configuration Options

### Cloud Run Settings

| Setting | Recommended Value | Description |
|---------|------------------|-------------|
| Memory | 1 GiB | Sufficient for pvlib calculations |
| CPU | 2 vCPU | Handles concurrent requests |
| Timeout | 300s | Allows for complex calculations |
| Max Instances | 10 | Auto-scaling limit |
| Min Instances | 0 | Cost optimization |

### Environment Variables

Set via Cloud Run console or CLI:

```bash
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --set-env-vars GCP_PROJECT=YOUR_PROJECT_ID,WXTECH_API_KEY=YOUR_KEY
```

## Monitoring

### View Logs

```bash
gcloud run services logs read solar-weather-api \
  --region asia-southeast1 \
  --limit 50
```

### Monitor Performance

Access Cloud Run metrics in GCP Console:
- Request count
- Request latency
- Container CPU utilization
- Container memory utilization

## Troubleshooting

### Build Fails

**Error**: `unrecognized arguments: --dockerfile`

**Solution**: Use Cloud Build YAML configuration instead of inline flags.

### Deployment Fails

**Error**: `Permission denied`

**Solution**: Enable required APIs:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
```

### API Returns Errors

**Error**: `BigQuery connection failed`

**Solution**: Verify BigQuery dataset exists and service account has permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member serviceAccount:YOUR_SERVICE_ACCOUNT \
  --role roles/bigquery.dataViewer
```

### Weather Endpoints Fail

**Error**: `WXTECH_API_KEY environment variable not set`

**Solution**: Set the environment variable in Cloud Run:
```bash
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --set-env-vars WXTECH_API_KEY=YOUR_KEY
```

## Cost Optimization

### Cloud Run Pricing

- **Free Tier**: 2 million requests/month
- **Compute**: Billed per 100ms of CPU time
- **Memory**: Billed per GiB-second
- **Requests**: $0.40 per million requests

### BigQuery Pricing

- **Storage**: $0.02 per GB/month
- **Queries**: $5 per TB processed
- **Free Tier**: 1 TB queries/month

### Optimization Tips

1. Set `min-instances=0` to avoid idle charges
2. Use appropriate `max-instances` to control costs
3. Implement caching for frequently accessed data
4. Use BigQuery partitioning for large queries

## Security

### Authentication

For production, enable authentication:

```bash
gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --no-allow-unauthenticated
```

Then use IAM or API keys for access control.

### Service Account

Create a dedicated service account with minimal permissions:

```bash
gcloud iam service-accounts create solar-api-sa \
  --display-name "Solar API Service Account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member serviceAccount:solar-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role roles/bigquery.dataViewer

gcloud run services update solar-weather-api \
  --region asia-southeast1 \
  --service-account solar-api-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Updating the API

### Deploy New Version

```bash
# Build new image
gcloud builds submit --config=cloudbuild-bigquery.yaml

# Cloud Run automatically deploys the new version
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service solar-weather-api --region asia-southeast1

# Rollback to previous revision
gcloud run services update-traffic solar-weather-api \
  --region asia-southeast1 \
  --to-revisions REVISION_NAME=100
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Deploy
        run: |
          gcloud builds submit --config=backend/cloudbuild-bigquery.yaml
          gcloud run deploy solar-weather-api \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/solar-bigquery-api \
            --region asia-southeast1 \
            --platform managed
```

## Support

For deployment issues:
- Check Cloud Run logs: `gcloud run services logs read`
- Review Cloud Build history in GCP Console
- Verify BigQuery permissions and dataset access

---

**Last Updated**: March 30, 2026
