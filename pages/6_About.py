"""
KROP - About
Comprehensive project documentation, technology stack, ML methodology, and agricultural disclaimers.
"""

import json

import streamlit as st

from src.config import EVAL_REPORT_JSON

st.title("🌾 About KROP")
st.subheader("Smart Crop Planning and Recommendation System")
st.write(
    "KROP is an intelligent, software-only agricultural decision-support platform designed specifically for "
    "small-scale Indian farmers. It makes data-driven crop selection accessible to farmers who may not have access "
    "to advanced agricultural testing facilities, soil laboratories, or technical knowledge."
)

st.markdown(
    """
    <div class="krop-card krop-card-accent" style="margin: 1.5rem 0;">
        <h4 style="margin-top: 0; color: #1b4332;">🛡️ Absolute Architectural Commitments</h4>
        <ul style="margin: 0.5rem 0 0 1.2rem; font-size: 0.95rem; color: #2b2d42; line-height: 1.6;">
            <li><strong>100% Software-Based</strong>: Zero hardware dependencies whatsoever. No physical soil sensors, IoT devices, ESP32, Arduino, or embedded components.</li>
            <li><strong>STRICTLY ZERO NPK</strong>: Nitrogen, Phosphorus, and Potassium (NPK) measurements are completely out of scope. KROP does not rely on synthetic nutrient tables or artificial soil values, acknowledging that Indian smallholders cannot practically afford laboratory chemical soil testing.</li>
            <li><strong>Genuine Machine Learning</strong>: Powered by Scikit-learn Random Forest classification trained on 206,000+ authentic Ministry of Agriculture historical cultivation records.</li>
            <li><strong>Open & Accessible</strong>: Utilizes free open-access APIs (Open-Meteo) and open government data (OGDL India).</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4 = st.tabs(["🚀 Core Objectives", "💻 Technology Stack", "🤖 ML Methodology", "📜 Agricultural Disclaimer"])

with tab1:
    st.markdown("### 🎯 Objectives & Design Principles")
    col_ob1, col_ob2 = st.columns(2)
    with col_ob1:
        st.markdown(
            """
            1. **Accessibility**: Farmers input only simple farm characteristics they know directly: state, district, village, land area, water availability, and irrigation type.
            2. **Simplicity**: No technical chemical soil tests required; soil type is entirely optional.
            3. **Location Awareness**: Models and rainfall normals adapt specifically to the farmer's state and administrative district.
            4. **Weather Intelligence**: Direct real-time and 7-day forecast integration via Open-Meteo API.
            """
        )
    with col_ob2:
        st.markdown(
            """
            5. **Evidence-Based Explainability**: Every recommendation includes understandable reasons citing historical cultivation success, water fit, and ICAR advisory notes.
            6. **Reliability**: Transparent distinction between ML model probability, agronomic constraint suitability, and historical frequency.
            7. **Offline Resiliency**: Fallback regional climate normals ensure the system functions smoothly even during external API downtime.
            8. **Data Persistence**: Local SQLite database securely archives farm profiles and recommendation histories.
            """
        )

with tab2:
    st.markdown("### 🛠️ Technology Stack")
    st.markdown(
        """
        | Component | Technology | Role in KROP |
        |---|---|---|
        | **Language** | Python 3.13+ | Core programming and computational runtime |
        | **Frontend UI** | Streamlit | Modern, accessible, interactive AgriTech web interface |
        | **Machine Learning** | Scikit-learn (RandomForest) | Multi-class probabilistic crop suitability candidate generation |
        | **Data Processing** | Pandas, NumPy | Cleaning, standardizing, joining, and engineering features across 200k+ records |
        | **Model Serialization** | Joblib | High-efficiency compression and deserialization of ML pipelines |
        | **Database** | SQLite 3 | Relational, ACID-compliant persistence for farm profiles and advisories |
        | **Weather Integration** | Open-Meteo API | Free, unauthenticated live weather telemetry and 7-day forecasts |
        | **Geocoding** | Open-Meteo Geocoding API | Resolution of Indian villages, talukas, towns, and districts to coordinates |
        | **Data Visualization** | Plotly Express & Graph Objects | Dynamic charts for rainfall normals, temperature trends, and score comparisons |
        | **Quality Assurance** | Pytest | Comprehensive test suite covering data, ML, weather, recommendations, and DB |
        """
    )

with tab3:
    st.markdown("### 🧠 Machine Learning Engine Architecture")
    
    # Read model evaluation metadata if available
    if EVAL_REPORT_JSON.exists():
        m = json.loads(EVAL_REPORT_JSON.read_text(encoding="utf-8")).get("metrics", {})

        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.metric("Top-1 (area-weighted)", f"{m.get('top_1_area_weighted_accuracy', 0)*100:.1f}%", "Single top pick", delta_color="off")
        c_m2.metric("Top-3 (area-weighted)", f"{m.get('top_3_area_weighted_accuracy', 0)*100:.1f}%", "In top 3 candidates", delta_color="off")
        c_m3.metric("Top-5 (area-weighted)", f"{m.get('top_5_area_weighted_accuracy', 0)*100:.1f}%", "In top 5 candidates", delta_color="off")
        st.caption(
            "Area-weighted: the share of historically cultivated area whose crop appears among the model's top picks. "
            f"Per-record Top-5 accuracy is {m.get('top_5_accuracy', 0)*100:.1f}% because minor crops with tiny records "
            "count equally there. The model is a candidate generator; final ranking applies agronomic validation."
        )

    st.markdown(
        """
        #### 1. Input Features
        The model is strictly trained on verifiable environmental and operational parameters:
        - `State_Name` (Categorical, OneHotEncoded)
        - `Season` (Categorical: Kharif, Rabi, Summer, Whole Year)
        - `annual_rainfall_mm` (Numerical, IMD normal annual precipitation)
        - `seasonal_rainfall_mm` (Numerical, IMD normal seasonal precipitation)
        - `rainfall_ratio` (Numerical, Seasonal / Annual fraction)

        Historical `Area` figures are district totals, not farm sizes, so they weight training samples
        (square root of cultivated area) instead of acting as a feature. Your farm size is recorded in your
        profile but does not change the ML candidates.

        #### 2. Hybrid Recommendation Scoring
        Unlike naive black-box models, KROP uses a hybrid architecture:
        - **Stage 1 (ML Candidate Generation)**: Predicts probability distribution across 33 staple crops.
        - **Stage 2 (Agronomic Validation)**: Evaluates soil compatibility (ICAR guidelines), water requirements vs farm irrigation, and live weather conditions.
        - **Stage 3 (Transparent Composite Ranking)**:
          $$\\text{Score} = 0.35 \\times \\text{Model} + 0.25 \\times \\text{Water} + 0.15 \\times \\text{Soil} + 0.15 \\times \\text{Weather} + 0.10 \\times \\text{Preference}$$
          When soil type is unknown, its 15% moves to the model (+5%) and water balance (+10%).
        """
    )

with tab4:
    st.markdown("### ⚠️ Agricultural & Legal Disclaimer")
    st.markdown(
        """
        <div class="krop-warning">
            <strong>Important Agricultural Advisory Notice:</strong><br>
            KROP is an artificial intelligence and machine learning powered decision-support platform designed for educational, informational, and preliminary agricultural planning purposes.
            <ul style="margin-top: 0.5rem; margin-bottom: 0.2rem;">
                <li>Crop cultivation decisions should always consider local ground observations, market prices, seed availability, and local Krishi Vigyan Kendra (KVK) advisories.</li>
                <li>Weather forecasts provided through external APIs are subject to natural meteorological variance. Short-term forecasts do not predict entire seasonal monsoon trends.</li>
                <li>The developers and researchers of KROP assume no legal liability for crop yield shortfalls, weather aberrations, pest infestations, or economic losses arising from the use of this software.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
