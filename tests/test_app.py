"""Headless smoke tests: every Streamlit page must render without exceptions."""

import pytest
from streamlit.testing.v1 import AppTest

from src.config import PROJECT_ROOT
from src.database import DatabaseManager

PAGES = [
    "pages/1_Home.py",
    "pages/2_Farm_Profile.py",
    "pages/3_Crop_Recommendations.py",
    "pages/4_Crop_Insights.py",
    "pages/5_Recommendation_History.py",
    "pages/6_About.py",
]

PROFILE = {
    "id": 1, "village": "<script>alert(1)</script>", "district": "Pune", "state": "Maharashtra",
    "latitude": 18.52, "longitude": 73.85, "land_area": 2.0, "land_unit": "Acres",
    "soil_type": "Black soil", "irrigation_method": "Borewell", "water_availability": "Good",
    "preferred_season": "Kharif", "crop_preferences": "No preference",
}


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "ui_test.db"))
    from src import ui_components
    ui_components.get_db_manager.clear()


@pytest.fixture(autouse=True)
def offline_services(monkeypatch):
    """Keep UI tests deterministic and network-free."""
    import requests

    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline in tests")

    monkeypatch.setattr("src.weather_service.requests.get", fail)
    monkeypatch.setattr("src.geolocation_service.requests.get", fail)


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_profile(page):
    at = AppTest.from_file(str(PROJECT_ROOT / page), default_timeout=60)
    at.session_state["db_manager"] = DatabaseManager()
    at.session_state["active_farm_profile"] = None
    at.run()
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_with_profile(page):
    at = AppTest.from_file(str(PROJECT_ROOT / page), default_timeout=60)
    at.session_state["db_manager"] = DatabaseManager()
    at.session_state["active_farm_profile"] = dict(PROFILE)
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_markup_is_escaped_in_profile_card():
    at = AppTest.from_file(str(PROJECT_ROOT / "pages/2_Farm_Profile.py"), default_timeout=60)
    at.session_state["db_manager"] = DatabaseManager()
    at.session_state["active_farm_profile"] = dict(PROFILE)
    at.run()
    html = " ".join(m.value for m in at.markdown)
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_recommendation_flow_and_save():
    at = AppTest.from_file(str(PROJECT_ROOT / "pages/3_Crop_Recommendations.py"), default_timeout=90)
    db = DatabaseManager()
    at.session_state["db_manager"] = db
    at.session_state["active_farm_profile"] = dict(PROFILE)
    at.run()
    assert not at.exception
    next(b for b in at.button if "Save Recommendation" in b.label).click().run()
    assert not at.exception
    assert db.count_recommendations() == 1
