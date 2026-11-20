"""
KROP - Input Validation Module
Validates farm profile parameters, coordinates, and agronomic inputs.
Zero hardware dependencies, strictly zero NPK.
"""

from typing import Dict, List, Tuple, Any

VALID_SEASONS = ["Kharif", "Rabi", "Summer", "Whole Year", "Not sure"]
VALID_LAND_UNITS = ["Acres", "Hectares", "Bighas", "Gunthas"]
VALID_SOIL_TYPES = [
    "Unknown", "Alluvial", "Black soil", "Red soil", "Laterite",
    "Sandy", "Clay", "Loamy", "Other"
]
VALID_IRRIGATION_METHODS = [
    "Rain-fed", "Borewell", "Open well", "Canal", "Drip irrigation", "Other", "Unknown"
]
VALID_WATER_AVAILABILITY = [
    "Limited", "Moderate", "Good", "Seasonal or uncertain"
]
VALID_CROP_PREFERENCES = [
    "No preference", "Cereals", "Pulses", "Oilseeds",
    "Vegetables", "Fruits", "Cash/Commercial Crops", "Spices", "Other"
]


def validate_farm_profile(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates user farm profile submission.
    Returns (True, []) if valid, or (False, [error_messages]) if invalid.
    """
    errors = []

    # 1. State Validation
    state = str(data.get("state", "")).strip()
    if not state:
        errors.append("State selection is required.")

    # 2. District Validation
    district = str(data.get("district", "")).strip()
    if not district:
        errors.append("District selection is required.")

    # 3. Land Area Validation
    land_area = data.get("land_area")
    try:
        area_val = float(land_area)
        if area_val <= 0:
            errors.append("Land area must be greater than zero.")
        elif area_val > 50000:
            errors.append("Land area exceeds plausible single-farm scale (> 50,000 units).")
    except (ValueError, TypeError):
        errors.append("Land area must be a valid positive numerical value.")

    # 4. Land Unit Validation
    unit = str(data.get("land_unit", "Acres")).strip()
    if unit not in VALID_LAND_UNITS:
        errors.append(f"Invalid land unit '{unit}'. Must be one of: {', '.join(VALID_LAND_UNITS)}.")

    # 5. Season Validation
    season = str(data.get("preferred_season", "Kharif")).strip()
    if season not in VALID_SEASONS:
        errors.append(f"Invalid farming season '{season}'.")

    # 6. Soil Type Validation (Optional, default Unknown)
    soil = str(data.get("soil_type", "Unknown")).strip()
    if soil and soil not in VALID_SOIL_TYPES:
        errors.append(f"Invalid soil type selection '{soil}'.")

    # 7. Irrigation Method Validation
    irrigation = str(data.get("irrigation_method", "Rain-fed")).strip()
    if irrigation and irrigation not in VALID_IRRIGATION_METHODS:
        errors.append(f"Invalid irrigation method '{irrigation}'.")

    # 8. Water Availability Validation
    water = str(data.get("water_availability", "Moderate")).strip()
    if water and water not in VALID_WATER_AVAILABILITY:
        errors.append(f"Invalid water availability selection '{water}'.")

    # 9. Crop Preferences Validation
    pref = str(data.get("crop_preferences", "No preference")).strip()
    if pref and pref not in VALID_CROP_PREFERENCES:
        errors.append(f"Invalid crop preference selection '{pref}'.")

    return len(errors) == 0, errors


def validate_coordinates(lat: Any, lon: Any) -> Tuple[bool, Optional[str]]:
    """Validates geographic latitude and longitude bounds for India."""
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        # Bounding box for India: Lat 6°N - 38°N, Lon 68°E - 98°E
        if not (6.0 <= lat_f <= 38.0):
            return False, f"Latitude {lat_f:.4f}° is outside Indian geographical limits (6°N to 38°N)."
        if not (68.0 <= lon_f <= 98.0):
            return False, f"Longitude {lon_f:.4f}° is outside Indian geographical limits (68°E to 98°E)."
        return True, None
    except (ValueError, TypeError):
        return False, "Coordinates must be valid numerical values."
