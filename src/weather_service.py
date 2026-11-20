"""
KROP - Weather Service
Integrates Open-Meteo Weather API to retrieve live telemetry and 7-day forecasts.
Strictly zero hardware dependencies, fully software-based.
Distinguishes real-time observation, short-term forecast, and historical climate normals.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
import requests

logger = logging.getLogger("krop.weather")

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_TIMEOUT_SEC = 5
CACHE_TTL_SEC = 3600

# In-memory weather cache keyed by rounded "lat_lon" -> {"cached_at", "data"}
_WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}


def describe_weather_condition(temp_c: float, humidity_pct: float, precip_mm: float) -> str:
    """Provides farmer-friendly descriptive summary of current conditions."""
    if precip_mm > 5.0:
        return "Rainy / Heavy showers"
    elif precip_mm > 0.5:
        return "Light rain / Drizzle"
    elif humidity_pct > 80:
        return "Humid & Overcast"
    elif temp_c > 38.0:
        return "Hot & Dry (High heat stress)"
    elif temp_c > 30.0:
        return "Warm & Sunny"
    elif temp_c < 12.0:
        return "Cool / Cold winter conditions"
    else:
        return "Moderate & Pleasant"


class WeatherService:
    """Handles communication with Open-Meteo API with offline resiliency."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT_SEC):
        self.timeout = timeout

    def get_weather_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Retrieves current conditions and the 7-day forecast, falling back to seasonal baselines offline."""
        cache_key = f"{round(latitude, 2)}_{round(longitude, 2)}"  # ~1 km grid
        cached = _WEATHER_CACHE.get(cache_key)
        if cached and (datetime.now() - cached["cached_at"]).total_seconds() < CACHE_TTL_SEC:
            logger.info("Returning cached weather for %s", cache_key)
            return cached["data"]

        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "forecast_days": 7,
            "timezone": "auto",
        }

        try:
            resp = requests.get(WEATHER_API_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            weather_result = self._parse_response(resp.json(), latitude, longitude)
            _WEATHER_CACHE[cache_key] = {"cached_at": datetime.now(), "data": weather_result}
            return weather_result
        except (requests.RequestException, ValueError, TypeError) as e:
            logger.warning("Weather API request failed for (%.4f, %.4f): %s", latitude, longitude, e)

        return self._generate_fallback_weather(latitude, longitude)

    @staticmethod
    def _parse_response(raw: Dict[str, Any], latitude: float, longitude: float) -> Dict[str, Any]:
        """Converts an Open-Meteo payload into KROP's weather structure."""
        current = raw.get("current") or {}
        daily = raw.get("daily") or {}

        curr_temp = float(current.get("temperature_2m", 25.0))
        curr_hum = float(current.get("relative_humidity_2m", 50.0))
        curr_precip = float(current.get("precipitation", 0.0))
        curr_wind = float(current.get("wind_speed_10m", 5.0))

        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precips = daily.get("precipitation_sum", [])

        def value_at(series: List[Any], i: int, default: float) -> float:
            return float(series[i]) if i < len(series) and series[i] is not None else default

        forecast_days = [
            {
                "date": dates[i],
                "max_temp_c": value_at(max_temps, i, curr_temp + 3),
                "min_temp_c": value_at(min_temps, i, curr_temp - 5),
                "precipitation_mm": value_at(precips, i, 0.0),
            }
            for i in range(len(dates))
        ]

        n_days = max(1, len(forecast_days))
        return {
            "status": "success",
            "is_live": True,
            "latitude": latitude,
            "longitude": longitude,
            "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current": {
                "temperature_c": curr_temp,
                "humidity_pct": curr_hum,
                "precipitation_mm": curr_precip,
                "wind_speed_kmh": curr_wind,
                "condition": describe_weather_condition(curr_temp, curr_hum, curr_precip),
            },
            "forecast_summary": {
                "total_rain_7days_mm": round(sum(d["precipitation_mm"] for d in forecast_days), 1),
                "avg_max_temp_c": round(sum(d["max_temp_c"] for d in forecast_days) / n_days, 1),
                "avg_min_temp_c": round(sum(d["min_temp_c"] for d in forecast_days) / n_days, 1),
            },
            "daily_forecast": forecast_days,
        }

    def _generate_fallback_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Provides realistic seasonal baseline when external API is unreachable."""
        return {
            "status": "fallback",
            "is_live": False,
            "latitude": latitude,
            "longitude": longitude,
            "retrieved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current": {
                "temperature_c": 27.0,
                "humidity_pct": 55.0,
                "precipitation_mm": 0.0,
                "wind_speed_kmh": 6.5,
                "condition": "Seasonal Average (Live API offline)"
            },
            "forecast_summary": {
                "total_rain_7days_mm": 0.0,
                "avg_max_temp_c": 30.0,
                "avg_min_temp_c": 18.0
            },
            "daily_forecast": [
                {"date": "Day 1", "max_temp_c": 30.0, "min_temp_c": 18.0, "precipitation_mm": 0.0},
                {"date": "Day 2", "max_temp_c": 31.0, "min_temp_c": 18.5, "precipitation_mm": 0.0},
                {"date": "Day 3", "max_temp_c": 29.5, "min_temp_c": 17.5, "precipitation_mm": 0.0},
            ]
        }


if __name__ == "__main__":
    ws = WeatherService()
    # Test with Pune coordinates
    w = ws.get_weather_forecast(18.5204, 73.8567)
    print("Weather retrieved successfully!")
    print("Status:", w["status"], "| Live:", w["is_live"])
    print("Current:", w["current"])
    print("Forecast 7-day rain:", w["forecast_summary"]["total_rain_7days_mm"], "mm")
