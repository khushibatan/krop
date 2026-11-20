"""
Unit tests for KROP Intelligent Recommendation Engine.
"""

import pytest
from src.recommendation_engine import RecommendationEngine


@pytest.fixture
def engine():
    return RecommendationEngine()


def test_recommendation_basic_run(engine):
    profile = {
        "state": "Maharashtra",
        "district": "Pune",
        "preferred_season": "Kharif",
        "land_area": 2.5,
        "land_unit": "Acres",
        "soil_type": "Black soil",
        "irrigation_method": "Borewell",
        "water_availability": "Good",
        "crop_preferences": "No preference"
    }
    result = engine.generate_recommendations(profile, top_n=5)
    assert "recommendations" in result
    recs = result["recommendations"]
    assert len(recs) == 5
    for r in recs:
        assert "crop_name" in r
        assert "rank" in r
        assert "composite_score" in r
        assert "explanation_points" in r
        assert len(r["explanation_points"]) >= 3


def test_unknown_soil_type_resilience(engine):
    """The system must remain fully functional when the farmer does not know soil type."""
    profile = {
        "state": "Rajasthan",
        "district": "Jaipur",
        "preferred_season": "Kharif",
        "land_area": 5.0,
        "land_unit": "Acres",
        "soil_type": "Unknown",  # Explicitly Unknown
        "irrigation_method": "Rain-fed",
        "water_availability": "Limited",
        "crop_preferences": "No preference"
    }
    result = engine.generate_recommendations(profile, top_n=5)
    recs = result["recommendations"]
    assert len(recs) == 5
    for r in recs:
        assert r["composite_score"] > 0
        assert r["soil_suitability_score"] > 0
        assert len(r["explanation_points"]) >= 3
    # Should recommend regionally suitable crops for Rajasthan Kharif
    crop_names = [c["crop_name"].lower() for c in recs]
    assert any(c in ["bajra", "moong(green gram)", "jowar", "sesamum", "small millets", "castor seed", "urad", "arhar/tur", "soyabean"] for c in crop_names)


def test_water_constraint_penalization(engine):
    """Water-intensive crops must receive lower water scores when irrigation is limited."""
    profile_dry = {
        "state": "Maharashtra",
        "district": "Solapur",
        "preferred_season": "Kharif",
        "land_area": 3.0,
        "land_unit": "Acres",
        "soil_type": "Medium Deep",
        "irrigation_method": "Rain-fed",
        "water_availability": "Limited",
        "crop_preferences": "No preference"
    }
    result = engine.generate_recommendations(profile_dry, top_n=5)
    for c in result["recommendations"]:
        # Sugarcane or Rice should not be ranked #1 in a dry, rain-fed setup with limited water
        if c["crop_name"] in ["Sugarcane", "Rice", "Banana"]:
            assert c["water_suitability_score"] < 50.0
