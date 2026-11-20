# KROP: Smart Crop Planning and Recommendation System

[![Python](https://img.shields.io/badge/Python-3.13+-2d6a4f.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.9-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zero NPK](https://img.shields.io/badge/Zero--NPK-Guaranteed-brightgreen.svg)]()
[![Zero Hardware](https://img.shields.io/badge/Hardware--Free-100%25--Software-success.svg)]()

> **KROP** is an intelligent, software-only agricultural decision-support platform designed specifically for small-scale Indian farmers. It pairs real-time weather intelligence and official climate normals with genuine machine learning to recommend viable, productive crops based on geography, seasonal conditions, irrigation access, and optional soil classification.

---

## 1. Project Introduction

Smallholder farmers constitute over 86% of India's farming population. Many face unpredictable weather aberrations, erratic monsoons, and shifting climatic conditions. Modern crop selection tools frequently demand laboratory soil tests (such as chemical Nitrogen, Phosphorus, and Potassium analyses) or physical IoT sensors that are inaccessible and unaffordable for smallholders.

**KROP** resolves this bottleneck by delivering an evidence-backed, purely software-based decision support system designed around verifiable geographic, climatic, seasonal, and farm management variables.

---

## 2. Problem Statement

Small-scale farmers are frequently forced to make crop selection choices based on tradition or hearsay without access to:
- District-specific long-term rainfall statistics and historical cultivation evidence.
- Real-time weather telemetry and short-term sowing window forecasts.
- Realistic crop water requirements matched against their farm's specific irrigation sources.
- Practical agronomic guidance that does not assume expensive laboratory soil testing.

Existing digital tools often suffer from:
1. **Hardware Dependencies**: Requiring soil moisture probes, IoT microcontrollers (ESP32/Arduino), or Raspberry Pi devices.
2. **Unrealistic Nutrient Demands (NPK)**: Requiring laboratory NPK inputs that smallholders cannot obtain.
3. **Black-Box Hardcoded Mockups**: Displaying static suggestions without genuine machine learning or validated agronomic constraints.

---

## 3. Project Objectives

- **Democratize Agricultural Science**: Provide smallholders with institutional agronomic intelligence from ICAR (Indian Council of Agricultural Research) and the Ministry of Agriculture.
- **Guarantee Zero Hardware & Zero NPK**: Operate completely in software with zero IoT dependencies and zero NPK reliance.
- **Deliver Probabilistic Machine Learning**: Train an ensemble multi-class classification model on over 206,000 real-world Indian agricultural survey records.
- **Integrate Free Live Weather**: Provide real-time temperature, humidity, and 7-day rainfall forecasts via Open-Meteo without requiring paid API keys.
- **Provide Actionable Explainability**: Every recommendation includes plain-language justifications explaining *why* a crop was selected.

---

## 4. Features

- **Intuitive Farm Profile Setup**: Simple, non-technical form capturing state, district, village, land area, irrigation type, water security, upcoming season, and optional soil type.
- **Open-Meteo Geocoding**: Automatic geographical coordinate resolution across Indian villages, towns, and districts.
- **Live Weather Dashboard**: Real-time ambient telemetry and 7-day precipitation forecasts to guide immediate sowing windows.
- **Multi-Factor Recommendation Engine**:
  - Stage 1: Random Forest probabilistic candidate generation (area-weighted Top-5 accuracy of 93%).
  - Stage 2: Season eligibility filtering and water balance verification against farm irrigation and seasonal rainfall normals.
  - Stage 3: Soil type compatibility matching (handles "Unknown" soil without penalty).
  - Stage 4: Live temperature growth-window evaluation.
  - Stage 5: Transparent composite scoring (0–100%) and plain-language evidence generation.
- **ICAR Crop Insights Knowledge Base**: Searchable agronomic catalog for 33 national staple crops with maturity durations, water requirements (in mm), sowing calendars, and cultivation guidance.
- **Persistent SQLite Audit Trail**: Full local ACID-compliant database storing farm profiles and recommendation histories with JSON serialization.
- **Interactive Plotly Visualizations**: Dynamic temperature trends, crop duration comparisons, and historical advisory trends.

---

## 5. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Runtime** | Python | 3.13+ | Core execution runtime |
| **User Interface** | Streamlit | 1.67 | Multipage AgriTech web interface (`st.navigation`) |
| **Machine Learning** | Scikit-learn | 1.9 | Multi-class Random Forest classification pipeline |
| **Model Storage** | Joblib | 1.6 | Pipeline serialization and compressed artifact storage |
| **Data Processing** | Pandas, NumPy | 3.1, 2.5 | Data wrangling, joining, feature extraction |
| **Database** | SQLite 3 | Built-in | Relational persistent storage for profiles & history |
| **Weather API** | Open-Meteo | Free REST API | Live ambient weather & 7-day forecast |
| **Geocoding API** | Open-Meteo Geocoding | Free REST API | Indian village/town/district coordinate search |
| **Visualizations** | Plotly | 7.1 | Interactive charts matching KROP visual identity |
| **Testing** | Pytest, Streamlit AppTest | 9.2 | Unit, integration and headless UI smoke tests |

---

## 6. Project Architecture

```
krop/
├── app.py                           # Entry point: shared setup + st.navigation router
├── pages/
│   ├── 1_Home.py                    # Home dashboard (KPIs, quick actions, weather)
│   ├── 2_Farm_Profile.py            # Farm characteristics, geocoding & profile management
│   ├── 3_Crop_Recommendations.py    # Recommendation generation, transparent ranking & scoring
│   ├── 4_Crop_Insights.py           # ICAR agronomic catalog, category filters & duration charts
│   ├── 5_Recommendation_History.py  # SQLite persistent history, comparisons & record management
│   └── 6_About.py                   # Architecture, objectives, methodology & disclaimers
├── src/
│   ├── __init__.py                  # Package definition
│   ├── config.py                    # Central paths, versions, .env loading, logging setup
│   ├── acquire_data.py              # Automated Kaggle/KaggleHub dataset downloader
│   ├── data_loader.py               # Raw and processed dataset retrieval
│   ├── data_preprocessing.py        # String cleaning, season standardization & IMD joins
│   ├── feature_engineering.py       # Rainfall features, sample weights & inference vectors
│   ├── train_model.py               # Production ML training pipeline & evaluation reporting
│   ├── prediction.py                # Model deserialization & probabilistic candidate inference
│   ├── recommendation_engine.py     # Multi-factor constraint evaluator & explanation generator
│   ├── weather_service.py           # Open-Meteo weather API client with offline caching
│   ├── geolocation_service.py       # Open-Meteo geocoding client with regional fallback
│   ├── crop_information.py          # Curated ICAR agronomic database & filtering
│   ├── database.py                  # SQLite database manager with parameterized queries
│   ├── validation.py                # Input validation for farm profiles and coordinates
│   ├── utils.py                     # Regional lookups for states, districts & rainfall normals
│   └── ui_components.py             # Styling, HTML escaping, shared cards, cached resources
├── data/
│   ├── raw/                         # Raw datasets from official government sources
│   │   ├── crop_production.csv
│   │   ├── district wise rainfall normal.csv
│   │   └── rainfall in india 1901-2015.csv
│   ├── processed/                   # Cleaned, standardized datasets & ICAR catalog
│   │   ├── clean_crop_rainfall.csv
│   │   └── crop_information.csv
│   └── README.md                    # Data provenance and schema documentation
├── models/
│   ├── krop_crop_model.joblib       # Serialized Random Forest Scikit-learn pipeline
│   ├── krop_model_metadata.json     # Feature list, classes, and training metadata
│   ├── evaluation/
│   │   ├── model_evaluation_report.json
│   │   └── model_evaluation_report.md
│   └── .gitkeep
├── database/
│   ├── krop.db                      # Local SQLite database file (created automatically)
│   └── .gitkeep
├── assets/
│   └── images/
│       └── krop_logo.svg            # Vector branding asset
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py          # Data presence and loading tests
│   ├── test_preprocessing.py        # Normalization, brackets & strict zero NPK tests
│   ├── test_model.py                # Pipeline serialization and class tests
│   ├── test_prediction.py           # Candidate inference and probability tests
│   ├── test_recommendation.py       # Constraint ranking, water balance & soil tests
│   ├── test_weather.py              # Mock API tests, offline fallbacks & parsing
│   ├── test_database.py             # SQLite CRUD, rollback, connection-closing tests
│   ├── test_validation.py           # Farm profile and coordinate validation tests
│   ├── test_utils.py                # Regional lookups and crop catalog tests
│   └── test_app.py                  # Headless Streamlit page smoke tests
├── .streamlit/
│   └── config.toml                  # Forest-green theme and server configuration
├── .gitignore                       # Clean repository exclusions
├── LICENSE                          # MIT License
├── requirements.txt                 # Pinned runtime dependencies
├── requirements-dev.txt             # Adds pytest and Kaggle tooling
└── README.md                        # Complete project manual
```

---

## 7. Dataset Sources and Provenance

KROP relies on authentic open government datasets acquired via Kaggle:

1. **Crop Production in India (1997–2015)**
   - *Source*: Directorate of Economics and Statistics, Ministry of Agriculture and Farmers Welfare, Govt of India.
   - *Kaggle Reference*: `abhinand05/crop-production-in-india`
   - *Records*: 246,091 raw records across 33 states/UTs and 646 districts (206,377 remain after restricting to the 33 catalogued crops).
   - *Variables*: State, District, Crop_Year, Season, Crop, Area (ha), Production (tonnes).

2. **Rainfall in India (District Normals & Historical Records)**
   - *Source*: India Meteorological Department (IMD), Ministry of Earth Sciences, Govt of India.
   - *Kaggle Reference*: `rajanand/rainfall-in-india`
   - *Records*: 641 districts with monthly normals (JAN–DEC) and seasonal aggregates (Jun-Sep Monsoon, Oct-Dec Post-Monsoon, Jan-Feb Winter, Mar-May Summer).

3. **ICAR Agronomic Knowledge Base**
   - *Source*: Compiled from Indian Council of Agricultural Research (ICAR) institute monographs (NRRI, IIWBR, IIMR, IIPR, CICR, CPRI, IISR) and State Agricultural University extension guides.
   - *Coverage*: 33 national staple crops detailing category, cycle duration, seasonal water need (mm), optimal temperature range (°C), suitable soil types, and management notes.

---

## 8. Dataset Acquisition

An automated script downloads and extracts the raw datasets using `kagglehub`:

```powershell
python -m src.acquire_data
```

(Requires `pip install -r requirements-dev.txt`.) The script will:
1. Query the Kaggle repository for `abhinand05/crop-production-in-india` and `rajanand/rainfall-in-india`.
2. Extract the CSV archives into `data/raw/`.
3. Validate row counts, columns, and file integrity.
4. If Kaggle API tokens are needed on a fresh machine, set `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env` or place `kaggle.json` in `~/.kaggle/`.

---

## 9. Data Preprocessing

Run the end-to-end data preparation module:

```powershell
python -m src.data_preprocessing
```

Preprocessing operations include:
- Standardizing state and district names for robust joins between agricultural surveys and meteorological normals.
- Mapping cropping seasons (`Autumn` $\rightarrow$ `Kharif`, `Winter` $\rightarrow$ `Rabi`).
- Imputing missing yield/production records via state-crop median baselines.
- Linking district-level normal seasonal rainfall (`Jun-Sep` for Kharif, `Jan-Feb + Oct-Dec` for Rabi, `Mar-May` for Summer, `ANNUAL` for Whole Year).
- Verifying strict zero NPK presence across all output columns.
- Saving clean data to `data/processed/clean_crop_rainfall.csv` (206,377 clean records).

---

## 10. Feature Engineering

Features are engineered with strict consistency between offline training and real-time farmer inference:

- **Geographical**: `State_Name` (Categorical, OneHotEncoded).
- **Seasonal**: `Season` (Categorical: `Kharif`, `Rabi`, `Summer`, `Whole Year`).
- **Climate & Hydrology**:
  - `annual_rainfall_mm` (Numerical, normal total precipitation).
  - `seasonal_rainfall_mm` (Numerical, normal seasonal rainfall).
  - `rainfall_ratio` (Numerical, ratio of seasonal to annual precipitation).
- **Training sample weights**: `sqrt(Area)`. The `Area` column of the survey is the *district-level total* area under a crop, not an individual farm size, so it is deliberately **not** used as a feature (feeding a 2-hectare farm into a model trained on district totals matched smallholders to the wrong kind of record). Weighting by the square root of cultivated area lets regionally dominant crops carry more evidence without letting very large districts swamp minor crops.

The farmer's land area is stored in the profile and converted to hectares (acres, bighas, gunthas supported) for reporting, but it does not alter the ML candidates.

---

## 11. Machine Learning Architecture & Training

The machine learning core is built using a Scikit-learn `Pipeline` composed of:
1. `ColumnTransformer`: One-Hot Encoding for categorical features (`handle_unknown='ignore'`), and `StandardScaler` for numerical metrics.
2. `RandomForestClassifier`: 60 estimators, max depth of 20, trained with `sqrt(Area)` sample weights across 33 target classes.

### Training the Model

Run the training script from the project root:

```powershell
python -m src.train_model
```

The script trains the model on an 80/20 stratified split, calculates comprehensive performance metrics, serializes the pipeline into `models/krop_crop_model.joblib`, and outputs evaluation reports to `models/evaluation/`.

---

## 12. Model Evaluation Results

Evaluated on 41,276 held-out survey records (stratified 80/20 split) from the 206k-record dataset:

| Metric | Area-weighted | Per record | Interpretation |
|---|---|---|---|
| **Top-1** | **60.54%** | 13.12% | The model's single best pick matches the crop grown on that share of cultivated area. |
| **Top-3** | **86.13%** | 35.82% | A historically grown crop is in the top 3 candidates. |
| **Top-5** | **93.44%** | 54.11% | A historically grown crop is in the top 5 candidates (random baseline for a single guess: 3.03%). |

*Area-weighted* metrics weight each test record by its cultivated area, which reflects what farmers actually grow. *Per-record* metrics count every record equally, so many tiny minor-crop records pull them down; they are reported for transparency. Because inputs are regional (state, season, rainfall), the model is a candidate generator, not a final decision-maker: the agronomic stages below re-rank its output.

*Detailed per-crop statistics are saved in `models/evaluation/model_evaluation_report.md`. Re-running training regenerates these numbers.*

---

## 13. Hybrid Recommendation & Ranking Engine

Rather than relying on a black-box model alone, KROP uses a hybrid decision-support architecture:

```
[Farmer Farm Profile] + [Live Open-Meteo Weather] + [District IMD Normals]
                         │
                         ▼
             [Feature Engineering Vector]
                         │
                         ▼
        [Random Forest Pipeline Inference]
           (Season-eligible Top 12 Candidates)
                         │
                         ▼
          [Agronomic Constraint Evaluation]
         ├── Water Balance (Farm Irrigation vs Crop Water Need)
         ├── Soil Type Compatibility (ICAR Guidelines)
         ├── Ambient Temperature Window Suitability
         └── Farmer Commodity Preference Alignment
                         │
                         ▼
         [Transparent Composite Scoring (0-100%)]
                         │
                         ▼
  [Top 3-5 Ranked Crops with Evidence-Based Explanations]
```

### Composite Score Formula

$$\text{Composite Score} = 0.35 \times S_{\text{model}} + 0.25 \times S_{\text{water}} + 0.15 \times S_{\text{soil}} + 0.15 \times S_{\text{weather}} + 0.10 \times S_{\text{preference}}$$

- $S_{\text{model}}$ is the candidate's predicted probability relative to the strongest eligible candidate, square-root compressed to $100\sqrt{p / p_{\max}}$ so runners-up stay visible when one staple dominates a region.
- Crops that cannot be grown in the chosen season (per the ICAR catalog) are excluded before scoring; perennial *Whole Year* crops remain eligible.
- When the farmer does not specify soil type, the 15% soil weight is redistributed (+5% model, +10% water balance): $0.40\,S_{\text{model}} + 0.35\,S_{\text{water}} + 0.15\,S_{\text{weather}} + 0.10\,S_{\text{preference}}$, without penalizing any crop.

---

## 14. Weather Intelligence

Integrated directly with Open-Meteo:
- **Geocoding API**: Resolves village, taluka, town, or district names to geographic coordinates in India.
- **Weather API**: Provides real-time 2m temperature (°C), relative humidity (%), current precipitation (mm), wind speed (km/h), and 7-day daily precipitation sums.
- **Offline Resiliency**: Built-in state centroid coordinates and seasonal baselines guarantee that the application continues running even during internet interruptions or API downtime.

---

## 15. Database Design

Local persistent SQLite database stored at `database/krop.db`:

### `farm_profiles` Table
- `id` (INTEGER PRIMARY KEY)
- `location`, `village`, `district`, `state` (TEXT)
- `latitude`, `longitude` (REAL)
- `land_area` (REAL), `land_unit` (TEXT)
- `soil_type`, `irrigation_method`, `water_availability` (TEXT)
- `preferred_season`, `crop_preferences` (TEXT)
- `created_at`, `updated_at` (TEXT ISO 8601)

### `recommendations` Table
- `id` (INTEGER PRIMARY KEY)
- `farm_profile_id` (INTEGER FOREIGN KEY $\rightarrow$ `farm_profiles.id`)
- `recommended_crops` (TEXT JSON array of ranked crops, scores, and explanations)
- `weather_summary` (TEXT JSON snapshot of ambient weather at recommendation time)
- `recommendation_details` (TEXT JSON full payload)
- `model_version` (TEXT)
- `created_at` (TEXT ISO 8601)

---

## 16. Installation & Execution Guide

### Prerequisites
- macOS, Linux or Windows
- Python 3.13+ (the pinned dependency versions require it)

### Setup

```bash
# 1. Enter the project directory
cd krop

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1

# 3. Install dependencies (requirements-dev.txt adds pytest and data-acquisition tools)
pip install -r requirements-dev.txt

# 4. (Optional) Re-acquire raw datasets, rebuild clean data and retrain the model.
#    The repository already ships with data and a trained model.
python -m src.acquire_data
python -m src.data_preprocessing
python -m src.train_model

# 5. Run automated tests
pytest -v

# 6. Launch the Streamlit application
streamlit run app.py
```

Configuration is optional: copy `.env.example` to `.env` to change `DATABASE_PATH`. All paths resolve relative to the project root, so commands work from any directory.

The application will start locally at:
👉 **`http://localhost:8501`**

---

## 17. Automated Testing

The project includes an automated test suite (unit, integration and headless UI tests) across all modules:

```powershell
pytest -v
```

### Test Coverage Highlights:
- `tests/test_data_loader.py`: Verifies dataset presence and schema loading.
- `tests/test_preprocessing.py`: Validates string normalization, landholding brackets, and enforces strict zero NPK checks.
- `tests/test_model.py`: Confirms Joblib deserialization and verifies area-weighted Top-5 accuracy exceeds 80%.
- `tests/test_prediction.py`: Validates probabilistic outputs and input validation.
- `tests/test_recommendation.py`: Tests constraint ranking, unknown soil resilience, and drought penalization.
- `tests/test_weather.py`: Mocks external API calls to test offline timeouts and parsing.
- `tests/test_database.py`: Tests SQLite CRUD, foreign keys, rollback, connection cleanup and JSON serialization.
- `tests/test_validation.py` / `tests/test_utils.py`: Input validation, rainfall resolution order and crop catalog lookups.
- `tests/test_app.py`: Renders every Streamlit page headlessly (with and without a profile, network mocked off) and checks that user text is HTML-escaped.

---

## 18. Deployment Guide

### Deploying to Streamlit Community Cloud
1. Push this repository to GitHub.
2. In Streamlit Community Cloud, click **New App**.
3. Select the repository, your default branch, and set the main file path to `app.py`.
4. Deploy!

> **Note on Cloud Persistence**: Ephemeral cloud hosts reset local SQLite storage on container rebuilds. For permanent multi-user cloud production, connect `src/database.py` to a managed PostgreSQL service (e.g. Supabase, Neon, or Cloud SQL) (the current implementation is SQLite-only, so a managed database requires adapting `src/database.py`).

---

## 19. Limitations

- **Historical Reporting Horizon**: Agricultural statistics reflect historical survey years up to 2015.
- **Short-Term Weather vs. Full Season**: Open-Meteo forecasts cover a 7-day immediate window, which assists sowing timing but does not replace full-monsoon seasonal forecasting.
- **District Boundary Changes**: Certain recently bifurcated districts map to their parent administrative district normals.

---

## 20. Future Scope

The modular architecture is designed for seamless future extensions without altering the core pipeline:
1. **Market Price & Mandi Trends**: Integrating Agmarknet API for real-time commodity pricing.
2. **Crop Profitability Estimation**: Net revenue estimation per acre based on state cost of cultivation surveys.
3. **Multilingual Interface**: Hindi, Marathi, Telugu, Tamil, and Punjabi localization.
4. **Voice-Assisted Navigation**: Regional voice querying for illiterate farmers.
5. **Computer Vision Disease Diagnosis**: Leaf disease classification using mobile camera uploads.

---

## 21. Agricultural Disclaimer

> **ADVISORY NOTICE**:  
> KROP is an artificial intelligence decision-support platform designed for educational, informational, and preliminary agricultural planning. Cultivation decisions should always be cross-referenced with ground soil observations, local seed availability, mandi prices, and advisories from your local Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer. The authors assume no liability for agricultural shortfalls, weather anomalies, or economic losses.

---

## 22. License

Distributed under the MIT License. See `LICENSE` for details.
