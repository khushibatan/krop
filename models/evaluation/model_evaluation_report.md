# KROP Machine Learning Model Evaluation Report

**Generated At**: 2026-11-20T17:29:08.401833  
**Model Architecture**: Random Forest Pipeline (ColumnTransformer + Balanced Random Forest Classifier)  
**Total Training Records**: 165,101  
**Total Test Records**: 41,276  
**Number of Target Crop Classes**: 33  

---

## 1. Summary Performance Metrics

| Metric | Score | Percentage | Agronomic Context |
|---|---|---|---|
| **Top-1 Accuracy** | `0.4373` | **43.73%** | Exact match on single highest-ranked crop |
| **Top-3 Recommendation Accuracy** | `0.7341` | **73.41%** | True historical crop falls in top 3 recommended candidates |
| **Top-5 Recommendation Accuracy** | `0.8514` | **85.14%** | True historical crop falls in top 5 recommended candidates |
| **Weighted Precision** | `0.4626` | **46.26%** | Precision weighted across crop cultivation frequencies |
| **Weighted Recall** | `0.4373` | **43.73%** | Sensitivity across all target crop classes |
| **Weighted F1-Score** | `0.4415` | **44.15%** | Harmonic balance between precision and recall |
| **Macro F1-Score** | `0.418` | **41.80%** | Unweighted mean across major and minor crops |

---

## 2. Features Utilized (Zero NPK Compliance)

The model is strictly trained on verifiable geographical, environmental, and farm-scale features:
1. `State_Name` (Categorical, One-Hot Encoded)
2. `Season` (Categorical, One-Hot Encoded: Kharif, Rabi, Summer, Whole Year)
3. `area_hectares` (Numerical, Standard Scaled)
4. `area_category` (Categorical: Marginal, Small, Semi-Medium, Medium, Large)
5. `annual_rainfall_mm` (Numerical, Normal annual precipitation from IMD records)
6. `seasonal_rainfall_mm` (Numerical, Normal seasonal precipitation matching crop cycle)
7. `rainfall_ratio` (Numerical, Seasonal rainfall fraction)

---

## 3. Top Crops Classification Overview

| Crop | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| Arhar/Tur | 0.419 | 0.423 | 0.421 | 1516.0 |
| Bajra | 0.408 | 0.479 | 0.441 | 1085.0 |
| Banana | 0.420 | 0.603 | 0.495 | 642.0 |
| Barley | 0.466 | 0.608 | 0.528 | 840.0 |
| Castor seed | 0.246 | 0.456 | 0.320 | 675.0 |
| Coriander | 0.321 | 0.420 | 0.364 | 674.0 |
| Cotton(lint) | 0.347 | 0.445 | 0.390 | 904.0 |
| Dry chillies | 0.362 | 0.351 | 0.356 | 1298.0 |
| Dry ginger | 0.277 | 0.450 | 0.343 | 602.0 |
| Garlic | 0.315 | 0.456 | 0.373 | 658.0 |
| Gram | 0.521 | 0.433 | 0.473 | 1472.0 |
| Groundnut | 0.417 | 0.333 | 0.370 | 1767.0 |
| Horse-gram | 0.203 | 0.364 | 0.261 | 780.0 |
| Jowar | 0.365 | 0.338 | 0.351 | 1413.0 |
| Linseed | 0.397 | 0.494 | 0.440 | 881.0 |
| Maize | 0.631 | 0.376 | 0.471 | 2790.0 |
| Masoor | 0.422 | 0.575 | 0.487 | 845.0 |
| Moong(Green Gram) | 0.418 | 0.269 | 0.327 | 2064.0 |
| Onion | 0.415 | 0.353 | 0.382 | 1402.0 |
| Peas & beans (Pulses) | 0.354 | 0.445 | 0.395 | 905.0 |

---

## 4. Key Agronomic Conclusions

1. **High Recommendation Accuracy**: A **Top-5 recommendation accuracy exceeding 85%** demonstrates that the ML candidate generation stage reliably identifies regionally and seasonally sound crops for Indian smallholders.
2. **Transparent Decision Support**: The ML output is utilized as a probabilistic candidate generator, which is subsequently validated against soil suitability, irrigation availability, and live weather conditions in the KROP Recommendation Engine.
3. **Zero Nutrient Assumption**: The model makes no assumptions regarding Nitrogen, Phosphorus, or Potassium, honoring real-world farming constraints where smallholder farmers lack laboratory soil testing.
