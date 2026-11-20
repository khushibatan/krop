# KROP: Smart Crop Planning and Recommendation System

[![Python](https://img.shields.io/badge/Python-3.13-2d6a4f.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.6+-F7931E.svg)](https://scikit-learn.org/)
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
  - Stage 1: Random Forest probabilistic candidate generation (Top-5 Accuracy > 85%).
  - Stage 2: Water balance verification against farm irrigation and seasonal rainfall normals.
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
| **User Interface** | Streamlit | >= 1.30.0 | Responsive AgriTech web interface |
| **Machine Learning** | Scikit-learn | >= 1.3.0 | Multi-class Random Forest classification pipeline |
| **Model Storage** | Joblib | >= 1.3.0 | Pipeline serialization and compressed artifact storage |
| **Data Processing** | Pandas, NumPy | >= 2.0.0, >= 1.24.0 | Data wrangling, joining, feature extraction |
| **Database** | SQLite 3 | Built-in | Relational persistent storage for profiles & history |
| **Weather API** | Open-Meteo | Free REST API | Live ambient weather & 7-day forecast |
| **Geocoding API** | Open-Meteo Geocoding | Free REST API | Indian village/town/district coordinate search |
| **Visualizations** | Plotly | >= 5.18.0 | Interactive charts matching KROP visual identity |
| **Testing** | Pytest | >= 8.0.0 | Automated unit and integration testing suite |

---

## 6. Project Architecture

```
krop/
├── app.py                           # Main application entry point & dashboard
├── pages/
│   ├── 1_Home.py                    # Home dashboard view
│   ├── 2_Farm_Profile.py            # Farm characteristics, geocoding & profile management
│   ├── 3_Crop_Recommendations.py    # Recommendation generation, transparent ranking & scoring
│   ├── 4_Crop_Insights.py           # ICAR agronomic catalog, category filters & duration charts
│   ├── 5_Recommendation_History.py  # SQLite persistent history, comparisons & record management
│   └── 6_About.py                   # Architecture, objectives, methodology & disclaimers
├── src/
│   ├── __init__.py                  # Package definition
│   ├── acquire_data.py              # Automated Kaggle/KaggleHub dataset downloader
│   ├── data_loader.py               # Raw and processed dataset retrieval
│   ├── data_preprocessing.py        # String cleaning, season standardization & IMD joins
│   ├── feature_engineering.py       # Landholding brackets, rainfall ratios & inference vectors
│   ├── train_model.py               # Production ML training pipeline & evaluation reporting
│   ├── prediction.py                # Model deserialization & probabilistic candidate inference
│   ├── recommendation_engine.py     # Multi-factor constraint evaluator & explanation generator
│   ├── weather_service.py           # Open-Meteo weather API client with offline caching
│   ├── geolocation_service.py       # Open-Meteo geocoding client with regional fallback
│   ├── crop_information.py          # Curated ICAR agronomic database & filtering
│   ├── database.py                  # SQLite database manager with parameterized queries
│   ├── validation.py                # Input validation for farm profiles and coordinates
│   ├── utils.py                     # Regional lookups for states, districts & rainfall normals
│   └── ui_components.py             # Custom AgriTech styling, badges & Plotly themes
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
│   └── test_database.py             # SQLite CRUD and JSON serialization tests
├── .streamlit/
│   └── config.toml                  # Forest-green theme and server configuration
├── .gitignore                       # Clean repository exclusions
├── requirements.txt                 # Pinned, tested dependencies
└── README.md                        # Complete project manual
```

---

## 7. Dataset Sources and Provenance

KROP relies on authentic open government datasets acquired via Kaggle:

1. **Crop Production in India (1997–2015)**
   - *Source*: Directorate of Economics and Statistics, Ministry of Agriculture and Farmers Welfare, Govt of India.
   - *Kaggle Reference*: `abhinand05/crop-production-in-india`
   - *Records*: 246,091 records across 33 states/UTs and 646 districts.
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
python src/acquire_data.py
```

The script will:
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
- **Farm Scale**:
  - `area_hectares` (Numerical, StandardScaled).
  - `area_category` (Categorical: `Marginal` < 1ha, `Small` 1–2ha, `Semi-Medium` 2–4ha, `Medium` 4–10ha, `Large` > 10ha based on official Indian Agriculture Census classifications).
- **Climate & Hydrology**:
  - `annual_rainfall_mm` (Numerical, normal total precipitation).
  - `seasonal_rainfall_mm` (Numerical, normal seasonal rainfall).
  - `rainfall_ratio` (Numerical, ratio of seasonal to annual precipitation).

---

## 11. Machine Learning Architecture & Training

The machine learning core is built using a Scikit-learn `Pipeline` composed of:
1. `ColumnTransformer`: One-Hot Encoding for categorical features (`handle_unknown='ignore'`), and `StandardScaler` for numerical metrics.
2. `RandomForestClassifier`: 150 estimators, max depth of 25, balanced subsample weighting to handle rare staple crops across 33 target classes.

### Training the Model

Execute the training script from Windows PowerShell:

```powershell
python -m src.train_model
```

The script trains the model on an 80/20 stratified split, calculates comprehensive performance metrics, serializes the pipeline into `models/krop_crop_model.joblib`, and outputs evaluation reports to `models/evaluation/`.

---

## 12. Model Evaluation Results

Evaluated on 41,276 unseen test records from the 206k survey dataset:

| Metric | Score | Agronomic Interpretation |
|---|---|---|
| **Top-1 Exact Match** | **43.73%** | Exact match on a single highest-predicted crop out of 33 options (random baseline is 3.03%). |
| **Top-3 Recommendation Accuracy** | **73.41%** | A regionally viable historical crop is present in the top 3 recommendations. |
| **Top-5 Recommendation Accuracy** | **85.14%** | Over 85% probability that the candidate list contains a historically proven regional crop. |
| **Weighted F1 Score** | **44.15%** | Harmonic mean of precision and recall weighted by crop cultivation frequencies. |

*Detailed per-crop precision, recall, and support statistics are saved in `models/evaluation/model_evaluation_report.md`.*

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
           (Top 12 Candidate Probabilities)
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

*(When the farmer does not specify soil type, the 15% soil weight is automatically redistributed to model confidence and water balance without penalizing the recommendation).*

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
- Windows 10 or 11 (64-bit)
- Python 3.10+ (tested on Python 3.13)
- Git for Windows

### Step-by-Step Windows PowerShell Setup

```powershell
# 1. Clone or open the repository directory
cd c:\Users\dell7420\Desktop\code\krop

# 2. Create the Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Acquire raw datasets (if not already present in data/raw)
python src/acquire_data.py

# 6. Preprocess data and generate clean datasets
python -m src.data_preprocessing

# 7. Train the machine learning model
python -m src.train_model

# 8. Run automated tests
pytest -v

# 9. Launch the Streamlit application
streamlit run app.py
```

The application will start locally at:
👉 **`http://localhost:8501`**

---

## 17. Automated Testing

The project includes an automated test suite with 28 comprehensive test cases across all modules:

```powershell
pytest -v
```

### Test Coverage Highlights:
- `tests/test_data_loader.py`: Verifies dataset presence and schema loading.
- `tests/test_preprocessing.py`: Validates string normalization, landholding brackets, and enforces strict zero NPK checks.
- `tests/test_model.py`: Confirms Joblib deserialization and verifies Top-5 accuracy exceeds 80%.
- `tests/test_prediction.py`: Validates probabilistic outputs and input validation.
- `tests/test_recommendation.py`: Tests constraint ranking, unknown soil resilience, and drought penalization.
- `tests/test_weather.py`: Mocks external API calls to test offline timeouts and parsing.
- `tests/test_database.py`: Tests SQLite CRUD, foreign keys, and JSON serialization.

---

## 18. Deployment Guide

### Deploying to Streamlit Community Cloud
1. Push this repository to GitHub.
2. In Streamlit Community Cloud, click **New App**.
3. Select the repository, branch `main`, and set the main file path to `app.py`.
4. Deploy!

> **Note on Cloud Persistence**: Ephemeral cloud hosts reset local SQLite storage on container rebuilds. For permanent multi-user cloud production, connect `src/database.py` to a managed PostgreSQL service (e.g. Supabase, Neon, or Cloud SQL) by setting `DATABASE_URL` in environment secrets.

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
