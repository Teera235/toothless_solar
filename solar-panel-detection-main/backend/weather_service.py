"""
Weather Service for WxTech API Integration
Provides weather forecast data for solar potential analysis
"""

import os
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WeatherCode(Enum):
    SUNNY = 100
    CLOUDY = 200
    RAIN = 300
    SNOW = 400
    SLEET = 430
    CLEAR = 500
    NO_DATA = 999

@dataclass
class HourlyForecast:
    forecast_time: datetime
    weather_code: int
    temperature_c: int
    precip_mm_per_hr: float
    pressure_hpa: int
    wind_direction: int
    wind_speed_mps: int
    humidity_pct: int
    solar_radiation_wm2: int
    
    @property
    def weather_main(self) -> str:
        """Convert weather code to main category"""
        if self.weather_code == 100 or self.weather_code == 500:
            return "sunny"
        elif 200 <= self.weather_code < 300:
            return "cloudy"
        elif 300 <= self.weather_code < 400:
            return "rain"
        elif 400 <= self.weather_code < 500:
            return "snow"
        else:
            return "unknown"
    
    @property
    def is_good_for_solar(self) -> bool:
        """Check if conditions are good for solar generation"""
        return (self.weather_main in ["sunny"] and 
                self.solar_radiation_wm2 > 200 and
                self.precip_mm_per_hr < 0.1)

@dataclass
class DailyForecast:
    forecast_date: str
    weather_code: int
    max_temp_c: int
    min_temp_c: int
    precip_mm_per_day: float
    precip_probability_pct: int
    wind_direction: int
    max_wind_speed_mps: int
    avg_humidity_pct: int
    daily_solar_radiation: float

@dataclass
class WeatherForecast:
    location: Tuple[float, float]  # (lat, lon)
    timezone: str
    hourly: List[HourlyForecast]
    daily: List[DailyForecast]
    fetched_at: datetime
    source: str = "wxtech"

class WxTechClient:
    """Client for WxTech Weather API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://wxtech.weathernews.com/api/v2/global/wx"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"X-API-Key": self.api_key},
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_forecast(self, lat: float, lon: float, timezone: str = "Asia/Bangkok") -> WeatherForecast:
        """Get weather forecast for location"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async with.")
        
        params = {
            "latlon": f"{lat}/{lon}",
            "tz": timezone
        }
        
        async with self.session.get(self.base_url, params=params) as response:
            if response.status != 200:
                raise Exception(f"WxTech API error: {response.status}")
            
            data = await response.json()
            return self._parse_response(data, lat, lon, timezone)
    
    def _parse_response(self, data: dict, lat: float, lon: float, timezone: str) -> WeatherForecast:
        """Parse WxTech API response"""
        location_key = f"{lat}/{lon}"
        wx_data = data["wxdata"][location_key]
        
        # Parse hourly forecasts (SRF)
        hourly = []
        for item in wx_data.get("srf", []):
            # Handle both 'time' and 'date' fields (API might use either)
            time_str = item.get("time") or item.get("date")
            if time_str:
                try:
                    forecast_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except:
                    # Fallback parsing
                    forecast_time = datetime.now()
            else:
                forecast_time = datetime.now()
                
            hourly.append(HourlyForecast(
                forecast_time=forecast_time,
                weather_code=item.get("wx", 999),
                temperature_c=item.get("temp", 25),
                precip_mm_per_hr=item.get("prec", 0.0),
                pressure_hpa=item.get("arpress", 1013),
                wind_direction=item.get("wnddir", 8),
                wind_speed_mps=item.get("wndspd", 3),
                humidity_pct=item.get("rhum", 70),
                solar_radiation_wm2=item.get("solrad", 0)
            ))
        
        # Parse daily forecasts (MRF)
        daily = []
        for item in wx_data.get("mrf", []):
            # Handle date field
            date_str = item.get("date", "")
            if date_str:
                try:
                    # Extract just the date part
                    date_part = date_str.split('T')[0] if 'T' in date_str else date_str
                except:
                    date_part = datetime.now().strftime('%Y-%m-%d')
            else:
                date_part = datetime.now().strftime('%Y-%m-%d')
                
            daily.append(DailyForecast(
                forecast_date=date_part,
                weather_code=item.get("wx", 100),
                max_temp_c=item.get("maxtemp", 30),
                min_temp_c=item.get("mintemp", 25),
                precip_mm_per_day=item.get("prec", 0.0),
                precip_probability_pct=item.get("pop", 0),
                wind_direction=item.get("wnddir", 8),
                max_wind_speed_mps=item.get("wndspd", 3),
                avg_humidity_pct=item.get("rhum", 70),
                daily_solar_radiation=item.get("solrad", 25.0)
            ))
        
        return WeatherForecast(
            location=(lat, lon),
            timezone=timezone,
            hourly=hourly,
            daily=daily,
            fetched_at=datetime.now()
        )

