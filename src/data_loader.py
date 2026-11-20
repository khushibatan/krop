"""
KROP - Data Loader Module
Loads raw and processed agricultural and rainfall datasets.
Adheres strictly to the software-only, zero-hardware, and ZERO-NPK specification.
"""

import logging
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from src.config import CLEAN_DATASET_PATH, PROCESSED_DATA_DIR, RAW_DATA_DIR

logger = logging.getLogger("krop.data_loader")

CROP_PRODUCTION_FILE = "crop_production.csv"
DISTRICT_RAINFALL_FILE = "district wise rainfall normal.csv"
HISTORICAL_RAINFALL_FILE = "rainfall in india 1901-2015.csv"
PROCESSED_DATASET = CLEAN_DATASET_PATH


class DataLoader:
    """Manages dataset retrieval, presence checks, and integrity validation."""

    def __init__(self, raw_dir: Path = RAW_DATA_DIR, processed_dir: Path = PROCESSED_DATA_DIR):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

    def check_raw_data_exists(self) -> Dict[str, bool]:
        """Check if all required raw datasets are present in data/raw/."""
        status = {
            "crop_production": (self.raw_dir / CROP_PRODUCTION_FILE).exists(),
            "district_rainfall": (self.raw_dir / DISTRICT_RAINFALL_FILE).exists(),
            "historical_rainfall": (self.raw_dir / HISTORICAL_RAINFALL_FILE).exists(),
        }
        return status

    def load_crop_production(self) -> pd.DataFrame:
        """Load the raw crop production dataset."""
        file_path = self.raw_dir / CROP_PRODUCTION_FILE
        if not file_path.exists():
            raise FileNotFoundError(
                f"Crop production dataset not found at {file_path}. "
                "Run `python -m src.acquire_data` to acquire raw data."
            )
        df = pd.read_csv(file_path, low_memory=False)
        logger.info("Loaded crop production data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_district_rainfall(self) -> pd.DataFrame:
        """Load the district-level normal rainfall dataset."""
        file_path = self.raw_dir / DISTRICT_RAINFALL_FILE
        if not file_path.exists():
            raise FileNotFoundError(
                f"District rainfall dataset not found at {file_path}. "
                "Run `python -m src.acquire_data` to acquire raw data."
            )
        df = pd.read_csv(file_path)
        logger.info("Loaded district rainfall data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_historical_rainfall(self) -> pd.DataFrame:
        """Load the subdivision-level historical rainfall dataset (1901-2015)."""
        file_path = self.raw_dir / HISTORICAL_RAINFALL_FILE
        if not file_path.exists():
            raise FileNotFoundError(
                f"Historical rainfall dataset not found at {file_path}. "
                "Run `python -m src.acquire_data` to acquire raw data."
            )
        df = pd.read_csv(file_path)
        logger.info("Loaded historical rainfall data: %d rows, %d cols", len(df), len(df.columns))
        return df

    def load_processed_data(self) -> Optional[pd.DataFrame]:
        """Load the preprocessed joined dataset if available."""
        dataset_path = self.processed_dir / PROCESSED_DATASET.name
        if dataset_path.exists():
            return pd.read_csv(dataset_path, low_memory=False)
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
