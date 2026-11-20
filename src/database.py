"""
KROP - Persistent SQLite Database Module
Manages farm profiles and historical crop recommendations with ACID compliance.
Zero hardware dependencies, purely software-driven, strictly zero NPK.
"""

import json
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from src.config import MODEL_VERSION, get_database_path

logger = logging.getLogger("krop.database")

PROFILE_FIELDS = (
    "location", "village", "district", "state", "latitude", "longitude",
    "land_area", "land_unit", "soil_type", "irrigation_method",
    "water_availability", "preferred_season", "crop_preferences",
)

_PROFILE_DEFAULTS: Dict[str, Any] = {
    "location": "",
    "village": "",
    "district": "",
    "state": "",
    "latitude": None,
    "longitude": None,
    "land_area": 1.0,
    "land_unit": "Acres",
    "soil_type": "Unknown",
    "irrigation_method": "Rain-fed",
    "water_availability": "Moderate",
    "preferred_season": "Kharif",
    "crop_preferences": "No preference",
}


def _profile_values(profile: Dict[str, Any]) -> tuple:
    """Extracts profile column values in PROFILE_FIELDS order, applying defaults."""
    values = []
    for field in PROFILE_FIELDS:
        value = profile.get(field)
        if value is None and field not in ("latitude", "longitude"):
            value = _PROFILE_DEFAULTS[field]
        if field == "land_area":
            value = float(value)
        values.append(value)
    return tuple(values)


class DatabaseManager:
    """Manages SQLite operations for KROP farm profiles and recommendation records."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else get_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Yields a SQLite connection with row factory and foreign keys configured.
        Commits on success, rolls back on error, and always closes the connection.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initializes database tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Farm Profiles Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS farm_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location TEXT,
                    village TEXT,
                    district TEXT NOT NULL,
                    state TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    land_area REAL NOT NULL,
                    land_unit TEXT NOT NULL,
                    soil_type TEXT,
                    irrigation_method TEXT,
                    water_availability TEXT,
                    preferred_season TEXT,
                    crop_preferences TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Recommendations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_profile_id INTEGER,
                    recommended_crops TEXT NOT NULL,
                    weather_summary TEXT,
                    recommendation_details TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (farm_profile_id) REFERENCES farm_profiles(id) ON DELETE SET NULL
                );
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_recommendations_created ON recommendations(created_at DESC);"
            )
            logger.info("Database schema initialized at %s", self.db_path)

    # ------------------ FARM PROFILES CRUD ------------------ #

    def save_farm_profile(self, profile: Dict[str, Any]) -> int:
        """Saves a new farm profile and returns the record ID."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"""
                INSERT INTO farm_profiles ({", ".join(PROFILE_FIELDS)}, created_at, updated_at)
                VALUES ({", ".join("?" * (len(PROFILE_FIELDS) + 2))})
                """,
                (*_profile_values(profile), now, now),
            )
            return cursor.lastrowid

    def update_farm_profile(self, profile_id: int, profile: Dict[str, Any]) -> bool:
        """Updates an existing farm profile by ID."""
        assignments = ", ".join(f"{field} = ?" for field in PROFILE_FIELDS)
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE farm_profiles SET {assignments}, updated_at = ? WHERE id = ?",
                (*_profile_values(profile), datetime.now().isoformat(), profile_id),
            )
            return cursor.rowcount > 0

    def get_farm_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a farm profile by its primary key ID."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM farm_profiles WHERE id = ?", (profile_id,)).fetchone()
            return dict(row) if row else None

    def get_latest_farm_profile(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recently saved or updated farm profile."""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM farm_profiles ORDER BY updated_at DESC, id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def get_all_farm_profiles(self) -> List[Dict[str, Any]]:
        """Retrieves all farm profiles."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM farm_profiles ORDER BY updated_at DESC, id DESC").fetchall()
            return [dict(row) for row in rows]

    def delete_farm_profile(self, profile_id: int) -> bool:
        """Deletes a farm profile by ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM farm_profiles WHERE id = ?", (profile_id,))
            return cursor.rowcount > 0

    # ------------------ RECOMMENDATIONS CRUD ------------------ #

    _RECOMMENDATION_SELECT = """
        SELECT r.*, p.village, p.district, p.state, p.land_area, p.land_unit, p.soil_type
        FROM recommendations r
        LEFT JOIN farm_profiles p ON r.farm_profile_id = p.id
    """

    @staticmethod
    def _decode_recommendation(row: sqlite3.Row) -> Dict[str, Any]:
        """Converts a recommendation row to a dict with JSON columns parsed (tolerating corrupt JSON)."""
        item = dict(row)
        defaults = {"recommended_crops": [], "weather_summary": {}, "recommendation_details": {}}
        for column, default in defaults.items():
            try:
                item[column] = json.loads(item[column]) if item.get(column) else default
            except (TypeError, ValueError):
                logger.warning("Corrupt JSON in recommendations.%s for id=%s", column, item.get("id"))
                item[column] = default
        return item

    def save_recommendation(
        self,
        farm_profile_id: Optional[int],
        recommended_crops: List[Dict[str, Any]],
        weather_summary: Optional[Dict[str, Any]],
        recommendation_details: Dict[str, Any],
        model_version: str = MODEL_VERSION,
    ) -> int:
        """Saves a generated recommendation into history (unlinked if the profile no longer exists)."""
        with self.get_connection() as conn:
            if farm_profile_id is not None and not conn.execute(
                "SELECT 1 FROM farm_profiles WHERE id = ?", (farm_profile_id,)
            ).fetchone():
                logger.warning("Farm profile %s not found; saving recommendation unlinked.", farm_profile_id)
                farm_profile_id = None
            cursor = conn.execute(
                """
                INSERT INTO recommendations (
                    farm_profile_id, recommended_crops, weather_summary,
                    recommendation_details, model_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    farm_profile_id,
                    json.dumps(recommended_crops),
                    json.dumps(weather_summary or {}),
                    json.dumps(recommendation_details),
                    model_version,
                    datetime.now().isoformat(),
                ),
            )
            return cursor.lastrowid

    def get_recommendation(self, rec_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single recommendation record with parsed JSON fields."""
        with self.get_connection() as conn:
            row = conn.execute(f"{self._RECOMMENDATION_SELECT} WHERE r.id = ?", (rec_id,)).fetchone()
            return self._decode_recommendation(row) if row else None

    def get_recommendation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves historical recommendations, newest first."""
        with self.get_connection() as conn:
            rows = conn.execute(
                f"{self._RECOMMENDATION_SELECT} ORDER BY r.created_at DESC, r.id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [self._decode_recommendation(row) for row in rows]

    def count_recommendations(self) -> int:
        """Returns the total number of stored recommendation records."""
        with self.get_connection() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0])

    def delete_recommendation(self, rec_id: int) -> bool:
        """Deletes a recommendation record by primary key."""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
            return cursor.rowcount > 0
