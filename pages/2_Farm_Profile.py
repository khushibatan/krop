"""
KROP - Farm Profile Management
Simple, accessible farm information collection for smallholder Indian farmers.
"""

import streamlit as st

from src.database import DatabaseManager
from src.geolocation_service import GeolocationService, get_approximate_coordinates
from src.ui_components import esc, flash, show_flash
from src.utils import get_districts_for_state, get_indian_states
from src.validation import (
    VALID_CROP_PREFERENCES,
    VALID_IRRIGATION_METHODS,
    VALID_LAND_UNITS,
    VALID_SEASONS,
    VALID_SOIL_TYPES,
    VALID_WATER_AVAILABILITY,
    validate_farm_profile,
)

db: DatabaseManager = st.session_state["db_manager"]
active_profile = st.session_state.get("active_farm_profile") or {}


def index_of(options, value, default=0):
    """Index of value in options, or default when absent (used to pre-fill saved selections)."""
    return options.index(value) if value in options else default


st.title("🚜 Farm Profile Setup")
st.write(
    "Provide basic geographical and operational details about your farm. "
    "KROP uses this information alongside official IMD climate normals and live weather telemetry to recommend suitable crops."
)
show_flash()

if active_profile:
    st.markdown(
        f"""
        <div class="krop-card krop-card-accent" style="margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0; color: #1b4332;">📍 Active Profile: {esc(active_profile.get('village'))} {esc(active_profile.get('district'))}, {esc(active_profile.get('state'))}</h4>
                <span class="krop-badge">Profile ID: #{esc(active_profile.get('id', 'unsaved'))}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; font-size: 0.88rem; color: #555b6e;">
                <div>🌾 Land Size: <strong>{esc(active_profile.get('land_area'))} {esc(active_profile.get('land_unit'))}</strong></div>
                <div>🌱 Soil Type: <strong>{esc(active_profile.get('soil_type', 'Unknown'))}</strong></div>
                <div>💧 Irrigation: <strong>{esc(active_profile.get('irrigation_method'))} ({esc(active_profile.get('water_availability'))})</strong></div>
                <div>🗓️ Season: <strong>{esc(active_profile.get('preferred_season', 'Kharif'))}</strong></div>
                <div>🎯 Preference: <strong>{esc(active_profile.get('crop_preferences', 'None'))}</strong></div>
                <div>🌐 Coords: <strong>{esc(active_profile.get('latitude', 'N/A'))}, {esc(active_profile.get('longitude', 'N/A'))}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### 📋 Farm Information Form")

# ---- Location ----
col_loc1, col_loc2, col_loc3 = st.columns(3)

states = get_indian_states()
saved_state = active_profile.get("state")
default_state = saved_state if saved_state in states else ("Maharashtra" if "Maharashtra" in states else None)
with col_loc1:
    selected_state = st.selectbox("State / Union Territory *", states, index=index_of(states, default_state))

districts = get_districts_for_state(selected_state)
with col_loc2:
    selected_district = st.selectbox(
        "District *", districts or ["General District"],
        index=index_of(districts, active_profile.get("district")),
    )

with col_loc3:
    village_input = st.text_input(
        "Village / Town / Taluka (Optional)", value=active_profile.get("village") or "", placeholder="e.g. Baramati, Rahuri"
    ).strip()

# ---- Coordinates ----
st.markdown("#### 🌐 Geographical Coordinates Resolution")
st.caption("Coordinates allow KROP to connect to Open-Meteo for real-time temperature, humidity, and 7-day rainfall forecasts.")

search_query = village_input or selected_district
search_signature = (selected_state, selected_district, village_input)
col_geo_search, col_geo_res = st.columns([1.5, 2.5])

with col_geo_search:
    if st.button("🔍 Resolve Coordinates via Open-Meteo", width="stretch"):
        with st.spinner("Searching Indian geospatial database..."):
            results = GeolocationService().search_locations(search_query, state_hint=selected_state)
        st.session_state["geo_results"] = results
        st.session_state["geo_signature"] = search_signature
        if not results:
            st.warning(f"Could not pinpoint '{search_query}'. A regional centroid will be used.")

# Search results are only valid for the location they were requested for.
geo_candidates = (
    st.session_state.get("geo_results", []) if st.session_state.get("geo_signature") == search_signature else []
)

if geo_candidates:
    labels = [c["display_label"] for c in geo_candidates]
    with col_geo_res:
        chosen = geo_candidates[labels.index(st.selectbox("Select Confirmed Location Match:", labels))]
        selected_lat, selected_lon = chosen["latitude"], chosen["longitude"]
        if chosen.get("is_fallback"):
            st.warning(f"⚠️ Approximate Centroid: **{chosen['name']}** ({selected_lat:.4f}°N, {selected_lon:.4f}°E)")
        else:
            st.success(f"✅ Coordinates Confirmed: **{chosen['name']}** ({selected_lat:.4f}°N, {selected_lon:.4f}°E)")
elif (
    active_profile.get("state") == selected_state
    and active_profile.get("district") == selected_district
    and active_profile.get("latitude") is not None
):
    selected_lat, selected_lon = float(active_profile["latitude"]), float(active_profile["longitude"])
    with col_geo_res:
        st.info(f"📍 Saved Farm Coordinates: **{selected_lat:.4f}°N, {selected_lon:.4f}°E** ({selected_district}, {selected_state})")
else:
    approx = get_approximate_coordinates(selected_state, selected_district)
    selected_lat, selected_lon = approx["latitude"], approx["longitude"]
    with col_geo_res:
        st.warning(
            f"⚠️ **Approximate Centroid Active**: Using regional coordinates (**{selected_lat:.4f}°N, {selected_lon:.4f}°E**) "
            f"for {selected_district}, {selected_state}. Click **'Resolve Coordinates via Open-Meteo'** for village precision."
        )

st.divider()

# ---- Land & soil ----
st.markdown("#### 🌾 Land & Soil Characteristics")
col_land1, col_land2, col_land3 = st.columns(3)

with col_land1:
    land_area = st.number_input(
        "Total Cultivable Land Area *", min_value=0.1, max_value=10000.0,
        value=float(active_profile.get("land_area") or 2.0), step=0.5,
    )
with col_land2:
    land_unit = st.selectbox(
        "Land Measurement Unit *", VALID_LAND_UNITS, index=index_of(VALID_LAND_UNITS, active_profile.get("land_unit"))
    )
with col_land3:
    soil_type = st.selectbox(
        "Soil Classification (Optional)", VALID_SOIL_TYPES,
        index=index_of(VALID_SOIL_TYPES, active_profile.get("soil_type")),
        help="Soil testing is optional. Choose 'Unknown' if you are unsure; the recommendation system will safely use regional agronomic suitability.",
    )

st.markdown(
    """
    <div class="krop-advisory">
        ℹ️ <strong>Soil Flexibility Note</strong>: You are not required to conduct lab soil tests.
        Selecting <em>Unknown</em> allows KROP to evaluate recommendations based purely on proven regional cultivation history,
        rainfall patterns, and irrigation capacity.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ---- Water & intent ----
st.markdown("#### 💧 Water Management & Cropping Intent")
col_water1, col_water2 = st.columns(2)
with col_water1:
    irrigation_method = st.selectbox(
        "Primary Irrigation Facility *", VALID_IRRIGATION_METHODS,
        index=index_of(VALID_IRRIGATION_METHODS, active_profile.get("irrigation_method")),
    )
with col_water2:
    water_availability = st.selectbox(
        "Water Availability Security *", VALID_WATER_AVAILABILITY,
        index=index_of(VALID_WATER_AVAILABILITY, active_profile.get("water_availability"), default=1),
    )

col_pref1, col_pref2 = st.columns(2)
with col_pref1:
    preferred_season = st.selectbox(
        "Upcoming Agricultural Season *", VALID_SEASONS,
        index=index_of(VALID_SEASONS, active_profile.get("preferred_season")),
        help="Kharif (Monsoon, June-Oct), Rabi (Winter, Oct-March), Summer/Zaid (March-June), Whole Year (Annual crops).",
    )
with col_pref2:
    crop_preferences = st.selectbox(
        "Crop Preference / Target Commodity", VALID_CROP_PREFERENCES,
        index=index_of(VALID_CROP_PREFERENCES, active_profile.get("crop_preferences")),
    )

st.markdown("<br>", unsafe_allow_html=True)

profile_data = {
    "location": ", ".join(part for part in (village_input, selected_district, selected_state) if part),
    "village": village_input,
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


def save_profile() -> bool:
    """Validates and persists the form as the active profile. Returns True on success."""
    is_valid, errors = validate_farm_profile(profile_data)
    if not is_valid:
        for err in errors:
            st.error(f"Validation Error: {err}")
        return False

    profile_id = active_profile.get("id")
    if profile_id and db.update_farm_profile(profile_id, profile_data):
        message = "Farm profile updated successfully!"
    else:
        profile_id = db.save_farm_profile(profile_data)
        message = f"Farm profile created and saved as Profile #{profile_id}!"
    st.session_state["active_farm_profile"] = {**profile_data, "id": profile_id}
    st.session_state["latest_recommendation"] = None  # force fresh advice for the new inputs
    flash(message)
    return True


col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1.5, 2.0])

with col_btn1:
    if st.button("💾 Save Profile", type="primary", width="stretch") and save_profile():
        st.rerun()

with col_btn2:
    if st.button("🌱 Save & Get Recommendations", width="stretch") and save_profile():
        st.switch_page("pages/3_Crop_Recommendations.py")

with col_btn3:
    if active_profile and st.button("➕ Create New / Reset Profile", width="stretch"):
        st.session_state["active_farm_profile"] = None
        st.session_state["latest_recommendation"] = None
        st.session_state["geo_results"] = []
        flash("Form reset. Fill in the details to create a new farm profile.", "warning")
        st.rerun()
