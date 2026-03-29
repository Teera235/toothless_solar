/**
 * Buildings Map Component
 * Display building footprints on interactive map
 */

import React, { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getBuildingsInBBox, calculateBuildingSolarPotential, buildingsToGeoJSON } from '../services/buildingsAPI';
import WeatherPanel from './WeatherPanel';

// Fix Leaflet default marker icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const BuildingsLayer = ({ buildings, onBuildingClick }) => {
  // Style function for buildings
  const buildingStyle = (feature) => {
    const confidence = feature.properties.confidence;

    // Color based on confidence
    let fillColor = '#3b82f6'; // blue
    if (confidence >= 0.9) fillColor = '#10b981'; // green
    else if (confidence >= 0.8) fillColor = '#3b82f6'; // blue
    else if (confidence >= 0.7) fillColor = '#f59e0b'; // orange
    else fillColor = '#ef4444'; // red

    return {
      fillColor,
      fillOpacity: 0.4,
      color: fillColor,
      weight: 1,
      opacity: 0.8
    };
  };

  // On each feature
  const onEachFeature = (feature, layer) => {
    const props = feature.properties;
    
    // Popup content
    const popupContent = `
      <div style="padding: 8px;">
        <h3 style="font-weight: bold; font-size: 14px; margin-bottom: 8px;">Building #${props.id}</h3>
        <div style="font-size: 12px;">
          <p><strong>Area:</strong> ${props.area_m2.toFixed(1)} m²</p>
          <p><strong>Confidence:</strong> ${(props.confidence * 100).toFixed(1)}%</p>
        </div>
      </div>
    `;

    layer.bindPopup(popupContent);

    // Click handler
    layer.on('click', () => {
      if (onBuildingClick) {
        onBuildingClick(props);
      }
    });
  };

  // Convert buildings to GeoJSON
  const geojson = buildingsToGeoJSON(buildings);

  return (
    <GeoJSON
      key={JSON.stringify(buildings)}
      data={geojson}
      style={buildingStyle}
      onEachFeature={onEachFeature}
    />
  );
};

const MapController = ({ onBoundsChange }) => {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds();
      onBoundsChange({
        minLat: bounds.getSouth(),
        maxLat: bounds.getNorth(),
        minLon: bounds.getWest(),
        maxLon: bounds.getEast()
      });
    }
  });

  return null;
};

