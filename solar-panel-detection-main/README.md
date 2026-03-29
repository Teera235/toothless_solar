# Toothless Solar Buildings Map

A geospatial web application for analyzing rooftop solar photovoltaic potential on building footprints across Thailand using Google Open Buildings Dataset and physics-based solar modeling.

## Overview

This application provides accurate solar energy potential assessments for buildings in Thailand by combining:

- **Google Open Buildings Dataset**: 107+ million building footprints with geometry and confidence scores
- **BigQuery GIS**: High-performance spatial queries and geometry processing at scale
- **pvlib-python**: Industry-standard photovoltaic system modeling library
- **NASA POWER API**: Satellite-derived solar irradiance data for location-specific calculations
- **Interactive Mapping**: Real-time visualization on satellite imagery with Leaflet

The system calculates technical and financial feasibility metrics including system sizing, energy production estimates, installation costs, payback periods, and carbon emission reductions based on Thailand-specific parameters.

## Technical Architecture

### Frontend

**Framework**: React 18.2.0  
**Mapping**: Leaflet 1.9.4 with React-Leaflet  
**Basemap**: Esri World Imagery (satellite) with labels overlay  
**Visualization**: GeoJSON rendering with confidence-based color coding  
**API Integration**: RESTful communication with FastAPI backend

**Key Features**:
- Interactive map with pan and zoom
- Building footprint visualization with polygon geometries
- Click-to-analyze solar potential
- Real-time data loading based on viewport bounds
- Responsive design for desktop and mobile

### Backend

**Framework**: FastAPI 0.109.0 (Python 3.11)  
**Database**: Google Cloud BigQuery with spatial functions  
**Solar Modeling**: pvlib-python 0.10.3+ for physics-based calculations  
**Data Source**: NASA POWER API for location-specific irradiance  
**Deployment**: Cloud Run serverless containers

**API Endpoints**:
- `GET /` - Health check
- `GET /stats` - Dataset statistics
- `GET /buildings/bbox` - Query buildings by bounding box
- `GET /buildings/nearby` - Query buildings by radius
- `GET /buildings/{id}` - Get building details
- `POST /solar/calculate` - Calculate solar potential with pvlib

### Database

**Engine**: Google Cloud BigQuery  
**Dataset**: `openbuildings.thailand_raw`  
**Records**: 107,682,434 building footprints  
**Storage**: Columnar format optimized for analytical queries  
**Spatial Functions**: ST_GEOGFROMTEXT, ST_ASGEOJSON, ST_DISTANCE, ST_DWITHIN

**Schema**:
- `full_plus_code`: Unique identifier (Plus Code format)
- `latitude`: Centroid latitude (FLOAT64)
- `longitude`: Centroid longitude (FLOAT64)
- `area_in_meters`: Building area in square meters (FLOAT64)
- `confidence`: Detection confidence score 0-1 (FLOAT64)
- `geometry`: WKT polygon geometry (STRING)

## Solar Calculation Methodology

### Calculation Engine

The application employs a two-tier calculation approach:

1. **Primary Method**: pvlib-python physics-based modeling
2. **Fallback Method**: Simplified empirical calculation

### pvlib-python Implementation

The primary calculation method uses pvlib-python, a community-supported library developed by Sandia National Laboratories. This approach provides research-grade accuracy through:

**Solar Position Calculation**:
- Astronomical algorithms for sun position (azimuth, zenith)
- Accounts for atmospheric refraction and equation of time
- Hourly resolution over full calendar year

**Irradiance Modeling**:
- Clear sky irradiance model (Ineichen-Perez)
- Decomposition of Global Horizontal Irradiance (GHI) into Direct Normal Irradiance (DNI) and Diffuse Horizontal Irradiance (DHI)
- Transposition to tilted plane-of-array (POA) irradiance
- Accounts for ground reflection (albedo)

