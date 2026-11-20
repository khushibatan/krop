"""
KROP - Page 2: Farm Profile Management
Simple, accessible farm information collection for smallholder Indian farmers.
Zero hardware dependencies, strictly zero NPK.
"""

import streamlit as st
from datetime import datetime

from src.ui_components import (
    apply_custom_styles,
    render_sidebar_header,
    init_session_state
)
from src.utils import get_indian_states, get_districts_for_state
from src.geolocation_service import GeolocationService, get_approximate_coordinates
from src.validation import (
    validate_farm_profile,
    VALID_SEASONS,
    VALID_LAND_UNITS,
    VALID_SOIL_TYPES,
    VALID_IRRIGATION_METHODS,
    VALID_WATER_AVAILABILITY,
    VALID_CROP_PREFERENCES
)
from src.database import DatabaseManager

st.set_page_config(
    page_title="Farm Profile - KROP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

db: DatabaseManager = st.session_state["db_manager"]
active_profile = st.session_state.get("active_farm_profile")

st.title("🚜 Farm Profile Setup")
st.write(
    "Provide basic geographical and operational details about your farm. "
    "KROP utilizes this information alongside official IMD climate normals and live weather telemetry to recommend suitable crops."
)

# Display existing active profile if configured
if active_profile:
    st.markdown(
        f"""
        <div class="krop-card krop-card-accent" style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1b4332;">📍 Active Profile: {active_profile.get('village', '')} {active_profile.get('district', '')}, {active_profile.get('state', '')}</h4>
                <span class="krop-badge">Profile ID: #{active_profile.get('id', 'Local')}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; font-size: 0.88rem; color: #555b6e;">
                <div>🌾 Land Size: <strong>{active_profile.get('land_area', '')} {active_profile.get('land_unit', '')}</strong></div>
                <div>🌱 Soil Type: <strong>{active_profile.get('soil_type', 'Unknown')}</strong></div>
                <div>💧 Irrigation: <strong>{active_profile.get('irrigation_method', '')} ({active_profile.get('water_availability', '')})</strong></div>
                <div>🗓️ Season: <strong>{active_profile.get('preferred_season', 'Kharif')}</strong></div>
                <div>🎯 Preference: <strong>{active_profile.get('crop_preferences', 'None')}</strong></div>
                <div>🌐 Coords: <strong>{active_profile.get('latitude', 'N/A')}, {active_profile.get('longitude', 'N/A')}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("### 📋 Farm Information Form")

# Form fields
col_loc1, col_loc2, col_loc3 = st.columns(3)

# 1. State
states = get_indian_states()
default_state_idx = 0
if active_profile and active_profile.get("state") in states:
    default_state_idx = states.index(active_profile.get("state"))
elif "Maharashtra" in states:
    default_state_idx = states.index("Maharashtra")

with col_loc1:
    selected_state = st.selectbox("State / Union Territory *", states, index=default_state_idx)

# 2. District
districts = get_districts_for_state(selected_state)
default_dist_idx = 0
if active_profile and active_profile.get("district") in districts:
    default_dist_idx = districts.index(active_profile.get("district"))

with col_loc2:
    selected_district = st.selectbox("District *", districts if districts else ["General District"], index=default_dist_idx if districts else 0)

# 3. Village / Town
with col_loc3:
    village_val = active_profile.get("village", "") if active_profile else ""
    village_input = st.text_input("Village / Town / Taluka (Optional)", value=village_val, placeholder="e.g. Baramati, Rahuri")

# Geocoding Coordinate Search
st.markdown("#### 🌐 Geographical Coordinates Resolution")
st.caption("Coordinates allow KROP to connect to Open-Meteo for real-time temperature, humidity, and 7-day rainfall forecasts.")

col_geo_search, col_geo_res = st.columns([1.5, 2.5])

with col_geo_search:
    search_q = village_input.strip() if village_input.strip() else selected_district
    if st.button("🔍 Resolve Coordinates via Open-Meteo", width="stretch"):
        geo_svc = GeolocationService()
        with st.spinner("Searching Indian geospatial database..."):
            results = geo_svc.search_locations(search_q, state_hint=selected_state)
            st.session_state["geo_results"] = results
            if not results:
                st.warning(f"Could not pinpoint '{search_q}'. Default regional centroid will be utilized.")

geo_candidates = st.session_state.get("geo_results", [])

# Determine coordinates based on confirmed search or regional centroid
is_approximate = True
if geo_candidates:
    options = [c["display_label"] for c in geo_candidates]
    with col_geo_res:
        chosen_label = st.selectbox("Select Confirmed Location Match:", options)
        chosen_rec = next((c for c in geo_candidates if c["display_label"] == chosen_label), geo_candidates[0])
        selected_lat = chosen_rec["latitude"]
        selected_lon = chosen_rec["longitude"]
        is_approximate = chosen_rec.get("is_fallback", False)
        if not is_approximate:
            st.success(f"✅ Exact Coordinates Confirmed: **{chosen_rec['name']}** ({selected_lat:.4f}°N, {selected_lon:.4f}°E)")
        else:
            st.warning(f"⚠️ Approximate Centroid: **{chosen_rec['name']}** ({selected_lat:.4f}°N, {selected_lon:.4f}°E)")
elif active_profile and active_profile.get("state") == selected_state and active_profile.get("district") == selected_district and active_profile.get("latitude"):
    selected_lat = float(active_profile["latitude"])
    selected_lon = float(active_profile["longitude"])
    is_approximate = False
    with col_geo_res:
        st.info(f"📍 Saved Farm Coordinates: **{selected_lat:.4f}°N, {selected_lon:.4f}°E** ({selected_district}, {selected_state})")
else:
    approx = get_approximate_coordinates(selected_state, selected_district)
    selected_lat = approx["latitude"]
    selected_lon = approx["longitude"]
    is_approximate = True
    with col_geo_res:
        st.warning(
            f"⚠️ **Approximate Centroid Active**: Using regional coordinates (**{selected_lat:.4f}°N, {selected_lon:.4f}°E**) for {selected_district}, {selected_state}. "
            "Click **'Resolve Coordinates via Open-Meteo'** for exact village precision."
        )

st.divider()

# Farm Land Characteristics
st.markdown("#### 🌾 Land & Soil Characteristics")

col_land1, col_land2, col_land3 = st.columns(3)

with col_land1:
    default_area = float(active_profile.get("land_area", 2.0)) if active_profile else 2.0
    land_area = st.number_input("Total Cultivable Land Area *", min_value=0.1, max_value=10000.0, value=default_area, step=0.5)

with col_land2:
    default_unit_idx = 0
    if active_profile and active_profile.get("land_unit") in VALID_LAND_UNITS:
        default_unit_idx = VALID_LAND_UNITS.index(active_profile.get("land_unit"))
    land_unit = st.selectbox("Land Measurement Unit *", VALID_LAND_UNITS, index=default_unit_idx)

with col_land3:
    default_soil_idx = 0
    if active_profile and active_profile.get("soil_type") in VALID_SOIL_TYPES:
        default_soil_idx = VALID_SOIL_TYPES.index(active_profile.get("soil_type"))
    soil_type = st.selectbox(
        "Soil Classification (Optional)",
        VALID_SOIL_TYPES,
        index=default_soil_idx,
        help="Soil testing is optional. Choose 'Unknown' if you are unsure; the recommendation system will safely use regional agronomic suitability."
    )

st.markdown(
    """
    <div class="krop-advisory">
        ℹ️ <strong>Soil Flexibility Note</strong>: You are not required to conduct lab soil tests.
        Selecting <em>Unknown</em> allows KROP to evaluate recommendations based purely on proven regional cultivation history, rainfall patterns, and irrigation capacity.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# Water & Operational Preferences
st.markdown("#### 💧 Water Management & Cropping Intent")

col_water1, col_water2 = st.columns(2)

with col_water1:
    default_irrig_idx = 0
    if active_profile and active_profile.get("irrigation_method") in VALID_IRRIGATION_METHODS:
        default_irrig_idx = VALID_IRRIGATION_METHODS.index(active_profile.get("irrigation_method"))
    irrigation_method = st.selectbox("Primary Irrigation Facility *", VALID_IRRIGATION_METHODS, index=default_irrig_idx)

with col_water2:
    default_avail_idx = 1
    if active_profile and active_profile.get("water_availability") in VALID_WATER_AVAILABILITY:
        default_avail_idx = VALID_WATER_AVAILABILITY.index(active_profile.get("water_availability"))
    water_availability = st.selectbox("Water Availability Security *", VALID_WATER_AVAILABILITY, index=default_avail_idx)

col_pref1, col_pref2 = st.columns(2)

with col_pref1:
    default_season_idx = 0
    if active_profile and active_profile.get("preferred_season") in VALID_SEASONS:
        default_season_idx = VALID_SEASONS.index(active_profile.get("preferred_season"))
    preferred_season = st.selectbox(
        "Upcoming Agricultural Season *",
        VALID_SEASONS,
        index=default_season_idx,
        help="Kharif (Monsoon, June-Oct), Rabi (Winter, Oct-March), Summer/Zaid (March-June), Whole Year (Annual crops)."
    )

with col_pref2:
    default_crop_pref_idx = 0
    if active_profile and active_profile.get("crop_preferences") in VALID_CROP_PREFERENCES:
        default_crop_pref_idx = VALID_CROP_PREFERENCES.index(active_profile.get("crop_preferences"))
    crop_preferences = st.selectbox("Crop Preference / Target Commodity", VALID_CROP_PREFERENCES, index=default_crop_pref_idx)

st.markdown("<br>", unsafe_allow_html=True)

# Action Buttons
col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 2.0])

