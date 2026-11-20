"""
KROP - Geolocation Service
Integrates Open-Meteo Geocoding API for village/town/district coordinate resolution across India.
Includes offline resilience and caching.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import requests

logger = logging.getLogger("krop.geolocation")

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
DEFAULT_TIMEOUT_SEC = 5

# Built-in fallback coordinates for all 33 Indian States/UTs
STATE_CAPITAL_COORDINATES = {
    "ANDAMAN AND NICOBAR ISLANDS": {"name": "Port Blair", "state": "Andaman and Nicobar Islands", "lat": 11.6234, "lon": 92.7265},
    "ANDHRA PRADESH": {"name": "Amaravati", "state": "Andhra Pradesh", "lat": 16.5417, "lon": 80.5158},
    "ARUNACHAL PRADESH": {"name": "Itanagar", "state": "Arunachal Pradesh", "lat": 27.0844, "lon": 93.6053},
    "ASSAM": {"name": "Dispur", "state": "Assam", "lat": 26.1433, "lon": 91.7898},
    "BIHAR": {"name": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376},
    "CHANDIGARH": {"name": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    "CHHATTISGARH": {"name": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296},
    "DADRA AND NAGAR HAVELI": {"name": "Silvassa", "state": "Dadra and Nagar Haveli", "lat": 20.2763, "lon": 73.0083},
    "GOA": {"name": "Panaji", "state": "Goa", "lat": 15.4909, "lon": 73.8278},
    "GUJARAT": {"name": "Gandhinagar", "state": "Gujarat", "lat": 23.2156, "lon": 72.6369},
    "HARYANA": {"name": "Chandigarh", "state": "Haryana", "lat": 29.0588, "lon": 76.0856},
    "HIMACHAL PRADESH": {"name": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734},
    "JAMMU AND KASHMIR": {"name": "Srinagar", "state": "Jammu and Kashmir", "lat": 34.0837, "lon": 74.7973},
    "JHARKHAND": {"name": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096},
    "KARNATAKA": {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946},
    "KERALA": {"name": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366},
    "MADHYA PRADESH": {"name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126},
    "MAHARASHTRA": {"name": "Mumbai", "state": "Maharashtra", "lat": 19.7515, "lon": 75.7139},
    "MANIPUR": {"name": "Imphal", "state": "Manipur", "lat": 24.8170, "lon": 93.9368},
    "MEGHALAYA": {"name": "Shillong", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933},
    "MIZORAM": {"name": "Aizawl", "state": "Mizoram", "lat": 23.7271, "lon": 92.7176},
    "NAGALAND": {"name": "Kohima", "state": "Nagaland", "lat": 25.6751, "lon": 94.1086},
    "ODISHA": {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245},
    "PUDUCHERRY": {"name": "Puducherry", "state": "Puducherry", "lat": 11.9416, "lon": 79.8083},
    "PUNJAB": {"name": "Chandigarh", "state": "Punjab", "lat": 31.1471, "lon": 75.3412},
    "RAJASTHAN": {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873},
    "SIKKIM": {"name": "Gangtok", "state": "Sikkim", "lat": 27.3389, "lon": 88.6065},
    "TAMIL NADU": {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    "TELANGANA": {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867},
    "TRIPURA": {"name": "Agartala", "state": "Tripura", "lat": 23.8315, "lon": 91.2868},
    "UTTAR PRADESH": {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462},
    "UTTARAKHAND": {"name": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322},
    "WEST BENGAL": {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639},
}


def get_approximate_coordinates(state: str, district: Optional[str] = None) -> Dict[str, Any]:
    """Returns regional centroid coordinates for a given state and optional district."""
    state_clean = state.strip().upper()
    if state_clean in STATE_CAPITAL_COORDINATES:
        fb = STATE_CAPITAL_COORDINATES[state_clean]
        name = f"{district}, {fb['state']}" if district else fb["state"]
        return {
            "name": name,
            "latitude": fb["lat"],
            "longitude": fb["lon"],
            "is_approximate": True,
            "display_label": f"{name} (Regional Centroid: {fb['lat']:.4f}°N, {fb['lon']:.4f}°E)"
        }
    return {
        "name": f"{district or state} (Central India Centroid)",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "is_approximate": True,
        "display_label": f"{district or state} (Central India Centroid: 21.1458°N, 79.0882°E)"
    }

# In-memory session cache
_GEO_CACHE: Dict[str, List[Dict]] = {}


class GeolocationService:
    """Provides geocoding queries with fallback to regional state centroids."""

    def __init__(self, timeout: int = DEFAULT_TIMEOUT_SEC):
        self.timeout = timeout

    def search_locations(self, query: str, state_hint: Optional[str] = None) -> List[Dict]:
        """
        Queries Open-Meteo Geocoding API for locations matching query.
        Returns formatted list of matching location candidate dictionaries.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        cache_key = f"{clean_q.lower()}_{state_hint.lower() if state_hint else ''}"
        if cache_key in _GEO_CACHE:
            return _GEO_CACHE[cache_key]

        search_text = f"{clean_q}, {state_hint}, India" if state_hint else f"{clean_q}, India"
        params = {
            "name": clean_q,
            "count": 6,
            "language": "en",
            "format": "json"
        }

        try:
            resp = requests.get(GEOCODING_URL, params=params, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                raw_results = data.get("results", [])
                
                # Filter / prioritize results in India
                indian_results = []
                for item in raw_results:
                    if item.get("country_code", "").upper() == "IN" or item.get("country", "").lower() == "india":
                        indian_results.append({
                            "name": item.get("name"),
                            "district": item.get("admin2", item.get("admin3", "")),
                            "state": item.get("admin1", ""),
                            "country": item.get("country", "India"),
                            "latitude": float(item.get("latitude")),
                            "longitude": float(item.get("longitude")),
                            "elevation": item.get("elevation"),
                            "display_label": f"{item.get('name')}, {item.get('admin1', '')} ({item.get('latitude'):.4f}°N, {item.get('longitude'):.4f}°E)"
                        })

                if indian_results:
                    _GEO_CACHE[cache_key] = indian_results
                    return indian_results
        except Exception as e:
            logger.warning("Geocoding request failed for '%s': %s", clean_q, e)

        # Fallback to state capital coordinates if available
        if state_hint and state_hint.strip().upper() in STATE_CAPITAL_COORDINATES:
            fallback = STATE_CAPITAL_COORDINATES[state_hint.strip().upper()]
            fb_res = [{
                "name": f"{clean_q} ({fallback['name']} region)",
                "district": clean_q,
                "state": fallback["state"],
                "country": "India",
                "latitude": fallback["lat"],
                "longitude": fallback["lon"],
                "elevation": 500.0,
                "display_label": f"{clean_q} (Approx {fallback['state']}: {fallback['lat']:.4f}°N, {fallback['lon']:.4f}°E)",
                "is_fallback": True
            }]
            return fb_res

        return []


if __name__ == "__main__":
    geo = GeolocationService()
    res = geo.search_locations("Latur", state_hint="Maharashtra")
    print("Found locations for Latur:", res)