**Temperature Effects**:
- Sandia Array Performance Model (SAPM) for cell temperature
- Accounts for ambient temperature, wind speed, and mounting configuration
- Temperature coefficient applied to power output (-0.4%/°C typical for monocrystalline silicon)

**System Performance**:
- PVWatts DC model for module power output
- Inverter efficiency modeling (96% nominal)
- System losses including soiling, wiring, and mismatch

### Calculation Parameters

All parameters are referenced to published sources and Thailand-specific data:

#### Solar Irradiance

**Default Value**: 5.06 kWh/m²/day  
**Source**: World Bank Global Solar Atlas via RatedPower (2022)  
**Regional Variation**: Bangkok/Central region 4.8-5.3 kWh/m²/day  
**Seasonal Peak**: April-May 5.6-6.7 kWh/m²/day  
**Dynamic Source**: NASA POWER API ALLSKY_SFC_SW_DWN parameter when available  
**Reference**: https://ratedpower.com/blog/solar-energy-thailand/

#### Panel Efficiency

**Value**: 20% (0.20)  
**Technology**: Standard commercial monocrystalline silicon  
**Industry Range**: 18-22% (IRENA, IEA PVPS Thailand 2021)  
**Justification**: Representative of current market-available modules

#### System Efficiency (Performance Ratio)

**Value**: 80% (0.80)  
**Standard**: IEC 61724  
**Thailand Studies**: 75-82% observed in rooftop installations

**Loss Factors**:
- Inverter losses: 2-5%
- Wiring losses: 2%
- Soiling/dust: 3%
- Temperature derating: 5-8% (Thailand climate)
- Mismatch losses: 2%

**Reference**: IEA PVPS National Survey Report Thailand 2021  
https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf

#### Usable Roof Area

**Value**: 50% (0.50)  
**Justification**: Conservative estimate for Thailand urban buildings

**Exclusions**:
- HVAC equipment and water tanks
- Roof edge setbacks (safety and wind loading)
- Shading from parapet walls and adjacent structures
- Access pathways and maintenance clearances

**Academic Basis**: GIS-based rooftop PV potential studies use 40-60% depending on building type

**Building Type Variation**:
- Residential: 55-60%
- Commercial/Industrial: 40-50%

**Reference**: "Evaluating rooftop solar PV potential in Thailand" (DEDE data 2022)  
https://www.researchgate.net/figure/Breakdown-of-the-costs-of-a-100-kWp-solar-rooftop-PV-system

#### Installation Cost

**Value**: 25 THB/Wp  
**Segment**: Commercial and Industrial (C&I) rooftop systems  
**Trend**: Decreased from 27.5 THB/Wp (2020) to 25 THB/Wp (2024)  
**Residential Systems**: Higher at approximately 39 THB/Wp due to smaller scale  
**Academic Benchmark**: 25.14 THB/Wp for 100 kWp hospital system in Southern Thailand

**References**:
- Krungsri Research "Rooftop Solar Business Models Thailand" 2025  
  https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
- ResearchGate breakdown study (DEDE data)

#### Electricity Rate

**Value**: 4.18 THB/kWh  
**Basis**: 2024 actual average rate  
**Context**: Government capped rate at 3.99 THB/kWh through end of 2025  
**Historical Average**: 4.26 THB/kWh (2024-2025 period)  
**Rate Authority**: Energy Regulatory Commission (ERC), Metropolitan Electricity Authority (MEA), Provincial Electricity Authority (PEA)

**References**:
- https://www.globalpetrolprices.com/Thailand/electricity_prices/
- https://www.nationthailand.com/business/economy/40049646
- Krungsri Research citing ERC data

#### CO₂ Emission Factor

**Value**: 0.40 kgCO₂/kWh  
**Exact Value**: 0.399 kgCO₂/kWh (2024)  
**Trend**: Decreased from 0.438 kgCO₂/kWh (2023)  
**Source**: Energy Policy and Planning Office (EPPO), Ministry of Energy Thailand  
**Data Provider**: CEIC  
**Reference**: https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

