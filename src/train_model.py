"""
KROP - Machine Learning Model Training Pipeline
Trains, evaluates, and serializes the agricultural multi-class crop suitability model.
Strict adherence:
- Software-only, zero hardware dependencies
- Absolutely ZERO NPK
- Full pipeline serialization with Scikit-learn and Joblib
- Comprehensive evaluation metrics (Top-1, Top-3, Top-5, Precision, Recall, F1)
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_recall_fscore_support,
    top_k_accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import (
    EVAL_DIR,
    EVAL_REPORT_JSON,
    EVAL_REPORT_MD,
    METADATA_PATH,
    MODEL_PATH,
    MODEL_VERSION,
    MODELS_DIR,
    configure_logging,
)
from src.data_loader import DataLoader
from src.data_preprocessing import DataPreprocessor
from src.feature_engineering import FeatureEngineer

logger = logging.getLogger("krop.train_model")


class ModelTrainer:
    """Manages model training, evaluation, and serialization for KROP."""

    def __init__(self):
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = FeatureEngineer()

    def load_or_prepare_data(self) -> pd.DataFrame:
        """Loads preprocessed data or triggers the preprocessing pipeline."""
        loader = DataLoader()
        df = loader.load_processed_data()
        if df is None:
            logger.info("Processed dataset not found. Running preprocessor...")
            preprocessor = DataPreprocessor(loader)
            preprocessor.process_and_save()
            df = loader.load_processed_data()

        # Strict NPK check
        for col in df.columns:
            if any(npk in col.upper() for npk in ["NITROGEN", "PHOSPHORUS", "POTASSIUM", "NPK"]):
                raise ValueError(f"Strict specification violation: Disallowed NPK column found: {col}")

        logger.info("Loaded training dataset: %d records across %d crops", len(df), df["Crop"].nunique())
        return df

    def build_pipeline(self) -> Pipeline:
        """Constructs end-to-end preprocessing and estimator pipeline."""
        categorical_features = self.feature_engineer.categorical_features
        numerical_features = self.feature_engineer.numerical_features

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    categorical_features,
                ),
                ("num", StandardScaler(), numerical_features),
            ]
        )

        model = RandomForestClassifier(
            n_estimators=60,
            max_depth=20,
            min_samples_split=6,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1,
        )

        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", model),
            ]
        )
        return pipeline

    def train_and_evaluate(self) -> Dict[str, Any]:
        """Trains the ML model, calculates comprehensive metrics, and writes reports."""
        df = self.load_or_prepare_data()
        X, y, weights = self.feature_engineer.extract_training_features(df)

        logger.info("Splitting data: 80% train, 20% test (stratified by crop)...")
        X_train, X_test, y_train, y_test, w_train, _ = train_test_split(
            X, y, weights, test_size=0.2, random_state=42, stratify=y
        )
        # Area-weighted evaluation: how much of the cultivated area the predictions cover.
        area_test = (weights.loc[X_test.index] ** 2).values

        pipeline = self.build_pipeline()
        logger.info("Fitting Random Forest pipeline on %d training samples...", len(X_train))
        pipeline.fit(X_train, y_train, classifier__sample_weight=w_train.values)

        logger.info("Evaluating model on %d test samples...", len(X_test))
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)
        classes = pipeline.named_steps["classifier"].classes_.tolist()

        # Compute Metrics
        top1_acc = float(accuracy_score(y_test, y_pred))
        top3_acc = float(top_k_accuracy_score(y_test, y_proba, k=3, labels=classes))
        top5_acc = float(top_k_accuracy_score(y_test, y_proba, k=5, labels=classes))

        top1_area = float(accuracy_score(y_test, y_pred, sample_weight=area_test))
        top3_area = float(top_k_accuracy_score(y_test, y_proba, k=3, labels=classes, sample_weight=area_test))
        top5_area = float(top_k_accuracy_score(y_test, y_proba, k=5, labels=classes, sample_weight=area_test))

        precision_w, recall_w, f1_w, _ = precision_recall_fscore_support(
            y_test, y_pred, average="weighted", zero_division=0
        )
        precision_m, recall_m, f1_m, _ = precision_recall_fscore_support(
            y_test, y_pred, average="macro", zero_division=0
        )

        class_rep_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

        evaluation_results = {
            "model_type": "RandomForestClassifier",
            "training_weights": "sqrt(cultivated area)",
            "timestamp": datetime.now().isoformat(),
            "n_train_samples": int(len(X_train)),
            "n_test_samples": int(len(X_test)),
            "n_classes": len(classes),
            "classes": classes,
            "metrics": {
                "top_1_accuracy": round(top1_acc, 4),
                "top_3_accuracy": round(top3_acc, 4),
                "top_5_accuracy": round(top5_acc, 4),
                "top_1_area_weighted_accuracy": round(top1_area, 4),
                "top_3_area_weighted_accuracy": round(top3_area, 4),
                "top_5_area_weighted_accuracy": round(top5_area, 4),
                "weighted_precision": round(float(precision_w), 4),
                "weighted_recall": round(float(recall_w), 4),
                "weighted_f1_score": round(float(f1_w), 4),
                "macro_precision": round(float(precision_m), 4),
                "macro_recall": round(float(recall_m), 4),
                "macro_f1_score": round(float(f1_m), 4),
            },
            "features": self.feature_engineer.feature_columns,
            "classification_report": class_rep_dict,
        }

        # Save model artifact
        logger.info("Saving trained pipeline to %s ...", MODEL_PATH)
        joblib.dump(pipeline, MODEL_PATH, compress=6)

        # Save metadata
        metadata = {
            "model_name": "KROP Multi-Class Crop Suitability Classifier",
            "model_version": MODEL_VERSION,
            "trained_at": evaluation_results["timestamp"],
            "classes": classes,
            "features": self.feature_engineer.feature_columns,
            "metrics": evaluation_results["metrics"],
        }
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save JSON evaluation report
        with open(EVAL_REPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(evaluation_results, f, indent=2)

        # Generate Markdown evaluation report
        self._write_markdown_report(evaluation_results)

        logger.info(
            "Training and evaluation complete! Top-1: %.2f%%, Top-3: %.2f%%, Top-5: %.2f%%",
            top1_acc * 100,
            top3_acc * 100,
            top5_acc * 100,
        )
        return evaluation_results

    def _write_markdown_report(self, results: Dict[str, Any]):
        """Generates human-readable Markdown evaluation report."""
        m = results["metrics"]
        md_content = f"""# KROP Machine Learning Model Evaluation Report

