/**
 * Weather API Service
 * Interface with backend weather endpoints
 */

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8080';

/**
 * Get weather forecast for location
 */
export const getWeatherForecast = async (lat, lon, timezone = 'Asia/Bangkok') => {
  try {
    const response = await fetch(
      `${API_BASE}/weather/forecast?lat=${lat}&lon=${lon}&timezone=${timezone}`
    );
    
    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('❌ Weather forecast error:', error);
    throw error;
  }
};

/**
 * Get solar generation forecast
 */
export const getSolarForecast = async (lat, lon, systemKwp, timezone = 'Asia/Bangkok') => {
  try {
    const response = await fetch(
      `${API_BASE}/solar/forecast?lat=${lat}&lon=${lon}&system_kwp=${systemKwp}&timezone=${timezone}`
    );
    
    if (!response.ok) {
      throw new Error(`Solar forecast API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('❌ Solar forecast error:', error);
    throw error;
  }
};

/**
 * Weather impact levels with colors and descriptions
 */
export const WEATHER_IMPACT_LEVELS = {
  excellent: {
    color: '#10b981',
    label: 'Excellent',
    description: 'Perfect conditions for solar generation'
  },
  good: {
    color: '#3b82f6',
    label: 'Good',
    description: 'Good conditions with minor weather impact'
  },
  moderate: {
    color: '#f59e0b',
    label: 'Moderate',
    description: 'Some weather impact on generation'
  },
  poor: {
    color: '#ef4444',
    label: 'Poor',
    description: 'Significant weather impact expected'
  }
};

/**
 * Format weather data for display
 */
export const formatWeatherData = (weatherData) => {
  if (!weatherData) return null;
  
  const { impact_summary, next_24h_preview } = weatherData;
  
  return {
    impactLevel: impact_summary.impact_level,
    impactColor: WEATHER_IMPACT_LEVELS[impact_summary.impact_level]?.color || '#6b7280',
    impactLabel: WEATHER_IMPACT_LEVELS[impact_summary.impact_level]?.label || 'Unknown',
    summary: impact_summary.summary,
    totalRain24h: impact_summary.total_rain_24h,
    rainyHours: impact_summary.rainy_hours,
    maxTemp: impact_summary.max_temperature,
    avgTemp: impact_summary.avg_temperature,
    peakSolarRadiation: impact_summary.peak_solar_radiation,
    avgSolarRadiation: impact_summary.avg_solar_radiation,
    hourlyPreview: next_24h_preview?.slice(0, 12) || [] // Next 12 hours
  };
};

/**
 * Format solar forecast data for charts
 */
export const formatSolarForecastData = (forecastData) => {
  if (!forecastData) return null;
  
  const { hourly_forecast, weekly_outlook } = forecastData;
  
  // Hourly chart data (next 24h)
  const hourlyChartData = hourly_forecast?.map(hour => ({
    time: new Date(hour.time).getHours(),
    generation: hour.generation_kwh,
    solarRadiation: hour.solar_radiation,
    temperature: hour.temperature,
    weather: hour.weather
  })) || [];
  
  // Daily chart data (next 7 days)
  const dailyChartData = weekly_outlook?.map(day => ({
    date: day.date,
    generation: day.estimated_generation,
    solarRadiation: day.solar_radiation,
    maxTemp: day.max_temp,
    rainProbability: day.rain_probability
  })) || [];
  
  return {
    next24hGeneration: forecastData.next_24h_generation_kwh,
    weatherQualityScore: forecastData.weather_quality_score,
    hourlyChart: hourlyChartData,
    dailyChart: dailyChartData,
    analysisTime: forecastData.analysis_time
  };
};