/**
 * Weather Panel Component
 * Display weather forecast and solar impact
 */

import React, { useState, useEffect } from 'react';
import { getWeatherForecast, getSolarForecast, formatWeatherData, formatSolarForecastData } from '../services/weatherAPI';

const WeatherIcon = ({ weather, size = 24 }) => {
  const icons = {
    sunny: '☀️',
    cloudy: '☁️',
    rain: '🌧️',
    snow: '❄️',
    unknown: '❓'
  };
  
  return (
    <span style={{ fontSize: `${size}px` }}>
      {icons[weather] || icons.unknown}
    </span>
  );
};

const WeatherPanel = ({ location, systemKwp, onClose }) => {
  const [weatherData, setWeatherData] = useState(null);
  const [solarForecast, setSolarForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (location) {
      loadWeatherData();
    }
  }, [location, systemKwp]);

  const loadWeatherData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [weather, solar] = await Promise.all([
        getWeatherForecast(location.lat, location.lon),
        systemKwp ? getSolarForecast(location.lat, location.lon, systemKwp) : null
      ]);
      
      setWeatherData(formatWeatherData(weather));
      setSolarForecast(formatSolarForecastData(solar));
    } catch (err) {
      setError(err.message);
      console.error('Weather data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{
        position: 'absolute',
        top: '16px',
        left: '16px',
        backgroundColor: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 1000,
        width: '320px'
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
          <span>Loading weather data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        position: 'absolute',
        top: '16px',
        left: '16px',
        backgroundColor: 'white',
        padding: '16px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 1000,
        width: '320px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h3 style={{ fontWeight: 'bold', color: '#ef4444' }}>Weather Error</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ fontSize: '14px', color: '#6b7280' }}>{error}</p>
        <button 
          onClick={loadWeatherData}
          style={{
            marginTop: '8px',
            padding: '6px 12px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{
      position: 'absolute',
      top: '16px',
      left: '16px',
      backgroundColor: 'white',
      padding: '16px',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      zIndex: 1000,
      width: '320px',
      maxHeight: '80vh',
      overflowY: 'auto'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontWeight: 'bold', fontSize: '16px' }}>Weather Forecast</h3>
        <button 
          onClick={onClose}
          style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#6b7280' }}
        >
          ✕
        </button>
      </div>

      {/* Location */}
      <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '16px' }}>
        {location.lat.toFixed(4)}, {location.lon.toFixed(4)}
      </div>

      {/* Weather Impact Summary */}
      {weatherData && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            padding: '12px',
            backgroundColor: weatherData.impactColor + '20',
            borderLeft: `4px solid ${weatherData.impactColor}`,
            borderRadius: '4px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                backgroundColor: weatherData.impactColor,
                borderRadius: '50%'
              }}></div>
              <span style={{ fontWeight: '600', fontSize: '14px' }}>
                {weatherData.impactLabel} Conditions
              </span>
            </div>
            <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
              {weatherData.summary}
            </p>
          </div>
        </div>
      )}

      {/* Solar Forecast Summary */}
      {solarForecast && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ fontWeight: '600', fontSize: '14px', marginBottom: '8px' }}>
            Solar Generation Forecast
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Next 24h</p>
              <p style={{ fontWeight: '600', color: '#10b981', margin: 0 }}>
                {solarForecast.next24hGeneration} kWh
              </p>
            </div>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Weather Score</p>
              <p style={{ fontWeight: '600', margin: 0 }}>
                {solarForecast.weatherQualityScore}/100
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Current Conditions */}
      {weatherData && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ fontWeight: '600', fontSize: '14px', marginBottom: '8px' }}>
            Current Conditions
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Temperature</p>
              <p style={{ fontWeight: '600', margin: 0 }}>{weatherData.avgTemp}°C</p>
            </div>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Solar Radiation</p>
              <p style={{ fontWeight: '600', margin: 0 }}>{weatherData.avgSolarRadiation} W/m²</p>
            </div>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Rain (24h)</p>
              <p style={{ fontWeight: '600', margin: 0 }}>{weatherData.totalRain24h} mm</p>
            </div>
            <div>
              <p style={{ color: '#6b7280', margin: 0 }}>Rainy Hours</p>
              <p style={{ fontWeight: '600', margin: 0 }}>{weatherData.rainyHours}/24</p>
            </div>
          </div>
        </div>
      )}

      {/* Hourly Preview */}
      {weatherData?.hourlyPreview && (
        <div style={{ marginBottom: '16px' }}>
          <h4 style={{ fontWeight: '600', fontSize: '14px', marginBottom: '8px' }}>
            Next 12 Hours
          </h4>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(4, 1fr)', 
            gap: '8px',
            fontSize: '11px'
          }}>
            {weatherData.hourlyPreview.slice(0, 8).map((hour, index) => (
              <div key={index} style={{
                textAlign: 'center',
                padding: '6px',
                backgroundColor: '#f9fafb',
                borderRadius: '4px'
              }}>
                <div style={{ marginBottom: '2px' }}>
                  {new Date(hour.time).getHours()}:00
                </div>
                <WeatherIcon weather={hour.weather} size={16} />
                <div style={{ marginTop: '2px', fontWeight: '600' }}>
                  {hour.temp}°C
                </div>
                <div style={{ color: '#6b7280' }}>
                  {hour.solar_radiation}W
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Weekly Outlook */}
      {solarForecast?.dailyChart && (
        <div>
          <h4 style={{ fontWeight: '600', fontSize: '14px', marginBottom: '8px' }}>
            7-Day Solar Outlook
          </h4>
          <div style={{ fontSize: '11px' }}>
            {solarForecast.dailyChart.slice(0, 5).map((day, index) => (
              <div key={index} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '6px 0',
                borderBottom: index < 4 ? '1px solid #f3f4f6' : 'none'
              }}>
                <div style={{ flex: 1 }}>
                  {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                </div>
                <div style={{ flex: 1, textAlign: 'center' }}>
                  {day.maxTemp}°C
                </div>
                <div style={{ flex: 1, textAlign: 'center', color: '#10b981', fontWeight: '600' }}>
                  {day.generation} kWh
                </div>
                <div style={{ flex: 1, textAlign: 'right', color: '#6b7280' }}>
                  {day.rainProbability}% rain
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ 
        marginTop: '16px', 
        paddingTop: '12px', 
        borderTop: '1px solid #f3f4f6',
        fontSize: '10px',
        color: '#9ca3af',
        textAlign: 'center'
      }}>
        Powered by WxTech 5km Weather API
      </div>
    </div>
  );
};

export default WeatherPanel;