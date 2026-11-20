"""
KROP - Intelligent Crop Recommendations
Combines Scikit-learn ML candidate generation, ICAR agronomic constraints,
soil/water matching and live weather telemetry into transparent, ranked advice.
"""

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import MODEL_VERSION
from src.recommendation_engine import WEIGHTS_WITHOUT_SOIL, WEIGHTS_WITH_SOIL
from src.ui_components import esc, get_plotly_theme, get_recommendation_engine, weather_card_html
from src.weather_service import WeatherService

db = st.session_state["db_manager"]
active_profile = st.session_state.get("active_farm_profile")

st.title("🌾 Intelligent Crop Recommendations")
st.write(
    "Evidence-based crop planning combining regional historical cultivation patterns, "
    "Indian Meteorological Department (IMD) rainfall normals, farm irrigation capacity, and live weather intelligence."
)

if not active_profile:
    st.warning("⚠️ No farm profile detected. Please configure your farm location, land size, and irrigation facilities first.")
    if st.button("Set Up Farm Profile Now", type="primary"):
        st.switch_page("pages/2_Farm_Profile.py")
    st.stop()

# ---- Profile & weather summary ----
lat = float(active_profile.get("latitude") if active_profile.get("latitude") is not None else 18.5204)
lon = float(active_profile.get("longitude") if active_profile.get("longitude") is not None else 73.8567)

col_sum1, col_sum2 = st.columns([1.6, 1.4], gap="large")

