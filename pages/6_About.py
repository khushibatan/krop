"""
KROP - Page 6: About KROP
Comprehensive project documentation, technology stack, ML methodology, and agricultural disclaimers.
Strictly zero hardware dependencies, absolutely ZERO NPK.
"""

import streamlit as st
import json
from pathlib import Path

from src.ui_components import (
    apply_custom_styles,
    render_sidebar_header,
    init_session_state
)

st.set_page_config(
    page_title="About KROP - Smart Crop Planning System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
init_session_state()
render_sidebar_header()

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
        | **Language** | Python 3.13 | Core programming and computational runtime |
        | **Frontend UI** | Streamlit | Modern, accessible, interactive AgriTech web interface |
        | **Machine Learning** | Scikit-learn (RandomForest) | Multi-class probabilistic crop suitability candidate generation |
        | **Data Processing** | Pandas, NumPy | Cleaning, standardizing, joining, and engineering features across 240k+ records |
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
    eval_json_path = Path("models/evaluation/model_evaluation_report.json")
    if eval_json_path.exists():
        with open(eval_json_path, "r") as f:
            eval_data = json.load(f)
        m = eval_data.get("metrics", {})
        
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Top-1 Exact Match", f"{m.get('top_1_accuracy', 0)*100:.2f}%", "Single Highest Crop")
        c_m2.metric("Top-3 Recommendation", f"{m.get('top_3_accuracy', 0)*100:.2f}%", "In Top 3 Candidates")
        c_m3.metric("Top-5 Recommendation", f"{m.get('top_5_accuracy', 0)*100:.2f}%", "In Top 5 Candidates")
        c_m4.metric("Weighted F1 Score", f"{m.get('weighted_f1_score', 0)*100:.2f}%", "Balanced Evaluation")

    st.markdown(
        """
        #### 1. Input Features
        The model is strictly trained on verifiable environmental and operational parameters:
        - `State_Name` (Categorical, OneHotEncoded)
        - `Season` (Categorical: Kharif, Rabi, Summer, Whole Year)
        - `area_hectares` (Numerical, StandardScaled)
        - `area_category` (Categorical: Marginal <1ha, Small 1-2ha, Semi-Medium 2-4ha, Medium 4-10ha, Large >10ha)
        - `annual_rainfall_mm` (Numerical, IMD normal annual precipitation)
        - `seasonal_rainfall_mm` (Numerical, IMD normal seasonal precipitation)
        - `rainfall_ratio` (Numerical, Seasonal / Annual fraction)

        #### 2. Hybrid Recommendation Scoring
        Unlike naive black-box models, KROP uses a hybrid architecture:
        - **Stage 1 (ML Candidate Generation)**: Predicts probability distribution across 33 staple crops.
        - **Stage 2 (Agronomic Validation)**: Evaluates soil compatibility (ICAR guidelines), water requirements vs farm irrigation, and live weather conditions.
        - **Stage 3 (Transparent Composite Ranking)**:
          $$\\text{Score} = 0.35 \\times \\text{Model} + 0.25 \\times \\text{Water} + 0.15 \\times \\text{Soil} + 0.15 \\times \\text{Weather} + 0.10 \\times \\text{Preference}$$
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
