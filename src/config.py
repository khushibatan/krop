"""
KROP - Central configuration.

All filesystem locations are resolved relative to the project root so the
application, training pipeline and tests behave identically regardless of the
directory they are launched from.
"""

import logging
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
CLEAN_DATASET_PATH = PROCESSED_DATA_DIR / "clean_crop_rainfall.csv"
CROP_INFO_CSV_PATH = PROCESSED_DATA_DIR / "crop_information.csv"
DISTRICT_RAINFALL_RAW = RAW_DATA_DIR / "district wise rainfall normal.csv"

# Models
MODELS_DIR = PROJECT_ROOT / "models"
EVAL_DIR = MODELS_DIR / "evaluation"
MODEL_PATH = MODELS_DIR / "krop_crop_model.joblib"
METADATA_PATH = MODELS_DIR / "krop_model_metadata.json"
EVAL_REPORT_JSON = EVAL_DIR / "model_evaluation_report.json"
EVAL_REPORT_MD = EVAL_DIR / "model_evaluation_report.md"

# Assets
LOGO_PATH = PROJECT_ROOT / "assets" / "images" / "krop_logo.svg"

# Application
APP_VERSION = "1.1.0"
MODEL_VERSION = "1.1.0"


def _load_dotenv() -> None:
    """Loads a local .env file when python-dotenv is installed (optional)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:  # pragma: no cover - optional dependency
        pass


_load_dotenv()


def get_database_path() -> Path:
    """Resolves the SQLite path from DATABASE_PATH (relative to project root) or the default."""
    configured = os.environ.get("DATABASE_PATH", "").strip()
    path = Path(configured) if configured else Path("database") / "krop.db"
    return path if path.is_absolute() else PROJECT_ROOT / path


def configure_logging(level: int = logging.INFO) -> None:
    """Configures root logging once; intended to be called from CLI entry points only."""
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
