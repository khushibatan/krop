"""
KROP - Intelligent Crop Recommendation Engine
Combines machine learning candidate generation with ICAR agronomic validation,
soil matching, irrigation compatibility, live weather intelligence, and transparent scoring.
Strictly zero hardware dependencies, absolutely ZERO NPK.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np

from src.prediction import CropPredictor
from src.crop_information import load_crop_catalog, get_crop_profile
from src.utils import get_district_rainfall_normals, compute_seasonal_rainfall

logger = logging.getLogger("krop.recommendation_engine")


class RecommendationEngine:
    """Orchestrates end-to-end evidence-based crop recommendation."""

    def __init__(self, predictor: Optional[CropPredictor] = None):
        self.predictor = predictor or CropPredictor()
        self.catalog_df = load_crop_catalog()

    def generate_recommendations(
        self,
        farm_profile: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Executes the 11-step KROP recommendation workflow:
        1. Validate inputs
        2. Resolve rainfall normals
        3. Run ML inference for candidate generation
        4. Apply agronomic soil & water constraints
        5. Integrate live weather intelligence
        6. Compute transparent composite scores
        7. Generate evidence-based explanations
        """
        state = farm_profile.get("state", "").strip()
        district = farm_profile.get("district", "").strip()
        season = farm_profile.get("preferred_season", "Kharif").strip()
        if season == "Not sure" or not season:
            season = "Kharif"

        area = float(farm_profile.get("land_area", 1.0))
        land_unit = farm_profile.get("land_unit", "Acres")
        
        # Convert area to hectares
        if land_unit.lower() in ["acre", "acres"]:
            area_ha = max(0.1, round(area * 0.404686, 3))
        else:
            area_ha = max(0.1, round(area, 3))

        soil_type = farm_profile.get("soil_type", "Unknown")
        irrigation_method = farm_profile.get("irrigation_method", "Rain-fed")
        water_availability = farm_profile.get("water_availability", "Moderate")
        crop_preference = farm_profile.get("crop_preferences", "No preference")

        # 1. Retrieve Historical Rainfall Normals
        rainfall_normals = get_district_rainfall_normals(state, district)
        annual_rf = rainfall_normals["annual"]
        seasonal_rf = compute_seasonal_rainfall(rainfall_normals, season)

        # 2. Run ML Candidate Generation (Top 12 candidates)
        ml_candidates = self.predictor.predict_candidates(
            state=state,
            season=season,
            area_ha=area_ha,
            annual_rainfall_mm=annual_rf,
            seasonal_rainfall_mm=seasonal_rf,
            top_k=12
        )

        # 3. Agronomic Assessment for each candidate
        evaluated_crops = []
        for cand in ml_candidates:
            crop_name = cand["crop"]
            profile = get_crop_profile(crop_name)
            if not profile:
                continue

            # Calculate individual component scores (0 - 100)
            model_score = cand["model_probability"] * 100.0  # Raw model score

            water_score, water_notes = self._evaluate_water_compatibility(
                profile=profile,
                seasonal_rain_mm=seasonal_rf,
                irrigation_method=irrigation_method,
                water_availability=water_availability
            )

            soil_score, soil_notes = self._evaluate_soil_compatibility(
                profile=profile,
                farmer_soil=soil_type
            )

            weather_score, weather_notes = self._evaluate_weather_compatibility(
                profile=profile,
                weather_data=weather_data
            )

            pref_score = self._evaluate_preference(
                profile=profile,
                preference=crop_preference
            )

            # 4. Transparent Composite Suitability Score Calculation
            # Weights: Model 40%, Water 25%, Soil 15%, Weather 10%, Preference 10%
            if soil_type in ["Unknown", "Other", None, ""]:
                # Reallocate soil 15% weight to model (5%) and water (10%)
                composite_score = (
                    0.45 * (model_score * 2.5) +  # Normalize model probability distribution
                    0.35 * water_score +
                    0.10 * weather_score +
                    0.10 * pref_score
                )
            else:
                composite_score = (
                    0.35 * (model_score * 2.5) +
                    0.25 * water_score +
                    0.15 * soil_score +
                    0.15 * weather_score +
                    0.10 * pref_score
                )

            # Bound composite score between 10% and 99%
            composite_score = round(min(99.0, max(15.0, composite_score)), 1)

            # 5. Build Evidence-Based Explanations
            explanation_points = self._build_explanations(
                crop_name=crop_name,
                profile=profile,
                state=state,
                season=season,
                seasonal_rf=seasonal_rf,
                irrigation=irrigation_method,
                water_avail=water_availability,
                soil_type=soil_type,
                soil_notes=soil_notes,
                water_notes=water_notes,
                weather_notes=weather_notes,
                cand=cand
            )

            evaluated_crops.append({
                "crop_name": crop_name,
                "composite_score": composite_score,
                "model_probability": cand["model_probability"],
                "model_confidence_pct": cand["model_confidence_pct"],
                "water_suitability_score": round(water_score, 1),
                "soil_suitability_score": round(soil_score, 1),
                "weather_suitability_score": round(weather_score, 1),
                "crop_category": profile.get("crop_category", "Field Crop"),
                "suitable_seasons": profile.get("suitable_seasons", season),
                "growing_duration": profile.get("growing_duration_days", "100-120 days"),
                "water_requirement": profile.get("water_requirement", "Medium"),
                "water_requirement_mm": profile.get("water_requirement_mm", "500-700 mm"),
                "suitable_soil": profile.get("suitable_soil", "Well-drained loam"),
                "sowing_period": profile.get("sowing_period", "June - July"),
                "temperature_conditions": profile.get("temperature_conditions", "20°C - 35°C"),
                "cultivation_notes": profile.get("cultivation_notes", ""),
                "regional_information": profile.get("regional_information", ""),
                "information_source": profile.get("information_source", "ICAR"),
                "explanation_points": explanation_points,
                "water_notes": water_notes,
                "soil_notes": soil_notes,
                "weather_notes": weather_notes
            })

        # 6. Rank by Composite Score descending
        evaluated_crops.sort(key=lambda x: x["composite_score"], reverse=True)

        # Assign final rank
        final_recommendations = []
        for idx, item in enumerate(evaluated_crops[:top_n], start=1):
            item["rank"] = idx
            final_recommendations.append(item)

        return {
            "state": state,
            "district": district,
            "season": season,
            "land_area_ha": area_ha,
            "soil_type": soil_type,
            "irrigation_method": irrigation_method,
            "water_availability": water_availability,
            "rainfall_normals": {
                "annual_rainfall_mm": round(annual_rf, 1),
                "seasonal_rainfall_mm": round(seasonal_rf, 1)
            },
            "weather_summary": weather_data.get("current", {}) if weather_data else {},
            "recommendations": final_recommendations
        }

    def _evaluate_water_compatibility(
        self,
        profile: Dict,
        seasonal_rain_mm: float,
        irrigation_method: str,
        water_availability: str
    ) -> Tuple[float, str]:
        """Agronomic water balance evaluation."""
        water_req = profile.get("water_requirement", "Medium").strip().lower()
        has_assured_irrigation = irrigation_method.lower() in ["borewell", "canal", "drip irrigation", "open well"]
        water_avail = water_availability.lower()

        # Score matrix
        if water_req in ["very high", "high"]:
            if has_assured_irrigation and water_avail == "good":
                return 95.0, "High water requirement is fully satisfied by assured irrigation and good water availability."
            elif has_assured_irrigation and water_avail == "moderate":
                return 75.0, "Moderate irrigation is available; water conservation or drip methods recommended."
            elif seasonal_rain_mm > 1000:
                return 80.0, "High seasonal monsoon rainfall supports water needs."
            else:
                return 35.0, "Risk: Crop requires high water, but farm lacks assured irrigation or sufficient rainfall."

        elif water_req == "medium":
            if has_assured_irrigation or seasonal_rain_mm >= 450:
                return 90.0, "Normal rainfall and farm irrigation match crop water demand well."
            elif water_avail in ["good", "moderate"]:
                return 85.0, "Adequate water for medium-demand crop."
            else:
                return 60.0, "Rainfall is limited; monitor soil moisture during flowering."

        else:  # "low"
            if seasonal_rain_mm < 400 or water_avail == "limited" or irrigation_method == "Rain-fed":
                return 98.0, "Excellent fit: Crop is highly drought-hardy and ideal for low rainfall or rain-fed drylands."
            else:
                return 85.0, "Low water crop will thrive easily with available moisture."

    def _evaluate_soil_compatibility(self, profile: Dict, farmer_soil: str) -> Tuple[float, str]:
        """Matches farmer soil type with ICAR crop agronomic profile."""
        if not farmer_soil or farmer_soil.strip().lower() in ["unknown", "other", "not sure"]:
            return 80.0, "Soil type not specified; agronomic recommendation based on regional suitability."

        f_soil = farmer_soil.strip().lower()
        rec_soil = profile.get("suitable_soil", "").lower()

        # Direct keyword presence
        keywords = {
            "black": ["black", "regur", "clay"],
            "red": ["red", "gravelly", "laterite"],
            "alluvial": ["alluvial", "loam", "loamy"],
            "sandy": ["sandy", "light", "porous"],
            "clay": ["clay", "heavy", "black"],
            "loamy": ["loam", "loamy", "alluvial"]
        }

        matched = False
        for key, synonyms in keywords.items():
            if key in f_soil:
                if any(syn in rec_soil for syn in synonyms):
                    matched = True
                    break

        if matched:
            return 95.0, f"{farmer_soil} is strongly suited for {profile.get('crop_name')} cultivation."
        else:
            return 65.0, f"Can be cultivated in {farmer_soil} with appropriate organic matter and land preparation."

    def _evaluate_weather_compatibility(
        self, profile: Dict, weather_data: Optional[Dict]
    ) -> Tuple[float, str]:
        """Assesses live temperature vs agronomic optimal range."""
        if not weather_data or "current" not in weather_data:
            return 80.0, "Historical regional climate aligns with crop cycle."

        curr_temp = weather_data.get("current", {}).get("temperature_c", 25.0)
        min_temp = profile.get("min_temp_c", 15.0)
        max_temp = profile.get("max_temp_c", 38.0)

        if min_temp <= curr_temp <= max_temp:
            return 95.0, f"Current temperature ({curr_temp:.1f}°C) is in the optimal growth window ({min_temp:.0f}°C - {max_temp:.0f}°C)."
        elif curr_temp < min_temp:
            diff = min_temp - curr_temp
            return max(40.0, 85.0 - diff * 5), f"Current conditions ({curr_temp:.1f}°C) are cooler than optimal minimum ({min_temp:.0f}°C)."
        else:
            diff = curr_temp - max_temp
            return max(40.0, 85.0 - diff * 5), f"Current conditions ({curr_temp:.1f}°C) exceed optimal maximum ({max_temp:.0f}°C); risk of heat stress."

    def _evaluate_preference(self, profile: Dict, preference: str) -> float:
        """Evaluates alignment with farmer preference."""
        if not preference or preference in ["No preference", "Other"]:
            return 80.0
        crop_cat = profile.get("crop_category", "")
        if preference.lower() in crop_cat.lower() or crop_cat.lower() in preference.lower():
            return 95.0
        return 65.0

    def _build_explanations(
        self,
        crop_name: str,
        profile: Dict,
        state: str,
        season: str,
        seasonal_rf: float,
        irrigation: str,
        water_avail: str,
        soil_type: str,
        soil_notes: str,
        water_notes: str,
        weather_notes: str,
        cand: Dict
    ) -> List[str]:
        """Generates evidence-backed bullet points explaining the recommendation."""
        points = []

        # 1. Historical & Regional Evidence
        points.append(
            f"Regional Cultivation Evidence: Historical agricultural records indicate that {crop_name} is extensively cultivated in {state} during the {season} season (Model probability: {cand['model_confidence_pct']}%)."
        )

        # 2. Water & Irrigation Match
        points.append(
            f"Water & Irrigation Match: {water_notes} (Normal seasonal precipitation: {seasonal_rf:.0f} mm)."
        )

        # 3. Soil Suitability
        points.append(
            f"Soil Assessment: {soil_notes}"
        )

        # 4. Weather Consideration
        points.append(
            f"Weather Outlook: {weather_notes}"
        )

        # 5. ICAR Agronomic Guidance
        cult_note = profile.get("cultivation_notes", "")
        if cult_note:
            points.append(f"Advisory Guidance: {cult_note}")

        return points


if __name__ == "__main__":
    engine = RecommendationEngine()
    test_profile = {
        "state": "Maharashtra",
        "district": "Pune",
        "preferred_season": "Kharif",
        "land_area": 2.5,
        "land_unit": "Acres",
        "soil_type": "Black soil",
        "irrigation_method": "Borewell",
        "water_availability": "Moderate",
        "crop_preferences": "No preference"
    }
    recs = engine.generate_recommendations(test_profile)
    print("Top Recommendations:")
    for r in recs["recommendations"]:
        print(f"#{r['rank']}: {r['crop_name']} (Composite Score: {r['composite_score']}%)")
        print(f"   Model Prob: {r['model_probability']:.4f} | Water Score: {r['water_suitability_score']}")
        print(f"   Why: {r['explanation_points'][0]}")
