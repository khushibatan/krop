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


BASE_PROFILE = {
    "state": "Punjab",
    "district": "Ludhiana",
    "preferred_season": "Rabi",
    "land_area": 5.0,
    "land_unit": "Acres",
    "soil_type": "Alluvial",
    "irrigation_method": "Canal",
    "water_availability": "Good",
    "crop_preferences": "No preference",
}


def test_regional_staple_ranks_first(engine):
    result = engine.generate_recommendations(BASE_PROFILE)
    assert result["recommendations"][0]["crop_name"] == "Wheat"


def test_ranks_are_sequential_and_scores_sorted_and_bounded(engine):
    recs = engine.generate_recommendations(BASE_PROFILE, top_n=5)["recommendations"]
    assert [r["rank"] for r in recs] == [1, 2, 3, 4, 5]
    scores = [r["composite_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)


def test_season_eligibility_is_enforced(engine):
    """Rabi-only crops such as Wheat must never be suggested for the Kharif season."""
    profile = {**BASE_PROFILE, "preferred_season": "Kharif"}
    names = [r["crop_name"] for r in engine.generate_recommendations(profile, top_n=10)["recommendations"]]
    assert "Wheat" not in names


@pytest.mark.parametrize("unit,area,expected_ha", [
    ("Acres", 10, 4.047), ("Hectares", 3, 3.0), ("Bighas", 8, 2.0), ("Gunthas", 100, 1.012),
])
def test_land_unit_conversion(engine, unit, area, expected_ha):
    profile = {**BASE_PROFILE, "land_unit": unit, "land_area": area}
    assert engine.generate_recommendations(profile)["land_area_ha"] == pytest.approx(expected_ha, abs=0.01)


def test_scoring_weights_sum_to_one_and_soil_redistribution(engine):
    known = engine.generate_recommendations(BASE_PROFILE)["scoring_weights"]
    unknown = engine.generate_recommendations({**BASE_PROFILE, "soil_type": "Unknown"})["scoring_weights"]
    assert sum(known.values()) == pytest.approx(1.0)
    assert sum(unknown.values()) == pytest.approx(1.0)
    assert unknown["soil"] == 0.0 and unknown["model"] > known["model"] and unknown["water"] > known["water"]


def test_hot_weather_lowers_weather_score(engine):
    hot = {"current": {"temperature_c": 44.0}}
    mild = {"current": {"temperature_c": 22.0}}
    wheat_hot = next(r for r in engine.generate_recommendations(BASE_PROFILE, hot, top_n=10)["recommendations"] if r["crop_name"] == "Wheat")
    wheat_mild = next(r for r in engine.generate_recommendations(BASE_PROFILE, mild, top_n=10)["recommendations"] if r["crop_name"] == "Wheat")
    assert wheat_hot["weather_suitability_score"] < wheat_mild["weather_suitability_score"]
