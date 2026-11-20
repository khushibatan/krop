"""
KROP - Automated Dataset Acquisition Script
Downloads and validates authentic Indian agricultural datasets from Kaggle.
Adheres strictly to the KROP specification:
- Pure software and machine learning
- Zero hardware dependencies
- Absolutely ZERO NPK usage
"""

import shutil
import logging
from pathlib import Path
import pandas as pd

from src.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, configure_logging

logger = logging.getLogger("krop.acquire_data")

DATASETS_METADATA = [
    {
        "id": "abhinand05/crop-production-in-india",
        "name": "India Agriculture Crop Production",
        "url": "https://www.kaggle.com/datasets/abhinand05/crop-production-in-india",
        "author": "Abhinand (Ministry of Agriculture and Farmers Welfare, Govt of India source)",
        "license": "CC0: Public Domain / Open Government Data",
        "expected_files": ["crop_production.csv"],
        "description": "Historical district-level agricultural crop production in India from 1997 to 2015."
    },
    {
        "id": "rajanand/rainfall-in-india",
        "name": "Rainfall in India (1901-2015 & District Normals)",
        "url": "https://www.kaggle.com/datasets/rajanand/rainfall-in-india",
        "author": "Raj Anand (India Meteorological Department - IMD source)",
        "license": "CC0: Public Domain / Open Government Data",
        "expected_files": ["district wise rainfall normal.csv", "rainfall in india 1901-2015.csv"],
        "description": "District-wise rainfall normals and monthly historical rainfall statistics for India."
    }
]


def acquire_kagglehub_dataset(dataset_info: dict, target_dir: Path) -> dict:
    """Download a dataset via kagglehub and copy files to raw data directory."""
    dataset_id = dataset_info["id"]
    logger.info("Starting acquisition for: %s (%s)", dataset_info["name"], dataset_id)
    
    target_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "id": dataset_id,
        "name": dataset_info["name"],
        "success": False,
        "files": [],
        "errors": []
    }
    
    download_path = None
    try:
        import kagglehub
        download_path = kagglehub.dataset_download(dataset_id)
        logger.info("Successfully fetched via kagglehub into cache: %s", download_path)
    except Exception as e:
        logger.warning("Kagglehub download failed for %s: %s", dataset_id, e)
        # Try kaggle CLI as fallback
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()
            api.dataset_download_files(dataset_id, path=str(target_dir), unzip=True)
            logger.info("Successfully fetched via Kaggle API into %s", target_dir)
            download_path = str(target_dir)
        except Exception as e_api:
            err_msg = f"Failed to acquire {dataset_id}. KaggleHub error: {e}. Kaggle API error: {e_api}"
            logger.error(err_msg)
            report["errors"].append(err_msg)
            return report

    # Copy files from cache to target_dir if different
    if download_path and Path(download_path) != target_dir:
        for src_file in Path(download_path).iterdir():
            file_name = src_file.name
            dst_file = target_dir / file_name
            if src_file.is_file():
                shutil.copy2(src_file, dst_file)
                logger.info("Copied raw data file: %s -> %s", file_name, dst_file)

    # Inspect contents
    for expected in dataset_info["expected_files"]:
        file_path = target_dir / expected
        if file_path.exists():
            try:
                df = pd.read_csv(file_path, low_memory=False)
                file_summary = {
                    "filename": expected,
                    "rows": len(df),
                    "cols": len(df.columns),
                    "columns": df.columns.tolist(),
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2)
                }
                report["files"].append(file_summary)
                logger.info("Verified file [%s]: %d rows x %d cols (%.2f MB)",
                            expected, len(df), len(df.columns), file_summary["size_mb"])
            except Exception as e:
                err_msg = f"Integrity check failed for {expected}: {e}"
                logger.error(err_msg)
                report["errors"].append(err_msg)
        else:
            err_msg = f"Expected file not found: {expected}"
            logger.warning(err_msg)
            report["errors"].append(err_msg)

    report["success"] = len(report["files"]) > 0
    return report


def run_acquisition():
    """Acquires all configured datasets and outputs summary."""
    configure_logging()
    logger.info("=== KROP DATASET ACQUISITION PIPELINE ===")
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    summary_reports = []
    for meta in DATASETS_METADATA:
        res = acquire_kagglehub_dataset(meta, RAW_DATA_DIR)
        summary_reports.append(res)

    print("\n" + "=" * 60)
    print("ACQUISITION RESULTS SUMMARY:")
    for rep in summary_reports:
        status = "SUCCESS" if rep["success"] else "FAILED"
        print(f"[{status}] {rep['name']} ({rep['id']})")
        for f in rep["files"]:
            print(f"  - {f['filename']}: {f['rows']:,} rows, {f['cols']} cols ({f['size_mb']} MB)")
        if rep["errors"]:
            for err in rep["errors"]:
                print(f"  ! ERROR: {err}")
    print("=" * 60 + "\n")
    return summary_reports


if __name__ == "__main__":
    run_acquisition()
