/**
 * Buildings API Service
 * Access to 1.88M building footprints from Google Open Buildings
 */

const API_BASE_URL = process.env.REACT_APP_BUILDINGS_API_URL || 'http://localhost:8001';
const NASA_POWER_API = 'https://power.larc.nasa.gov/api/temporal/monthly/point';

console.log('🔧 API Configuration:', {
  API_BASE_URL,
  env: process.env.REACT_APP_BUILDINGS_API_URL
});

/**
 * Get API statistics
 */
export const getBuildingsStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return await response.json();
  } catch (error) {
    console.error('Error fetching buildings stats:', error);
    throw error;
  }
};

/**
 * Get solar irradiance data from NASA POWER API
 * @param {number} latitude - Latitude
 * @param {number} longitude - Longitude
 * @returns {Promise<Object>} Solar irradiance data with monthly averages
 */
export const getNASASolarData = async (latitude, longitude) => {
  try {
    // NASA POWER API for monthly climatology (long-term average)
    const params = new URLSearchParams({
      parameters: 'ALLSKY_SFC_SW_DWN',  // All-sky surface shortwave downward irradiance
      community: 'RE',                   // Renewable Energy community
      longitude: longitude.toFixed(2),
      latitude: latitude.toFixed(2),
      format: 'JSON'
    });

    const url = `${NASA_POWER_API}?${params}`;
    console.log('🛰️ Fetching NASA POWER data:', url);

    const response = await fetch(url);
    if (!response.ok) {
      console.warn('⚠️ NASA POWER API error:', response.status);
      return null;
    }

    const data = await response.json();
    
    // Extract monthly averages
    const monthlyData = data?.properties?.parameter?.ALLSKY_SFC_SW_DWN;
    
    if (!monthlyData) {
      console.warn('⚠️ No solar data in NASA response');
      return null;
    }

    // Calculate annual average (kWh/m²/day)
    const monthlyValues = Object.values(monthlyData).filter(v => typeof v === 'number');
    const annualAverage = monthlyValues.reduce((sum, val) => sum + val, 0) / monthlyValues.length;

    console.log('✅ NASA POWER data received:', {
      annualAverage: annualAverage.toFixed(2),
      monthlyRange: [Math.min(...monthlyValues).toFixed(2), Math.max(...monthlyValues).toFixed(2)]
    });

    return {
      avgIrradiance: annualAverage,
      monthlyIrradiance: monthlyData,
      source: 'NASA POWER',
      coordinates: { latitude, longitude }
    };
  } catch (error) {
    console.error('❌ Error fetching NASA POWER data:', error);
    return null; // Fallback to default values
  }
};

/**
 * Get buildings within bounding box
 * @param {Object} bbox - {minLat, maxLat, minLon, maxLon}
 * @param {Object} options - {limit, minConfidence}
 */
export const getBuildingsInBBox = async (bbox, options = {}) => {
  const {
    limit = 1000,
    minConfidence = 0.7
  } = options;

  try {
    const params = new URLSearchParams({
      min_lat: bbox.minLat,
      max_lat: bbox.maxLat,
      min_lon: bbox.minLon,
      max_lon: bbox.maxLon,
      limit,
      min_confidence: minConfidence
    });

    const url = `${API_BASE_URL}/buildings/bbox?${params}`;
    console.log('🔗 Fetching from:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      mode: 'cors'
    });

    if (!response.ok) {
      console.error('❌ API Error:', response.status, response.statusText);
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    console.log('✅ Data received:', data.buildings?.length, 'buildings');

    // Parse GeoJSON geometries safely
    if (data.buildings) {
      data.buildings = data.buildings.map(building => {
        try {
          return {
            ...building,
            geometry: typeof building.geometry === 'string'
              ? JSON.parse(building.geometry)
              : building.geometry
          };
        } catch (e) {
          console.warn('Failed to parse geometry for building', building.id, e);
          return { ...building, geometry: null };
        }
      });
    }

    return data;
  } catch (error) {
    console.error('❌ Error fetching buildings in bbox:', error);
    throw error;
  }
};

