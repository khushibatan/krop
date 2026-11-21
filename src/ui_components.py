"""
KROP - UI Components and Styling Module
Provides consistent styling, custom CSS, sidebar branding, and Plotly color themes.
Refined AgriTech design: Forest green (#1b4332, #2d6a4f), leaf green (#52b788),
warm neutral backgrounds (#f8f9fa), clean card styling.
"""

from html import escape
from typing import Any, Dict, Optional

import streamlit as st

from src.config import APP_VERSION, LOGO_PATH
from src.database import DatabaseManager
from src.recommendation_engine import RecommendationEngine

# Color Palette Constants
COLOR_FOREST_DARK = "#1b4332"
COLOR_PRIMARY_GREEN = "#2d6a4f"
COLOR_LEAF_GREEN = "#52b788"
COLOR_LIGHT_BG = "#f8f9fa"
COLOR_ACCENT_BG = "#e8f5e9"
COLOR_CARD_BORDER = "#d8e2dc"
COLOR_TEXT_MUTED = "#555b6e"
COLOR_WARNING = "#d97706"
COLOR_DANGER = "#b91c1c"

CUSTOM_CSS = """
<style>
    /* Global Styles */
    .stApp {
        background-color: #f8f9fa;
        color: #1b4332;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }

    /* Headings */
    h1, h2, h3, h4 {
        color: #1b4332 !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Primary Buttons */
    .stButton>button {
        background-color: #2d6a4f !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1.25rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 4px rgba(45, 106, 79, 0.2) !important;
    }
    .stButton>button:hover {
        background-color: #1b4332 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 8px rgba(27, 67, 50, 0.3) !important;
        transform: translateY(-1px);
    }

    /* AgriTech Cards */
    .krop-card {
        background: #ffffff;
        border: 1px solid #e0e5e2;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .krop-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
    .krop-card-accent {
        border-left: 5px solid #2d6a4f;
    }

    /* Recommendation Highlight Card */
    .krop-rec-box {
        background: #ffffff;
        border: 1px solid #d8e2dc;
        border-left: 6px solid #2d6a4f;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(45, 106, 79, 0.06);
    }

    /* Metric Badges */
    .krop-badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 20px;
        background-color: #e8f5e9;
        color: #2d6a4f;
        margin-right: 0.4rem;
        border: 1px solid #c8e6c9;
    }
    .krop-badge-gold {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    /* Advisory Box */
    .krop-advisory {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        color: #1e3a8a;
        font-size: 0.95rem;
        margin-top: 0.75rem;
    }
    
    /* Warning Box */
    .krop-warning {
        background-color: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        color: #92400e;
        font-size: 0.95rem;
        margin-top: 0.75rem;
    }

    /* Sidebar Cleanliness */
    [data-testid="stSidebar"] {
        background-color: #edf2f4 !important;
        border-right: 1px solid #d8e2dc;
    }
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #1b4332 !important;
    }
</style>
"""


def esc(value: Any) -> str:
    """HTML-escapes any value so user-supplied text can be embedded safely in unsafe_allow_html blocks."""
    return escape("" if value is None else str(value))


def apply_custom_styles() -> None:
    """Applies modern AgriTech CSS styling across the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_sidebar_header() -> None:
    """Renders product branding and the active farm profile in the sidebar."""
    with st.sidebar:
        if LOGO_PATH.exists():
            svg_data = LOGO_PATH.read_text(encoding="utf-8")
            st.markdown(
                f'<div style="text-align: center; margin-bottom: 0.5rem;">{svg_data}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<h2 style="color: #2d6a4f; margin-bottom: 0;">🌾 KROP</h2>'
                '<p style="color: #52b788; font-size: 0.85rem; font-weight: 600;">SMART CROP PLANNING SYSTEM</p>',
                unsafe_allow_html=True,
            )

        st.caption("Decisions based on geography, seasonal normals & live weather. Zero hardware, zero NPK.")
        st.divider()

        profile = st.session_state.get("active_farm_profile")
        if profile:
            st.markdown(
                f"""
                <div style="background: #ffffff; padding: 0.75rem; border-radius: 8px; border: 1px solid #d8e2dc; font-size: 0.85rem;">
                    <strong>📍 Active Farm Profile</strong><br>
                    <span>{esc(profile.get('district'))}, {esc(profile.get('state'))}</span><br>
                    <span style="color: #555b6e;">Season: {esc(profile.get('preferred_season', 'Kharif'))} | Area: {esc(profile.get('land_area'))} {esc(profile.get('land_unit', 'Acres'))}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No active farm profile selected. Go to **Farm Profile** to set up.")

        st.divider()
        st.markdown(
            f'<div style="font-size: 0.75rem; color: #555b6e; text-align: center;">'
            f'KROP v{APP_VERSION} &bull; ICAR & IMD Sourced<br>Built for Indian Smallholder Farmers</div>',
            unsafe_allow_html=True,
        )


