"""
KROP - Agricultural Utilities and Regional Lookup Module
Provides state/district listings, IMD rainfall normals retrieval, and formatting helpers.
Zero hardware dependencies, absolutely ZERO NPK.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger("krop.utils")

PROCESSED_DATA_PATH = Path("data/processed/clean_crop_rainfall.csv")
DISTRICT_RAIN_PATH = Path("data/raw/district wise rainfall normal.csv")

# Cached lookups
_STATE_DISTRICT_MAP: Optional[Dict[str, List[str]]] = None
_DISTRICT_RAINFALL_MAP: Optional[Dict[Tuple[str, str], Dict[str, float]]] = None
_STATE_RAINFALL_MAP: Optional[Dict[str, Dict[str, float]]] = None


def _init_lookups():
    """Initializes in-memory lookup dictionaries from clean datasets."""
    global _STATE_DISTRICT_MAP, _DISTRICT_RAINFALL_MAP, _STATE_RAINFALL_MAP
    if _STATE_DISTRICT_MAP is not None:
        return

    _STATE_DISTRICT_MAP = {}
    _DISTRICT_RAINFALL_MAP = {}
    _STATE_RAINFALL_MAP = {}

    if PROCESSED_DATA_PATH.exists():
        df = pd.read_csv(PROCESSED_DATA_PATH, low_memory=False)
        grouped = df.groupby("State_Name")["District_Name"].unique()
        for state, dists in grouped.items():
            _STATE_DISTRICT_MAP[str(state)] = sorted(
                [str(d).title() for d in dists if str(d).strip()]
            )

        # Average rainfall per state
        state_rain = df.groupby("State_Name")[
            ["annual_rainfall_mm", "Jun-Sep", "Jan-Feb", "Mar-May", "Oct-Dec"]
        ].mean()
        for state, row in state_rain.iterrows():
            _STATE_RAINFALL_MAP[str(state).upper()] = {
                "annual": float(row["annual_rainfall_mm"]),
                "Jun-Sep": float(row["Jun-Sep"]),
                "Jan-Feb": float(row["Jan-Feb"]),
                "Mar-May": float(row["Mar-May"]),
                "Oct-Dec": float(row["Oct-Dec"]),
            }

        # Average rainfall per district
        dist_rain = df.groupby(["State_Name", "District_Name"])[
            ["annual_rainfall_mm", "Jun-Sep", "Jan-Feb", "Mar-May", "Oct-Dec"]
        ].mean()
        for (st, dist), row in dist_rain.iterrows():
            key = (str(st).upper(), str(dist).upper())
            _DISTRICT_RAINFALL_MAP[key] = {
                "annual": float(row["annual_rainfall_mm"]),
                "Jun-Sep": float(row["Jun-Sep"]),
                "Jan-Feb": float(row["Jan-Feb"]),
                "Mar-May": float(row["Mar-May"]),
                "Oct-Dec": float(row["Oct-Dec"]),
            }


def get_indian_states() -> List[str]:
    """Returns sorted list of Indian States and UTs present in the agricultural records."""
    _init_lookups()
    return sorted(list(_STATE_DISTRICT_MAP.keys())) if _STATE_DISTRICT_MAP else []


def get_districts_for_state(state: str) -> List[str]:
    """Returns sorted list of districts for a specific state."""
    _init_lookups()
    if not _STATE_DISTRICT_MAP:
        return []
    return _STATE_DISTRICT_MAP.get(state, [])


def get_district_rainfall_normals(state: str, district: str) -> Dict[str, float]:
    """Retrieves long-term normal rainfall values (IMD) for a state and district."""
    _init_lookups()
    key = (state.strip().upper(), district.strip().upper())
    if key in _DISTRICT_RAINFALL_MAP:
        return _DISTRICT_RAINFALL_MAP[key]

    # Partial match on district
    for (st, dist), vals in _DISTRICT_RAINFALL_MAP.items():
        if st == state.strip().upper() and (
            district.strip().upper() in dist or dist in district.strip().upper()
        ):
            return vals

    # Fallback to state average
    st_upper = state.strip().upper()
    if st_upper in _STATE_RAINFALL_MAP:
        return _STATE_RAINFALL_MAP[st_upper]

    # National average fallback
    return {
        "annual": 1100.0,
        "Jun-Sep": 750.0,
        "Jan-Feb": 40.0,
        "Mar-May": 120.0,
        "Oct-Dec": 190.0,
    }


def compute_seasonal_rainfall(normals: Dict[str, float], season: str) -> float:
    """Computes expected seasonal rainfall in mm based on season and IMD normals."""
    s = season.strip().title()
    if s == "Kharif":
        return normals.get("Jun-Sep", 750.0)
    elif s == "Rabi":
        return normals.get("Jan-Feb", 40.0) + normals.get("Oct-Dec", 190.0)
    elif s in ["Summer", "Zaid"]:
        return normals.get("Mar-May", 120.0)
    else:  # Whole Year
        return normals.get("annual", 1100.0)


if __name__ == "__main__":
    states = get_indian_states()
    print("Found states:", len(states))
    if states:
        sample_st = "Maharashtra"
        sample_dists = get_districts_for_state(sample_st)
        print(f"Districts in {sample_st}: {len(sample_dists)}, sample: {sample_dists[:5]}")
        pune_rain = get_district_rainfall_normals(sample_st, "Pune")
        print("Pune normals:", pune_rain)
        kharif_rain = compute_seasonal_rainfall(pune_rain, "Kharif")
        print("Pune Kharif expected rainfall:", kharif_rain, "mm")