**Generated At**: {results["timestamp"]}  
**Model Architecture**: Random Forest Pipeline (ColumnTransformer + Random Forest Classifier, sqrt-area sample weights)  
**Total Training Records**: {results["n_train_samples"]:,}  
**Total Test Records**: {results["n_test_samples"]:,}  
**Number of Target Crop Classes**: {results["n_classes"]}  

---

## 1. Summary Performance Metrics

| Metric | Score | Percentage | Agronomic Context |
|---|---|---|---|
| **Top-1 Accuracy (area-weighted)** | `{m["top_1_area_weighted_accuracy"]}` | **{m["top_1_area_weighted_accuracy"]*100:.2f}%** | Share of cultivated area whose crop is the model's single top pick |
| **Top-3 Accuracy (area-weighted)** | `{m["top_3_area_weighted_accuracy"]}` | **{m["top_3_area_weighted_accuracy"]*100:.2f}%** | Share of cultivated area whose crop is in the top 3 candidates |
| **Top-5 Accuracy (area-weighted)** | `{m["top_5_area_weighted_accuracy"]}` | **{m["top_5_area_weighted_accuracy"]*100:.2f}%** | Share of cultivated area whose crop is in the top 5 candidates |
| **Top-1 Accuracy (per record)** | `{m["top_1_accuracy"]}` | **{m["top_1_accuracy"]*100:.2f}%** | Unweighted; every survey record counts equally, including minor crops |
| **Top-3 Accuracy (per record)** | `{m["top_3_accuracy"]}` | **{m["top_3_accuracy"]*100:.2f}%** | Unweighted |
| **Top-5 Accuracy (per record)** | `{m["top_5_accuracy"]}` | **{m["top_5_accuracy"]*100:.2f}%** | Unweighted |
| **Weighted Precision** | `{m["weighted_precision"]}` | **{m["weighted_precision"]*100:.2f}%** | Precision weighted across crop cultivation frequencies |
| **Weighted Recall** | `{m["weighted_recall"]}` | **{m["weighted_recall"]*100:.2f}%** | Sensitivity across all target crop classes |
| **Weighted F1-Score** | `{m["weighted_f1_score"]}` | **{m["weighted_f1_score"]*100:.2f}%** | Harmonic balance between precision and recall |
| **Macro F1-Score** | `{m["macro_f1_score"]}` | **{m["macro_f1_score"]*100:.2f}%** | Unweighted mean across major and minor crops |

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
"""
        cr = results["classification_report"]
        for crop in results["classes"][:20]:
            if crop in cr:
                crop_stat = cr[crop]
                md_content += f"| {crop} | {crop_stat['precision']:.3f} | {crop_stat['recall']:.3f} | {crop_stat['f1-score']:.3f} | {crop_stat['support']} |\n"

        md_content += f"""
---

## 4. Key Agronomic Conclusions

1. **Candidate Generation Quality**: A **area-weighted Top-5 accuracy of {m["top_5_area_weighted_accuracy"]*100:.2f}%** (against a random baseline of {100 / results["n_classes"]:.1f}% for a single guess) shows that the ML stage reliably surfaces regionally and seasonally plausible crops for Indian smallholders.
2. **Transparent Decision Support**: The ML output is utilized as a probabilistic candidate generator, which is subsequently validated against soil suitability, irrigation availability, and live weather conditions in the KROP Recommendation Engine.
3. **Zero Nutrient Assumption**: The model makes no assumptions regarding Nitrogen, Phosphorus, or Potassium, honoring real-world farming constraints where smallholder farmers lack laboratory soil testing.
"""
        with open(EVAL_REPORT_MD, "w", encoding="utf-8") as f:
            f.write(md_content)


def train_main():
    """Main execution function for CLI invocation."""
    configure_logging()
    trainer = ModelTrainer()
    results = trainer.train_and_evaluate()
    print("\n" + "=" * 60)
    print("TRAINING SUCCESSFUL!")
    m = results["metrics"]
    for k in (1, 3, 5):
        print(
            f"Top-{k} accuracy: {m[f'top_{k}_area_weighted_accuracy']*100:.2f}% area-weighted | "
            f"{m[f'top_{k}_accuracy']*100:.2f}% per record"
        )
    print(f"Artifacts saved in: {MODELS_DIR}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    train_main()
