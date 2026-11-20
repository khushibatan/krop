"""
Unit tests for KROP Weather & Geolocation Services.
Mocks external API calls to verify offline resiliency and response parsing.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.weather_service import WeatherService, describe_weather_condition
from src.geolocation_service import GeolocationService


def test_describe_weather_condition():
    assert "Rainy" in describe_weather_condition(25.0, 80.0, 10.0)
    assert "Hot" in describe_weather_condition(40.0, 30.0, 0.0)
    assert "Cool" in describe_weather_condition(10.0, 50.0, 0.0)
    assert "Pleasant" in describe_weather_condition(24.0, 45.0, 0.0)


@patch("src.weather_service.requests.get")
def test_weather_service_successful_api(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 26.5,
            "relative_humidity_2m": 45.0,
            "precipitation": 0.0,
            "wind_speed_10m": 8.0
        },
        "daily": {
            "time": ["2026-11-20", "2026-11-21"],
            "temperature_2m_max": [29.0, 30.0],
            "temperature_2m_min": [16.0, 17.0],
            "precipitation_sum": [0.0, 2.5]
        }
    }
    mock_get.return_value = mock_response

    service = WeatherService()
    weather = service.get_weather_forecast(19.99, 73.78)

    assert weather["status"] == "success"
    assert weather["is_live"] is True
    assert weather["current"]["temperature_c"] == 26.5
    assert weather["current"]["humidity_pct"] == 45.0
    assert len(weather["daily_forecast"]) == 2
    assert weather["forecast_summary"]["total_rain_7days_mm"] == 2.5


@patch("src.weather_service.requests.get")
def test_weather_service_api_timeout_fallback(mock_get):
    """The application must remain usable when weather API times out."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    service = WeatherService()
    weather = service.get_weather_forecast(20.0, 74.0)

    # Must gracefully return fallback, not crash
    assert weather["status"] == "fallback"
    assert weather["is_live"] is False
    assert "temperature_c" in weather["current"]
    assert weather["current"]["temperature_c"] > 0


@patch("src.geolocation_service.requests.get")
def test_geolocation_service_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "name": "Baramati",
                "admin1": "Maharashtra",
                "admin2": "Pune",
                "country_code": "IN",
                "country": "India",
                "latitude": 18.15,
                "longitude": 74.58,
                "elevation": 538.0
            }
        ]
    }
    mock_get.return_value = mock_resp

    geo = GeolocationService()
    locations = geo.search_locations("Baramati", state_hint="Maharashtra")
    assert len(locations) >= 1
    assert locations[0]["name"] == "Baramati"
    assert locations[0]["latitude"] == 18.15
    assert locations[0]["state"] == "Maharashtra"


@patch("src.geolocation_service.requests.get")
def test_geolocation_offline_state_centroid_fallback(mock_get):
    """Fallback coordinates when geocoding network fails."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("Network down")

    geo = GeolocationService()
    locations = geo.search_locations("Rural Area", state_hint="Punjab")
    assert len(locations) == 1
    assert "Punjab" in locations[0]["state"]
    assert locations[0]["is_fallback"] is True


@patch("src.geolocation_service.requests.get")
def test_geolocation_prioritises_hinted_state(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"results": [
        {"name": "Aurangabad", "admin1": "Bihar", "country_code": "IN", "latitude": 24.75, "longitude": 84.37},
        {"name": "Aurangabad", "admin1": "Maharashtra", "country_code": "IN", "latitude": 19.88, "longitude": 75.34},
        {"name": "Aurangabad", "admin1": "Elsewhere", "country_code": "PK", "latitude": 30.0, "longitude": 70.0},
    ]}
    mock_get.return_value = mock_resp
    results = GeolocationService().search_locations("Aurangabad-test", state_hint="Maharashtra")
    assert [r["state"] for r in results] == ["Maharashtra", "Bihar"]


@patch("src.weather_service.requests.get")
def test_weather_http_error_falls_back(mock_get):
    import requests
    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.HTTPError("503")
    mock_get.return_value = resp
    assert WeatherService().get_weather_forecast(11.11, 77.77)["status"] == "fallback"