with col_sum1:
    st.markdown(
        f"""
        <div class="krop-card krop-card-accent">
            <h4 style="margin-top: 0; color: #1b4332;">📍 Farm Profile Summary</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 0.9rem;">
                <div>Location: <strong>{esc(active_profile.get('village'))} {esc(active_profile.get('district'))}, {esc(active_profile.get('state'))}</strong></div>
                <div>Cultivable Land: <strong>{esc(active_profile.get('land_area'))} {esc(active_profile.get('land_unit'))}</strong></div>
                <div>Target Season: <strong>{esc(active_profile.get('preferred_season', 'Kharif'))}</strong></div>
                <div>Soil Classification: <strong>{esc(active_profile.get('soil_type', 'Unknown'))}</strong></div>
                <div>Irrigation Facility: <strong>{esc(active_profile.get('irrigation_method', 'Rain-fed'))}</strong></div>
                <div>Water Security: <strong>{esc(active_profile.get('water_availability', 'Moderate'))}</strong></div>
                <div>Crop Preference: <strong>{esc(active_profile.get('crop_preferences', 'No preference'))}</strong></div>
                <div>Coordinates: <strong>{lat:.4f}°N, {lon:.4f}°E</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_sum2:
    with st.spinner("Fetching current weather telemetry..."):
        weather_data = WeatherService().get_weather_forecast(lat, lon)
    st.session_state["weather_cache"] = weather_data
    st.markdown(
        weather_card_html(weather_data, title="⛅ Weather Intelligence", offline_label="FALLBACK"),
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---- Generate (or reuse) the recommendation ----
profile_signature = json.dumps(
    {k: v for k, v in active_profile.items() if k not in ("created_at", "updated_at")}, sort_keys=True, default=str
)

col_btn, _ = st.columns([1.5, 3.5])
with col_btn:
    regenerate = st.button("🌱 Generate Recommendations", type="primary", width="stretch")

rec_result = st.session_state.get("latest_recommendation")
is_stale = rec_result is None or st.session_state.get("latest_recommendation_profile") != profile_signature

if regenerate or is_stale:
    with st.spinner("Running ML inference and multi-factor agronomic validation..."):
        rec_result = get_recommendation_engine().generate_recommendations(
            farm_profile=active_profile, weather_data=weather_data, top_n=5
        )
    st.session_state["latest_recommendation"] = rec_result
    st.session_state["latest_recommendation_profile"] = profile_signature

recommendations = rec_result.get("recommendations", [])
if not recommendations:
    st.error("No eligible crops satisfied the regional constraints. Please review your seasonal selection.")
    st.stop()

# ---- Ranked overview ----
st.markdown("### 🏆 Top Recommended Crops")
weights = rec_result.get("scoring_weights") or (
    WEIGHTS_WITH_SOIL if (active_profile.get("soil_type") or "Unknown") not in ("Unknown", "Other") else WEIGHTS_WITHOUT_SOIL
)
parts = [
    f"**{label} ({weights[key] * 100:.0f}%)**"
    for key, label in (
        ("model", "Regional ML Model"), ("water", "Water Balance"), ("soil", "Soil Match"),
        ("weather", "Weather Suitability"), ("preference", "Preference Alignment"),
    )
    if weights.get(key)
]
st.write("Rankings are calculated via transparent multi-factor scoring: " + ", ".join(parts) + ".")
if not weights.get("soil"):
    st.caption("Soil type is unknown, so its weight was redistributed to the model and water balance rather than penalising any crop.")

df_chart = pd.DataFrame([{"Crop": r["crop_name"], "Composite Suitability (%)": r["composite_score"]} for r in recommendations])
fig_scores = px.bar(
    df_chart, x="Composite Suitability (%)", y="Crop", orientation="h",
    text="Composite Suitability (%)", color="Composite Suitability (%)",
    color_continuous_scale=["#74c69d", "#40916c", "#1b4332"], range_color=(0, 100),
    title="Candidate Crop Suitability Score Comparison",
)
fig_scores.update_layout(height=260, margin=dict(l=20, r=20, t=35, b=20), coloraxis_showscale=False, **get_plotly_theme())
fig_scores.update_yaxes(autorange="reversed")
fig_scores.update_xaxes(range=[0, 100])
st.plotly_chart(fig_scores, width="stretch")

st.divider()

# ---- Detailed cards (each rendered as one complete HTML block) ----
for crop in recommendations:
    explanations = "".join(f"<li>{esc(point)}</li>" for point in crop.get("explanation_points", []))
    note = crop.get("cultivation_notes", "")
    advisory = (
        f'<div class="krop-advisory"><strong>💡 ICAR Advisory Note:</strong> {esc(note)}</div>' if note else ""
    )
    st.markdown(
        f"""
        <div class="krop-rec-box">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="background: #2d6a4f; color: #ffffff; border-radius: 50%; width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem;">{crop['rank']}</span>
                    <h3 style="margin: 0; color: #1b4332;">{esc(crop['crop_name'])}</h3>
                    <span class="krop-badge">{esc(crop.get('crop_category'))}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 1.5rem; font-weight: 800; color: #2d6a4f;">{crop['composite_score']}%</span>
                    <div style="font-size: 0.78rem; color: #555b6e;">COMPOSITE SUITABILITY</div>
                </div>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.8rem 0; font-size: 0.85rem;">
                <span class="krop-badge krop-badge-gold">🤖 ML Model Probability: <strong>{crop['model_confidence_pct']:.2f}%</strong></span>
                <span class="krop-badge">💧 Water Match: <strong>{crop['water_suitability_score']}%</strong></span>
                <span class="krop-badge">🌱 Soil Match: <strong>{crop['soil_suitability_score']}%</strong></span>
                <span class="krop-badge">⛅ Weather Match: <strong>{crop['weather_suitability_score']}%</strong></span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.6rem; padding: 0.75rem; background: #f8f9fa; border-radius: 8px; font-size: 0.88rem; margin: 0.75rem 0;">
                <div>🗓️ <strong>Duration:</strong> {esc(crop.get('growing_duration', 'N/A'))}</div>
                <div>💧 <strong>Water Need:</strong> {esc(crop.get('water_requirement'))} ({esc(crop.get('water_requirement_mm'))})</div>
                <div>🌱 <strong>Ideal Soil:</strong> {esc(crop.get('suitable_soil'))}</div>
                <div>🌡️ <strong>Temperature:</strong> {esc(crop.get('temperature_conditions'))}</div>
                <div>🌾 <strong>Sowing Window:</strong> {esc(crop.get('sowing_period'))}</div>
                <div>🏛️ <strong>Reference Source:</strong> {esc(crop.get('information_source'))}</div>
            </div>
            <div style="margin-top: 0.75rem;">
                <strong>🔍 Why This Crop Is Recommended:</strong>
                <ul style="margin: 0.4rem 0 0.8rem 1.2rem; font-size: 0.9rem; color: #2b2d42; line-height: 1.5;">{explanations}</ul>
            </div>
            {advisory}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Save ----
st.divider()
col_save1, col_save2 = st.columns([2, 3])

with col_save1:
    if st.button("💾 Save Recommendation Record to History", type="primary", width="stretch"):
        saved_id = db.save_recommendation(
            farm_profile_id=active_profile.get("id"),
            recommended_crops=recommendations,
            weather_summary=weather_data.get("current", {}),
            recommendation_details=rec_result,
            model_version=MODEL_VERSION,
        )
        st.success(f"✅ Advisory saved to history as Record #{saved_id}.")
        if not active_profile.get("id"):
            st.caption("This record is not linked to a saved farm profile. Save your profile to link future records.")

with col_save2:
    if st.button("📜 View Recommendation History", width="stretch"):
        st.switch_page("pages/5_Recommendation_History.py")