### Calculation Formulas

The following formulas are applied in sequence:

#### 1. Usable Roof Area

```
usable_roof_area = building_area × usable_roof_ratio × confidence_adjustment
```

where `confidence_adjustment = max(building_confidence, 0.7)` to account for Google Open Buildings detection uncertainty.

#### 2. System Size

```
system_size_kWp = usable_roof_area × panel_efficiency
```

Based on Standard Test Conditions (STC): 1 m² of panel at 20% efficiency under 1 kW/m² irradiance = 0.20 kWp.

#### 3. Annual Energy Production

**pvlib method (primary)**:

```
For each hour in year:
  solar_position = calculate_sun_position(latitude, longitude, timestamp)
  clearsky_irradiance = ineichen_clearsky_model(solar_position)
  poa_irradiance = transpose_to_plane(clearsky_irradiance, tilt, azimuth)
  cell_temperature = sapm_temperature_model(poa_irradiance, ambient_temp, wind_speed)
  dc_power = pvwatts_dc_model(poa_irradiance, cell_temperature, system_size_kWp)
  ac_power = dc_power × inverter_efficiency

annual_production_kWh = sum(ac_power) / 1000
```

**Simplified method (fallback)**:

```
annual_production_kWh = system_size_kWp × avg_irradiance × 365 × system_efficiency
```

#### 4. Financial Metrics

```
installation_cost_THB = system_size_kWp × 1000 × cost_per_Wp
annual_savings_THB = annual_production_kWh × electricity_rate
payback_period_years = installation_cost_THB / annual_savings_THB
```

#### 5. Environmental Impact

```
co2_reduction_kg_per_year = annual_production_kWh × co2_emission_factor
co2_reduction_tonnes_per_year = co2_reduction_kg_per_year / 1000
```

## Data Sources

### Building Footprints

**Primary Source**: Google Open Buildings Dataset v3  
**Coverage**: Thailand nationwide  
**Records**: 107,682,434 buildings  
**Attributes**: Geometry (polygon), area, confidence score, centroid coordinates  
**License**: Open Data Commons Open Database License (ODbL)  
**Access**: https://sites.research.google/open-buildings/  
**Storage**: Google Cloud BigQuery `trim-descent-452802-t2.openbuildings.thailand_raw`

**Data Quality**:
- Confidence scores range from 0.5 to 1.0
- Higher confidence indicates more reliable building detection
- Geometries in WKT format, converted to GeoJSON for frontend

### Solar Irradiance

**Primary Source**: NASA POWER (Prediction Of Worldwide Energy Resources)  
**Parameter**: ALLSKY_SFC_SW_DWN (All-Sky Surface Shortwave Downward Irradiance)  
**Temporal Resolution**: Monthly climatology (long-term average)  
**Spatial Resolution**: 0.5° × 0.625° (approximately 50 km)  
**Data Period**: 1984-present (GEWEX SRB + CERES SYN1deg)  
**API**: https://power.larc.nasa.gov/api/temporal/monthly/point  
**Documentation**: https://power.larc.nasa.gov/docs/

## System Requirements

### Minimum Requirements

**Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)  
**RAM**: 4 GB  
**Disk Space**: 2 GB free space

**Software**:
- Node.js 16.0.0 or higher
- Python 3.9.0 or higher
- Google Cloud SDK (for deployment)

### Recommended Requirements

**RAM**: 8 GB or higher  
**Disk Space**: 10 GB or higher  
**Network**: Broadband internet connection for NASA POWER API access

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/Teera235/toothless_solar.git
cd toothless_solar/solar-panel-detection-main
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

**Required Python packages**:
- fastapi==0.109.0
- uvicorn[standard]==0.24.0
- google-cloud-bigquery==3.14.1
- python-dotenv==1.0.0
- pydantic==2.5.0
- pvlib==0.10.3
- pandas==2.1.4
- numpy==1.26.2
- requests==2.31.0

