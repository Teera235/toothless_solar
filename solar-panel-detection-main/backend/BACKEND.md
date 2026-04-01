# Backend API Documentation

## Overview

The Solar Weather API is a RESTful service that provides comprehensive solar photovoltaic potential analysis for buildings across Thailand. The system integrates Google Open Buildings dataset (107M+ building footprints), real-time weather forecasting, and physics-based solar modeling to deliver accurate energy generation estimates.

**Base URL**: `https://solar-weather-api-715107904640.asia-southeast1.run.app`

**Version**: 2.1.0

**Technology Stack**:
- Framework: FastAPI 0.109.0 (Python 3.11)
- Database: Google Cloud BigQuery
- Solar Modeling: pvlib-python 0.10.3
- Weather Data: WxTech 5km Global Weather Forecast API
- Deployment: Google Cloud Run (serverless containers)

---

## Architecture

### Data Sources

1. **Building Footprints**
   - Source: Google Open Buildings Dataset v3
   - Records: 107,682,789 building footprints
   - Coverage: Thailand nationwide
   - Attributes: Geometry (WKT polygon), area, confidence score, coordinates
   - Storage: BigQuery `trim-descent-452802-t2.openbuildings.thailand_raw`

2. **Weather Forecasting**
   - Provider: WxTech (Weathernews Inc.)
   - Resolution: 5km mesh grid
   - Temporal Coverage: 72-hour hourly + 14-day daily forecasts
   - Update Frequency: 4 times per day
   - Parameters: Solar radiation, temperature, precipitation, humidity, wind, pressure

3. **Solar Irradiance**
   - Primary: pvlib-python clear sky models (Ineichen-Perez)
   - Fallback: NASA POWER API (ALLSKY_SFC_SW_DWN)
   - Resolution: Hourly calculations over full calendar year

### Calculation Methodology

The API employs a two-tier calculation approach:

**Primary Method: pvlib-python Physics-Based Modeling**

The system uses pvlib-python, a community-supported library developed by Sandia National Laboratories, providing research-grade accuracy through:

1. **Solar Position Calculation**
   - Astronomical algorithms for sun position (azimuth, zenith)
   - Accounts for atmospheric refraction and equation of time
   - Hourly resolution over full calendar year

2. **Irradiance Modeling**
   - Clear sky irradiance model (Ineichen-Perez)
   - Decomposition of GHI into DNI and DHI
   - Transposition to tilted plane-of-array (POA) irradiance
   - Ground reflection (albedo) consideration

3. **Temperature Effects**
   - Sandia Array Performance Model (SAPM) for cell temperature
   - Ambient temperature, wind speed, and mounting configuration
   - Temperature coefficient: -0.4%/°C (monocrystalline silicon)

4. **System Performance**
   - PVWatts DC model for module power output
   - Inverter efficiency: 96% nominal
   - System losses: soiling, wiring, mismatch

**Fallback Method: Simplified Empirical Calculation**

Used when pvlib calculation fails or for rapid estimates:
```
annual_production_kWh = system_size_kWp × avg_irradiance × 365 × system_efficiency
```

---

## API Endpoints

### 1. Root Endpoint

