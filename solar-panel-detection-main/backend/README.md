# Solar Potential API - Backend

RESTful API service for solar photovoltaic potential analysis across Thailand's 107M+ building footprints.

## Features

- Query 107,682,789 building footprints from Google Open Buildings dataset via BigQuery
- Real-time weather forecasting integration (WxTech 5km global mesh)
- Physics-based solar modeling using pvlib-python
- Weather-enhanced generation forecasts
- Financial analysis (ROI, payback period)
- Environmental impact calculations (CO2 reduction)

## Technology Stack

- **Framework**: FastAPI 0.104.1 (Python 3.11)
- **Database**: Google Cloud BigQuery
- **Solar Modeling**: pvlib-python 0.10.3
- **Weather API**: WxTech Global Weather Forecast
- **Deployment**: Google Cloud Run (serverless containers)

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud SDK
- GCP project with BigQuery API enabled
- WxTech API key (optional, for weather features)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. Run the API:
```bash
uvicorn api_bigquery:app --reload --port 8080
```

4. Access API documentation:
```
http://localhost:8080/docs
```

### Environment Variables

Create a `.env` file with:

```env
# Google Cloud Platform
GCP_PROJECT=your-gcp-project-id

# WxTech Weather API (optional)
WXTECH_API_KEY=your_wxtech_api_key
```

See `.env.example` for complete configuration template.

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /stats` - Database statistics (107M+ buildings)
- `GET /stats/distribution` - Confidence distribution for charts
- `GET /buildings/bbox` - Query buildings by bounding box
- `GET /buildings/nearby` - Query buildings by radius

### Solar Analysis

- `POST /solar/calculate` - Calculate solar potential for a building
- `GET /solar/forecast` - Weather-enhanced generation forecast

### Weather Integration

- `GET /weather/forecast` - Real-time weather forecast

## Deployment

### Deploy to Google Cloud Run

1. Build and deploy using Cloud Build:
```bash
gcloud builds submit --config=cloudbuild-bigquery.yaml
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy solar-weather-api \
  --image gcr.io/YOUR_PROJECT/solar-bigquery-api \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=YOUR_PROJECT,WXTECH_API_KEY=YOUR_KEY
```

### Using Deployment Script

```powershell
./deploy-bigquery-api.ps1
```

## Architecture

### Data Flow

```
Client Request
    ↓
FastAPI (Cloud Run)
    ↓
├─→ BigQuery (Building Data)
├─→ WxTech API (Weather)
└─→ pvlib (Solar Calculations)
    ↓
JSON Response
```

### Key Components

1. **api_bigquery.py** - Main API application with all endpoints
2. **weather_service.py** - WxTech API client and solar weather analyzer
3. **Dockerfile.bigquery** - Production container configuration
4. **cloudbuild-bigquery.yaml** - Cloud Build configuration

## Calculation Methodology

### Solar Potential Calculation

The API uses a two-tier approach:

**Primary: pvlib-python Physics-Based Modeling**
- Astronomical solar position calculations
- Clear sky irradiance models (Ineichen-Perez)
- Temperature effects on panel performance
- System losses (inverter, wiring, soiling)

**Fallback: Simplified Empirical Model**
- NASA POWER API for irradiance data
- Fixed system efficiency (80%)
- Thailand-specific parameters

### Parameters (Thailand-Specific)

| Parameter | Value | Source |
|-----------|-------|--------|
| Panel Efficiency | 20% | Industry standard monocrystalline |
| System Efficiency | 80% | IEA PVPS Thailand 2021 |
| Usable Roof Ratio | 50% | DEDE research data |
| Installation Cost | 25 THB/Wp | Krungsri Research 2025 |
| Electricity Rate | 4.18 THB/kWh | ERC 2024 average |
| CO2 Factor | 0.40 kgCO2/kWh | EPPO/CEIC 2024 |

All parameters are referenced to published academic and industry sources. See `BACKEND.md` for detailed references.

## Performance

### Response Times

- Building queries: < 600ms
- Solar calculations: < 600ms
- Weather forecasts: < 500ms

### Scalability

- Auto-scaling: 0-10 instances
- BigQuery: Handles 107M+ records efficiently
- Concurrent requests: 1000+ per second

## Testing

### Test Building Query

```bash
curl "https://solar-weather-api-715107904640.asia-southeast1.run.app/buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=5"
```

### Test Solar Calculation

```bash
curl -X POST "https://solar-weather-api-715107904640.asia-southeast1.run.app/solar/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 13.7563,
    "longitude": 100.5018,
    "area_m2": 250,
    "confidence": 0.95
  }'
```

### Test Weather Forecast

```bash
curl "https://solar-weather-api-715107904640.asia-southeast1.run.app/weather/forecast?lat=13.7563&lon=100.5018"
```

## Documentation

- **API Documentation**: See `BACKEND.md` for comprehensive API reference
- **Interactive Docs**: Visit `/docs` endpoint for Swagger UI
- **OpenAPI Schema**: Visit `/openapi.json` for machine-readable schema

## License

MIT License

## References

1. IEA PVPS National Survey Report Thailand 2021
2. Krungsri Research - Rooftop Solar Business Models 2025
3. Google Open Buildings Dataset v3
4. pvlib-python Documentation
5. WxTech Global Weather Forecast API

---

**Version**: 2.1.0  
**Last Updated**: March 30, 2026
