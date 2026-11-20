"""
KROP - Feature Engineering Module
Transforms clean agricultural records and farmer inputs into machine learning feature matrices.
Strictly adheres to:
- Zero hardware dependency
- Absolutely ZERO NPK
- Exact compatibility between training and application prediction features
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np

logger = logging.getLogger("krop.feature_engineering")

# Official Government of India (Agriculture Census) Landholding Categories
LAND_CATEGORIES = ["Marginal", "Small", "Semi-Medium", "Medium", "Large"]


def categorize_land_area(area_ha: float) -> str:
    """Categorize land size into official Indian agricultural holding brackets."""
    if area_ha < 1.0:
        return "Marginal"      # < 1.0 hectare
    elif area_ha < 2.0:
        return "Small"         # 1.0 to 2.0 hectares
    elif area_ha < 4.0:
        return "Semi-Medium"   # 2.0 to 4.0 hectares
    elif area_ha < 10.0:
        return "Medium"        # 4.0 to 10.0 hectares
    else:
        return "Large"         # > 10.0 hectares


def convert_to_hectares(area: float, unit: str) -> float:
    """Convert farmer land area inputs into standard hectares."""
    u = unit.strip().lower()
    if u in ["acre", "acres"]:
        return round(area * 0.404686, 4)
    elif u in ["bigha", "bighas"]:
        # Standard average Indian bigha (~0.25 ha)
        return round(area * 0.25, 4)
    elif u in ["guntha", "gunthas"]:
        return round(area * 0.010117, 4)
    else:  # "hectare", "hectares", "ha"
        return round(area, 4)


class FeatureEngineer:
    """Extracts and formats features for model training and inference."""

    def __init__(self):
        self.feature_columns = [
            "State_Name",
            "Season",
            "area_hectares",
            "area_category",
            "annual_rainfall_mm",
            "seasonal_rainfall_mm",
            "rainfall_ratio"
        ]
        self.target_column = "Crop"

    def extract_training_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Engineers feature matrix X and target y from preprocessed historical dataset."""
        df_feat = df.copy()

        df_feat["area_hectares"] = df_feat["Area"].astype(float)
        df_feat["area_category"] = df_feat["area_hectares"].apply(categorize_land_area)
        
        # Rainfall indicators
        df_feat["annual_rainfall_mm"] = df_feat["annual_rainfall_mm"].astype(float)
        df_feat["seasonal_rainfall_mm"] = df_feat["seasonal_rainfall_mm"].astype(float)
        df_feat["rainfall_ratio"] = (
            df_feat["seasonal_rainfall_mm"] / (df_feat["annual_rainfall_mm"] + 1e-5)
        ).clip(0.0, 1.5)

        X = df_feat[self.feature_columns].copy()
        y = df_feat[self.target_column].copy()

        logger.info("Feature engineering complete: %d samples, %d features", X.shape[0], X.shape[1])
        return X, y

    def build_inference_feature(
        self,
        state: str,
        season: str,
        area_ha: float,
        annual_rainfall_mm: float,
        seasonal_rainfall_mm: float
    ) -> pd.DataFrame:
        """Constructs a single-row feature DataFrame strictly matching training features."""
        area_cat = categorize_land_area(area_ha)
        rf_ratio = round(min(1.5, max(0.0, seasonal_rainfall_mm / (annual_rainfall_mm + 1e-5))), 4)

        row = {
            "State_Name": state.strip(),
            "Season": season.strip(),
            "area_hectares": float(area_ha),
            "area_category": area_cat,
            "annual_rainfall_mm": float(annual_rainfall_mm),
            "seasonal_rainfall_mm": float(seasonal_rainfall_mm),
            "rainfall_ratio": float(rf_ratio)
        }
        return pd.DataFrame([row])[self.feature_columns]


if __name__ == "__main__":
    fe = FeatureEngineer()
    test_vec = fe.build_inference_feature(
        state="Maharashtra",
        season="Kharif",
        area_ha=2.5,
        annual_rainfall_mm=1100.0,
        seasonal_rainfall_mm=850.0
    )
    print("Inference feature shape:", test_vec.shape)
    print("Inference feature vector:\n", test_vec)
