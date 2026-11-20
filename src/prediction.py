"""
KROP - Prediction Module
Loads serialized ML pipeline and performs probabilistic inference for crop candidates.
Strictly zero NPK: features are purely geographical, seasonal, farm-scale, and rainfall-based.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import pandas as pd
import numpy as np

from src.feature_engineering import FeatureEngineer

logger = logging.getLogger("krop.prediction")

MODEL_PATH = Path("models/krop_crop_model.joblib")
METADATA_PATH = Path("models/krop_model_metadata.json")

_CACHED_PIPELINE = None


def load_model(model_path: Path = MODEL_PATH):
    """Loads and caches the serialized Random Forest pipeline."""
    global _CACHED_PIPELINE
    if _CACHED_PIPELINE is not None:
        return _CACHED_PIPELINE

    if not model_path.exists():
        logger.warning("Model file not found at '%s'. Triggering automatic training...", model_path)
        try:
            from src.train_model import ModelTrainer
            trainer = ModelTrainer()
            trainer.train_and_evaluate()
        except Exception as e:
            raise FileNotFoundError(
                f"Trained model artifact not found at '{model_path}' and automatic training failed: {e}. "
                "Please train the model manually by executing: `python -m src.train_model`."
            )

    try:
        _CACHED_PIPELINE = joblib.load(model_path)
        logger.info("Successfully loaded ML pipeline from %s", model_path)
        return _CACHED_PIPELINE
    except Exception as e:
        logger.error("Error loading model artifact: %s", e)
        raise RuntimeError(f"Failed to deserialize model artifact from '{model_path}': {e}")


class CropPredictor:
    """Performs crop suitability predictions using the trained model."""

    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.feature_engineer = FeatureEngineer()
        self.pipeline = load_model(self.model_path)
        self.classes_ = self.pipeline.named_steps["classifier"].classes_

    def predict_candidates(
        self,
        state: str,
        season: str,
        area_ha: float,
        annual_rainfall_mm: float,
        seasonal_rainfall_mm: float,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Runs model inference on farmer profile features and returns top_k candidates with probabilities.
        """
        # Validate inputs
        if area_ha <= 0:
            raise ValueError(f"Land area must be greater than zero. Received: {area_ha}")

        # Construct single-row inference vector
        feature_df = self.feature_engineer.build_inference_feature(
            state=state,
            season=season,
            area_ha=area_ha,
            annual_rainfall_mm=annual_rainfall_mm,
            seasonal_rainfall_mm=seasonal_rainfall_mm
        )

        # Predict probabilities across all 33 classes
        probas = self.pipeline.predict_proba(feature_df)[0]
        
        # Sort descending by model probability
        indices = np.argsort(probas)[::-1][:top_k]

        candidates = []
        for rank, idx in enumerate(indices, start=1):
            crop_name = self.classes_[idx]
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
        area_ha=1.5,
        annual_rainfall_mm=1050.0,
        seasonal_rainfall_mm=800.0,
        top_k=5
    )
    print("Predicted Candidates for Maharashtra (Kharif, 1.5 ha, 800mm rain):")
    for r in results:
        print(f"Rank {r['initial_rank']}: {r['crop']} (Model Probability: {r['model_probability']:.4f})")
