"""
Unit tests for KROP Database Module.
Tests SQLite persistence, JSON serialization, and parameterized CRUD operations.
"""

import pytest
from pathlib import Path
from src.database import DatabaseManager


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_krop.db"
    return DatabaseManager(db_file)


def test_db_initialization(test_db):
    assert test_db.db_path.exists()
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        assert "farm_profiles" in tables
        assert "recommendations" in tables


def test_farm_profile_crud(test_db):
    profile = {
        "village": "Rahuri",
        "district": "Ahmednagar",
        "state": "Maharashtra",
        "land_area": 4.5,
        "land_unit": "Acres",
        "soil_type": "Black soil",
        "irrigation_method": "Canal",
        "water_availability": "Good",
        "preferred_season": "Kharif",
        "crop_preferences": "Pulses"
    }
    p_id = test_db.save_farm_profile(profile)
    assert p_id > 0

    # Retrieve
    retrieved = test_db.get_farm_profile(p_id)
    assert retrieved is not None
    assert retrieved["district"] == "Ahmednagar"
    assert retrieved["land_area"] == 4.5
    assert retrieved["soil_type"] == "Black soil"

    # Update
    profile["land_area"] = 6.0
    updated = test_db.update_farm_profile(p_id, profile)
    assert updated is True
    assert test_db.get_farm_profile(p_id)["land_area"] == 6.0

    # Delete
    deleted = test_db.delete_farm_profile(p_id)
    assert deleted is True
    assert test_db.get_farm_profile(p_id) is None


def test_recommendation_crud(test_db):
    # Save a profile first
    p_id = test_db.save_farm_profile({
        "village": "Karnal",
        "district": "Karnal",
        "state": "Haryana",
        "land_area": 3.0,
        "land_unit": "Acres",
        "soil_type": "Alluvial",
        "irrigation_method": "Borewell",
        "water_availability": "Good",
        "preferred_season": "Rabi",
        "crop_preferences": "Cereals"
    })

    rec_crops = [
        {"crop_name": "Wheat", "rank": 1, "composite_score": 92.5},
        {"crop_name": "Barley", "rank": 2, "composite_score": 84.0}
    ]
    weather = {"temperature_c": 18.0, "condition": "Cool"}
    details = {"model": "RandomForest", "top_k": 2}

    rec_id = test_db.save_recommendation(
        farm_profile_id=p_id,
        recommended_crops=rec_crops,
        weather_summary=weather,
        recommendation_details=details
    )
    assert rec_id > 0

    # Retrieve and check JSON deserialization
    rec = test_db.get_recommendation(rec_id)
    assert rec is not None
    assert isinstance(rec["recommended_crops"], list)
    assert rec["recommended_crops"][0]["crop_name"] == "Wheat"
    assert rec["weather_summary"]["temperature_c"] == 18.0

    # History retrieval
    history = test_db.get_recommendation_history()
    assert len(history) == 1
    assert history[0]["id"] == rec_id

    # Delete
    del_ok = test_db.delete_recommendation(rec_id)
    assert del_ok is True
    assert test_db.get_recommendation(rec_id) is None
