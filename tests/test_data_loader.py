"""
Unit tests for KROP Data Loader Module.
"""

import pytest
from pathlib import Path
import pandas as pd
from src.data_loader import DataLoader


def test_data_loader_initialization():
    loader = DataLoader()
    assert loader.raw_dir == Path("data/raw")
    assert loader.processed_dir == Path("data/processed")


def test_raw_data_presence():
    loader = DataLoader()
    status = loader.check_raw_data_exists()
    assert "crop_production" in status
    assert "district_rainfall" in status
    assert "historical_rainfall" in status
    assert status["crop_production"] is True
    assert status["district_rainfall"] is True


def test_load_crop_production():
    loader = DataLoader()
    df = loader.load_crop_production()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 100000
    assert "State_Name" in df.columns
    assert "District_Name" in df.columns
    assert "Crop" in df.columns
    assert "Season" in df.columns


def test_load_district_rainfall():
    loader = DataLoader()
    df = loader.load_district_rainfall()
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 500
    assert "DISTRICT" in df.columns
    assert "ANNUAL" in df.columns
    assert "Jun-Sep" in df.columns