/**
 * Get buildings near a point
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @param {Object} options - {radiusM, limit, minConfidence}
 */
export const getBuildingsNearby = async (lat, lon, options = {}) => {
  const {
    radiusM = 500,
    limit = 100,
    minConfidence = 0.7
  } = options;

  try {
    const params = new URLSearchParams({
      lat,
      lon,
      radius_m: radiusM,
      limit,
      min_confidence: minConfidence
    });

    const response = await fetch(`${API_BASE_URL}/buildings/nearby?${params}`);
    if (!response.ok) throw new Error('Failed to fetch nearby buildings');

    const data = await response.json();

    // Parse GeoJSON geometries
    data.buildings = data.buildings.map(building => ({
      ...building,
      geometry: building.geometry ? JSON.parse(building.geometry) : null
    }));

    return data;
  } catch (error) {
    console.error('Error fetching nearby buildings:', error);
    throw error;
  }
};

/**
 * Get building details by ID
 * @param {number} buildingId - Building ID
 */
export const getBuildingDetail = async (buildingId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/buildings/${buildingId}`);
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Building not found');
      }
      throw new Error('Failed to fetch building details');
    }

    const building = await response.json();

    // Parse GeoJSON
    if (building.geometry) {
      building.geometry = JSON.parse(building.geometry);
    }
    if (building.centroid) {
      building.centroid = JSON.parse(building.centroid);
    }

    return building;
  } catch (error) {
    console.error('Error fetching building detail:', error);
    throw error;
  }
};

/**
 * Convert buildings to GeoJSON FeatureCollection
 * @param {Array} buildings - Array of buildings
 */
export const buildingsToGeoJSON = (buildings) => {
  return {
    type: 'FeatureCollection',
    features: buildings.map(building => ({
      type: 'Feature',
      id: building.id,
      geometry: building.geometry,
      properties: {
        id: building.id,
        open_buildings_id: building.open_buildings_id,
        area_m2: building.area_m2,
        confidence: building.confidence,
        latitude: building.latitude,
        longitude: building.longitude,
        distance_m: building.distance_m
      }
    }))
  };
};

/**
 * Solar calculation constants — Thailand-specific
 * All values are referenced to published sources.
 *
 * SOLAR IRRADIANCE
 *   5.06 kWh/m²/day — national average (World Bank Global Solar Atlas via RatedPower, 2022)
 *   Bangkok / Central region typically 4.8–5.3 kWh/m²/day
 *   Peak months (Apr–May): 5.6–6.7 kWh/m²/day
 *   Source: https://ratedpower.com/blog/solar-energy-thailand/
 *
 * PANEL EFFICIENCY
 *   0.20 (20%) — standard commercial monocrystalline panel, industry norm 2024
 *   Typical range: 18–22% (IRENA, IEA PVPS Thailand 2021)
 *
 * SYSTEM EFFICIENCY (Performance Ratio)
 *   0.80 (80%) — IEC 61724 standard; Thai PV rooftop studies use 75–82%
 *   Accounts for: inverter losses (~2–5%), wiring losses (~2%), soiling/dust (~3%),
 *   temperature derating (~5–8% in Thailand's heat), mismatch losses (~2%)
 *   Source: IEA PVPS National Survey Report Thailand 2021
 *           https://iea-pvps.org/wp-content/uploads/2022/09/NSR-of-PV-Power-Applications-in-Thailand-2021.pdf
 *
 * USABLE ROOF AREA
 *   0.50 (50%) — conservative estimate for Thailand urban buildings
 *   Accounts for: HVAC units, water tanks, setbacks from roof edges, shading from parapet walls
 *   Academic studies on Thailand GIS-based rooftop PV potential use 40–60% depending on building type
 *   Source: "Evaluating rooftop solar PV potential in Thailand" (ResearchGate / DEDE data 2022)
 *           https://www.researchgate.net/figure/Breakdown-of-the-costs-of-a-100-kWp-solar-rooftop-PV-system...
 *   Note: residential may be 55–60%, commercial/industrial typically 40–50%
 *
 * INSTALLATION COST
 *   25 THB/Wp — commercial/industrial rooftop (C&I segment)
 *   Source: Krungsri Research "Rooftop Solar Business Models Thailand" 2025
 *           https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
 *   (Down from 27.5 THB/Wp in 2020; residential systems higher ~39 THB/Wp)
 *   Academic benchmark (100 kWp hospital system, Southern Thailand): 25.14 THB/Wp
 *   Source: ResearchGate breakdown study (DEDE data)
 *
 * ELECTRICITY RATE
 *   4.26 THB/kWh — Thailand residential average (GlobalPetrolPrices, sourced from ERC/MEA/PEA, 2024–2025)
 *   Government has capped rate at 3.99 THB/kWh through end of 2025 (NEPC announcement May 2025)
 *   Source: https://www.globalpetrolprices.com/Thailand/electricity_prices/
 *           https://www.nationthailand.com/business/economy/40049646
 *   Using 4.18 THB/kWh as mid-point average reflecting 2024 actual rate
 *   Source: https://www.krungsri.com/en/research/research-intelligence/solar-rooftop-2-2025
 *
 * CO₂ EMISSION FACTOR
 *   0.40 kgCO₂/kWh — Thailand national grid (EPPO / Ministry of Energy 2024)
 *   Exact reported value: 0.399 kgCO₂/kWh (2024), down from 0.438 (2023)
 *   Source: CEIC / Energy Policy and Planning Office (EPPO) Thailand
 *           https://www.ceicdata.com/en/thailand/carbon-dioxide-emissions-statistics/...
 */
const SOLAR_CONSTANTS = {
  avgIrradiance: 5.06,       // kWh/m²/day — World Bank Global Solar Atlas (Thailand national avg)
  panelEfficiency: 0.20,     // 20% — standard monocrystalline panel
  systemEfficiency: 0.80,    // 80% Performance Ratio — IEA PVPS Thailand 2021
  usableRoofRatio: 0.50,     // 50% — conservative urban Thailand estimate (DEDE GIS study 2022)
  costPerWp: 25,             // THB/Wp — C&I rooftop avg 2023–2024 (Krungsri Research / DEDE)
  electricityRate: 4.18,     // THB/kWh — 2024 actual average (Krungsri Research citing ERC data)
  co2Factor: 0.40,           // kgCO₂/kWh — Thailand grid 2024 (EPPO via CEIC)
};

/**
 * Calculate solar potential using backend pvlib endpoint
 * @param {Object} building - Building object with area_m2, confidence, latitude, longitude
 * @returns {Promise<Object>} Solar potential metrics from pvlib calculation
 */
export const calculateSolarPotentialPvlib = async (building) => {
  try {
    const response = await fetch(`${API_BASE_URL}/solar/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude: building.latitude,
        longitude: building.longitude,
        area_m2: building.area_m2,
        confidence: building.confidence,
        tilt: null,  // Use optimal (latitude)
        azimuth: 180  // South-facing
      })
    });

    if (!response.ok) {
      console.warn('⚠️ pvlib calculation failed, using fallback');
      return null;
    }

    const data = await response.json();
    
    console.log('✅ pvlib calculation received:', data);
    
    // Transform to match frontend format
    return {
      usableRoofArea: data.usable_roof_area,
      systemSizeKWp: data.system_size_kwp,
      annualProduction: data.annual_production_kwh,
      installationCost: data.installation_cost_thb,
      annualSavings: data.annual_savings_thb,
      paybackPeriod: data.payback_period_years,
      co2ReductionKg: data.co2_reduction_kg,
      co2ReductionTon: data.co2_reduction_ton,
      confidence: Math.round(building.confidence * 100),
      irradianceSource: data.irradiance_source,
      irradianceValue: data.irradiance_kwh_m2_day,
      assumptionsUsed: data.assumptions
    };
  } catch (error) {
    console.error('❌ Error calculating solar potential with pvlib:', error);
    return null;
  }
};