### 3. Frontend Setup

```bash
cd ../frontend
npm install
```

### 4. Environment Configuration

#### Backend Configuration

Create `backend/.env`:

```env
PROJECT_ID=your-gcp-project-id
DATASET=openbuildings
TABLE=thailand_raw
```

For production deployment, ensure the service account has:
- `roles/bigquery.dataViewer`
- `roles/bigquery.jobUser`

#### Frontend Configuration

Create `frontend/.env`:

```env
REACT_APP_BUILDINGS_API_URL=http://localhost:8001
```

For production:

```env
REACT_APP_BUILDINGS_API_URL=https://your-api-domain.run.app
```

### 5. Data Import to BigQuery

The application uses Google Open Buildings data stored in BigQuery.

#### Download Dataset

```bash
# Download Thailand building data from Google Cloud Storage
gsutil -m cp -r gs://open-buildings-data/v3/polygons_s2_level_4_gzip/thailand_* ./data/
```

#### Load to BigQuery

```bash
# Create dataset
bq mk --dataset PROJECT_ID:openbuildings

# Load CSV files
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  PROJECT_ID:openbuildings.thailand_raw \
  gs://your-bucket/thailand/*.csv \
  latitude:FLOAT,longitude:FLOAT,area_in_meters:FLOAT,confidence:FLOAT,geometry:STRING,full_plus_code:STRING
```

#### Optimize for Queries

```sql
-- Add clustering for better performance
CREATE OR REPLACE TABLE `PROJECT_ID.openbuildings.thailand_raw`
CLUSTER BY confidence, area_in_meters
AS SELECT * FROM `PROJECT_ID.openbuildings.thailand_raw`;
```

## Running the Application

### Development Mode

**Terminal 1: Start Backend API**

```bash
cd backend
python api_bigquery.py
```

Backend will run at: http://localhost:8001  
API documentation available at: http://localhost:8001/docs

**Terminal 2: Start Frontend**

```bash
cd frontend
npm start
```

Frontend will run at: http://localhost:3000

### Production Mode

#### Backend

```bash
cd backend
uvicorn api_bigquery:app --host 0.0.0.0 --port 8001 --workers 4
```

#### Frontend

```bash
cd frontend
npm run build
# Serve build directory with nginx, Apache, or static hosting service
```

## API Endpoints

### Buildings Data

#### GET /stats

**Description**: Database statistics and extent

**Response**:
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

#### GET /buildings/bbox

**Description**: Retrieve buildings within bounding box

**Parameters**:
- `min_lat` (float, required): Minimum latitude
- `max_lat` (float, required): Maximum latitude
- `min_lon` (float, required): Minimum longitude
- `max_lon` (float, required): Maximum longitude
- `limit` (int, optional): Maximum results (default: 1000, max: 5000)
- `min_confidence` (float, optional): Minimum confidence threshold (default: 0.7)

**Response**:
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

#### GET /buildings/nearby

**Description**: Retrieve buildings near a point

**Parameters**:
- `lat` (float, required): Latitude
- `lon` (float, required): Longitude
- `radius_m` (float, optional): Search radius in meters (default: 500)
- `limit` (int, optional): Maximum results (default: 100, max: 1000)
- `min_confidence` (float, optional): Minimum confidence threshold (default: 0.7)

**Response**: Array of building objects with distance

#### GET /buildings/{id}

**Description**: Retrieve detailed building information

**Parameters**:
- `id` (int, required): Building ID (row number in BigQuery)

**Response**: Building object with full geometry and metadata

### Solar Calculations

#### POST /solar/calculate

**Description**: Calculate solar potential using pvlib-python

**Request Body**:
```json
{
  "latitude": 13.7563,
  "longitude": 100.5018,
  "area_m2": 250.0,
  "confidence": 0.95,
  "tilt": null,
  "azimuth": 180
}
```

