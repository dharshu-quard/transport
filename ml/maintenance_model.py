import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "maintenance_model.joblib")
REPORT_PATH = os.path.join(REPORT_DIR, "predictive_maintenance_report.json")

def generate_synthetic_fleet_data(n_samples: int = 3000):
    np.random.seed(42)
    mileage_km = np.random.uniform(40000, 450000, size=n_samples)
    days_since_service = np.random.randint(1, 120, size=n_samples)
    past_breakdowns = np.random.poisson(lam=1.5, size=n_samples)
    failed_inspections = np.random.poisson(lam=0.8, size=n_samples)
    engine_temp_avg = np.random.normal(88.0, 7.0, size=n_samples)

    # Risk factor combination
    risk_raw = (
        (mileage_km / 450000.0) * 35.0 +
        (days_since_service / 120.0) * 30.0 +
        (past_breakdowns / 5.0) * 20.0 +
        (failed_inspections / 3.0) * 15.0
    )
    # Target: 0=Low (<35), 1=Moderate (35-65), 2=High (>65)
    risk_class = np.zeros(n_samples, dtype=int)
    risk_class[(risk_raw >= 35) & (risk_raw < 65)] = 1
    risk_class[risk_raw >= 65] = 2

    X = pd.DataFrame({
        "mileage_km": mileage_km,
        "days_since_service": days_since_service,
        "past_breakdowns": past_breakdowns,
        "failed_inspections": failed_inspections,
        "engine_temp_avg": engine_temp_avg
    })
    y = risk_class
    return X, y

def train_maintenance_model():
    X, y = generate_synthetic_fleet_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    clf_rep = classification_report(y_test, y_pred, target_names=["Low", "Moderate", "High"], output_dict=True)

    joblib.dump(model, MODEL_PATH)

    report = {
        "model_name": "Fleet Predictive Maintenance Risk Classifier",
        "algorithm": "RandomForestClassifier(n_estimators=100, max_depth=8)",
        "samples_trained": len(X_train),
        "test_samples": len(X_test),
        "accuracy": round(float(acc), 4),
        "classification_metrics": clf_rep,
        "feature_importances": {
            col: round(float(imp), 4)
            for col, imp in zip(X.columns, model.feature_importances_)
        }
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ML] Predictive maintenance model trained. Accuracy={acc:.4f}")
    return report

def calculate_maintenance_risk(
    mileage_km: float,
    days_since_service: int,
    past_breakdowns: int,
    failed_inspections: int,
    engine_temp_avg: float = 88.0
) -> dict:
    if not os.path.exists(MODEL_PATH):
        train_maintenance_model()
    model = joblib.load(MODEL_PATH)

    df_in = pd.DataFrame([{
        "mileage_km": mileage_km,
        "days_since_service": days_since_service,
        "past_breakdowns": past_breakdowns,
        "failed_inspections": failed_inspections,
        "engine_temp_avg": engine_temp_avg
    }])
    pred_class = int(model.predict(df_in)[0])
    probs = model.predict_proba(df_in)[0]

    # Compute a continuous 0-100 score
    score = (
        (min(mileage_km, 400000.0) / 400000.0) * 35.0 +
        (min(days_since_service, 90) / 90.0) * 30.0 +
        (min(past_breakdowns, 4) / 4.0) * 20.0 +
        (min(failed_inspections, 3) / 3.0) * 15.0
    )
    score = min(100.0, max(5.0, score))

    level_map = {0: "Low", 1: "Moderate", 2: "High"}
    risk_level = level_map[pred_class]

    recommendations = []
    if mileage_km > 250000:
        recommendations.append("Brake shoes and wheel bearing overhaul required.")
    if days_since_service > 45:
        recommendations.append("Engine oil and diesel particulate filter service overdue.")
    if past_breakdowns > 1:
        recommendations.append("Cooling system radiator pressure test needed.")
    if not recommendations:
        recommendations.append("Fleet health optimal. Routine pre-trip checks suffice.")

    return {
        "risk_score": round(score, 1),
        "risk_level": risk_level,
        "failure_probability": round(float(probs[-1]), 3),
        "recommended_actions": recommendations
    }

if __name__ == "__main__":
    train_maintenance_model()
