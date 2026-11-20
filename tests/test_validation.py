"""Unit tests for input validation."""

import pytest
from src.validation import validate_coordinates, validate_farm_profile

VALID = {
    "state": "Maharashtra", "district": "Pune", "land_area": 2.0, "land_unit": "Acres",
    "preferred_season": "Kharif", "soil_type": "Unknown", "irrigation_method": "Rain-fed",
    "water_availability": "Moderate", "crop_preferences": "No preference",
    "latitude": 18.5, "longitude": 73.8,
}


def test_valid_profile_passes():
    assert validate_farm_profile(VALID) == (True, [])


@pytest.mark.parametrize("field,value", [
    ("state", ""), ("district", " "), ("land_area", 0), ("land_area", -3), ("land_area", "abc"),
    ("land_area", float("nan")), ("land_area", 60000), ("land_unit", "Cents"),
    ("preferred_season", "Monsoon"), ("soil_type", "Moon dust"), ("latitude", 60.0),
])
def test_invalid_profile_fields_are_rejected(field, value):
    ok, errors = validate_farm_profile({**VALID, field: value})
    assert not ok and errors


def test_coordinate_bounds():
    assert validate_coordinates(18.5, 73.8)[0]
    assert not validate_coordinates(0, 73.8)[0]
    assert not validate_coordinates("x", 73.8)[0]
    assert not validate_coordinates(float("nan"), 73.8)[0]