class SolarWeatherAnalyzer:
    """Analyze weather data for solar potential"""
    
    @staticmethod
    def calculate_solar_forecast(forecast: WeatherForecast, system_kwp: float) -> Dict:
        """Calculate solar generation forecast"""
        
        # Next 24h analysis
        now = datetime.now(forecast.hourly[0].forecast_time.tzinfo) if forecast.hourly else datetime.now()
        next_24h = [h for h in forecast.hourly if h.forecast_time <= now + timedelta(hours=24)]
        
        # Calculate hourly generation estimates
        hourly_generation = []
        for hour in next_24h:
            # Simple generation model: solrad * system_size * efficiency
            # solrad is in W/m², convert to generation factor
            generation_factor = min(hour.solar_radiation_wm2 / 1000, 1.0)  # Cap at 1.0
            
            # Temperature derating (panels lose efficiency when hot)
            temp_derating = 1.0 - (max(hour.temperature_c - 25, 0) * 0.004)
            
            # Weather condition derating
            weather_derating = 1.0
            if hour.weather_main == "cloudy":
                weather_derating = 0.7
            elif hour.weather_main == "rain":
                weather_derating = 0.3
            elif hour.precip_mm_per_hr > 0:
                weather_derating = 0.4
            
            # Calculate hourly generation
            hourly_kwh = (system_kwp * generation_factor * 
                         temp_derating * weather_derating * 0.85)  # System efficiency
            
            hourly_generation.append({
                "time": hour.forecast_time.isoformat(),
                "solar_radiation": hour.solar_radiation_wm2,
                "temperature": hour.temperature_c,
                "weather": hour.weather_main,
                "generation_kwh": round(hourly_kwh, 2),
                "generation_factor": round(generation_factor, 3)
            })
        
        # Summary statistics
        total_24h_generation = sum(h["generation_kwh"] for h in hourly_generation)
        avg_solar_radiation = sum(h.solar_radiation_wm2 for h in next_24h) / len(next_24h) if next_24h else 0
        
        # Weather quality score (0-100)
        good_hours = sum(1 for h in next_24h if h.is_good_for_solar)
        weather_quality_score = (good_hours / len(next_24h) * 100) if next_24h else 0
        
        # 7-day outlook
        weekly_outlook = []
        for day in forecast.daily[:7]:
            daily_generation = (day.daily_solar_radiation / 1000 * system_kwp * 
                              8 * 0.85)  # Assume 8 peak sun hours, 85% efficiency
            weekly_outlook.append({
                "date": day.forecast_date,
                "solar_radiation": day.daily_solar_radiation,
                "max_temp": day.max_temp_c,
                "rain_probability": day.precip_probability_pct,
                "estimated_generation": round(daily_generation, 1)
            })
        
        return {
            "next_24h_generation_kwh": round(total_24h_generation, 1),
            "avg_solar_radiation_24h": round(avg_solar_radiation),
            "weather_quality_score": round(weather_quality_score),
            "hourly_forecast": hourly_generation,
            "weekly_outlook": weekly_outlook,
            "analysis_time": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_weather_impact_summary(forecast: WeatherForecast) -> Dict:
        """Get weather impact summary for UI"""
        if not forecast.hourly:
            return {"status": "no_data"}
            
        # Use timezone-aware datetime
        now = datetime.now(forecast.hourly[0].forecast_time.tzinfo) if forecast.hourly else datetime.now()
        next_24h = [h for h in forecast.hourly if h.forecast_time <= now + timedelta(hours=24)]
        
        if not next_24h:
            return {"status": "no_data"}
        
        # Rain analysis
        total_rain = sum(h.precip_mm_per_hr for h in next_24h)
        rainy_hours = sum(1 for h in next_24h if h.precip_mm_per_hr > 0.1)
        
        # Temperature analysis
        max_temp = max(h.temperature_c for h in next_24h)
        avg_temp = sum(h.temperature_c for h in next_24h) / len(next_24h)
        
        # Solar radiation analysis
        peak_solar = max(h.solar_radiation_wm2 for h in next_24h)
        avg_solar = sum(h.solar_radiation_wm2 for h in next_24h) / len(next_24h)
        
        # Overall impact assessment
        impact_level = "excellent"
        if total_rain > 5 or rainy_hours > 6:
            impact_level = "poor"
        elif total_rain > 1 or rainy_hours > 3 or avg_solar < 300:
            impact_level = "moderate"
        elif avg_solar > 500 and total_rain < 0.5:
            impact_level = "excellent"
        else:
            impact_level = "good"
        
        return {
            "impact_level": impact_level,
            "total_rain_24h": round(total_rain, 1),
            "rainy_hours": rainy_hours,
            "max_temperature": max_temp,
            "avg_temperature": round(avg_temp, 1),
            "peak_solar_radiation": peak_solar,
            "avg_solar_radiation": round(avg_solar),
            "summary": f"Weather impact: {impact_level.title()}"
        }

# Singleton weather service
weather_service = None

def get_weather_service() -> WxTechClient:
    """Get weather service instance"""
    global weather_service
    if weather_service is None:
        api_key = os.getenv("WXTECH_API_KEY")
        if not api_key:
            raise ValueError("WXTECH_API_KEY environment variable not set")
        weather_service = WxTechClient(api_key)
    return weather_service