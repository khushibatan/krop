"""
KROP - Data Preprocessing Module
Cleans, standardizes, validates, and merges agricultural and meteorological datasets.
Adheres strictly to the KROP specification:
- Pure software and machine learning
- Zero hardware dependencies
- Absolutely ZERO NPK measurements
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.config import CLEAN_DATASET_PATH, PROCESSED_DATA_DIR, configure_logging
from src.data_loader import DataLoader
from src.crop_information import load_crop_catalog

logger = logging.getLogger("krop.data_preprocessing")

SEASON_MAPPING = {
    "Kharif": "Kharif",
    "Autumn": "Kharif",       # Autumn refers to early Kharif harvest in eastern states
    "Rabi": "Rabi",
    "Winter": "Rabi",         # Winter season corresponds to the Rabi cycle
    "Summer": "Summer",       # Zaid / Summer crop cycle
    "Whole Year": "Whole Year"
}


def normalize_name(name: str) -> str:
    """Standardize string for robust cross-dataset joining."""
    if not isinstance(name, str):
        return ""
    # Strip, uppercase, replace dashes/underscores with space, collapse spaces
    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", name).upper()
    return " ".join(cleaned.split())


class DataPreprocessor:
    """Processes raw agricultural statistics and IMD rainfall records."""

    def __init__(self, data_loader: Optional[DataLoader] = None):
        self.loader = data_loader or DataLoader()
        self.crop_catalog = load_crop_catalog()
        self.valid_crops = set(self.crop_catalog["crop_name"].tolist())

    def clean_crop_data(self, df_crop: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize crop production records."""
        df = df_crop.copy()
        
        # Standardize column names
        df.columns = [c.strip() for c in df.columns]
        
        # Strip strings
        df["State_Name"] = df["State_Name"].astype(str).str.strip()
        df["District_Name"] = df["District_Name"].astype(str).str.strip()
        df["Season"] = df["Season"].astype(str).str.strip()
        df["Crop"] = df["Crop"].astype(str).str.strip()

        # Standardize season
        df["Season"] = df["Season"].map(SEASON_MAPPING).fillna(df["Season"])

        # Filter to crops in our verified catalog
        df = df[df["Crop"].isin(self.valid_crops)].copy()

        # Remove invalid Area (<= 0)
        df = df[df["Area"] > 0].copy()

        # Handle Production nulls: fill with median yield of that crop in the state
        # First calculate yield where production is present
        valid_prod_mask = df["Production"].notnull() & (df["Production"] >= 0)
        df["Yield"] = np.nan
        df.loc[valid_prod_mask, "Yield"] = df.loc[valid_prod_mask, "Production"] / df.loc[valid_prod_mask, "Area"]

        # Compute median yield by State and Crop
        state_crop_yield = df.groupby(["State_Name", "Crop"])["Yield"].transform("median")
        crop_yield = df.groupby("Crop")["Yield"].transform("median")
        
        # Fill missing yield with state-crop median, then general crop median
        df["Yield"] = df["Yield"].fillna(state_crop_yield).fillna(crop_yield).fillna(1.0)
        
        # Recalculate production if missing
        missing_prod = df["Production"].isnull() | (df["Production"] < 0)
        df.loc[missing_prod, "Production"] = df.loc[missing_prod, "Area"] * df.loc[missing_prod, "Yield"]

        # Normalized names for joining
        df["norm_state"] = df["State_Name"].apply(normalize_name)
        df["norm_district"] = df["District_Name"].apply(normalize_name)

        logger.info("Cleaned crop records: %d valid rows across %d crops", len(df), df["Crop"].nunique())
        return df

    def clean_rainfall_data(self, df_rain: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Clean district-level rainfall normals and compute state averages."""
        df = df_rain.copy()
        df.columns = [c.strip() for c in df.columns]

        df["norm_state"] = df["STATE_UT_NAME"].apply(normalize_name)
        df["norm_district"] = df["DISTRICT"].apply(normalize_name)

        # Ensure numeric rainfall
        rain_cols = ["ANNUAL", "Jan-Feb", "Mar-May", "Jun-Sep", "Oct-Dec"]
        for col in rain_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        # Compute state-level fallback averages
        state_rain_avg = df.groupby("norm_state")[rain_cols].mean().reset_index()

        return df, state_rain_avg

    def merge_crop_and_rainfall(
        self, df_crop: pd.DataFrame, df_rain: pd.DataFrame, state_rain: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge crop records with district or state rainfall normals."""
        rain_cols = ["ANNUAL", "Jan-Feb", "Mar-May", "Jun-Sep", "Oct-Dec"]
        rain_subset = df_rain[["norm_state", "norm_district"] + rain_cols].drop_duplicates(
            subset=["norm_state", "norm_district"]
        )

        # 1. District-level exact join
        merged = pd.merge(
            df_crop,
            rain_subset,
            on=["norm_state", "norm_district"],
            how="left",
            suffixes=("", "_dist")
        )

        # 2. State-level fallback for unmatched districts
        missing_mask = merged["ANNUAL"].isnull()
        if missing_mask.any():
            unmatched = merged.loc[missing_mask].drop(columns=rain_cols)
            state_merged = pd.merge(
                unmatched,
                state_rain,
                on="norm_state",
                how="left"
            )
            merged.loc[missing_mask, rain_cols] = state_merged[rain_cols].values

        # 3. Overall national fallback for any rare remaining nulls
        for col in rain_cols:
            national_avg = df_rain[col].median()
            merged[col] = merged[col].fillna(national_avg)

        # Compute season-specific rainfall
        def extract_seasonal_rain(row):
            season = row["Season"]
            if season == "Kharif":
                return row["Jun-Sep"]
            elif season == "Rabi":
                return row["Jan-Feb"] + row["Oct-Dec"]
            elif season == "Summer":
                return row["Mar-May"]
            else:  # Whole Year
                return row["ANNUAL"]

        merged["seasonal_rainfall_mm"] = merged.apply(extract_seasonal_rain, axis=1)
        merged["annual_rainfall_mm"] = merged["ANNUAL"]

        # Drop temporary joining columns
        final_cols = [
            "State_Name", "District_Name", "Crop_Year", "Season", "Crop",
            "Area", "Production", "Yield",
            "annual_rainfall_mm", "seasonal_rainfall_mm",
            "Jun-Sep", "Jan-Feb", "Mar-May", "Oct-Dec"
        ]
        result = merged[final_cols].copy()

        # Final assertion: verify strictly zero NPK present
        for col in result.columns:
            assert not any(npk in col.upper() for npk in ["NITROGEN", "PHOSPHORUS", "POTASSIUM", "NPK"]), (
                f"Violation: Disallowed nutrient column detected: {col}"
            )

        logger.info("Successfully merged crop and rainfall dataset: %d rows", len(result))
        return result

    def process_and_save(self) -> Path:
        """Executes full preprocessing pipeline and writes clean dataset."""
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        raw_crop = self.loader.load_crop_production()
        raw_rain = self.loader.load_district_rainfall()

        clean_crop = self.clean_crop_data(raw_crop)
        clean_rain, state_rain = self.clean_rainfall_data(raw_rain)

        final_df = self.merge_crop_and_rainfall(clean_crop, clean_rain, state_rain)
        
        output_path = CLEAN_DATASET_PATH
        final_df.to_csv(output_path, index=False)
        logger.info("Saved preprocessed dataset to: %s", output_path)
        return output_path


if __name__ == "__main__":
    configure_logging()
    preprocessor = DataPreprocessor()
    path = preprocessor.process_and_save()
    print("Preprocessing completed successfully. Output saved to:", path)