/**
 * Calculate solar potential for a building
 * Tries pvlib backend first, falls back to client-side calculation
 *
 * @param {Object} building - Building object with area_m2, confidence, latitude, longitude
 * @param {Object} solarData - Optional override for solar parameters
 * @returns {Promise<Object>} Solar potential metrics
 */
export const calculateBuildingSolarPotential = async (building, solarData = {}) => {
  // Try pvlib backend first
  const pvlibResult = await calculateSolarPotentialPvlib(building);
  if (pvlibResult) {
    return pvlibResult;
  }

  // Fallback to client-side calculation
  console.log('📊 Using client-side solar calculation');
  
  const { area_m2, confidence } = building;

  // Merge defaults with any caller-supplied overrides (e.g. location-specific irradiance from NASA POWER)
  const params = { ...SOLAR_CONSTANTS, ...solarData };

  // Step 1: Usable roof area
  // confidence score from Google Open Buildings (0–1) adjusts effective area
  // Low-confidence footprints may be less accurate, so we scale usable area down accordingly.
  // Minimum floor of 0.7 prevents over-penalising moderately confident detections.
  const confidenceAdjustment = Math.max(confidence, 0.7);
  const usableRoofArea = area_m2 * params.usableRoofRatio * confidenceAdjustment;

  // Step 2: System size in kWp
  // 1 m² of panel at panelEfficiency under Standard Test Conditions (1 kW/m²) = panelEfficiency kWp
  const systemSizeKWp = usableRoofArea * params.panelEfficiency;

  // Step 3: Annual energy production
  // kWp × peak sun hours/day × days/yr × Performance Ratio
  const annualProduction = systemSizeKWp * params.avgIrradiance * 365 * params.systemEfficiency;

  // Step 4: Financial
  const installationCost = systemSizeKWp * 1000 * params.costPerWp; // kWp → W → × THB/W
  const annualSavings = annualProduction * params.electricityRate;
  const paybackPeriod = annualSavings > 0 ? installationCost / annualSavings : null;

  // Step 5: Environmental
  const co2Reduction = annualProduction * params.co2Factor; // kgCO₂/yr

  return {
    // Physical
    usableRoofArea:   Math.round(usableRoofArea),           // m²
    systemSizeKWp:    Math.round(systemSizeKWp * 10) / 10,  // kWp
    annualProduction: Math.round(annualProduction),          // kWh/yr

    // Financial (THB)
    installationCost: Math.round(installationCost),
    annualSavings:    Math.round(annualSavings),
    paybackPeriod:    paybackPeriod !== null
      ? Math.round(paybackPeriod * 10) / 10
      : null,                                                // years

    // Environmental
    co2ReductionKg:   Math.round(co2Reduction),             // kgCO₂/yr
    co2ReductionTon:  Math.round(co2Reduction / 1000 * 10) / 10, // tCO₂/yr

    // Data quality
    confidence:       Math.round(confidence * 100),          // %
    
    // Data source
    irradianceSource: 'Client-side calculation',
    irradianceValue:  Math.round(params.avgIrradiance * 100) / 100,

    // Expose parameters used so callers can display assumptions
    assumptionsUsed: {
      avgIrradiance:    params.avgIrradiance,
      panelEfficiency:  params.panelEfficiency,
      systemEfficiency: params.systemEfficiency,
      usableRoofRatio:  params.usableRoofRatio,
      costPerWp:        params.costPerWp,
      electricityRate:  params.electricityRate,
      co2Factor:        params.co2Factor,
      calculation_method: 'simplified'
    }
  };
};

export default {
  getBuildingsStats,
  getNASASolarData,
  getBuildingsInBBox,
  getBuildingsNearby,
  getBuildingDetail,
  buildingsToGeoJSON,
  calculateBuildingSolarPotential,
  calculateSolarPotentialPvlib,
  SOLAR_CONSTANTS,
};

