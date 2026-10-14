import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "demand_model.joblib")
REPORT_PATH = os.path.join(REPORT_DIR, "demand_prediction_report.json")

def generate_synthetic_demand_data(n_samples: int = 5000):
    np.random.seed(42)
    # Features: route_index (0-19), hour_of_day (5-23), day_of_week (0-6), is_weekend (0/1), base_demand
    route_indices = np.random.randint(0, 20, size=n_samples)
    hours = np.random.randint(5, 24, size=n_samples)
    days = np.random.randint(0, 7, size=n_samples)
    is_weekend = (days >= 5).astype(int)

    # Peak hour effect: morning 7-10, evening 17-20
    is_peak = (((hours >= 7) & (hours <= 10)) | ((hours >= 17) & (hours <= 20))).astype(int)

    # Base capacity is ~50 seats. Demand surges during peak and weekends for intercity
    base = 22 + (route_indices % 5) * 4
    demand = (
        base +
        is_peak * np.random.uniform(18, 28, size=n_samples) +
        is_weekend * np.random.uniform(6, 14, size=n_samples) +
        np.random.normal(0, 3.5, size=n_samples)
    )
    demand = np.clip(demand, 5, 60) # Capped at reasonable bus passenger load

    X = pd.DataFrame({
        "route_index": route_indices,
        "hour_of_day": hours,
        "day_of_week": days,
        "is_weekend": is_weekend,
        "is_peak": is_peak
    })
    y = demand
    return X, y

def train_demand_model():
    X, y = generate_synthetic_demand_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    joblib.dump(model, MODEL_PATH)

    report = {
        "model_name": "Route Passenger Demand Predictor",
        "algorithm": "RandomForestRegressor(n_estimators=100, max_depth=10)",
        "samples_trained": len(X_train),
        "test_samples": len(X_test),
        "metrics": {
            "mean_absolute_error_passengers": round(float(mae), 3),
            "root_mean_squared_error": round(float(rmse), 3),
            "r2_score": round(float(r2), 4)
        },
        "feature_importances": {
            col: round(float(imp), 4)
            for col, imp in zip(X.columns, model.feature_importances_)
        }
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ML] Demand model trained successfully. R2={r2:.4f}, MAE={mae:.2f}")
    return report

def predict_demand(route_index: int, hour_of_day: int, day_of_week: int) -> float:
    if not os.path.exists(MODEL_PATH):
        train_demand_model()
    model = joblib.load(MODEL_PATH)
    is_weekend = 1 if day_of_week >= 5 else 0
    is_peak = 1 if ((7 <= hour_of_day <= 10) or (17 <= hour_of_day <= 20)) else 0
    X_single = pd.DataFrame([{
        "route_index": route_index,
        "hour_of_day": hour_of_day,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_peak": is_peak
    }])
    pred = model.predict(X_single)[0]
    return round(float(pred), 1)

if __name__ == "__main__":
    train_demand_model()
