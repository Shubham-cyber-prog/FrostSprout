"""
Benchmark script comparing Random Forest, XGBoost, and TabPFN on synthetic microclimate data.
Fixed seed and reproducible train/test split.
"""

import os
import sys
import time

# Automatically load .env if present
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.ensemble import RandomForestClassifier

# Check XGBoost
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

# Check TabPFN
try:
    from tabpfn import TabPFNClassifier
    HAS_TABPFN_LIB = True
except ImportError:
    HAS_TABPFN_LIB = False


def run_benchmark():
    seed = 42
    np.random.seed(seed)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "frost_history.csv")

    if not os.path.exists(data_path):
        from data.generate_climate_data import generate_frost_dataset
        generate_frost_dataset(seed=seed)

    df = pd.read_csv(data_path)
    features = [
        "latitude", "elevation_m", "day_of_year", "daily_min_temp_c",
        "daily_max_temp_c", "soil_temp_5cm_c", "humidity_pct",
        "cloud_cover_pct", "barometric_pressure_hpa", "rolling_min_7d_c"
    ]
    target = "frost_imminent"

    X = df[features].values
    y = df[target].values

    # Fixed train/test split: 75% train, 25% test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )

    print("================================================================================")
    print("FROSTSPROUT BENCHMARK: Random Forest vs XGBoost vs TabPFN")
    print(f"Data source: {data_path} (SYNTHETIC DATA, N={len(df)})")
    print(f"Split: Train={len(X_train)} samples, Test={len(X_test)} samples (seed={seed})")
    print("================================================================================")

    results = []

    # 1. Random Forest
    rf_start = time.time()
    rf = RandomForestClassifier(n_estimators=100, random_state=seed)
    rf.fit(X_train, y_train)
    rf_fit_time = time.time() - rf_start
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)[:, 1]

    rf_acc = accuracy_score(y_test, rf_preds)
    rf_auc = roc_auc_score(y_test, rf_probs)
    rf_loss = log_loss(y_test, rf_probs)

    results.append({
        "Model": "Random Forest",
        "ROC-AUC": f"{rf_auc:.4f}",
        "Accuracy": f"{rf_acc * 100:.2f}%",
        "Log-Loss": f"{rf_loss:.4f}",
        "Fit Time (s)": f"{rf_fit_time:.4f}",
        "Status": "VERIFIED (sklearn)"
    })

    # 2. XGBoost
    if HAS_XGBOOST:
        xgb_start = time.time()
        xgb = XGBClassifier(n_estimators=100, eval_metric='logloss', random_state=seed)
        xgb.fit(X_train, y_train)
        xgb_fit_time = time.time() - xgb_start
        xgb_preds = xgb.predict(X_test)
        xgb_probs = xgb.predict_proba(X_test)[:, 1]

        xgb_acc = accuracy_score(y_test, xgb_preds)
        xgb_auc = roc_auc_score(y_test, xgb_probs)
        xgb_loss = log_loss(y_test, xgb_probs)

        results.append({
            "Model": "XGBoost",
            "ROC-AUC": f"{xgb_auc:.4f}",
            "Accuracy": f"{xgb_acc * 100:.2f}%",
            "Log-Loss": f"{xgb_loss:.4f}",
            "Fit Time (s)": f"{xgb_fit_time:.4f}",
            "Status": "VERIFIED (xgboost)"
        })
    else:
        results.append({
            "Model": "XGBoost",
            "ROC-AUC": "N/A",
            "Accuracy": "N/A",
            "Log-Loss": "N/A",
            "Fit Time (s)": "N/A",
            "Status": "FAILED (xgboost package not found)"
        })

    # 3. TabPFN
    if HAS_TABPFN_LIB:
        print("\nAttempting TabPFNClassifier execution...")
        print(f"TabPFN class: {TabPFNClassifier}")
        tab_start = time.time()
        try:
            tab = TabPFNClassifier(device='cpu')
            tab.fit(X_train, y_train)
            tab_fit_time = time.time() - tab_start
            tab_preds = tab.predict(X_test)
            tab_probs = tab.predict_proba(X_test)[:, 1]

            tab_acc = accuracy_score(y_test, tab_preds)
            tab_auc = roc_auc_score(y_test, tab_probs)
            tab_loss = log_loss(y_test, tab_probs)

            results.append({
                "Model": "TabPFN",
                "ROC-AUC": f"{tab_auc:.4f}",
                "Accuracy": f"{tab_acc * 100:.2f}%",
                "Log-Loss": f"{tab_loss:.4f}",
                "Fit Time (s)": f"{tab_fit_time:.4f}",
                "Status": "VERIFIED (tabpfn)"
            })
        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e).splitlines()[0]}"
            print(f"TabPFN fit failed: {e}")
            results.append({
                "Model": "TabPFN",
                "ROC-AUC": "NOT VERIFIED",
                "Accuracy": "NOT VERIFIED",
                "Log-Loss": "NOT VERIFIED",
                "Fit Time (s)": "NOT VERIFIED",
                "Status": f"FAILED ({err_msg})"
            })
    else:
        results.append({
            "Model": "TabPFN",
            "ROC-AUC": "NOT VERIFIED",
            "Accuracy": "NOT VERIFIED",
            "Log-Loss": "NOT VERIFIED",
            "Fit Time (s)": "NOT VERIFIED",
            "Status": "FAILED (tabpfn library not installed)"
        })

    print("\n--------------------------------------------------------------------------------")
    print(f"{'Model':<16} | {'ROC-AUC':<10} | {'Accuracy':<10} | {'Log-Loss':<10} | {'Fit Time (s)':<12} | {'Status'}")
    print("--------------------------------------------------------------------------------")
    for r in results:
        print(f"{r['Model']:<16} | {r['ROC-AUC']:<10} | {r['Accuracy']:<10} | {r['Log-Loss']:<10} | {r['Fit Time (s)']:<12} | {r['Status']}")
    print("--------------------------------------------------------------------------------")
    print("NOTE: All results above are evaluated strictly on synthetic microclimate data.")
    return results


if __name__ == "__main__":
    run_benchmark()
