"""
KROP - Smart Crop Planning and Recommendation System
Main Application Entry Point and Executive Dashboard.
Purely software-based, zero hardware dependencies, strictly zero NPK.
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
from src.database import DatabaseManager
from src.weather_service import WeatherService
from src.crop_information import load_crop_catalog

# Page Configuration
st.set_page_config(
    page_title="KROP - Smart Crop Planning System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

# Header Banner
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%); padding: 2.2rem 2.5rem; border-radius: 14px; color: #ffffff; margin-bottom: 2rem; box-shadow: 0 4px 14px rgba(27,67,50,0.18);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
            <div>
                <span style="background: rgba(255,255,255,0.2); padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600; letter-spacing: 1px;">DECISION SUPPORT PLATFORM</span>
                <h1 style="color: #ffffff !important; font-size: 2.5rem; margin: 0.4rem 0 0.3rem 0; font-weight: 800;">KROP</h1>
                <p style="color: #d8f3dc; font-size: 1.15rem; margin: 0; max-width: 650px;">
                    Intelligent agricultural planning empowering small-scale Indian farmers with ML-driven crop selection, regional climate normals, and live weather intelligence.
                </p>
            </div>
            <div style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.25); border-radius: 10px; padding: 1rem 1.4rem; text-align: center; min-width: 220px;">
                <div style="font-size: 0.85rem; color: #d8f3dc; font-weight: 500;">ARCHITECTURAL GUARANTEE</div>
                <div style="font-size: 1.25rem; font-weight: 700; color: #ffffff; margin: 0.2rem 0;">100% Software</div>
                <div style="font-size: 0.8rem; color: #b7e4c7;">Strictly Zero Hardware &bull; Zero NPK</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

db: DatabaseManager = st.session_state["db_manager"]
active_profile = st.session_state.get("active_farm_profile")

# Top KPI Metric Strip
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    profile_status = "Configured" if active_profile else "Not Set"
    loc_text = f"{active_profile.get('district', '')}, {active_profile.get('state', '')}" if active_profile else "Configure Profile"
    st.metric(label="Farm Profile Status", value=profile_status, delta=loc_text if active_profile else None)

with col_kpi2:
    season_val = active_profile.get("preferred_season", "Kharif") if active_profile else "Kharif / Rabi"
    st.metric(label="Active Crop Season", value=season_val, delta="Historical Normals Active")

with col_kpi3:
    history = db.get_recommendation_history(limit=10)
    st.metric(label="Saved Advisory Records", value=len(history), delta=f"Last updated: {history[0]['created_at'][:10]}" if history else "No records yet")

with col_kpi4:
    catalog_df = load_crop_catalog()
    st.metric(label="ICAR Validated Crops", value=len(catalog_df), delta="33 National Staples")

st.markdown("<br>", unsafe_allow_html=True)

# Main Section: Quick Actions & Live Weather Overview
col_left, col_right = st.columns([1.6, 1.2], gap="large")

with col_left:
    st.subheader("⚡ Quick Agricultural Actions")
    st.write("Start with simple details about your land and receive evidence-based crop recommendations backed by Scikit-learn and ICAR agronomic rules.")

    c_act1, c_act2 = st.columns(2)
    with c_act1:
        st.markdown(
            """
            <div class="krop-card krop-card-accent">
                <h4 style="margin-top:0;">📝 1. Farm Profile</h4>
                <p style="color: #555b6e; font-size: 0.9rem;">
                    Specify village, district, land size, water sources, and optional soil type.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Set Up Farm Profile &rarr;", key="btn_farm_profile", width="stretch"):
            st.switch_page("pages/2_Farm_Profile.py")

    with c_act2:
        st.markdown(
            """
            <div class="krop-card krop-card-accent">
                <h4 style="margin-top:0;">🌱 2. Recommendations</h4>
                <p style="color: #555b6e; font-size: 0.9rem;">
                    Generate top 3-5 ranked crops with complete suitability explanations.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Generate Recommendations &rarr;", key="btn_recommendations", width="stretch"):
            st.switch_page("pages/3_Crop_Recommendations.py")

    c_act3, c_act4 = st.columns(2)
    with c_act3:
        st.markdown(
            """
            <div class="krop-card">
                <h4 style="margin-top:0;">📖 3. Crop Insights</h4>
                <p style="color: #555b6e; font-size: 0.9rem;">
                    Explore ICAR duration, water requirements, and optimal sowing calendars.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Browse Crop Catalog &rarr;", key="btn_insights", width="stretch"):
            st.switch_page("pages/4_Crop_Insights.py")

    with c_act4:
        st.markdown(
            """
            <div class="krop-card">
                <h4 style="margin-top:0;">📜 4. Past Advisories</h4>
                <p style="color: #555b6e; font-size: 0.9rem;">
                    Review, compare, and manage previously saved recommendations.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View History &rarr;", key="btn_history", width="stretch"):
            st.switch_page("pages/5_Recommendation_History.py")

with col_right:
    st.subheader("⛅ Weather & Regional Intelligence")
    
    if active_profile and active_profile.get("latitude") and active_profile.get("longitude"):
        lat = float(active_profile["latitude"])
        lon = float(active_profile["longitude"])
        
        weather_svc = WeatherService()
        w_data = weather_svc.get_weather_forecast(lat, lon)
        st.session_state["weather_cache"] = w_data

        curr = w_data.get("current", {})
        f_sum = w_data.get("forecast_summary", {})
        
        st.markdown(
            f"""
            <div class="krop-card" style="border-top: 4px solid #52b788;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 1.1rem; color: #1b4332;">
                        📍 {active_profile.get('village') or active_profile.get('district')}, {active_profile.get('state')}
                    </span>
                    <span class="krop-badge">{'LIVE' if w_data.get('is_live') else 'SEASONAL AVG'}</span>
                </div>
                <div style="font-size: 0.85rem; color: #555b6e; margin-bottom: 0.8rem;">
                    Coordinates: {lat:.4f}°N, {lon:.4f}°E
                </div>
                <div style="display: flex; align-items: baseline; gap: 1rem; margin: 0.5rem 0;">
                    <span style="font-size: 2.2rem; font-weight: 800; color: #2d6a4f;">{curr.get('temperature_c', 25.0):.1f}°C</span>
                    <span style="color: #555b6e; font-size: 1rem;">{curr.get('condition', 'Clear')}</span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.8rem; font-size: 0.88rem;">
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 6px;">💧 Humidity: <strong>{curr.get('humidity_pct', 50)}%</strong></div>
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 6px;">💨 Wind: <strong>{curr.get('wind_speed_kmh', 5)} km/h</strong></div>
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 6px;">🌧️ Current Rain: <strong>{curr.get('precipitation_mm', 0.0)} mm</strong></div>
                    <div style="background: #f8f9fa; padding: 0.5rem; border-radius: 6px;">📅 7-Day Forecast Rain: <strong>{f_sum.get('total_rain_7days_mm', 0.0)} mm</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 7-day temperature trajectory chart
        daily = w_data.get("daily_forecast", [])
        if daily:
            df_daily = pd.DataFrame(daily)
            fig_w = go.Figure()
            fig_w.add_trace(go.Scatter(
                x=df_daily["date"], y=df_daily["max_temp_c"],
                mode="lines+markers", name="Max Temp (°C)",
                line=dict(color="#d97706", width=2.5)
            ))
            fig_w.add_trace(go.Scatter(
                x=df_daily["date"], y=df_daily["min_temp_c"],
                mode="lines+markers", name="Min Temp (°C)",
                line=dict(color="#2d6a4f", width=2.5)
            ))
            fig_w.update_layout(
                title=dict(text="7-Day Temperature Trend (°C)", font=dict(size=13, color="#1b4332")),
                height=210,
                margin=dict(l=20, r=20, t=35, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                **get_plotly_theme()
            )
            st.plotly_chart(fig_w, width="stretch")

    else:
        st.markdown(
            """
            <div class="krop-card" style="text-align: center; padding: 2rem 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📍</div>
                <h4 style="margin: 0.2rem 0;">No Location Configured</h4>
                <p style="color: #555b6e; font-size: 0.88rem;">
                    Set your farm's state, district, or village in the <strong>Farm Profile</strong> to enable live Open-Meteo weather intelligence and IMD rainfall normals.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Configure Farm Location", key="btn_goto_profile", width="stretch"):
            st.switch_page("pages/2_Farm_Profile.py")

# Bottom Section: Recent Advisory Preview & National Crop Distribution
st.divider()
st.subheader("🌾 Agricultural Insights & Diversity")

col_hist, col_chart = st.columns([1.2, 1.8], gap="large")

with col_hist:
    st.markdown("#### Latest Saved Recommendations")
    if history:
        latest_rec = history[0]
        st.markdown(
            f"""
            <div class="krop-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>{latest_rec.get('district', '')}, {latest_rec.get('state', '')}</strong>
                    <span style="font-size: 0.8rem; color: #555b6e;">{latest_rec.get('created_at', '')[:10]}</span>
                </div>
                <div style="font-size: 0.85rem; color: #555b6e; margin-bottom: 0.6rem;">
                    Area: {latest_rec.get('land_area', '')} {latest_rec.get('land_unit', '')} | Soil: {latest_rec.get('soil_type', 'Unknown')}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">
            """,
            unsafe_allow_html=True
        )
        for crop in latest_rec.get("recommended_crops", [])[:4]:
            st.markdown(
                f'<span class="krop-badge">{crop.get("crop_name", "")} ({crop.get("composite_score", 0)}%)</span>',
                unsafe_allow_html=True
            )
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.info("No recommendations saved yet. Complete your profile and run recommendations to store advisory history.")

with col_chart:
    st.markdown("#### ICAR Validated Crop Categories & Duration")
    cat_counts = catalog_df["crop_category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Crops Count"]
    
    fig_cat = px.bar(
        cat_counts,
        x="Category",
        y="Crops Count",
        color="Category",
        color_discrete_sequence=["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2", "#b7e4c7", "#d8f3dc"],
        text="Crops Count"
    )
    fig_cat.update_layout(
        height=240,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        **get_plotly_theme()
    )
    st.plotly_chart(fig_cat, width="stretch")
