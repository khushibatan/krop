# KROP Data Repository Documentation

This directory contains authentic agricultural and meteorological datasets sourced from official open government datasets via Kaggle for the **KROP (Smart Crop Planning and Recommendation System)**.

> **CRITICAL ARCHITECTURAL GUARANTEE**:
> Neither these datasets nor any derived data contain Nitrogen, Phosphorus, Potassium (NPK) measurements. KROP is strictly built on geographical, environmental, seasonal, and agricultural management information.

---

## 1. India Agriculture Crop Production Dataset

- **Dataset Name**: Crop Production in India
- **Kaggle URL**: [https://www.kaggle.com/datasets/abhinand05/crop-production-in-india](https://www.kaggle.com/datasets/abhinand05/crop-production-in-india)
- **Original Source**: Ministry of Agriculture & Farmers Welfare, Directorate of Economics and Statistics, Government of India.
- **Author**: Abhinand
- **License**: CC0: Public Domain / Open Government Data License - India (OGDL)
- **Raw File Name**: `data/raw/crop_production.csv`
- **Number of Records**: 246,091 rows, 7 columns
- **Download Procedure**:
  - Automated download via `src/acquire_data.py` utilizing `kagglehub.dataset_download('abhinand05/crop-production-in-india')` or Kaggle API CLI `kaggle datasets download -d abhinand05/crop-production-in-india`.
- **Columns**:
  - `State_Name`: Name of the Indian State/UT (e.g., Maharashtra, Punjab, Tamil Nadu, Uttar Pradesh).
  - `District_Name`: Administrative district within the state (e.g., PUNE, LUDHIANA, COIMBATORE).
  - `Crop_Year`: Agricultural year of cultivation (1997 to 2015).
  - `Season`: Cropping season (`Kharif`, `Rabi`, `Whole Year`, `Summer`, `Autumn`, `Winter`).
  - `Crop`: Name of the cultivated crop (124 distinct crops e.g., Rice, Wheat, Maize, Cotton, Gram, Groundnut, Sugarcane).
  - `Area`: Land area under cultivation (in Hectares).
  - `Production`: Total agricultural yield production (in Metric Tonnes, or nuts for Coconut).
- **Preprocessing Performed**:
  - Stripping leading/trailing whitespaces in state, district, crop, and season names.
  - Standardizing season categories (`Kharif`, `Rabi`, `Summer`/`Zaid`, `Whole Year`).
  - Imputing/filtering null production values (accounting for missing statistics in certain remote districts).
  - Computing `Yield = Production / Area` (Tonnes/Hectare) with outlier capping.
- **Limitations**:
  - Covers historical reporting up to 2015.
  - Some districts do not report production for minor horticulture crops.

---

## 2. Rainfall in India (District Normals & Historical Records)

- **Dataset Name**: Rainfall in India (1901-2015 & District-wise Rainfall Normals)
- **Kaggle URL**: [https://www.kaggle.com/datasets/rajanand/rainfall-in-india](https://www.kaggle.com/datasets/rajanand/rainfall-in-india)
- **Original Source**: India Meteorological Department (IMD), Ministry of Earth Sciences, Government of India.
- **Author**: Raj Anand
- **License**: CC0: Public Domain / Open Government Data License - India
- **Raw File Names**:
  - `data/raw/district wise rainfall normal.csv` (641 rows, 19 columns)
  - `data/raw/rainfall in india 1901-2015.csv` (4,116 rows, 19 columns)
- **Download Procedure**:
  - Automated download via `src/acquire_data.py` using `kagglehub.dataset_download('rajanand/rainfall-in-india')` or `kaggle datasets download -d rajanand/rainfall-in-india`.
- **Columns**:
  - `STATE_UT_NAME`: Standard state or Union Territory name.
  - `DISTRICT`: Name of the district (641 districts covered).
  - `JAN` through `DEC`: Long-term normal precipitation for each month (in millimeters).
  - `ANNUAL`: Cumulative normal annual rainfall (mm).
  - `Jan-Feb`, `Mar-May`, `Jun-Sep` (Southwest Monsoon), `Oct-Dec` (Northeast/Post-monsoon): Seasonal aggregate normals in millimeters.
- **Preprocessing Performed**:
  - Upper-case normalization and fuzzy name resolution between district names in crop statistics and IMD rainfall records.
  - Extracting seasonal rainfall variables (`monsoon_rainfall_mm`, `winter_rainfall_mm`, `annual_rainfall_mm`).
- **Limitations**:
  - District boundaries reflect historical administrative delineations. Recent district bifurcations are mapped to their parent administrative zones.

---

## 3. Crop Agronomic Profiles and Reference Information

- **Processed File**: `data/processed/crop_information.csv`
- **Origin**: Curated from Indian Council of Agricultural Research (ICAR), Krishi Vigyan Kendras (KVK), and State Agricultural University (SAU) crop production guides.
- **Key Columns**:
  - `crop_name`: Canonical crop name matching production datasets.
  - `crop_category`: `Cereals`, `Pulses`, `Oilseeds`, `Cash/Commercial Crops`, `Vegetables`, `Fruits`, `Spices`, `Fibre`.
  - `suitable_seasons`: Suitable cropping seasons (`Kharif`, `Rabi`, `Zaid/Summer`, `Whole Year`).
  - `growing_duration_days`: Typical crop cycle length from sowing to maturity.
  - `water_requirement`: Water requirement category (`Low`, `Medium`, `High`, `Very High`) and estimated seasonal requirement in mm.
  - `suitable_soil`: Suitable soil types (`Alluvial`, `Black`, `Red`, `Laterite`, `Sandy Loam`, `Clay Loam`, etc.).
  - `sowing_period`: Standard sowing window in major agricultural zones.
  - `temperature_conditions`: Optimal ambient temperature range (°C).
  - `cultivation_notes`: Essential agronomic guidance for Indian farmers.
  - `regional_information`: Key producing states and agro-climatic zones in India.
  - `information_source`: Official ICAR / KVK reference publication.
