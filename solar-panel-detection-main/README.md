# Solar Panel Detection System

A geospatial web application for analyzing rooftop solar photovoltaic potential on building footprints across Thailand. The system combines Google Open Buildings Dataset with physics-based solar modeling to provide accurate technical and financial feasibility assessments for solar installations.

## Overview

This application provides comprehensive solar energy potential assessments by integrating:

- **Google Open Buildings Dataset**: 107+ million building footprints with geometry and confidence scores
- **BigQuery GIS**: High-performance spatial queries and geometry processing
- **pvlib-python**: Industry-standard photovoltaic system modeling
- **Interactive Mapping**: Real-time visualization on satellite imagery
- **Cloud Infrastructure**: Scalable deployment on Google Cloud Platform

The system calculates key metrics including system sizing, energy production estimates, installation costs, payback periods, and carbon emission reductions based on Thailand-specific parameters.

## Architecture

### Frontend

**Technology Stack:**
- React 18.2.0
- Leaflet 1.9.4 with React-Leaflet
- Esri World Imagery basemap
- GeoJSON rendering with confidence-based styling

**Key Features:**
- Interactive map with pan and zoom
- Building footprint visualization with polygon geometries
- Click-to-analyze solar potential
- Real-time data loading based on viewport
- Responsive design for desktop and mobile

### Backend

**Technology Stack:**
- FastAPI 0.109.0 (Python 3.11)
- Google Cloud BigQuery 3.14.1
- Cloud Run serverless deployment
- BigQuery GIS functions for geometry processing

**API Endpoints:**
- `GET /` - Health check
- `GET /stats` - Dataset statistics
- `GET /buildings/bbox` - Query buildings by bounding box
- `GET /buildings/nearby` - Query buildings by radius
- `GET /buildings/{id}` - Get building details
- `POST /solar/calculate` - Calculate solar potential

### Database

**Data Source:**
- Google Open Buildings Dataset v3
- Coverage: Thailand
- Records: 107,682,434 buildings
- Storage: BigQuery table with spatial indexing

**Schema:**
- `full_plus_code`: Unique identifier (Plus Code)
- `latitude`: Centroid latitude
- `longitude`: Centroid longitude
- `area_in_meters`: Building area in square meters
- `confidence`: Detection confidence score (0-1)
- `geometry`: WKT polygon geometry

## Solar Calculation Methodology

### Data Sources

**Solar Irradiance:**
- Value: 5.06 kWh/m²/day (Thailand national average)
- Source: World Bank Global Solar Atlas
- Reference: RatedPower Thailand Solar Energy Report 2022

**System Parameters:**
- Panel Efficiency: 20% (standard monocrystalline)
- System Efficiency: 80% (IEA PVPS Thailand 2021)
- Usable Roof Ratio: 50% (conservative urban estimate)
- Installation Cost: 25 THB/Wp (C&I segment 2024)
- Electricity Rate: 4.18 THB/kWh (2024 average)
- CO2 Factor: 0.40 kgCO2/kWh (Thailand grid 2024)

### Calculation Process

1. **Usable Roof Area**: Building area × usable roof ratio × confidence adjustment
2. **System Size**: Usable area × panel efficiency (kWp)
3. **Annual Production**: System size × irradiance × 365 days × system efficiency (kWh/year)
4. **Installation Cost**: System size × 1000 × cost per Wp (THB)
5. **Annual Savings**: Annual production × electricity rate (THB/year)
6. **Payback Period**: Installation cost / annual savings (years)
7. **CO2 Reduction**: Annual production × CO2 factor (kg/year)

## Installation

### Prerequisites

