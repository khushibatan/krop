"""
KROP - Page 4: Crop Insights and Agronomic Catalog
Searchable agronomic reference database curated from ICAR and Agricultural Universities.
Strictly zero hardware dependencies, absolutely ZERO NPK.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.ui_components import (
    apply_custom_styles,
    render_sidebar_header,
    init_session_state,
    get_plotly_theme
)
from src.crop_information import (
    load_crop_catalog,
    get_crop_categories,
    filter_crops
)

st.set_page_config(
    page_title="Crop Insights - KROP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

st.title("📖 Crop Agronomic Insights & Knowledge Base")
st.write(
    "Explore agronomic profiles for major Indian crops based on verified data from the "
    "Indian Council of Agricultural Research (ICAR) and State Agricultural Universities. "
    "All parameters reflect real environmental thresholds with zero chemical NPK assumptions."
)

catalog_df = load_crop_catalog()

# Filter Controls Strip
col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    categories = ["All"] + get_crop_categories()
    selected_cat = st.selectbox("Crop Category", categories)

with col_f2:
    seasons = ["All", "Kharif", "Rabi", "Summer", "Whole Year"]
    selected_season = st.selectbox("Cropping Season", seasons)

with col_f3:
    water_opts = ["All", "Low", "Medium", "High", "Very High"]
    selected_water = st.selectbox("Water Requirement", water_opts)

with col_f4:
    max_dur = st.slider("Max Growing Duration (Days)", min_value=60, max_value=420, value=420, step=15)

search_term = st.text_input("🔍 Search Crop by Name", placeholder="e.g. Wheat, Gram, Cotton, Maize, Rice").strip().lower()

# Apply Filters
filtered_df = filter_crops(
    category=selected_cat,
    season=selected_season,
    water_req=selected_water,
    max_duration=max_dur
)

if search_term:
    filtered_df = filtered_df[
        filtered_df["crop_name"].str.lower().str.contains(search_term) |
        filtered_df["cultivation_notes"].str.lower().str.contains(search_term)
    ]

# Summary Strip
st.markdown("<br>", unsafe_allow_html=True)
c_k1, c_k2, c_k3, c_k4 = st.columns(4)
c_k1.metric("Matching Crops", len(filtered_df), f"of {len(catalog_df)} total")
avg_dur = int(filtered_df["duration_max_days"].mean()) if not filtered_df.empty else 0
c_k2.metric("Average Maturity Duration", f"{avg_dur} days" if avg_dur else "N/A")
low_water_cnt = (filtered_df["water_requirement"] == "Low").sum() if not filtered_df.empty else 0
c_k3.metric("Drought-Resilient Crops", low_water_cnt, "Low Water Demand")
c_k4.metric("Categories Represented", filtered_df["crop_category"].nunique() if not filtered_df.empty else 0)

st.divider()

if filtered_df.empty:
    st.info("No crops matched your selected filter criteria. Try expanding the duration slider or selecting 'All' categories.")
    st.stop()

# Visual Comparisons
col_chart1, col_chart2 = st.columns([1.5, 1.2], gap="large")

with col_chart1:
    st.markdown("#### ⏱️ Crop Maturity Duration (Days)")
    fig_dur = px.bar(
        filtered_df.sort_values("duration_max_days"),
        x="duration_max_days",
        y="crop_name",
        orientation="h",
        color="crop_category",
        labels={"duration_max_days": "Maturity Duration (Max Days)", "crop_name": "Crop", "crop_category": "Category"},
        color_discrete_sequence=["#2d6a4f", "#52b788", "#74c69d", "#95d5b2", "#d8f3dc", "#b7e4c7"]
    )
    fig_dur.update_layout(
        height=max(260, len(filtered_df) * 22),
        margin=dict(l=20, r=20, t=20, b=20),
        **get_plotly_theme()
    )
    st.plotly_chart(fig_dur, width="stretch")

with col_chart2:
    st.markdown("#### 💧 Water Requirement Breakdown")
    water_counts = filtered_df["water_requirement"].value_counts().reset_index()
    water_counts.columns = ["Requirement", "Count"]
    fig_water = px.pie(
        water_counts,
        names="Requirement",
        values="Count",
        color="Requirement",
        color_discrete_map={
            "Low": "#52b788",
            "Medium": "#74c69d",
            "High": "#2d6a4f",
            "Very High": "#1b4332"
        },
        hole=0.4
    )
    fig_water.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=20, b=20),
        **get_plotly_theme()
    )
    st.plotly_chart(fig_water, width="stretch")

st.divider()

# Individual Crop Cards
st.markdown("### 🌾 Comprehensive Crop Profiles")

for _, row in filtered_df.iterrows():
    c_name = row["crop_name"]
    cat = row["crop_category"]
    seasons_str = row["suitable_seasons"]
    duration = row["growing_duration_days"]
    water_req = row["water_requirement"]
    water_mm = row["water_requirement_mm"]
    soil = row["suitable_soil"]
    temp = row["temperature_conditions"]
    sowing = row["sowing_period"]
    notes = row["cultivation_notes"]
    regions = row["regional_information"]
    src = row["information_source"]

    with st.expander(f"🌱 {c_name} — {cat} ({seasons_str})", expanded=False):
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.markdown(f"**🗓️ Duration:** {duration}")
        c_p1.markdown(f"**💧 Water Demand:** {water_req} ({water_mm})")
        
        c_p2.markdown(f"**🌱 Soil Compatibility:** {soil}")
        c_p2.markdown(f"**🌡️ Temperature Window:** {temp}")

        c_p3.markdown(f"**🌾 Sowing Window:** {sowing}")
        c_p3.markdown(f"**🏛️ Reference Authority:** {src}")

        st.markdown(
            f"""
            <div style="background: #ffffff; padding: 0.8rem; border-radius: 8px; border: 1px solid #d8e2dc; margin-top: 0.5rem; font-size: 0.9rem;">
                <strong>💡 Agronomic & Cultivation Guidance:</strong><br>
                {notes}
            </div>
            <div style="margin-top: 0.4rem; font-size: 0.85rem; color: #555b6e;">
                <strong>📍 Major Producing Regions in India:</strong> {regions}
            </div>
            """,
            unsafe_allow_html=True
        )