**Response**:
```json
{
  "usable_roof_area": 119,
  "system_size_kwp": 23.8,
  "annual_production_kwh": 34560,
  "installation_cost_thb": 595000,
  "annual_savings_thb": 144461,
  "payback_period_years": 4.1,
  "co2_reduction_kg": 13824,
  "co2_reduction_ton": 13.8,
  "irradiance_source": "pvlib (Clear Sky Model)",
  "irradiance_kwh_m2_day": 5.12,
  "assumptions": {
    "panel_efficiency": 0.20,
    "usable_roof_ratio": 0.50,
    "cost_per_wp": 25,
    "electricity_rate": 4.18,
    "co2_factor": 0.40,
    "calculation_method": "pvlib"
  }
}
```

## User Interface

### Map View

**Basemap**: Esri World Imagery (satellite)  
**Overlay**: Esri World Boundaries and Places (labels)  
**Building Rendering**: GeoJSON polygons with confidence-based coloring

**Color Coding**:
- Green (≥90%): High confidence
- Blue (80-90%): Good confidence
- Orange (70-80%): Moderate confidence
- Red (<70%): Low confidence

### Information Panels

#### Buildings Data Panel (Top Right)

- Displayed buildings count
- Total buildings in current view
- Truncation notice if limit exceeded

#### Solar Potential Panel (Bottom Left)

Appears when building is selected:
- Building area and usable roof area
- System size (kWp)
- Confidence score
- Annual energy production (kWh)
- Annual savings (THB)
- Installation cost (THB)
- Payback period (years)
- CO₂ reduction (kg/year)
- Solar irradiance value and data source

#### Confidence Legend (Bottom Right)

Color-coded confidence level reference

## Performance Considerations

### Frontend

- Building rendering limited to 1000 features per view to maintain responsiveness
- GeoJSON features cached by React state
- Map bounds change debounced to reduce API calls

### Backend

- BigQuery spatial functions for fast geometry queries
- Query result streaming for large datasets
- CORS configured for cross-origin requests

### Database

- BigQuery columnar storage optimized for analytical queries
- Clustering by confidence and area for query optimization
- Spatial functions (ST_GEOGFROMTEXT, ST_ASGEOJSON) for geometry processing

## Deployment

### Google Cloud Platform

#### Backend (Cloud Run)

```bash
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/buildings-api-bq --timeout=10m
gcloud run deploy buildings-api \
  --image gcr.io/PROJECT_ID/buildings-api-bq \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 60 \
  --max-instances 10
```

#### Frontend (Cloud Run)

```bash
cd frontend
npm run build
gcloud builds submit --tag gcr.io/PROJECT_ID/solar-frontend
gcloud run deploy solar-frontend \
  --image gcr.io/PROJECT_ID/solar-frontend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated
```

#### Frontend (Firebase Hosting)

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

### Service Account Permissions

Grant BigQuery permissions to Cloud Run service account:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

## Limitations and Assumptions

### Data Limitations

- Building footprints represent 2D roof area; actual 3D geometry not available
- Confidence scores reflect detection certainty, not roof condition or structural suitability
- No information on roof material, age, or load-bearing capacity
- Shading from trees, adjacent buildings, or terrain not modeled
- Dataset accuracy varies by region and imagery quality

### Calculation Assumptions

- Assumes flat or optimally-tilted roof surfaces
- Does not account for roof orientation variations within single building
- Temperature modeling uses regional averages, not microclimate data
- Soiling losses based on typical urban environment
- No consideration of local regulations, grid connection requirements, or permitting

### Operational Assumptions

- System maintenance performed according to manufacturer specifications
- No major component failures during payback period
- Electricity rates remain constant (actual rates may vary)
- Net metering or feed-in tariff policies not modeled

## Troubleshooting

