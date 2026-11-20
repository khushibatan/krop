"""Unit tests for regional lookups and crop catalog helpers."""

import pytest
from src.crop_information import filter_crops, get_crop_profile, is_suitable_for_season, load_crop_catalog
from src.utils import (
    NATIONAL_AVERAGE_NORMALS,
    compute_seasonal_rainfall,
    get_district_rainfall_normals,
    get_districts_for_state,
    get_indian_states,
)


def test_states_and_districts_available():
    states = get_indian_states()
    assert "Maharashtra" in states
    assert "Pune" in get_districts_for_state("Maharashtra")
    assert get_districts_for_state("Atlantis") == []


def test_rainfall_resolution_order():
    district = get_district_rainfall_normals("Maharashtra", "Pune")
    state_level = get_district_rainfall_normals("Maharashtra", "")
    assert district != state_level  # empty district must not match an arbitrary district
    assert get_district_rainfall_normals("Atlantis", "Nowhere") == NATIONAL_AVERAGE_NORMALS


def test_seasonal_rainfall():
    n = {"annual": 1000, "Jun-Sep": 700, "Jan-Feb": 20, "Mar-May": 80, "Oct-Dec": 200}
    assert compute_seasonal_rainfall(n, "Kharif") == 700
    assert compute_seasonal_rainfall(n, "rabi") == 220
    assert compute_seasonal_rainfall(n, "Summer") == 80
    assert compute_seasonal_rainfall(n, "Whole Year") == 1000


def test_crop_profile_lookup_handles_special_characters():
    assert get_crop_profile("cotton(lint)")["crop_name"] == "Cotton(lint)"
    assert get_crop_profile("Rapeseed &Mustard") is not None
    assert get_crop_profile("(((") is None  # must not be interpreted as a regex
    assert get_crop_profile("") is None


def test_season_suitability_and_filtering():
    wheat, banana = get_crop_profile("Wheat"), get_crop_profile("Banana")
    assert is_suitable_for_season(wheat, "Rabi") and not is_suitable_for_season(wheat, "Kharif")
    assert is_suitable_for_season(banana, "Kharif")  # perennial / whole-year crop
    assert "Wheat" in filter_crops(season="Rabi")["crop_name"].tolist()
    assert len(load_crop_catalog()) == 33