const BuildingsMap = () => {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [solarPotential, setSolarPotential] = useState(null);
  const [stats, setStats] = useState({ total: 0, displayed: 0 });
  const [showWeather, setShowWeather] = useState(false);
  const [weatherLocation, setWeatherLocation] = useState(null);

  // Bangkok center
  const center = [13.7563, 100.5018];

  // Load buildings when map bounds change
  const handleBoundsChange = useCallback(async (bounds) => {
    console.log('🗺️ Loading buildings for bounds:', bounds);
    setLoading(true);
    try {
      const data = await getBuildingsInBBox(bounds, {
        limit: 1000,
        minConfidence: 0.7
      });
      
      console.log('📊 Buildings data received:', {
        total: data.total,
        count: data.buildings.length
      });
      
      setBuildings(data.buildings);
      setStats({
        total: data.total,
        displayed: data.buildings.length
      });
    } catch (error) {
      console.error('❌ Error loading buildings:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Load initial buildings on mount
  useEffect(() => {
    console.log('🚀 BuildingsMap mounted');
  }, []);

  // Handle building selection
  const handleBuildingClick = useCallback(async (building) => {
    setSelectedBuilding(building);
    setSolarPotential(null); // Clear previous data
    
    // Calculate solar potential (will try pvlib backend first, then fallback)
    const potential = await calculateBuildingSolarPotential(building);
    setSolarPotential(potential);
    
    // Set weather location for this building
    setWeatherLocation({
      lat: building.latitude,
      lon: building.longitude
    });
  }, []);

  // Handle weather panel toggle
  const handleWeatherToggle = () => {
    if (!showWeather && !weatherLocation) {
      // Default to Bangkok center if no building selected
      setWeatherLocation({ lat: 13.7563, lon: 100.5018 });
    }
    setShowWeather(!showWeather);
  };

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh' }}>
      {/* Map */}
      <MapContainer
        center={center}
        zoom={13}
        style={{ width: '100%', height: '100%' }}
      >
        {/* Satellite imagery from Esri */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
          maxZoom={19}
        />
        
        {/* Optional: Add labels overlay */}
        <TileLayer
          attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
          maxZoom={19}
        />
        
        <MapController onBoundsChange={handleBoundsChange} />
        
        {buildings.length > 0 && (
          <BuildingsLayer
            buildings={buildings}
            onBuildingClick={handleBuildingClick}
          />
        )}
      </MapContainer>

      {/* Loading indicator */}
      {loading && (
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'white',
          padding: '8px 16px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 1000
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid #3b82f6',
              borderTopColor: 'transparent',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
            <span style={{ fontSize: '14px' }}>Loading buildings...</span>
          </div>
        </div>
      )}

      {/* Stats panel */}
      <div style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        backgroundColor: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 1000,
        maxWidth: '300px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ fontWeight: 'bold', fontSize: '14px' }}>Buildings Data</h3>
          <button
            onClick={handleWeatherToggle}
            style={{
              padding: '4px 8px',
              backgroundColor: showWeather ? '#3b82f6' : '#f3f4f6',
              color: showWeather ? 'white' : '#6b7280',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
            title="Toggle weather forecast"
          >
            🌤️ Weather
          </button>
        </div>
        <div style={{ fontSize: '12px' }}>
          <p>Displayed: <span style={{ fontWeight: '600' }}>{stats.displayed.toLocaleString()}</span></p>
          <p>Total in view: <span style={{ fontWeight: '600' }}>{stats.total.toLocaleString()}</span></p>
          {stats.total > stats.displayed && (
            <p style={{ color: '#6b7280', marginTop: '8px' }}>
              Showing top {stats.displayed} buildings
            </p>
          )}
        </div>
      </div>

      {/* Weather Panel */}
      {showWeather && weatherLocation && (
        <WeatherPanel
          location={weatherLocation}
          systemKwp={solarPotential?.systemSizeKWp}
          onClose={() => setShowWeather(false)}
        />
      )}

      {/* Solar potential panel */}
      {selectedBuilding && solarPotential && (
        <div style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          backgroundColor: 'white',
          padding: '16px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 1000,
          maxWidth: '400px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
            <h3 style={{ fontWeight: 'bold' }}>Solar Potential Analysis</h3>
            <button
              onClick={() => {
                setSelectedBuilding(null);
                setSolarPotential(null);
              }}
              style={{
                background: 'none',
                border: 'none',
                color: '#6b7280',
                cursor: 'pointer',
                fontSize: '18px'
              }}
            >
              ✕
            </button>
          </div>

          <div style={{ fontSize: '14px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              <div>
                <p style={{ color: '#6b7280' }}>Building Area</p>
                <p style={{ fontWeight: '600' }}>{selectedBuilding.area_m2.toFixed(1)} m²</p>
              </div>
              <div>
                <p style={{ color: '#6b7280' }}>Usable Roof</p>
                <p style={{ fontWeight: '600' }}>{solarPotential.usableRoofArea} m²</p>
              </div>
              <div>
                <p style={{ color: '#6b7280' }}>System Size</p>
                <p style={{ fontWeight: '600' }}>{solarPotential.systemSizeKWp} kW</p>
              </div>
              <div>
                <p style={{ color: '#6b7280' }}>Confidence</p>
                <p style={{ fontWeight: '600' }}>{solarPotential.confidence}%</p>
              </div>
            </div>

            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '12px', marginTop: '12px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <p style={{ color: '#6b7280' }}>Annual Production</p>
                  <p style={{ fontWeight: '600', color: '#10b981' }}>
                    {solarPotential.annualProduction.toLocaleString()} kWh
                  </p>
                </div>
                <div>
                  <p style={{ color: '#6b7280' }}>Annual Savings</p>
                  <p style={{ fontWeight: '600', color: '#10b981' }}>
                    ฿{solarPotential.annualSavings.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#6b7280' }}>Installation Cost</p>
                  <p style={{ fontWeight: '600' }}>
                    ฿{solarPotential.installationCost.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p style={{ color: '#6b7280' }}>Payback Period</p>
                  <p style={{ fontWeight: '600' }}>
                    {solarPotential.paybackPeriod} years
                  </p>
                </div>
              </div>
            </div>

            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '12px', marginTop: '12px' }}>
              <p style={{ color: '#6b7280' }}>CO₂ Reduction</p>
              <p style={{ fontWeight: '600', color: '#10b981' }}>
                {solarPotential.co2ReductionKg.toLocaleString()} kg/year
              </p>
            </div>

            {solarPotential.irradianceSource && (
              <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '12px', marginTop: '12px', fontSize: '12px', color: '#6b7280' }}>
                <p>
                  <strong>Solar Irradiance:</strong> {solarPotential.irradianceValue?.toFixed(2)} kWh/m²/day
                </p>
                <p style={{ marginTop: '4px' }}>
                  <strong>Data Source:</strong> {solarPotential.irradianceSource}
                </p>
                {solarPotential.weatherForecast && (
                  <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
                    <p style={{ fontWeight: '600', marginBottom: '4px' }}>Weather Forecast:</p>
                    <p>Next 24h: {solarPotential.weatherForecast.next_24h_generation} kWh</p>
                    <p>Weather Score: {solarPotential.weatherForecast.weather_quality_score}/100</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Legend */}
      <div style={{
        position: 'absolute',
        bottom: '16px',
        right: '16px',
        backgroundColor: 'white',
        padding: '12px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 1000
      }}>
        <h4 style={{ fontWeight: 'bold', fontSize: '12px', marginBottom: '8px' }}>Confidence Level</h4>
        <div style={{ fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{ width: '16px', height: '16px', backgroundColor: '#10b981', borderRadius: '2px' }}></div>
            <span>≥ 90%</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{ width: '16px', height: '16px', backgroundColor: '#3b82f6', borderRadius: '2px' }}></div>
            <span>80-90%</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{ width: '16px', height: '16px', backgroundColor: '#f59e0b', borderRadius: '2px' }}></div>
            <span>70-80%</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '16px', height: '16px', backgroundColor: '#ef4444', borderRadius: '2px' }}></div>
            <span>&lt; 70%</span>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default BuildingsMap;
