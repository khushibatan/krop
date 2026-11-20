"""
KROP - Home Dashboard
Executive overview: farm status, quick actions, live weather and advisory history.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.crop_information import load_crop_catalog
from src.ui_components import esc, get_plotly_theme, weather_card_html
from src.weather_service import WeatherService

db = st.session_state["db_manager"]
active_profile = st.session_state.get("active_farm_profile")
catalog_df = load_crop_catalog()

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
    unsafe_allow_html=True,
)

# ---- KPI strip ----
history = db.get_recommendation_history(limit=1)
total_records = db.count_recommendations()

k1, k2, k3, k4 = st.columns(4)
with k1:
    if active_profile:
        st.metric("Farm Profile Status", "Configured", f"{active_profile.get('district', '')}, {active_profile.get('state', '')}", delta_color="off")
    else:
        st.metric("Farm Profile Status", "Not Set")
with k2:
    st.metric("Active Crop Season", active_profile.get("preferred_season", "Kharif") if active_profile else "Not set")
with k3:
    st.metric(
        "Saved Advisory Records", total_records,
        f"Last: {history[0]['created_at'][:10]}" if history else "No records yet", delta_color="off",
    )
with k4:
    st.metric("ICAR Validated Crops", len(catalog_df), "National staples", delta_color="off")

st.markdown("<br>", unsafe_allow_html=True)

# ---- Quick actions and weather ----
col_left, col_right = st.columns([1.6, 1.2], gap="large")

QUICK_ACTIONS = [
    ("📝 1. Farm Profile", "Specify village, district, land size, water sources, and optional soil type.",
     "Set Up Farm Profile →", "pages/2_Farm_Profile.py", True),
    ("🌱 2. Recommendations", "Generate top 3-5 ranked crops with complete suitability explanations.",
     "Generate Recommendations →", "pages/3_Crop_Recommendations.py", True),
    ("📖 3. Crop Insights", "Explore ICAR duration, water requirements, and optimal sowing calendars.",
     "Browse Crop Catalog →", "pages/4_Crop_Insights.py", False),
    ("📜 4. Past Advisories", "Review, compare, and manage previously saved recommendations.",
     "View History →", "pages/5_Recommendation_History.py", False),
]

with col_left:
    st.subheader("⚡ Quick Agricultural Actions")
    st.write(
        "Start with simple details about your land and receive evidence-based crop recommendations "
        "backed by Scikit-learn and ICAR agronomic rules."
    )
    for row_start in (0, 2):
        for column, (title, text, label, target, accent) in zip(st.columns(2), QUICK_ACTIONS[row_start:row_start + 2]):
            with column:
                st.markdown(
                    f'''<div class="krop-card{" krop-card-accent" if accent else ""}">
                        <h4 style="margin-top:0;">{title}</h4>
                        <p style="color: #555b6e; font-size: 0.9rem;">{text}</p></div>''',
                    unsafe_allow_html=True,
                )
                if st.button(label, key=f"home_{target}", width="stretch"):
                    st.switch_page(target)

with col_right:
    st.subheader("⛅ Weather & Regional Intelligence")
    if active_profile and active_profile.get("latitude") is not None and active_profile.get("longitude") is not None:
        lat, lon = float(active_profile["latitude"]), float(active_profile["longitude"])
        with st.spinner("Fetching weather..."):
            weather = WeatherService().get_weather_forecast(lat, lon)
        st.session_state["weather_cache"] = weather

        place = active_profile.get("village") or active_profile.get("district")
        st.markdown(
            weather_card_html(
                weather,
                title=f"📍 {place}, {active_profile.get('state')}",
                subtitle=f"Coordinates: {lat:.4f}°N, {lon:.4f}°E",
            ),
            unsafe_allow_html=True,
        )

        daily = weather.get("daily_forecast", [])
        if daily:
            df_daily = pd.DataFrame(daily)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_daily["date"], y=df_daily["max_temp_c"], mode="lines+markers",
                                     name="Max Temp (°C)", line=dict(color="#d97706", width=2.5)))
            fig.add_trace(go.Scatter(x=df_daily["date"], y=df_daily["min_temp_c"], mode="lines+markers",
                                     name="Min Temp (°C)", line=dict(color="#2d6a4f", width=2.5)))
            fig.update_layout(
                title=dict(text="7-Day Temperature Trend (°C)", font=dict(size=13, color="#1b4332")),
                height=210,
                margin=dict(l=20, r=20, t=35, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                **get_plotly_theme(),
            )
            st.plotly_chart(fig, width="stretch")
    else:
        st.markdown(
            """
            <div class="krop-card" style="text-align: center; padding: 2rem 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📍</div>
                <h4 style="margin: 0.2rem 0;">No Location Configured</h4>
                <p style="color: #555b6e; font-size: 0.88rem;">
                    Set your farm's state, district, or village in the <strong>Farm Profile</strong> to enable live
                    Open-Meteo weather intelligence and IMD rainfall normals.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Configure Farm Location", key="home_goto_profile", width="stretch"):
            st.switch_page("pages/2_Farm_Profile.py")

# ---- Latest advisory & catalog overview ----
st.divider()
st.subheader("🌾 Agricultural Insights & Diversity")

col_hist, col_chart = st.columns([1.2, 1.8], gap="large")

with col_hist:
    st.markdown("#### Latest Saved Recommendation")
    if history:
        latest = history[0]
        badges = "".join(
            f'<span class="krop-badge">{esc(c.get("crop_name"))} ({c.get("composite_score", 0)}%)</span>'
            for c in latest.get("recommended_crops", [])[:4]
        )
        st.markdown(
            f"""
            <div class="krop-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <strong>{esc(latest.get('district') or 'Unlinked profile')}, {esc(latest.get('state') or '')}</strong>
                    <span style="font-size: 0.8rem; color: #555b6e;">{esc(latest['created_at'][:10])}</span>
                </div>
                <div style="font-size: 0.85rem; color: #555b6e; margin-bottom: 0.6rem;">
                    Area: {esc(latest.get('land_area') or '-')} {esc(latest.get('land_unit') or '')} | Soil: {esc(latest.get('soil_type') or 'Unknown')}
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">{badges}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("No recommendations saved yet. Complete your profile and run recommendations to store advisory history.")

with col_chart:
    st.markdown("#### ICAR Validated Crop Categories")
    cat_counts = catalog_df["crop_category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Crops Count"]
    fig_cat = px.bar(
        cat_counts, x="Category", y="Crops Count", color="Category", text="Crops Count",
        color_discrete_sequence=["#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2", "#b7e4c7", "#d8f3dc"],
    )
    fig_cat.update_layout(height=240, margin=dict(l=20, r=20, t=20, b=20), showlegend=False, **get_plotly_theme())
    st.plotly_chart(fig_cat, width="stretch")
