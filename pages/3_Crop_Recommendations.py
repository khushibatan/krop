"""
KROP - Page 3: Intelligent Crop Recommendations
Core recommendation engine combining Scikit-learn ML candidate generation,
ICAR agronomic constraints, soil/water matching, and live weather telemetry.
Strictly zero hardware dependencies, absolutely ZERO NPK.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from src.ui_components import (
    apply_custom_styles,
    render_sidebar_header,
    init_session_state,
    get_plotly_theme,
    COLOR_PRIMARY_GREEN,
    COLOR_LEAF_GREEN,
    COLOR_FOREST_DARK
)
from src.recommendation_engine import RecommendationEngine
from src.weather_service import WeatherService
from src.database import DatabaseManager

st.set_page_config(
    page_title="Crop Recommendations - KROP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

db: DatabaseManager = st.session_state["db_manager"]
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

# 1. Farm & Environmental Summary Banner
col_sum1, col_sum2 = st.columns([1.6, 1.4], gap="large")

with col_sum1:
    st.markdown(
        f"""
        <div class="krop-card krop-card-accent">
            <h4 style="margin-top: 0; color: #1b4332;">📍 Farm Profile Summary</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; font-size: 0.9rem;">
                <div>Location: <strong>{active_profile.get('village', '')} {active_profile.get('district', '')}, {active_profile.get('state', '')}</strong></div>
                <div>Cultivable Land: <strong>{active_profile.get('land_area', '')} {active_profile.get('land_unit', '')}</strong></div>
                <div>Target Season: <strong>{active_profile.get('preferred_season', 'Kharif')}</strong></div>
                <div>Soil Classification: <strong>{active_profile.get('soil_type', 'Unknown')}</strong></div>
                <div>Irrigation Facility: <strong>{active_profile.get('irrigation_method', 'Rain-fed')}</strong></div>
                <div>Water Security: <strong>{active_profile.get('water_availability', 'Moderate')}</strong></div>
                <div>Crop Preference: <strong>{active_profile.get('crop_preferences', 'No preference')}</strong></div>
                <div>Coordinates: <strong>{float(active_profile.get('latitude', 18.5)):.4f}°N, {float(active_profile.get('longitude', 73.8)):.4f}°E</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_sum2:
    # Weather retrieval
    weather_svc = WeatherService()
    lat = float(active_profile.get("latitude", 18.5204))
    lon = float(active_profile.get("longitude", 73.8567))
    
    with st.spinner("Fetching current weather telemetry..."):
        weather_data = weather_svc.get_weather_forecast(lat, lon)
        st.session_state["weather_cache"] = weather_data

    curr = weather_data.get("current", {})
    f_sum = weather_data.get("forecast_summary", {})

    st.markdown(
        f"""
        <div class="krop-card" style="border-top: 4px solid #2d6a4f;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1b4332;">⛅ Weather Intelligence</h4>
                <span class="krop-badge">{'LIVE' if weather_data.get('is_live') else 'FALLBACK'}</span>
            </div>
            <div style="display: flex; align-items: baseline; gap: 1rem; margin: 0.5rem 0;">
                <span style="font-size: 2rem; font-weight: 800; color: #2d6a4f;">{curr.get('temperature_c', 25.0):.1f}°C</span>
                <span style="color: #555b6e;">{curr.get('condition', 'Clear')}</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem; font-size: 0.85rem;">
                <div>💧 Relative Humidity: <strong>{curr.get('humidity_pct', 50)}%</strong></div>
                <div>💨 Wind Speed: <strong>{curr.get('wind_speed_kmh', 5)} km/h</strong></div>
                <div>🌧️ Precipitation: <strong>{curr.get('precipitation_mm', 0.0)} mm</strong></div>
                <div>📅 7-Day Rain Sum: <strong>{f_sum.get('total_rain_7days_mm', 0.0)} mm</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# Generate Recommendation Trigger
col_btn, col_count = st.columns([1.5, 3.5])
with col_btn:
    generate_clicked = st.button("🌱 Generate Recommendations", type="primary", width="stretch")

# Engine Execution
rec_result = st.session_state.get("latest_recommendation")

if generate_clicked or rec_result is None:
    with st.spinner("Running ML inference and multi-factor agronomic validation..."):
        engine = RecommendationEngine()
        rec_result = engine.generate_recommendations(
            farm_profile=active_profile,
            weather_data=weather_data,
            top_n=5
        )
        st.session_state["latest_recommendation"] = rec_result

recommendations = rec_result.get("recommendations", [])

if not recommendations:
    st.error("No eligible crops satisfied the regional constraints. Please review your seasonal selection.")
    st.stop()

# 2. Recommendations Display
st.markdown("### 🏆 Top Recommended Crops")
st.write(
    "Rankings are calculated via transparent multi-factor scoring: "
    "**Random Forest Regional Model (35-45%)**, **Water Balance (25-35%)**, **Soil Match (15%)**, **Weather Suitability (10-15%)**, and **Preference Alignment (10%)**."
)

# Comparison Bar Chart of Composite Scores
df_chart = pd.DataFrame([
    {
        "Crop": r["crop_name"],
        "Composite Suitability (%)": r["composite_score"],
        "Water Score": r["water_suitability_score"],
        "Soil Score": r["soil_suitability_score"],
        "Weather Score": r["weather_suitability_score"],
        "Model Prob (%)": r["model_confidence_pct"]
    }
    for r in recommendations
])

fig_scores = px.bar(
    df_chart,
    x="Composite Suitability (%)",
    y="Crop",
    orientation="h",
    text="Composite Suitability (%)",
    color="Composite Suitability (%)",
    color_continuous_scale=["#74c69d", "#40916c", "#1b4332"],
    title="Candidate Crop Suitability Score Comparison"
)
fig_scores.update_layout(
    height=260,
    margin=dict(l=20, r=20, t=35, b=20),
    **get_plotly_theme()
)
fig_scores.update_yaxes(autorange="reversed")
st.plotly_chart(fig_scores, width="stretch")

st.divider()

# Detailed Cards for Each Recommended Crop
for crop in recommendations:
    rank = crop["rank"]
    c_name = crop["crop_name"]
    comp_score = crop["composite_score"]
    model_prob = crop["model_confidence_pct"]
    
    st.markdown(
        f"""
        <div class="krop-rec-box">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <span style="background: #2d6a4f; color: #ffffff; border-radius: 50%; width: 34px; height: 34px; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem;">
                        {rank}
                    </span>
                    <h3 style="margin: 0; color: #1b4332;">{c_name}</h3>
                    <span class="krop-badge">{crop.get('crop_category', '')}</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 1.5rem; font-weight: 800; color: #2d6a4f;">{comp_score}%</span>
                    <div style="font-size: 0.78rem; color: #555b6e;">COMPOSITE SUITABILITY</div>
                </div>
            </div>

            <!-- Score Breakdown Pills -->
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.8rem 0; font-size: 0.85rem;">
                <span class="krop-badge krop-badge-gold">🤖 ML Model Probability: <strong>{model_prob:.2f}%</strong></span>
                <span class="krop-badge">💧 Water Match: <strong>{crop['water_suitability_score']}%</strong></span>
                <span class="krop-badge">🌱 Soil Match: <strong>{crop['soil_suitability_score']}%</strong></span>
                <span class="krop-badge">⛅ Weather Match: <strong>{crop['weather_suitability_score']}%</strong></span>
            </div>

            <!-- Agronomic Facts Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.6rem; padding: 0.75rem; background: #f8f9fa; border-radius: 8px; font-size: 0.88rem; margin: 0.75rem 0;">
                <div>🗓️ <strong>Duration:</strong> {crop.get('growing_duration', 'N/A')}</div>
                <div>💧 <strong>Water Need:</strong> {crop.get('water_requirement', 'Medium')} ({crop.get('water_requirement_mm', '')})</div>
                <div>🌱 <strong>Ideal Soil:</strong> {crop.get('suitable_soil', 'Loam')}</div>
                <div>🌡️ <strong>Temperature:</strong> {crop.get('temperature_conditions', '20°C - 35°C')}</div>
                <div>🌾 <strong>Sowing Window:</strong> {crop.get('sowing_period', 'June - July')}</div>
                <div>🏛️ <strong>Reference Source:</strong> {crop.get('information_source', 'ICAR')}</div>
            </div>

            <!-- Evidence-Based Explanations -->
            <div style="margin-top: 0.75rem;">
                <strong>🔍 Why This Crop Is Recommended:</strong>
                <ul style="margin: 0.4rem 0 0.8rem 1.2rem; font-size: 0.9rem; color: #2b2d42; line-height: 1.5;">
        """,
        unsafe_allow_html=True
    )

    for pt in crop.get("explanation_points", []):
        st.markdown(f"- {pt}")

    # Advisory Guidance Box
    cult_note = crop.get("cultivation_notes", "")
    if cult_note:
        st.markdown(
            f"""
            <div class="krop-advisory">
                <strong>💡 ICAR Advisory Note:</strong> {cult_note}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# 3. Persistent Save Action
st.divider()
col_save1, col_save2 = st.columns([2, 3])

with col_save1:
    if st.button("💾 Save Recommendation Record to History", type="primary", width="stretch"):
        saved_id = db.save_recommendation(
            farm_profile_id=active_profile.get("id"),
            recommended_crops=recommendations,
            weather_summary=weather_data.get("current", {}),
            recommendation_details=rec_result,
            model_version="1.0.0"
        )
        st.success(f"✅ Advisory record saved permanently to SQLite database as Record #{saved_id}!")

with col_save2:
    if st.button("📜 View Recommendation History", width="stretch"):
        st.switch_page("pages/5_Recommendation_History.py")
