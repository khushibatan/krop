"""
Unit tests for KROP Prediction Module.
"""

import pytest
from src.prediction import CropPredictor


@pytest.fixture
def predictor():
    return CropPredictor()


def test_predict_candidates_structure(predictor):
    candidates = predictor.predict_candidates(
        state="Maharashtra",
        season="Kharif",
        area_ha=2.0,
        annual_rainfall_mm=1000.0,
        seasonal_rainfall_mm=750.0,
        top_k=5
    )
    assert len(candidates) == 5
    for c in candidates:
        assert "crop" in c
        assert "initial_rank" in c
        assert "model_probability" in c
        assert 0.0 <= c["model_probability"] <= 1.0


def test_predict_candidates_ranking_order(predictor):
    candidates = predictor.predict_candidates(
        state="Punjab",
        season="Rabi",
        area_ha=4.0,
        annual_rainfall_mm=600.0,
        seasonal_rainfall_mm=120.0,
        top_k=3
    )
    assert len(candidates) == 3
    # Check probabilities are in descending order
    probs = [c["model_probability"] for c in candidates]
    assert probs == sorted(probs, reverse=True)


def test_invalid_area_raises(predictor):
    with pytest.raises(ValueError, match="must be greater than zero"):
        predictor.predict_candidates(
            state="Gujarat",
            season="Kharif",
            area_ha=-1.5,
            annual_rainfall_mm=800.0,
            seasonal_rainfall_mm=600.0
        )