- Node.js 18 or higher
- npm 8 or higher
- Google Cloud SDK
- Firebase CLI (optional, for hosting)
- Git

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd solar-panel-detection-main
```

2. Install frontend dependencies:
```bash
cd frontend
npm install
```

3. Configure environment variables:
```bash
# Create frontend/.env
REACT_APP_BUILDINGS_API_URL=https://buildings-api-715107904640.asia-southeast1.run.app
```

4. Start development server:
```bash
npm start
```

The application will be available at http://localhost:3000

### Production Build

```bash
cd frontend
npm run build
```

The optimized production build will be created in the `build` directory.

## Deployment

### Frontend Deployment

**Option 1: Firebase Hosting**
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

**Option 2: Cloud Run**
```bash
cd frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/solar-frontend
gcloud run deploy solar-frontend \
  --image gcr.io/PROJECT_ID/solar-frontend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

### Backend Deployment

1. Build Docker image:
```bash
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/buildings-api-bq --timeout=10m
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy buildings-api \
  --image gcr.io/PROJECT_ID/buildings-api-bq \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 60 \
  --max-instances 10
```

3. Grant BigQuery permissions:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

## Configuration

### Environment Variables

**Frontend (.env):**
```
REACT_APP_BUILDINGS_API_URL=https://your-api-url.run.app
```

**Backend (Cloud Run):**
```
PROJECT_ID=your-gcp-project-id
DATASET=openbuildings
TABLE=thailand_raw
```

### API Configuration

**Rate Limits:**
- Max buildings per request: 5,000
- Default limit: 1,000
- Min confidence threshold: 0.5 (adjustable)

**Query Optimization:**
- Spatial indexing on geometry column
- Confidence-based filtering
- Area-based sorting for relevance

## API Reference

### GET /stats

Returns dataset statistics.

**Response:**
```json
{
  "total_buildings": 107682789,
  "confidence": {
    "average": 0.787,
    "min": 0.5,
    "max": 1.0
  },
  "area_m2": {
    "average": 96.1,
    "min": 10.0,
    "max": 500000.0
  }
}
```

### GET /buildings/bbox

Query buildings within a bounding box.

**Parameters:**
- `min_lat` (required): Minimum latitude
- `max_lat` (required): Maximum latitude
- `min_lon` (required): Minimum longitude
- `max_lon` (required): Maximum longitude
- `limit` (optional): Maximum results (default: 1000, max: 5000)
- `min_confidence` (optional): Minimum confidence (default: 0.7)

**Response:**
```json
{
  "total": 254709,
  "buildings": [
    {
      "id": 340527,
      "open_buildings_id": "7P52PHF5+MGJR",
      "latitude": 13.72422327,
      "longitude": 100.55875705,
      "area_m2": 43690.3299,
      "confidence": 0.976,
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[100.5575567, 13.7236898], ...]]
      }
    }
  ]
}
```

### POST /solar/calculate

Calculate solar potential for a building.

**Request Body:**
```json
{
  "latitude": 13.7563,
  "longitude": 100.5018,
  "area_m2": 100.0,
  "confidence": 0.95,
  "tilt": null,
  "azimuth": 180
}
```

**Response:**
```json
{
  "usable_roof_area": 50.0,
  "system_size_kwp": 10.0,
  "annual_production_kwh": 14708.0,
  "installation_cost_thb": 250000.0,
  "annual_savings_thb": 61479.0,
  "payback_period_years": 4.1,
  "co2_reduction_kg": 5883.2,
  "co2_reduction_ton": 5.9,
  "irradiance_source": "Thailand national average",
  "irradiance_kwh_m2_day": 5.06
}
```

## Data Import

The system uses Google Open Buildings Dataset stored in BigQuery. To import data:

1. Download dataset from Google Cloud Storage:
```bash
gsutil -m cp -r gs://open-buildings-data/v3/polygons_s2_level_4_gzip/thailand_* ./data/
```

2. Load to BigQuery:
```bash
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  PROJECT_ID:openbuildings.thailand_raw \
  gs://your-bucket/thailand/*.csv \
  latitude:FLOAT,longitude:FLOAT,area_in_meters:FLOAT,confidence:FLOAT,geometry:STRING,full_plus_code:STRING
```

