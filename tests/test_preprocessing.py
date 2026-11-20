"""
Unit tests for KROP Data Preprocessing and Feature Engineering.
Strict verification of ZERO NPK and data transformations.
"""

import pytest
import pandas as pd
import numpy as np
from src.config import CLEAN_DATASET_PATH
from src.data_preprocessing import DataPreprocessor, normalize_name, SEASON_MAPPING
from src.feature_engineering import categorize_land_area, convert_to_hectares, FeatureEngineer


def test_normalize_name():
    assert normalize_name(" Pune-District ") == "PUNE DISTRICT"
    assert normalize_name("Maharashtra_State") == "MAHARASHTRA STATE"
    assert normalize_name(None) == ""


def test_season_mapping():
    assert SEASON_MAPPING["Autumn"] == "Kharif"
    assert SEASON_MAPPING["Winter"] == "Rabi"
    assert SEASON_MAPPING["Summer"] == "Summer"
    assert SEASON_MAPPING["Whole Year"] == "Whole Year"


def test_land_area_categorization():
    assert categorize_land_area(0.5) == "Marginal"
    assert categorize_land_area(1.5) == "Small"
    assert categorize_land_area(3.0) == "Semi-Medium"
    assert categorize_land_area(7.5) == "Medium"
    assert categorize_land_area(25.0) == "Large"


def test_area_unit_conversion():
    # 1 Acre ≈ 0.4047 Hectares
    assert round(convert_to_hectares(10.0, "Acres"), 1) == 4.0
    assert convert_to_hectares(5.0, "Hectares") == 5.0
    assert convert_to_hectares(4.0, "Bighas") == 1.0


def test_feature_engineer_vector():
    fe = FeatureEngineer()
    vec = fe.build_inference_feature(
        state="Maharashtra",
        season="Kharif",
        annual_rainfall_mm=1000.0,
        seasonal_rainfall_mm=750.0
    )
    assert isinstance(vec, pd.DataFrame)
    assert len(vec) == 1
    assert vec.iloc[0]["State_Name"] == "Maharashtra"
    assert vec.iloc[0]["Season"] == "Kharif"
    assert list(vec.columns) == fe.feature_columns
    assert "area_hectares" not in vec.columns  # district-level area is not a farm-size feature
    assert vec.iloc[0]["rainfall_ratio"] == pytest.approx(0.75, abs=1e-4)

    # STRICT ZERO NPK ASSERTION
    for col in vec.columns:
        assert not any(npk in col.upper() for npk in ["NITROGEN", "PHOSPHORUS", "POTASSIUM", "NPK"])


def test_clean_dataset_strict_zero_npk():
    """Verify that processed dataset exists and has absolutely zero NPK columns."""
    df = pd.read_csv(CLEAN_DATASET_PATH, nrows=100)
    for col in df.columns:
        upper_c = col.upper()
        assert "NITROGEN" not in upper_c
        assert "PHOSPHORUS" not in upper_c
        assert "POTASSIUM" not in upper_c
        assert "NPK" not in upper_c
