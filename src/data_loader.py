"""
KROP - Data Loader Module
Loads raw and processed agricultural and rainfall datasets.
Adheres strictly to the software-only, zero-hardware, and ZERO-NPK specification.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger("krop.data_loader")

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

CROP_PRODUCTION_RAW = RAW_DATA_DIR / "crop_production.csv"
DISTRICT_RAINFALL_RAW = RAW_DATA_DIR / "district wise rainfall normal.csv"
HISTORICAL_RAINFALL_RAW = RAW_DATA_DIR / "rainfall in india 1901-2015.csv"
PROCESSED_DATASET = PROCESSED_DATA_DIR / "clean_crop_rainfall.csv"


class DataLoader:
    """Manages dataset retrieval, presence checks, and integrity validation."""

    def __init__(self, raw_dir: Path = RAW_DATA_DIR, processed_dir: Path = PROCESSED_DATA_DIR):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

    def check_raw_data_exists(self) -> Dict[str, bool]:
        """Check if all required raw datasets are present in data/raw/."""
        status = {
            "crop_production": (self.raw_dir / "crop_production.csv").exists(),
            "district_rainfall": (self.raw_dir / "district wise rainfall normal.csv").exists(),
            "historical_rainfall": (self.raw_dir / "rainfall in india 1901-2015.csv").exists(),
        }
        return status

    def load_crop_production(self) -> pd.DataFrame:
        """Load the raw crop production dataset."""
        file_path = self.raw_dir / "crop_production.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"Crop production dataset not found at {file_path}. "
                "Run `python src/acquire_data.py` to acquire raw data."
            )
        df = pd.read_csv(file_path, low_memory=False)
        logger.info("Loaded crop production data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_district_rainfall(self) -> pd.DataFrame:
        """Load the district-level normal rainfall dataset."""
        file_path = self.raw_dir / "district wise rainfall normal.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"District rainfall dataset not found at {file_path}. "
                "Run `python src/acquire_data.py` to acquire raw data."
            )
        df = pd.read_csv(file_path)
        logger.info("Loaded district rainfall data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_historical_rainfall(self) -> pd.DataFrame:
        """Load the subdivision-level historical rainfall dataset (1901-2015)."""
        file_path = self.raw_dir / "rainfall in india 1901-2015.csv"
        if not file_path.exists():
            raise FileNotFoundError(
                f"Historical rainfall dataset not found at {file_path}. "
                "Run `python src/acquire_data.py` to acquire raw data."
            )
        df = pd.read_csv(file_path)
        logger.info("Loaded historical rainfall data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_processed_data(self) -> Optional[pd.DataFrame]:
        """Load the preprocessed joined dataset if available."""
        if PROCESSED_DATASET.exists():
            return pd.read_csv(PROCESSED_DATASET, low_memory=False)
        return None


if __name__ == "__main__":
    loader = DataLoader()
    exists = loader.check_raw_data_exists()
    print("Raw data status:", exists)
    if all(exists.values()):
        cp = loader.load_crop_production()
        dr = loader.load_district_rainfall()
        print(f"Crop production shape: {cp.shape}")
        print(f"District rainfall shape: {dr.shape}")
