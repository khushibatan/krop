"""
KROP - Smart Crop Planning and Recommendation System
Application entry point: shared page setup and multipage navigation.

Run with:  streamlit run app.py
"""

import streamlit as st

from src.ui_components import apply_custom_styles, init_session_state, render_sidebar_header

st.set_page_config(
    page_title="KROP - Smart Crop Planning System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

navigation = st.navigation([
    st.Page("pages/1_Home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/2_Farm_Profile.py", title="Farm Profile", icon="🚜"),
    st.Page("pages/3_Crop_Recommendations.py", title="Crop Recommendations", icon="🌱"),
    st.Page("pages/4_Crop_Insights.py", title="Crop Insights", icon="📖"),
    st.Page("pages/5_Recommendation_History.py", title="Recommendation History", icon="📜"),
    st.Page("pages/6_About.py", title="About", icon="ℹ️"),
])
navigation.run()
