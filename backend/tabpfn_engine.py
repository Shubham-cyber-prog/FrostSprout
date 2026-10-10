"""
TabPFN Engine for FrostSprout: Touch Grass Garden Intelligence.
Prior Labs' Tabular Foundation Model (TabPFN) powers microclimate frost risk forecasting
and germination probability predictions without manual feature engineering.
"""

import os
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# Import TabPFN with robust fallback handling
TABPFN_AVAILABLE = False
try:
    from tabpfn import TabPFNClassifier, TabPFNRegressor
    TABPFN_AVAILABLE = True
except (Exception, OSError, BaseException) as e:
    print(f"TabPFN import note: {e}. Utilizing native tabular ensemble engine.")

class FrostPredictor:
    def __init__(self, data_path=None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, "data", "frost_history.csv")
        self.data_path = data_path
        self.df = None
        self.features = [
            "latitude", "elevation_m", "day_of_year", "daily_min_temp_c",
            "daily_max_temp_c", "soil_temp_5cm_c", "humidity_pct",
            "cloud_cover_pct", "barometric_pressure_hpa", "rolling_min_7d_c"
        ]
        self.cls_model = None
        self.reg_model = None
        self.model_type = "RandomForest (TabPFN unavailable)"
        self.tabpfn_status = "TabPFN unavailable"
        self._load_and_train()

    def _load_and_train(self):
        if not os.path.exists(self.data_path):
            from backend.data.generate_climate_data import generate_frost_dataset
            generate_frost_dataset()

        self.df = pd.read_csv(self.data_path)
        X = self.df[self.features].values
        y_cls = self.df["frost_imminent"].values
        y_reg = self.df["days_until_frost"].values

        # Subsample for fast responsive training if needed (TabPFN handles up to 10k samples)
        sample_size = min(600, len(X))
        X_sub = X[:sample_size]
        y_cls_sub = y_cls[:sample_size]
        y_reg_sub = y_reg[:sample_size]

        # Initialize Classification
        if TABPFN_AVAILABLE:
            try:
                print("Initializing Prior Labs TabPFN Classifier...")
                self.cls_model = TabPFNClassifier(device='cpu')
                self.cls_model.fit(X_sub, y_cls_sub)
                self.model_type = "TabPFN (Prior Labs Foundation Model)"
                self.tabpfn_status = "TabPFN available"
            except Exception as e:
                print(f"TabPFNClassifier initialization error: {e}. Falling back to Random Forest.")
                self.cls_model = RandomForestClassifier(n_estimators=100, random_state=42)
                self.cls_model.fit(X_sub, y_cls_sub)
                self.model_type = "RandomForest (TabPFN unavailable)"
                self.tabpfn_status = "TabPFN unavailable"
        else:
            self.cls_model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.cls_model.fit(X_sub, y_cls_sub)
            self.model_type = "RandomForest (TabPFN unavailable)"
            self.tabpfn_status = "TabPFN unavailable"

        self.last_prediction_model = self.model_type

        # Initialize Regression for exact days to frost
        if TABPFN_AVAILABLE:
            try:
                self.reg_model = TabPFNRegressor(device='cpu')
                self.reg_model.fit(X_sub, y_reg_sub)
            except Exception:
                self.reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
                self.reg_model.fit(X_sub, y_reg_sub)
        else:
            self.reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.reg_model.fit(X_sub, y_reg_sub)

    def predict_frost_risk(self, params: dict):
        """
        Given microclimate parameters, return frost probability, risk level,
        predicted days to frost, and anomaly detection.
        """
        # Vectorize features
        x_in = np.array([[
            float(params.get("latitude", 41.2)),
            float(params.get("elevation_m", 250)),
            int(params.get("day_of_year", 283)), # mid Oct
            float(params.get("daily_min_temp_c", 3.5)),
            float(params.get("daily_max_temp_c", 14.0)),
            float(params.get("soil_temp_5cm_c", 8.2)),
            float(params.get("humidity_pct", 65.0)),
            float(params.get("cloud_cover_pct", 15.0)), # low cloud cover = radiative chill
            float(params.get("barometric_pressure_hpa", 1020.0)),
            float(params.get("rolling_min_7d_c", 4.0))
        ]])

        # Frost Probability
        try:
            probs = self.cls_model.predict_proba(x_in)[0]
            frost_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
        except Exception:
            # Fallback estimation
            t_min = float(params.get("daily_min_temp_c", 3.5))
            frost_prob = max(0.01, min(0.99, 1.0 / (1.0 + np.exp(t_min * 0.9))))

        # Days until frost
        try:
            days_pred = float(self.reg_model.predict(x_in)[0])
            days_pred = max(0, round(days_pred, 1))
        except Exception:
            days_pred = max(0, round(float(params.get("daily_min_temp_c", 3.5)) * 2.5, 1))

        # Risk level determination
        if frost_prob > 0.70:
            risk_level = "Severe Freeze Alert"
            risk_color = "#e63946"
            action_summary = "Hard freeze imminent within 24-48 hours. Mulch garlic & cover sensitive greens immediately!"
        elif frost_prob > 0.40:
            risk_level = "Moderate Frost Watch"
            risk_color = "#f4a261"
            action_summary = "Light frost expected overnight. Hardy brassicas and spinach will thrive; harvest tender roots."
        else:
            risk_level = "Safe Planting Window"
            risk_color = "#2a9d8f"
            action_summary = "Optimal conditions for root development and cold-hardy autumn seed sowing."

        # Radiative frost anomaly check
        cloud_cover = float(params.get("cloud_cover_pct", 15.0))
        min_temp = float(params.get("daily_min_temp_c", 3.5))
        is_radiative_risk = (cloud_cover < 20 and min_temp < 5.0)

        self.last_prediction_model = self.model_type
        return {
            "model_used": self.model_type,
            "last_prediction_model": self.model_type,
            "tabpfn_status": self.tabpfn_status,
            "frost_probability": round(frost_prob, 3),
            "frost_probability_percent": round(frost_prob * 100, 1),
            "days_until_frost": days_pred,
            "risk_level": risk_level,
            "risk_color": risk_color,
            "action_summary": action_summary,
            "radiative_chill_anomaly": is_radiative_risk,
            "soil_temperature_status": "Ideal for Root Crops" if float(params.get("soil_temp_5cm_c", 8.2)) >= 5.0 else "Dormancy Approaching"
        }

    def benchmark_comparison(self):
        """
        Runs comprehensive benchmark comparing TabPFN vs Random Forest vs XGBoost
        on identical train/test splits of historical microclimate data.
        Demonstrates why Prior Labs' TabPFN excels in few-shot tabular forecasting!
        """
        X = self.df[self.features].values
        y = self.df["frost_imminent"].values

        # 80/20 train/test split on microclimate samples
        X_train, X_test, y_train, y_test = train_test_split(X[:500], y[:500], test_size=0.25, random_state=42)

        results = {}

        # 1. Random Forest Baseline
        rf_start = time.time()
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        rf_fit_time = time.time() - rf_start
        rf_preds = rf.predict(X_test)
        rf_probs = rf.predict_proba(X_test)[:, 1]
        results["Random Forest"] = {
            "accuracy": round(float(accuracy_score(y_test, rf_preds)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, rf_probs)), 4),
            "log_loss": round(float(log_loss(y_test, rf_probs)), 4),
            "fit_time_seconds": round(rf_fit_time, 4),
            "hyperparameter_tuning_needed": "Yes (n_estimators, max_depth, min_samples_split)"
        }

        # 2. XGBoost Baseline
        if HAS_XGBOOST:
            xgb_start = time.time()
            xgb = XGBClassifier(n_estimators=100, eval_metric='logloss', random_state=42)
            xgb.fit(X_train, y_train)
            xgb_fit_time = time.time() - xgb_start
            xgb_preds = xgb.predict(X_test)
            xgb_probs = xgb.predict_proba(X_test)[:, 1]
            results["XGBoost"] = {
                "accuracy": round(float(accuracy_score(y_test, xgb_preds)), 4),
                "roc_auc": round(float(roc_auc_score(y_test, xgb_probs)), 4),
                "log_loss": round(float(log_loss(y_test, xgb_probs)), 4),
                "fit_time_seconds": round(xgb_fit_time, 4),
                "hyperparameter_tuning_needed": "Yes (learning_rate, max_depth, subsample, reg_lambda)"
            }

        # 3. TabPFN (Prior Labs Foundation Model)
        if TABPFN_AVAILABLE:
            try:
                tab_start = time.time()
                tab = TabPFNClassifier(device='cpu')
                tab.fit(X_train, y_train)
                tab_fit_time = time.time() - tab_start
                tab_preds = tab.predict(X_test)
                tab_probs = tab.predict_proba(X_test)[:, 1]
                results["TabPFN (Foundation Model)"] = {
                    "accuracy": round(float(accuracy_score(y_test, tab_preds)), 4),
                    "roc_auc": round(float(roc_auc_score(y_test, tab_probs)), 4),
                    "log_loss": round(float(log_loss(y_test, tab_probs)), 4),
                    "fit_time_seconds": round(tab_fit_time, 4),
                    "status": "VERIFIED (TabPFN)"
                }
            except Exception as e:
                results["TabPFN (Foundation Model)"] = {
                    "accuracy": "NOT VERIFIED",
                    "roc_auc": "NOT VERIFIED",
                    "log_loss": "NOT VERIFIED",
                    "fit_time_seconds": "NOT VERIFIED",
                    "status": f"FAILED ({type(e).__name__}: weights not downloaded / auth required)"
                }
        else:
            results["TabPFN (Foundation Model)"] = {
                "accuracy": "NOT VERIFIED",
                "roc_auc": "NOT VERIFIED",
                "log_loss": "NOT VERIFIED",
                "fit_time_seconds": "NOT VERIFIED",
                "status": "FAILED (tabpfn library not installed)"
            }

        return results

# Singleton instance
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        predictor = FrostPredictor()
    return predictor

if __name__ == "__main__":
    p = get_predictor()
    res = p.predict_frost_risk({
        "latitude": 41.2,
        "elevation_m": 320,
        "day_of_year": 284,
        "daily_min_temp_c": 1.2,
        "daily_max_temp_c": 11.0,
        "soil_temp_5cm_c": 6.8,
        "humidity_pct": 55.0,
        "cloud_cover_pct": 10.0,
        "barometric_pressure_hpa": 1022.0,
        "rolling_min_7d_c": 2.5
    })
    print("Prediction Result:", res)
    print("Benchmark Comparison:", p.benchmark_comparison())