3. Convert geometry to GEOGRAPHY type:
```sql
CREATE OR REPLACE TABLE `PROJECT_ID.openbuildings.thailand_processed` AS
SELECT 
  full_plus_code,
  latitude,
  longitude,
  area_in_meters,
  confidence,
  ST_GEOGFROMTEXT(geometry) as geometry
FROM `PROJECT_ID.openbuildings.thailand_raw`
WHERE confidence >= 0.5;
```

## Performance Optimization

### Frontend Optimization

- Lazy loading of map tiles
- Debounced viewport change events
- Efficient GeoJSON rendering
- Conditional component rendering
- Production build minification

### Backend Optimization

- BigQuery spatial indexing
- Query result caching
- Connection pooling
- Async request handling
- Response compression

### Database Optimization

- Partitioning by geographic region
- Clustering by confidence score
- Materialized views for common queries
- Regular table optimization
- Query cost monitoring

## Monitoring and Logging

### Cloud Run Metrics

View service logs:
```bash
gcloud run services logs read buildings-api \
  --region asia-southeast1 \
  --limit 100
```

View service metrics:
```bash
gcloud run services describe buildings-api \
  --region asia-southeast1
```

### BigQuery Monitoring

Check query history:
```bash
bq ls -j -a -n 100
```

View table information:
```bash
bq show PROJECT_ID:openbuildings.thailand_raw
```

## Troubleshooting

### Common Issues

**Issue: API returns empty results**
- Verify BigQuery table exists and contains data
- Check service account has BigQuery permissions
- Confirm correct PROJECT_ID, DATASET, and TABLE values

**Issue: Geometry parsing errors**
- Ensure geometry column uses WKT format
- Verify ST_GEOGFROMTEXT conversion in queries
- Check for invalid or malformed geometries

**Issue: Frontend cannot connect to API**
- Verify API URL in .env file
- Check Cloud Run service is deployed and running
- Confirm CORS is enabled (allow-unauthenticated flag)

**Issue: Slow query performance**
- Add spatial indexes on geometry column
- Reduce query limit parameter
- Implement result caching
- Consider table partitioning

## Cost Estimation

### Monthly Costs (Approximate)

- **Cloud Run**: $5-20 (depends on traffic)
- **BigQuery**: $5-10 (query and storage costs)
- **Firebase Hosting**: Free tier sufficient
- **Cloud Build**: Free tier (120 build minutes/day)

**Total Estimated Cost**: $10-30/month for moderate usage

### Cost Optimization

- Set Cloud Run min instances to 0
- Enable BigQuery query caching
- Use Cloud CDN for static assets
- Implement client-side caching
- Monitor and optimize expensive queries

## Security Considerations

### API Security

- Rate limiting on API endpoints
- Input validation and sanitization
- HTTPS-only communication
- CORS configuration
- Service account least privilege

### Data Security

- BigQuery access controls
- Encrypted data at rest and in transit
- Audit logging enabled
- Regular security updates
- Vulnerability scanning

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Add tests for new functionality
5. Update documentation as needed
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## References

### Data Sources

- Google Open Buildings Dataset: https://sites.research.google/open-buildings/
- World Bank Global Solar Atlas: https://globalsolaratlas.info/
- NASA POWER API: https://power.larc.nasa.gov/

### Technical Documentation

- BigQuery GIS Functions: https://cloud.google.com/bigquery/docs/gis-intro
- pvlib-python: https://pvlib-python.readthedocs.io/
- Leaflet: https://leafletjs.com/
- React: https://react.dev/

### Research Papers

- IEA PVPS National Survey Report Thailand 2021
- RatedPower Thailand Solar Energy Report 2022
- Google Open Buildings Dataset Technical Paper

## Support

For issues, questions, or contributions:
- Create an issue in the repository
- Review existing documentation
- Check Cloud Run and BigQuery logs
- Consult GCP status page for service issues

## Acknowledgments

- Google Open Buildings Dataset team
- World Bank Global Solar Atlas
- pvlib-python community
- Esri for satellite imagery
- OpenStreetMap contributors