@st.cache_resource(show_spinner=False)
def get_db_manager() -> DatabaseManager:
    """Shared database manager (one per server process)."""
    return DatabaseManager()


@st.cache_resource(show_spinner="Loading crop recommendation model...")
def get_recommendation_engine() -> RecommendationEngine:
    """Shared recommendation engine; the ML pipeline is loaded once per server process."""
    return RecommendationEngine()


def init_session_state() -> None:
    """Initializes persistent application session state."""
    if "db_manager" not in st.session_state:
        st.session_state["db_manager"] = get_db_manager()
    if "active_farm_profile" not in st.session_state:
        st.session_state["active_farm_profile"] = st.session_state["db_manager"].get_latest_farm_profile()
    st.session_state.setdefault("latest_recommendation", None)
    st.session_state.setdefault("weather_cache", None)


def flash(message: str, kind: str = "success") -> None:
    """Queues a message that survives the next st.rerun() and is shown by show_flash()."""
    st.session_state["_flash"] = (kind, message)


def show_flash() -> None:
    """Displays and clears any queued flash message."""
    pending = st.session_state.pop("_flash", None)
    if pending:
        kind, message = pending
        {"success": st.success, "warning": st.warning, "error": st.error}.get(kind, st.info)(message)


def weather_card_html(
    weather: Dict[str, Any],
    title: str,
    subtitle: Optional[str] = None,
    live_label: str = "LIVE",
    offline_label: str = "SEASONAL AVG",
) -> str:
    """Returns the weather summary card as a single, self-contained HTML block."""
    curr = weather.get("current", {})
    forecast = weather.get("forecast_summary", {})
    badge = live_label if weather.get("is_live") else offline_label
    sub = f'<div style="font-size: 0.85rem; color: #555b6e; margin-bottom: 0.8rem;">{esc(subtitle)}</div>' if subtitle else ""
    cell = 'background: #f8f9fa; padding: 0.5rem; border-radius: 6px;'
    return f"""
    <div class="krop-card" style="border-top: 4px solid #52b788;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 700; font-size: 1.1rem; color: #1b4332;">{esc(title)}</span>
            <span class="krop-badge">{esc(badge)}</span>
        </div>
        {sub}<div style="display: flex; align-items: baseline; gap: 1rem; margin: 0.5rem 0;">
            <span style="font-size: 2.2rem; font-weight: 800; color: #2d6a4f;">{curr.get('temperature_c', 25.0):.1f}°C</span>
            <span style="color: #555b6e; font-size: 1rem;">{esc(curr.get('condition', 'Clear'))}</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.8rem; font-size: 0.88rem;">
            <div style="{cell}">💧 Humidity: <strong>{curr.get('humidity_pct', 50):.0f}%</strong></div>
            <div style="{cell}">💨 Wind: <strong>{curr.get('wind_speed_kmh', 5):.1f} km/h</strong></div>
            <div style="{cell}">🌧️ Current Rain: <strong>{curr.get('precipitation_mm', 0.0):.1f} mm</strong></div>
            <div style="{cell}">📅 7-Day Forecast Rain: <strong>{forecast.get('total_rain_7days_mm', 0.0):.1f} mm</strong></div>
        </div>
    </div>
    """


def get_plotly_theme(**overrides):
    """Returns consistent Plotly layout settings matching KROP visual identity."""
    theme = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#1b4332", family="'Segoe UI', sans-serif"),
        colorway=["#2d6a4f", "#52b788", "#74c69d", "#95d5b2", "#d8f3dc", "#b7e4c7"],
        xaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#e5e7eb"),
        yaxis=dict(gridcolor="#e5e7eb", zerolinecolor="#e5e7eb"),
    )
    for key, value in overrides.items():
        if key in ("xaxis", "yaxis") and isinstance(value, dict):
            theme[key] = {**theme[key], **value}
        else:
            theme[key] = value
    return theme