**GET /**

Returns API information and available endpoints.

**Response**:
```json
{
  "name": "Toothless Solar Buildings API",
  "version": "2.1.0",
  "source": "BigQuery + WxTech Weather",
  "buildings": "107M+ in Thailand",
  "endpoints": {
    "/stats": "Get database statistics",
    "/buildings/bbox": "Get buildings in bounding box",
    "/buildings/nearby": "Get buildings near a point",
    "/weather/forecast": "Get weather forecast for location",
    "/solar/calculate": "Calculate solar potential",
    "/solar/forecast": "Get weather-enhanced solar forecast"
  }
}
```

---

### 2. Database Statistics

**GET /stats**

Retrieves comprehensive statistics about the building footprint database.

**Response**:
```json
{
  "total_buildings": 107682789,
  "confidence": {
    "average": 0.787,
    "min": 0.65,
    "max": 0.987
  },
  "area_m2": {
    "average": 96.1,
    "min": 2.5,
    "max": 49979.0
  },
  "extent": {
    "latitude": [4.92366889, 22.35084353],
    "longitude": [95.06391105, 106.53483782]
  }
}
```

**Field Descriptions**:
- `total_buildings`: Total number of building footprints in database
- `confidence.average`: Mean detection confidence score (0-1 scale)
- `area_m2`: Building area statistics in square meters
- `extent`: Geographic bounding box of dataset coverage

---

### 3. Buildings by Bounding Box

**GET /buildings/bbox**

Queries building footprints within a specified geographic bounding box.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| min_lat | float | Yes | - | Minimum latitude (decimal degrees) |
| max_lat | float | Yes | - | Maximum latitude (decimal degrees) |
| min_lon | float | Yes | - | Minimum longitude (decimal degrees) |
| max_lon | float | Yes | - | Maximum longitude (decimal degrees) |
| limit | integer | No | 1000 | Maximum results (max: 5000) |
| min_confidence | float | No | 0.7 | Minimum confidence threshold (0-1) |

**Example Request**:
```
GET /buildings/bbox?min_lat=13.7&max_lat=13.8&min_lon=100.5&max_lon=100.6&limit=10
```

**Response**:
```json
{
  "total": 254709,
  "buildings": [
    {
      "id": 338792,
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

**Field Descriptions**:
- `total`: Total buildings matching query (before limit applied)
- `id`: Internal database row number
- `open_buildings_id`: Google Open Buildings Plus Code identifier
- `geometry`: GeoJSON polygon geometry in WGS84 (EPSG:4326)

---

### 4. Buildings Near Point

**GET /buildings/nearby**

Retrieves buildings within a specified radius of a geographic point.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| lat | float | Yes | - | Center point latitude |
| lon | float | Yes | - | Center point longitude |
| radius_m | float | No | 500 | Search radius in meters |
| limit | integer | No | 100 | Maximum results (max: 1000) |
| min_confidence | float | No | 0.7 | Minimum confidence threshold |

**Example Request**:
```
GET /buildings/nearby?lat=13.7563&lon=100.5018&radius_m=1000&limit=5
```

**Response**: Same structure as `/buildings/bbox` with additional `distance_m` field for each building.

---

### 5. Weather Forecast

**GET /weather/forecast**

Retrieves real-time weather forecast data for a specified location.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| lat | float | Yes | - | Latitude (decimal degrees) |
| lon | float | Yes | - | Longitude (decimal degrees) |
| timezone | string | No | Asia/Bangkok | IANA timezone identifier |

**Example Request**:
```
GET /weather/forecast?lat=13.7563&lon=100.5018
```

**Response**:
```json
{
  "location": {
    "lat": 13.7563,
    "lon": 100.5018,
    "timezone": "Asia/Bangkok"
  },
  "impact_summary": {
    "impact_level": "good",
    "total_rain_24h": 0,
    "rainy_hours": 0,
    "max_temperature": 36,
    "avg_temperature": 31.1,
    "peak_solar_radiation": 1165,
    "avg_solar_radiation": 380,
    "summary": "Weather impact: Good"
  },
  "hourly_count": 73,
  "daily_count": 15,
  "fetched_at": "2026-03-30T15:30:00+07:00",
  "next_24h_preview": [
    {
      "time": "2026-03-30T16:00:00+07:00",
      "weather": "sunny",
      "temp": 34,
      "solar_radiation": 1079,
      "rain": 0.0
    }
  ]
}
```

**Weather Impact Levels**:
- `excellent`: No rain, high solar radiation (>800 W/m²)
- `good`: Minimal rain (<5mm), moderate radiation (400-800 W/m²)
- `fair`: Light rain (5-20mm), reduced radiation (200-400 W/m²)
- `poor`: Heavy rain (>20mm), low radiation (<200 W/m²)

---

### 6. Solar Generation Forecast

**GET /solar/forecast**

Generates weather-enhanced solar generation forecast for a PV system.

**Query Parameters**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| lat | float | Yes | - | System latitude |
| lon | float | Yes | - | System longitude |
| system_kwp | float | Yes | - | System size in kWp |
| timezone | string | No | Asia/Bangkok | IANA timezone identifier |

**Example Request**:
```
GET /solar/forecast?lat=13.7563&lon=100.5018&system_kwp=5
```

**Response**:
```json
{
  "location": {
    "lat": 13.7563,
    "lon": 100.5018
  },
  "system_kwp": 5.0,
  "next_24h_generation_kwh": 37.0,
  "weather_quality_score": 44,
  "avg_solar_radiation_24h": 380,
  "hourly_forecast": [
    {
      "time": "2026-03-30T16:00:00+07:00",
      "solar_radiation": 1079,
      "temperature": 34,
      "weather": "sunny",
      "generation_kwh": 4.2,
      "generation_factor": 0.85
    }
  ],
  "weekly_outlook": [
    {
      "date": "2026-03-30",
      "solar_radiation": 28.86,
      "max_temp": 34,
      "rain_probability": 0,
      "estimated_generation": 25.8
    }
  ],
  "analysis_time": "2026-03-30T15:30:00+07:00"
}
```

**Calculation Method**:
```
generation_kwh = system_kwp × (solar_radiation / 1000) × generation_factor
```

Where:
- `generation_factor`: Accounts for temperature derating, system losses, and inverter efficiency
- Typical range: 0.75-0.90 depending on conditions

---

### 7. Solar Potential Calculation

**POST /solar/calculate**

Calculates comprehensive solar photovoltaic potential for a building.

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

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| latitude | float | Yes | - | Building latitude |
| longitude | float | Yes | - | Building longitude |
| area_m2 | float | Yes | - | Building roof area (m²) |
| confidence | float | Yes | - | Detection confidence (0-1) |
| tilt | float | No | latitude | Panel tilt angle (degrees) |
| azimuth | float | No | 180 | Panel azimuth (0=N, 180=S) |

**Response**:
```json
{
  "usable_roof_area": 119.0,
  "system_size_kwp": 23.8,
  "annual_production_kwh": 49080.0,
  "installation_cost_thb": 593750.0,
  "annual_savings_thb": 205153.0,
  "payback_period_years": 2.9,
  "co2_reduction_kg": 19632.0,
  "co2_reduction_ton": 19.6,
  "irradiance_source": "pvlib (Clear Sky Model)",
  "irradiance_kwh_m2_day": 5.64,
  "weather_forecast": {
    "next_24h_generation": 58.4,
    "weather_quality_score": 44,
    "weekly_outlook": [...]
  },
  "assumptions": {
    "panel_efficiency": 0.20,
    "system_efficiency": 0.80,
    "usable_roof_ratio": 0.50,
    "cost_per_wp": 25,
    "electricity_rate": 4.18,
    "co2_factor": 0.40,
    "calculation_method": "pvlib_with_weather"
  }
}
```

---

## Calculation Parameters

All parameters are referenced to published sources and Thailand-specific data.

### Solar Irradiance

**Default Value**: 5.06 kWh/m²/day

**Source**: World Bank Global Solar Atlas via RatedPower (2022)

**Regional Variation**:
- Bangkok/Central: 4.8-5.3 kWh/m²/day
- Seasonal Peak (April-May): 5.6-6.7 kWh/m²/day

**Dynamic Source**: NASA POWER API ALLSKY_SFC_SW_DWN parameter when available

**Reference**: https://ratedpower.com/blog/solar-energy-thailand/

### Panel Efficiency

**Value**: 20% (0.20)

**Technology**: Standard commercial monocrystalline silicon

**Industry Range**: 18-22% (IRENA, IEA PVPS Thailand 2021)

**Justification**: Representative of current market-available modules

### System Efficiency (Performance Ratio)

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

### Usable Roof Area

**Value**: 50% (0.50)

**Justification**: Conservative estimate for Thailand urban buildings

**Exclusions**:
- HVAC equipment and water tanks
- Roof edge setbacks (safety and wind loading)
- Shading from parapet walls and adjacent structures
- Access pathways and maintenance clearances

**Building Type Variation**:
- Residential: 55-60%
- Commercial/Industrial: 40-50%

**Reference**: "Evaluating rooftop solar PV potential in Thailand" (DEDE data 2022)
https://www.researchgate.net/figure/Breakdown-of-the-costs-of-a-100-kWp-solar-rooftop-PV-system

### Installation Cost

**Value**: 25 THB/Wp

**Segment**: Commercial and Industrial (C&I) rooftop systems

**Trend**: Decreased from 27.5 THB/Wp (2020) to 25 THB/Wp (2024)

**Residential Systems**: Higher at approximately 39 THB/Wp due to smaller scale

**Academic Benchmark**: 25.14 THB/Wp for 100 kWp hospital system in Southern Thailand

**References**:
- Krungsri Research "Rooftop Solar Business Models Thailand" 2025
  https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
- ResearchGate breakdown study (DEDE data)

### Electricity Rate

**Value**: 4.18 THB/kWh

**Basis**: 2024 actual average rate

**Context**: Government capped rate at 3.99 THB/kWh through end of 2025

**Historical Average**: 4.26 THB/kWh (2024-2025 period)

**Rate Authority**: Energy Regulatory Commission (ERC), Metropolitan Electricity Authority (MEA), Provincial Electricity Authority (PEA)

**References**:
- https://www.globalpetrolprices.com/Thailand/electricity_prices/
- https://www.nationthailand.com/business/economy/40049646
- Krungsri Research citing ERC data

### CO₂ Emission Factor

**Value**: 0.40 kgCO₂/kWh

**Exact Value**: 0.399 kgCO₂/kWh (2024)

**Trend**: Decreased from 0.438 kgCO₂/kWh (2023)

**Source**: Energy Policy and Planning Office (EPPO), Ministry of Energy Thailand

**Data Provider**: CEIC

**Reference**: https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

---

## Calculation Formulas

### 1. Usable Roof Area

```
usable_roof_area = building_area × usable_roof_ratio × confidence_adjustment
```

Where:
```
confidence_adjustment = max(building_confidence, 0.7)
```

This accounts for Google Open Buildings detection uncertainty.

### 2. System Size

```
system_size_kWp = usable_roof_area × panel_efficiency
```

Based on Standard Test Conditions (STC): 1 m² of panel at 20% efficiency under 1 kW/m² irradiance = 0.20 kWp.

### 3. Annual Energy Production

**pvlib method (primary)**:

```python
for each hour in year:
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

### 4. Financial Metrics

```
installation_cost_THB = system_size_kWp × 1000 × cost_per_Wp

annual_savings_THB = annual_production_kWh × electricity_rate

payback_period_years = installation_cost_THB / annual_savings_THB
```

### 5. Environmental Impact

```
co2_reduction_kg_per_year = annual_production_kWh × co2_emission_factor

co2_reduction_tonnes_per_year = co2_reduction_kg_per_year / 1000
```

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Endpoint does not exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Common Errors

**Invalid Coordinates**:
```json
{
  "detail": "Latitude must be between -90 and 90"
}
```

**Missing Required Parameters**:
```json
{
  "detail": [
    {
      "loc": ["query", "lat"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Performance Considerations

### Query Optimization

1. **Bounding Box Queries**
   - Use appropriate `limit` values (default: 1000, max: 5000)
   - Smaller geographic areas return faster
   - BigQuery spatial functions optimized for large-scale queries

2. **Confidence Filtering**
   - Higher `min_confidence` values reduce result set size
   - Recommended: 0.7 for general use, 0.8+ for high-quality data

3. **Caching**
   - Weather forecasts cached for 1 hour
   - Building queries cached based on bbox parameters
   - Stats endpoint cached for 24 hours

### Response Times

| Endpoint | Typical Response Time |
|----------|----------------------|
| GET / | < 100ms |
| GET /stats | < 400ms |
| GET /buildings/bbox | < 600ms |
| GET /weather/forecast | < 500ms |
| POST /solar/calculate | < 600ms |
| GET /solar/forecast | < 800ms |

---

## Rate Limiting

Currently no rate limiting is enforced. For production use, implement client-side throttling:

- Recommended: 10 requests per second per client
- Burst: Up to 50 requests per second for short periods

---

## Authentication

Current deployment: No authentication required (public API)

For production deployment with authentication:
- Implement API key authentication
- Use Cloud Run IAM for service-to-service calls
- Consider OAuth 2.0 for user-facing applications

---

## Deployment Information

### Infrastructure

- **Platform**: Google Cloud Run (serverless)
- **Region**: asia-southeast1 (Singapore)
- **Container**: Python 3.11-slim with FastAPI
- **Memory**: 1 GiB
- **CPU**: 2 vCPU
- **Scaling**: 0-10 instances (auto-scaling)
- **Timeout**: 300 seconds

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GCP_PROJECT | Google Cloud Project ID | Yes |
| WXTECH_API_KEY | WxTech Weather API key | No |

### Dependencies

Core packages (requirements.txt):
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
google-cloud-bigquery==3.14.1
pandas==2.1.4
numpy==1.26.2
requests==2.31.0
pvlib==0.10.3
aiohttp==3.9.1
```

---

## Testing

### Health Check

```bash
curl https://solar-weather-api-715107904640.asia-southeast1.run.app/
```

Expected: HTTP 200 with API information

### Database Connectivity

```bash
curl https://solar-weather-api-715107904640.asia-southeast1.run.app/stats
```

Expected: HTTP 200 with database statistics

### Solar Calculation

```bash
curl -X POST https://solar-weather-api-715107904640.asia-southeast1.run.app/solar/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 13.7563,
    "longitude": 100.5018,
    "area_m2": 250,
    "confidence": 0.95
  }'
```

Expected: HTTP 200 with solar potential calculations

---

## API Versioning

Current version: 2.1.0

Version history:
- 2.1.0 (2026-03-30): Added BigQuery integration, weather forecasting
- 2.0.0: Initial production release with pvlib integration
- 1.0.0: Beta release with basic solar calculations

---

## Support and Contact

For technical issues or questions:
- GitHub Issues: https://github.com/Teera235/toothless_solar/issues
- Repository: https://github.com/Teera235/toothless_solar

---

## References

1. IEA PVPS (2021). "National Survey Report of PV Power Applications in Thailand 2021"
   https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf

2. Krungsri Research (2025). "Rooftop Solar Business Models Thailand"
   https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025

3. RatedPower (2022). "Solar Energy in Thailand: Market Overview and Potential"
   https://ratedpower.com/blog/solar-energy-thailand/

4. CEIC Data. "Thailand Carbon Dioxide Emissions Statistics"
   https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics

5. Google Research (2024). "Open Buildings Dataset"
   https://sites.research.google/open-buildings/

6. pvlib-python Documentation
   https://pvlib-python.readthedocs.io/

7. BigQuery Documentation
   https://cloud.google.com/bigquery/docs

8. FastAPI Documentation
   https://fastapi.tiangolo.com/

---

**Document Version**: 1.0  
**Last Updated**: March 30, 2026  
**API Version**: 2.1.0
