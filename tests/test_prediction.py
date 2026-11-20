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
        annual_rainfall_mm=600.0,
        seasonal_rainfall_mm=120.0,
        top_k=3
    )
    assert len(candidates) == 3
    # Check probabilities are in descending order
    probs = [c["model_probability"] for c in candidates]
    assert probs == sorted(probs, reverse=True)


def test_invalid_inputs_raise(predictor):
    with pytest.raises(ValueError, match="at least 1"):
        predictor.predict_candidates("Gujarat", "Kharif", 800.0, 600.0, top_k=0)
    with pytest.raises(ValueError, match="negative"):
        predictor.predict_candidates("Gujarat", "Kharif", -5.0, 600.0)


def test_top_k_beyond_class_count_returns_all_classes(predictor):
    candidates = predictor.predict_candidates("Gujarat", "Kharif", 800.0, 600.0, top_k=500)
    assert len(candidates) == predictor.n_classes


def test_regional_staples_are_surfaced(predictor):
    """Sanity check that the model reflects well-known regional staples."""
    wheat_belt = predictor.predict_candidates("Punjab", "Rabi", 600.0, 120.0, top_k=3)
    assert "Wheat" in [c["crop"] for c in wheat_belt]
