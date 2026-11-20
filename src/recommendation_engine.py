"""
KROP - Intelligent Crop Recommendation Engine
Combines machine learning candidate generation with ICAR agronomic validation,
soil matching, irrigation compatibility, live weather intelligence, and transparent scoring.
Strictly zero hardware dependencies, absolutely ZERO NPK.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from src.crop_information import get_crop_profile, is_suitable_for_season
from src.feature_engineering import convert_to_hectares
from src.prediction import CropPredictor
from src.utils import compute_seasonal_rainfall, get_district_rainfall_normals

logger = logging.getLogger("krop.recommendation_engine")

# Number of ML candidates (after seasonal eligibility filtering) passed to agronomic validation.
CANDIDATE_POOL_SIZE = 12

# Composite score weights. Each set sums to 1.0.
WEIGHTS_WITH_SOIL = {"model": 0.35, "water": 0.25, "soil": 0.15, "weather": 0.15, "preference": 0.10}
# When soil is unknown, its 15% is redistributed: +5% to the model and +10% to water balance.
WEIGHTS_WITHOUT_SOIL = {"model": 0.40, "water": 0.35, "soil": 0.0, "weather": 0.15, "preference": 0.10}

ASSURED_IRRIGATION = {"borewell", "canal", "drip irrigation", "open well"}
UNSPECIFIED_SOIL = {"", "unknown", "other", "not sure"}
UNSPECIFIED_PREFERENCE = {"", "no preference", "other"}

# Farmer soil class -> keywords that indicate a match in a crop's ICAR soil description.
SOIL_KEYWORDS = {
    "black": ["black", "regur", "clay"],
    "red": ["red", "gravelly", "laterite"],
    "laterite": ["laterite", "red", "gravelly"],
    "alluvial": ["alluvial", "loam"],
    "sandy": ["sandy", "light", "porous"],
    "clay": ["clay", "heavy", "black"],
    "loamy": ["loam", "alluvial"],
}


def _is_soil_specified(soil_type: Optional[str]) -> bool:
    return (soil_type or "").strip().lower() not in UNSPECIFIED_SOIL


class RecommendationEngine:
    """Orchestrates end-to-end evidence-based crop recommendation."""

    def __init__(self, predictor: Optional[CropPredictor] = None):
        self.predictor = predictor or CropPredictor()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def generate_recommendations(
        self,
        farm_profile: Dict[str, Any],
        weather_data: Optional[Dict[str, Any]] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """
        Runs the KROP recommendation workflow:
        1. Normalize the farm profile (season, units, categorical inputs)
        2. Resolve IMD rainfall normals for the district
        3. Generate ML candidates and keep those eligible for the season
        4. Score water, soil, live-weather and preference compatibility per candidate
        5. Combine into a transparent composite score and rank
        6. Attach plain-language evidence for each recommendation
        """
        state = (farm_profile.get("state") or "").strip()
        district = (farm_profile.get("district") or "").strip()
        season = (farm_profile.get("preferred_season") or "").strip()
        if not season or season.lower() == "not sure":
            season = "Kharif"

        area_ha = max(0.1, convert_to_hectares(
            float(farm_profile.get("land_area") or 1.0),
            farm_profile.get("land_unit") or "Acres",
        ))

        soil_type = farm_profile.get("soil_type") or "Unknown"
        irrigation_method = farm_profile.get("irrigation_method") or "Rain-fed"
        water_availability = farm_profile.get("water_availability") or "Moderate"
        crop_preference = farm_profile.get("crop_preferences") or "No preference"

        rainfall_normals = get_district_rainfall_normals(state, district)
        annual_rf = rainfall_normals["annual"]
        seasonal_rf = compute_seasonal_rainfall(rainfall_normals, season)

        candidates = self._eligible_candidates(state, season, annual_rf, seasonal_rf)
        top_probability = max((c["model_probability"] for c in candidates), default=0.0)

        weights = WEIGHTS_WITH_SOIL if _is_soil_specified(soil_type) else WEIGHTS_WITHOUT_SOIL

        evaluated: List[Dict[str, Any]] = []
        for cand in candidates:
            profile = cand["profile"]
            crop_name = profile["crop_name"]

            # Raw probabilities are spread over 33 classes, so each is expressed relative to the
            # strongest eligible candidate. The square root keeps runners-up visible when a single
            # staple dominates the region, putting the score on the same 0-100 scale as the others.
            model_score = (
                100.0 * (cand["model_probability"] / top_probability) ** 0.5 if top_probability else 0.0
            )

            water_score, water_notes = self._evaluate_water_compatibility(
                profile, seasonal_rf, irrigation_method, water_availability
            )
            soil_score, soil_notes = self._evaluate_soil_compatibility(profile, soil_type)
            weather_score, weather_notes = self._evaluate_weather_compatibility(profile, weather_data)
            pref_score = self._evaluate_preference(profile, crop_preference)

            composite = (
                weights["model"] * model_score
                + weights["water"] * water_score
                + weights["soil"] * soil_score
                + weights["weather"] * weather_score
                + weights["preference"] * pref_score
            )
            composite = round(min(100.0, max(0.0, composite)), 1)

            evaluated.append({
                "crop_name": crop_name,
                "composite_score": composite,
                "model_probability": cand["model_probability"],
                "model_confidence_pct": cand["model_confidence_pct"],
                "model_score": round(model_score, 1),
                "water_suitability_score": round(water_score, 1),
                "soil_suitability_score": round(soil_score, 1),
                "weather_suitability_score": round(weather_score, 1),
                "preference_score": round(pref_score, 1),
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
                "explanation_points": self._build_explanations(
                    crop_name=crop_name,
                    profile=profile,
                    state=state,
                    season=season,
                    seasonal_rf=seasonal_rf,
                    soil_notes=soil_notes,
                    water_notes=water_notes,
                    weather_notes=weather_notes,
                    cand=cand,
                ),
                "water_notes": water_notes,
                "soil_notes": soil_notes,
                "weather_notes": weather_notes,
            })

        evaluated.sort(key=lambda c: (c["composite_score"], c["model_probability"]), reverse=True)
        recommendations = evaluated[:top_n]
        for rank, item in enumerate(recommendations, start=1):
            item["rank"] = rank

        return {
            "state": state,
            "district": district,
            "season": season,
            "land_area_ha": round(area_ha, 3),
            "soil_type": soil_type,
            "irrigation_method": irrigation_method,
            "water_availability": water_availability,
            "scoring_weights": dict(weights),
            "rainfall_normals": {
                "annual_rainfall_mm": round(annual_rf, 1),
                "seasonal_rainfall_mm": round(seasonal_rf, 1),
            },
            "weather_summary": (weather_data or {}).get("current", {}),
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------ #
    # Candidate generation
    # ------------------------------------------------------------------ #

    def _eligible_candidates(
        self, state: str, season: str, annual_rf: float, seasonal_rf: float
    ) -> List[Dict[str, Any]]:
        """Ranks every crop with the ML model, keeps those that can be grown in the season."""
        ranked = self.predictor.predict_candidates(
            state=state,
            season=season,
            annual_rainfall_mm=annual_rf,
            seasonal_rainfall_mm=seasonal_rf,
            top_k=self.predictor.n_classes,
        )

        eligible = []
        for cand in ranked:
            profile = get_crop_profile(cand["crop"])
            if profile and is_suitable_for_season(profile, season):
                eligible.append({**cand, "profile": profile})
            if len(eligible) == CANDIDATE_POOL_SIZE:
                break

        if not eligible:
            logger.warning("No season-eligible candidates for %s / %s", state, season)
        return eligible

    # ------------------------------------------------------------------ #
    # Component scorers (each returns a 0-100 score and a plain-language note)
    # ------------------------------------------------------------------ #

    def _evaluate_water_compatibility(
        self,
        profile: Dict,
        seasonal_rain_mm: float,
        irrigation_method: str,
        water_availability: str,
    ) -> Tuple[float, str]:
        """Agronomic water balance: crop demand versus rainfall, irrigation and supply security."""
        water_req = str(profile.get("water_requirement", "Medium")).strip().lower()
        irrigation = (irrigation_method or "").strip().lower()
        avail = (water_availability or "").strip().lower()
        assured = irrigation in ASSURED_IRRIGATION
        reliable_supply = avail in ("good", "moderate")

        if water_req in ("very high", "high"):
            if assured and avail == "good":
                return 95.0, "High water requirement is fully satisfied by assured irrigation and good water availability."
            if assured and avail == "moderate":
                return 75.0, "Moderate irrigation is available; water conservation or drip methods recommended."
            if seasonal_rain_mm > 1000:
                return 80.0, "High seasonal monsoon rainfall supports water needs."
            if assured:
                return 50.0, "Irrigation exists, but limited or uncertain supply puts this water-hungry crop at risk."
            return 35.0, "Risk: Crop requires high water, but farm lacks assured irrigation or sufficient rainfall."

        if water_req == "medium":
            if (assured and reliable_supply) or seasonal_rain_mm >= 450:
                return 90.0, "Normal rainfall and farm irrigation match crop water demand well."
            if assured:
                return 70.0, "Irrigation is available but supply is limited; schedule watering at critical growth stages."
            if reliable_supply:
                return 75.0, "Adequate water for medium-demand crop."
            return 60.0, "Rainfall is limited; monitor soil moisture during flowering."

        # Low water demand
        if seasonal_rain_mm < 400 or avail == "limited" or irrigation == "rain-fed":
            return 98.0, "Excellent fit: Crop is highly drought-hardy and ideal for low rainfall or rain-fed drylands."
        return 85.0, "Low water crop will thrive easily with available moisture."

    def _evaluate_soil_compatibility(self, profile: Dict, farmer_soil: str) -> Tuple[float, str]:
        """Matches the farmer's soil class against the ICAR soil description for the crop."""
        if not _is_soil_specified(farmer_soil):
            return 80.0, "Soil type not specified; agronomic recommendation based on regional suitability."

        f_soil = farmer_soil.strip().lower()
        rec_soil = str(profile.get("suitable_soil", "")).lower()
        crop_name = profile.get("crop_name", "this crop")

        matched = any(
            key in f_soil and any(syn in rec_soil for syn in synonyms)
            for key, synonyms in SOIL_KEYWORDS.items()
        )
        if matched:
            return 95.0, f"{farmer_soil} is strongly suited for {crop_name} cultivation."
        return 65.0, f"Can be cultivated in {farmer_soil} with appropriate organic matter and land preparation."

    def _evaluate_weather_compatibility(
        self, profile: Dict, weather_data: Optional[Dict]
    ) -> Tuple[float, str]:
        """Assesses the current temperature against the crop's optimal growth range."""
        current = (weather_data or {}).get("current")
        if not current or current.get("temperature_c") is None:
            return 80.0, "Historical regional climate aligns with crop cycle."

        temp = float(current["temperature_c"])
        min_temp = float(profile.get("min_temp_c", 15.0))
        max_temp = float(profile.get("max_temp_c", 38.0))

        if min_temp <= temp <= max_temp:
            return 95.0, f"Current temperature ({temp:.1f}°C) is in the optimal growth window ({min_temp:.0f}°C - {max_temp:.0f}°C)."
        if temp < min_temp:
            score = max(40.0, 85.0 - (min_temp - temp) * 5)
            return score, f"Current conditions ({temp:.1f}°C) are cooler than optimal minimum ({min_temp:.0f}°C)."
        score = max(40.0, 85.0 - (temp - max_temp) * 5)
        return score, f"Current conditions ({temp:.1f}°C) exceed optimal maximum ({max_temp:.0f}°C); risk of heat stress."

    def _evaluate_preference(self, profile: Dict, preference: str) -> float:
        """Scores alignment with the farmer's preferred crop category."""
        pref = (preference or "").strip().lower()
        if pref in UNSPECIFIED_PREFERENCE:
            return 80.0
        category = str(profile.get("crop_category", "")).lower()
        return 95.0 if pref in category or category in pref else 65.0

    # ------------------------------------------------------------------ #
    # Explanations
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_explanations(
        crop_name: str,
        profile: Dict,
        state: str,
        season: str,
        seasonal_rf: float,
        soil_notes: str,
        water_notes: str,
        weather_notes: str,
        cand: Dict,
    ) -> List[str]:
        """Generates evidence-backed bullet points explaining the recommendation."""
        points = [
            f"Regional Cultivation Evidence: Historical agricultural records show {crop_name} is grown in "
            f"{state or 'this region'} during the {season} season "
            f"(model probability: {cand['model_confidence_pct']}%).",
            f"Water & Irrigation Match: {water_notes} Normal seasonal rainfall: {seasonal_rf:.0f} mm.",
            f"Soil Assessment: {soil_notes}",
            f"Weather Outlook: {weather_notes}",
        ]
        cultivation_note = profile.get("cultivation_notes", "")
        if cultivation_note:
            points.append(f"Advisory Guidance: {cultivation_note}")
        return points


if __name__ == "__main__":
    engine = RecommendationEngine()
    sample_profile = {
        "state": "Maharashtra",
        "district": "Pune",
        "preferred_season": "Kharif",
        "land_area": 2.5,
        "land_unit": "Acres",
        "soil_type": "Black soil",
        "irrigation_method": "Borewell",
        "water_availability": "Moderate",
        "crop_preferences": "No preference",
    }
    result = engine.generate_recommendations(sample_profile)
    print("Top Recommendations:")
    for r in result["recommendations"]:
        print(f"#{r['rank']}: {r['crop_name']} (Composite Score: {r['composite_score']}%)")
        print(f"   Model Prob: {r['model_probability']:.4f} | Water Score: {r['water_suitability_score']}")
        print(f"   Why: {r['explanation_points'][0]}")
