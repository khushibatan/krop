"""
KROP - Agricultural Utilities and Regional Lookup Module
Provides state/district listings, IMD rainfall normals retrieval, and formatting helpers.
Zero hardware dependencies, absolutely ZERO NPK.
"""

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd

from src.config import CLEAN_DATASET_PATH

logger = logging.getLogger("krop.utils")

PROCESSED_DATA_PATH = CLEAN_DATASET_PATH

RAIN_COLUMNS = ["annual_rainfall_mm", "Jun-Sep", "Jan-Feb", "Mar-May", "Oct-Dec"]

# National fallback normals (mm) used only when neither district nor state data is available.
NATIONAL_AVERAGE_NORMALS: Dict[str, float] = {
    "annual": 1100.0,
    "Jun-Sep": 750.0,
    "Jan-Feb": 40.0,
    "Mar-May": 120.0,
    "Oct-Dec": 190.0,
}

# Cached lookups
_STATE_DISTRICT_MAP: Optional[Dict[str, List[str]]] = None
_DISTRICT_RAINFALL_MAP: Optional[Dict[Tuple[str, str], Dict[str, float]]] = None
_STATE_RAINFALL_MAP: Optional[Dict[str, Dict[str, float]]] = None


def _row_to_normals(row: pd.Series) -> Dict[str, float]:
    return {
        "annual": float(row["annual_rainfall_mm"]),
        "Jun-Sep": float(row["Jun-Sep"]),
        "Jan-Feb": float(row["Jan-Feb"]),
        "Mar-May": float(row["Mar-May"]),
        "Oct-Dec": float(row["Oct-Dec"]),
    }


def _init_lookups() -> None:
    """Initializes in-memory lookup dictionaries from the clean dataset (once per process)."""
    global _STATE_DISTRICT_MAP, _DISTRICT_RAINFALL_MAP, _STATE_RAINFALL_MAP
    if _STATE_DISTRICT_MAP is not None:
        return

    state_districts: Dict[str, List[str]] = {}
    district_rain: Dict[Tuple[str, str], Dict[str, float]] = {}
    state_rain: Dict[str, Dict[str, float]] = {}

    if PROCESSED_DATA_PATH.exists():
        df = pd.read_csv(
            PROCESSED_DATA_PATH,
            usecols=["State_Name", "District_Name", *RAIN_COLUMNS],
            low_memory=False,
        )
        for state, dists in df.groupby("State_Name")["District_Name"].unique().items():
            state_districts[str(state)] = sorted(
                {str(d).strip().title() for d in dists if str(d).strip()}
            )

        for state, row in df.groupby("State_Name")[RAIN_COLUMNS].mean().iterrows():
            state_rain[str(state).strip().upper()] = _row_to_normals(row)

        grouped = df.groupby(["State_Name", "District_Name"])[RAIN_COLUMNS].mean()
        for (st, dist), row in grouped.iterrows():
            district_rain[(str(st).strip().upper(), str(dist).strip().upper())] = _row_to_normals(row)
    else:
        logger.warning("Processed dataset not found at %s; regional lookups are empty.", PROCESSED_DATA_PATH)

    _STATE_DISTRICT_MAP, _DISTRICT_RAINFALL_MAP, _STATE_RAINFALL_MAP = (
        state_districts, district_rain, state_rain,
    )


def get_indian_states() -> List[str]:
    """Returns sorted list of Indian States and UTs present in the agricultural records."""
    _init_lookups()
    return sorted(_STATE_DISTRICT_MAP)


def get_districts_for_state(state: str) -> List[str]:
    """Returns sorted list of districts for a specific state."""
    _init_lookups()
    return _STATE_DISTRICT_MAP.get(state, [])


def get_district_rainfall_normals(state: str, district: str) -> Dict[str, float]:
    """
    Retrieves long-term normal rainfall values (IMD) for a state and district.
    Resolution order: exact district -> partial district name -> state average -> national average.
    """
    _init_lookups()
    st_upper = (state or "").strip().upper()
    dist_upper = (district or "").strip().upper()

    if dist_upper:
        exact = _DISTRICT_RAINFALL_MAP.get((st_upper, dist_upper))
        if exact:
            return exact

        for (st, dist), vals in _DISTRICT_RAINFALL_MAP.items():
            if st == st_upper and (dist_upper in dist or dist in dist_upper):
                return vals

    if st_upper in _STATE_RAINFALL_MAP:
        return _STATE_RAINFALL_MAP[st_upper]

    return dict(NATIONAL_AVERAGE_NORMALS)


def compute_seasonal_rainfall(normals: Dict[str, float], season: str) -> float:
    """Computes expected seasonal rainfall in mm based on season and IMD normals."""
    s = (season or "").strip().title()
    if s == "Kharif":
        return normals.get("Jun-Sep", NATIONAL_AVERAGE_NORMALS["Jun-Sep"])
    if s == "Rabi":
        return normals.get("Jan-Feb", NATIONAL_AVERAGE_NORMALS["Jan-Feb"]) + normals.get(
            "Oct-Dec", NATIONAL_AVERAGE_NORMALS["Oct-Dec"]
        )
    if s in ("Summer", "Zaid"):
        return normals.get("Mar-May", NATIONAL_AVERAGE_NORMALS["Mar-May"])
    return normals.get("annual", NATIONAL_AVERAGE_NORMALS["annual"])  # Whole Year


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
