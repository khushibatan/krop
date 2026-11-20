"""
Unit tests for KROP Machine Learning Model and Metadata.
"""

import pytest
import json
from pathlib import Path
import joblib
from sklearn.pipeline import Pipeline
from src.config import METADATA_PATH, MODEL_PATH, MODEL_VERSION
from src.prediction import load_model


def test_model_artifact_exists():
    assert MODEL_PATH.exists(), "Trained model artifact krop_crop_model.joblib does not exist."


def test_model_deserialization():
    pipeline = load_model()
    assert isinstance(pipeline, Pipeline)
    assert "preprocessor" in pipeline.named_steps
    assert "classifier" in pipeline.named_steps


def test_model_classes_count():
    pipeline = load_model()
    classes = pipeline.named_steps["classifier"].classes_
    assert len(classes) >= 30, f"Expected at least 30 target crops, got {len(classes)}"
    assert "Wheat" in classes
    assert "Rice" in classes
    assert "Cotton(lint)" in classes


def test_evaluation_metadata():
    assert METADATA_PATH.exists()
    with open(METADATA_PATH, "r") as f:
        meta = json.load(f)
    assert meta["model_version"] == MODEL_VERSION
    assert "metrics" in meta
    metrics = meta["metrics"]
    assert metrics["top_5_area_weighted_accuracy"] >= 0.80, "Area-weighted Top-5 accuracy must exceed 80%."
