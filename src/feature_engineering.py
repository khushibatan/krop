"""
KROP - Feature Engineering Module
Transforms clean agricultural records and farmer inputs into machine learning feature matrices.
Strictly adheres to:
- Zero hardware dependency
- Absolutely ZERO NPK
- Exact compatibility between training and application prediction features
"""

import logging
from typing import Tuple
import numpy as np
import pandas as pd

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
    """
    Extracts and formats features for model training and inference.

    The model deliberately uses only regional and climatic signals (state, season, IMD rainfall
    normals). Historical ``Area`` values are district-level totals, not individual farm sizes, so
    they are used as training *sample weights* rather than as an input feature.
    """

    def __init__(self):
        self.categorical_features = ["State_Name", "Season"]
        self.numerical_features = ["annual_rainfall_mm", "seasonal_rainfall_mm", "rainfall_ratio"]
        self.feature_columns = self.categorical_features + self.numerical_features
        self.target_column = "Crop"
        self.weight_column = "Area"

    @staticmethod
    def rainfall_ratio(seasonal_rainfall_mm, annual_rainfall_mm):
        """Seasonal share of annual rainfall, bounded to [0, 1.5]."""
        return (seasonal_rainfall_mm / (annual_rainfall_mm + 1e-5)).clip(0.0, 1.5) \
            if hasattr(seasonal_rainfall_mm, "clip") \
            else min(1.5, max(0.0, seasonal_rainfall_mm / (annual_rainfall_mm + 1e-5)))

    def extract_training_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Engineers the feature matrix X, target y and sample weights from the preprocessed dataset.
        Weights are sqrt(cultivated area): regionally dominant crops count for more, without letting
        a handful of very large districts swamp the minor crops that smallholders often grow.
        """
        df_feat = df.copy()
        df_feat["annual_rainfall_mm"] = df_feat["annual_rainfall_mm"].astype(float)
        df_feat["seasonal_rainfall_mm"] = df_feat["seasonal_rainfall_mm"].astype(float)
        df_feat["rainfall_ratio"] = self.rainfall_ratio(
            df_feat["seasonal_rainfall_mm"], df_feat["annual_rainfall_mm"]
        )

        X = df_feat[self.feature_columns].copy()
        y = df_feat[self.target_column].copy()
        weights = np.sqrt(df_feat[self.weight_column].astype(float).clip(lower=0.0))

        logger.info("Feature engineering complete: %d samples, %d features", X.shape[0], X.shape[1])
        return X, y, weights

    def build_inference_feature(
        self,
        state: str,
        season: str,
        annual_rainfall_mm: float,
        seasonal_rainfall_mm: float,
    ) -> pd.DataFrame:
        """Constructs a single-row feature DataFrame strictly matching the training features."""
        row = {
            "State_Name": state.strip(),
            "Season": season.strip(),
            "annual_rainfall_mm": float(annual_rainfall_mm),
            "seasonal_rainfall_mm": float(seasonal_rainfall_mm),
            "rainfall_ratio": round(float(self.rainfall_ratio(seasonal_rainfall_mm, annual_rainfall_mm)), 4),
        }
        return pd.DataFrame([row])[self.feature_columns]


if __name__ == "__main__":
    fe = FeatureEngineer()
    print(fe.build_inference_feature("Maharashtra", "Kharif", 1100.0, 850.0))