profile_data = {
    "location": f"{village_input}, {selected_district}, {selected_state}".strip(", "),
    "village": village_input.strip(),
    "district": selected_district.strip(),
    "state": selected_state.strip(),
    "latitude": float(selected_lat),
    "longitude": float(selected_lon),
    "land_area": float(land_area),
    "land_unit": land_unit,
    "soil_type": soil_type,
    "irrigation_method": irrigation_method,
    "water_availability": water_availability,
    "preferred_season": preferred_season,
    "crop_preferences": crop_preferences,
}

with col_btn1:
    if st.button("💾 Save Profile", type="primary", width="stretch"):
        is_valid, errors = validate_farm_profile(profile_data)
        if not is_valid:
            for err in errors:
                st.error(f"Validation Error: {err}")
        else:
            if active_profile and active_profile.get("id"):
                db.update_farm_profile(active_profile["id"], profile_data)
                profile_data["id"] = active_profile["id"]
                st.session_state["active_farm_profile"] = profile_data
                st.success("Farm profile updated successfully!")
            else:
                new_id = db.save_farm_profile(profile_data)
                profile_data["id"] = new_id
                st.session_state["active_farm_profile"] = profile_data
                st.success(f"Farm profile created and saved as Profile #{new_id}!")
            st.rerun()

with col_btn2:
    if st.button("🌱 Proceed to Recommendations", width="stretch"):
        st.session_state["active_farm_profile"] = profile_data
        st.switch_page("pages/3_Crop_Recommendations.py")

with col_btn3:
    if active_profile and st.button("➕ Create New / Reset Profile", width="stretch"):
        st.session_state["active_farm_profile"] = None
        st.session_state["geo_results"] = []
        st.info("Reset to blank profile form.")
        st.rerun()
