"""
KROP - Prediction Module
Loads serialized ML pipeline and performs probabilistic inference for crop candidates.
Strictly zero NPK: features are purely geographical, seasonal, farm-scale, and rainfall-based.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List
import joblib
import numpy as np

from src.config import METADATA_PATH, MODEL_PATH
from src.feature_engineering import FeatureEngineer

logger = logging.getLogger("krop.prediction")

_PIPELINE_CACHE: Dict[Path, Any] = {}


def load_model(model_path: Path = MODEL_PATH):
    """Loads and caches the serialized Random Forest pipeline (cached per artifact path)."""
    model_path = Path(model_path)
    if model_path in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[model_path]

    if not model_path.exists():
        logger.warning("Model file not found at '%s'. Triggering automatic training...", model_path)
        try:
            from src.train_model import ModelTrainer
            ModelTrainer().train_and_evaluate()
        except Exception as e:
            raise FileNotFoundError(
                f"Trained model artifact not found at '{model_path}' and automatic training failed: {e}. "
                "Please train the model manually by executing: `python -m src.train_model`."
            ) from e

    try:
        pipeline = joblib.load(model_path)
    except Exception as e:
        logger.error("Error loading model artifact: %s", e)
        raise RuntimeError(f"Failed to deserialize model artifact from '{model_path}': {e}") from e

    logger.info("Successfully loaded ML pipeline from %s", model_path)
    _PIPELINE_CACHE[model_path] = pipeline
    return pipeline


class CropPredictor:
    """Performs crop suitability predictions using the trained model."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.feature_engineer = FeatureEngineer()
        self.pipeline = load_model(self.model_path)
        self.classes_ = self.pipeline.named_steps["classifier"].classes_
        self.n_classes = len(self.classes_)

    def predict_candidates(
        self,
        state: str,
        season: str,
        annual_rainfall_mm: float,
        seasonal_rainfall_mm: float,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Runs model inference on regional/seasonal features and returns top_k crop candidates
        with their predicted probabilities, highest first.
        """
        if top_k < 1:
            raise ValueError(f"top_k must be at least 1. Received: {top_k}")
        if annual_rainfall_mm < 0 or seasonal_rainfall_mm < 0:
            raise ValueError("Rainfall values must not be negative.")

        feature_df = self.feature_engineer.build_inference_feature(
            state=state,
            season=season,
            annual_rainfall_mm=annual_rainfall_mm,
            seasonal_rainfall_mm=seasonal_rainfall_mm
        )

        # Predict probabilities across all 33 classes
        probas = self.pipeline.predict_proba(feature_df)[0]
        
        # Sort descending by model probability
        indices = np.argsort(probas)[::-1][:top_k]  # top_k beyond n_classes simply returns all classes

        candidates = []
        for rank, idx in enumerate(indices, start=1):
            crop_name = str(self.classes_[idx])
            prob = float(probas[idx])
            candidates.append({
                "crop": crop_name,
                "initial_rank": rank,
                "model_probability": round(prob, 4),
                "model_confidence_pct": round(prob * 100, 2)
            })

        return candidates


if __name__ == "__main__":
    predictor = CropPredictor()
    results = predictor.predict_candidates(
        state="Maharashtra",
        season="Kharif",
        annual_rainfall_mm=1050.0,
        seasonal_rainfall_mm=800.0,
        top_k=5
    )
    print("Predicted Candidates for Maharashtra (Kharif, 800mm seasonal rain):")
    for r in results:
        print(f"Rank {r['initial_rank']}: {r['crop']} (Model Probability: {r['model_probability']:.4f})")