### BigQuery Connection Errors

- Verify service account has BigQuery permissions
- Check PROJECT_ID, DATASET, and TABLE in backend/.env
- Ensure BigQuery API is enabled in GCP project
- Verify network connectivity to BigQuery

### Frontend Not Displaying Buildings

- Check backend API is running: `curl http://localhost:8001/stats`
- Verify BigQuery contains data: Check BigQuery console
- Open browser console for JavaScript errors
- Check CORS configuration in backend API

### pvlib Calculation Errors

- Verify pvlib installation: `pip show pvlib`
- Check Python version compatibility (3.9+)
- Review backend logs for detailed error messages
- Fallback to simplified calculation if pvlib unavailable

### Performance Issues

- Reduce limit parameter in API calls
- Use clustering in BigQuery for better query performance
- Consider caching frequently accessed data
- Monitor BigQuery query costs and optimize queries

## Cost Estimation

### Monthly Costs (Approximate)

- **Cloud Run (Backend)**: $5-20 (depends on traffic)
- **Cloud Run (Frontend)**: $5-15 (depends on traffic)
- **BigQuery**: $5-10 (query and storage costs)
- **Firebase Hosting**: Free tier sufficient (alternative to Cloud Run frontend)
- **Cloud Build**: Free tier (120 build minutes/day)

**Total Estimated Cost**: $15-45/month for moderate usage

### Cost Optimization

- Set Cloud Run min instances to 0
- Enable BigQuery query caching
- Use Cloud CDN for static assets
- Implement client-side caching
- Monitor and optimize expensive queries

## License

This project is licensed under the MIT License. See LICENSE file for details.

### Third-Party Licenses

- **Google Open Buildings**: Open Data Commons Open Database License (ODbL)
- **pvlib-python**: BSD 3-Clause License
- **NASA POWER Data**: Public domain (U.S. Government work)
- **Leaflet**: BSD 2-Clause License
- **React**: MIT License
- **FastAPI**: MIT License

## References

### Academic and Technical Publications

**IEA PVPS (2021)**. "National Survey Report of PV Power Applications in Thailand 2021"  
International Energy Agency Photovoltaic Power Systems Programme  
https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf

**Krungsri Research (2025)**. "Rooftop Solar Business Models Thailand"  
Bank of Ayudhya PCL Research Department  
https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025

**RatedPower (2022)**. "Solar Energy in Thailand: Market Overview and Potential"  
https://ratedpower.com/blog/solar-energy-thailand/

**CEIC Data**. "Thailand Carbon Dioxide Emissions Statistics"  
Energy Policy and Planning Office (EPPO) data  
https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

**Global Petrol Prices (2024)**. "Thailand Electricity Prices"  
https://www.globalpetrolprices.com/Thailand/electricity_prices/

### Data Sources

**Google Research (2024)**. "Open Buildings Dataset"  
https://sites.research.google/open-buildings/

**NASA POWER Project**. "Prediction Of Worldwide Energy Resources"  
https://power.larc.nasa.gov/

### Software Documentation

**pvlib-python Documentation**  
https://pvlib-python.readthedocs.io/

**BigQuery Documentation**  
https://cloud.google.com/bigquery/docs

**FastAPI Documentation**  
https://fastapi.tiangolo.com/

## Contact and Support

For technical issues, feature requests, or questions:

- **GitHub Issues**: https://github.com/Teera235/toothless_solar/issues
- **Repository**: https://github.com/Teera235/toothless_solar

## Acknowledgments

This project utilizes data and tools from:

- Google Research Open Buildings team
- NASA Langley Research Center POWER Project
- pvlib-python development community
- Sandia National Laboratories (pvlib original development)
- Thailand Department of Alternative Energy Development and Efficiency (DEDE)
- Energy Regulatory Commission of Thailand (ERC)

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Tested On**: Windows 11, Node.js 18, Python 3.11, BigQuery
