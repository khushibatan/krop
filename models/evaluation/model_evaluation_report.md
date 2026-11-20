# KROP Machine Learning Model Evaluation Report

**Generated At**: 2026-11-20T20:13:21.246372  
**Model Architecture**: Random Forest Pipeline (ColumnTransformer + Random Forest Classifier, sqrt-area sample weights)  
**Total Training Records**: 165,101  
**Total Test Records**: 41,276  
**Number of Target Crop Classes**: 33  

---

## 1. Summary Performance Metrics

| Metric | Score | Percentage | Agronomic Context |
|---|---|---|---|
| **Top-1 Accuracy (area-weighted)** | `0.6054` | **60.54%** | Share of cultivated area whose crop is the model's single top pick |
| **Top-3 Accuracy (area-weighted)** | `0.8613` | **86.13%** | Share of cultivated area whose crop is in the top 3 candidates |
| **Top-5 Accuracy (area-weighted)** | `0.9344` | **93.44%** | Share of cultivated area whose crop is in the top 5 candidates |
| **Top-1 Accuracy (per record)** | `0.1312` | **13.12%** | Unweighted; every survey record counts equally, including minor crops |
| **Top-3 Accuracy (per record)** | `0.3582` | **35.82%** | Unweighted |
| **Top-5 Accuracy (per record)** | `0.5411` | **54.11%** | Unweighted |
| **Weighted Precision** | `0.1052` | **10.52%** | Precision weighted across crop cultivation frequencies |
| **Weighted Recall** | `0.1312` | **13.12%** | Sensitivity across all target crop classes |
| **Weighted F1-Score** | `0.0841` | **8.41%** | Harmonic balance between precision and recall |
| **Macro F1-Score** | `0.0684` | **6.84%** | Unweighted mean across major and minor crops |

---

## 2. Features Utilized (Zero NPK Compliance)

The model is strictly trained on verifiable geographical, environmental, and farm-scale features:
1. `State_Name` (Categorical, One-Hot Encoded)
2. `Season` (Categorical, One-Hot Encoded: Kharif, Rabi, Summer, Whole Year)
3. `annual_rainfall_mm` (Numerical, Normal annual precipitation from IMD records)
4. `seasonal_rainfall_mm` (Numerical, Normal seasonal precipitation matching crop cycle)
5. `rainfall_ratio` (Numerical, Seasonal rainfall fraction)

Historical `Area` values are district-level totals rather than farm sizes, so they are used only as
training sample weights (square root of cultivated area), not as an input feature.

---

## 3. Top Crops Classification Overview

| Crop | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Arhar/Tur | 0.052 | 0.008 | 0.014 | 1516.0 |
| Bajra | 0.118 | 0.139 | 0.128 | 1085.0 |
| Banana | 0.159 | 0.114 | 0.133 | 642.0 |
| Barley | 0.000 | 0.000 | 0.000 | 840.0 |
| Castor seed | 0.000 | 0.000 | 0.000 | 675.0 |
| Coriander | 0.087 | 0.039 | 0.053 | 674.0 |
| Cotton(lint) | 0.081 | 0.112 | 0.094 | 904.0 |
| Dry chillies | 0.136 | 0.071 | 0.093 | 1298.0 |
| Dry ginger | 0.190 | 0.013 | 0.025 | 602.0 |
| Garlic | 0.153 | 0.029 | 0.049 | 658.0 |
| Gram | 0.101 | 0.075 | 0.086 | 1472.0 |
| Groundnut | 0.160 | 0.068 | 0.095 | 1767.0 |
| Horse-gram | 0.071 | 0.014 | 0.024 | 780.0 |
| Jowar | 0.073 | 0.060 | 0.066 | 1413.0 |
| Linseed | 0.120 | 0.003 | 0.007 | 881.0 |
| Maize | 0.154 | 0.104 | 0.124 | 2790.0 |
| Masoor | 0.000 | 0.000 | 0.000 | 845.0 |
| Moong(Green Gram) | 0.167 | 0.026 | 0.045 | 2064.0 |
| Onion | 0.110 | 0.026 | 0.042 | 1402.0 |
| Peas & beans (Pulses) | 0.000 | 0.000 | 0.000 | 905.0 |

---

## 4. Key Agronomic Conclusions

1. **Candidate Generation Quality**: A **area-weighted Top-5 accuracy of 93.44%** (against a random baseline of 3.0% for a single guess) shows that the ML stage reliably surfaces regionally and seasonally plausible crops for Indian smallholders.
2. **Transparent Decision Support**: The ML output is utilized as a probabilistic candidate generator, which is subsequently validated against soil suitability, irrigation availability, and live weather conditions in the KROP Recommendation Engine.
3. **Zero Nutrient Assumption**: The model makes no assumptions regarding Nitrogen, Phosphorus, or Potassium, honoring real-world farming constraints where smallholder farmers lack laboratory soil testing.
