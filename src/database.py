"""
KROP - Persistent SQLite Database Module
Manages farm profiles and historical crop recommendations with ACID compliance.
Zero hardware dependencies, purely software-driven, strictly zero NPK.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("krop.database")

DATABASE_DIR = Path("database")
DB_PATH = DATABASE_DIR / "krop.db"


class DatabaseManager:
    """Manages SQLite operations for KROP farm profiles and recommendation records."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with row factory configured."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
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
            conn.commit()
            logger.info("Database schema initialized at %s", self.db_path)

    # ------------------ FARM PROFILES CRUD ------------------ #

    def save_farm_profile(self, profile: Dict[str, Any]) -> int:
        """Saves a new farm profile and returns the record ID."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO farm_profiles (
                    location, village, district, state, latitude, longitude,
                    land_area, land_unit, soil_type, irrigation_method,
                    water_availability, preferred_season, crop_preferences,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.get("location", ""),
                profile.get("village", ""),
                profile.get("district", ""),
                profile.get("state", ""),
                profile.get("latitude"),
                profile.get("longitude"),
                float(profile.get("land_area", 1.0)),
                profile.get("land_unit", "Acres"),
                profile.get("soil_type", "Unknown"),
                profile.get("irrigation_method", "Rain-fed"),
                profile.get("water_availability", "Moderate"),
                profile.get("preferred_season", "Kharif"),
                profile.get("crop_preferences", "No preference"),
                now,
                now
            ))
            conn.commit()
            return cursor.lastrowid

    def update_farm_profile(self, profile_id: int, profile: Dict[str, Any]) -> bool:
        """Updates an existing farm profile by ID."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE farm_profiles SET
                    location = ?, village = ?, district = ?, state = ?,
                    latitude = ?, longitude = ?, land_area = ?, land_unit = ?,
                    soil_type = ?, irrigation_method = ?, water_availability = ?,
                    preferred_season = ?, crop_preferences = ?, updated_at = ?
                WHERE id = ?
            """, (
                profile.get("location", ""),
                profile.get("village", ""),
                profile.get("district", ""),
                profile.get("state", ""),
                profile.get("latitude"),
                profile.get("longitude"),
                float(profile.get("land_area", 1.0)),
                profile.get("land_unit", "Acres"),
                profile.get("soil_type", "Unknown"),
                profile.get("irrigation_method", "Rain-fed"),
                profile.get("water_availability", "Moderate"),
                profile.get("preferred_season", "Kharif"),
                profile.get("crop_preferences", "No preference"),
                now,
                profile_id
            ))
            conn.commit()
            return cursor.rowcount > 0

    def get_farm_profile(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a farm profile by its primary key ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farm_profiles WHERE id = ?", (profile_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_latest_farm_profile(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recently saved or updated farm profile."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farm_profiles ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_farm_profiles(self) -> List[Dict[str, Any]]:
        """Retrieves all farm profiles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farm_profiles ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_farm_profile(self, profile_id: int) -> bool:
        """Deletes a farm profile by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM farm_profiles WHERE id = ?", (profile_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ------------------ RECOMMENDATIONS CRUD ------------------ #

    def save_recommendation(
        self,
        farm_profile_id: Optional[int],
        recommended_crops: List[Dict[str, Any]],
        weather_summary: Optional[Dict[str, Any]],
        recommendation_details: Dict[str, Any],
        model_version: str = "1.0.0"
    ) -> int:
        """Saves a generated recommendation into history."""
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recommendations (
                    farm_profile_id, recommended_crops, weather_summary,
                    recommendation_details, model_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                farm_profile_id,
                json.dumps(recommended_crops),
                json.dumps(weather_summary or {}),
                json.dumps(recommendation_details),
                model_version,
                now
            ))
            conn.commit()
            return cursor.lastrowid

    def get_recommendation(self, rec_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single recommendation record with parsed JSON fields."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, p.village, p.district, p.state, p.land_area, p.land_unit, p.soil_type
                FROM recommendations r
                LEFT JOIN farm_profiles p ON r.farm_profile_id = p.id
                WHERE r.id = ?
            """, (rec_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["recommended_crops"] = json.loads(data["recommended_crops"])
            data["weather_summary"] = json.loads(data["weather_summary"])
            data["recommendation_details"] = json.loads(data["recommendation_details"])
            return data

    def get_recommendation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves historical recommendations ordered by creation date."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, p.village, p.district, p.state, p.land_area, p.land_unit, p.soil_type
                FROM recommendations r
                LEFT JOIN farm_profiles p ON r.farm_profile_id = p.id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                try:
                    item["recommended_crops"] = json.loads(item["recommended_crops"])
                    item["weather_summary"] = json.loads(item["weather_summary"])
                    item["recommendation_details"] = json.loads(item["recommendation_details"])
                except Exception:
                    pass
                results.append(item)
            return results

    def delete_recommendation(self, rec_id: int) -> bool:
        """Deletes a recommendation record by primary key."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recommendations WHERE id = ?", (rec_id,))
            conn.commit()
            return cursor.rowcount > 0


if __name__ == "__main__":
    db = DatabaseManager()
    p_id = db.save_farm_profile({
        "village": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "land_area": 3.0,
        "land_unit": "Acres",
        "soil_type": "Black soil",
        "irrigation_method": "Borewell",
        "water_availability": "Moderate",
        "preferred_season": "Kharif",
        "crop_preferences": "Cash/Commercial Crops"
    })
    print("Inserted test farm profile ID:", p_id)
    retrieved = db.get_farm_profile(p_id)
    print("Retrieved profile:", retrieved["district"], retrieved["state"])
    rec_id = db.save_recommendation(
        farm_profile_id=p_id,
        recommended_crops=[{"crop_name": "Cotton(lint)", "rank": 1, "composite_score": 85.0}],
        weather_summary={"temperature_c": 28.5},
        recommendation_details={"status": "success"},
        model_version="1.0.0"
    )
    print("Inserted test recommendation ID:", rec_id)
    history = db.get_recommendation_history(5)
    print("History count:", len(history))
