# FrostSprout: Open-Source AI Garden Planner

[![Prior Labs TabPFN](https://img.shields.io/badge/Prior%20Labs-TabPFN%20Foundation%20Model-38bdf8.svg)](https://github.com/automl/TabPFN)
[![Google Gemma](https://img.shields.io/badge/Google-Gemma%20Open--Weight-34d399.svg)](https://ai.google.dev/gemma)

FrostSprout is a hyperlocal microclimate garden planning assistant designed to reduce screen time and guide outdoor planting. The system integrates tabular prediction logic via Prior Labs' TabPFN (with local Random Forest fallback) and outdoor action plans via Google Gemma (with local heuristic template fallback). Hands-free audio guidance is powered directly by the browser Web Speech API.

---

## Targeted Categories

- **Use of TabPFN**: Tabular prediction architecture configured for frost probability, days until freezing, and radiative cooling detection from microclimate parameters.
- **Use of Gemma**: Action guide generator targeting local Ollama (`gemma3`) or remote endpoints to convert tabular metrics into physical outdoor chore lists and sensory observations.

---

## Key Features

### 1. Tabular Frost Risk Estimation
- Evaluates hyperlocal microclimate parameters: elevation, daily min/max temperature, 5cm soil temperature, relative humidity, barometric pressure, and nighttime cloud cover.
- **Radiative cooling heuristic**: Flags ground freeze risk when night cloud cover drops below 20% under low temperatures (commonly said observational meteorological heuristic; unverified across diverse geographic microclimates).
- Model architecture uses `TabPFNClassifier` when Prior Labs authentication and model weights are present, falling back to scikit-learn `RandomForestClassifier` when running unauthenticated.

### 2. Autumn Crop Guidance
- Curates 10 cold-hardy autumn crops (Garlic, Lacinato Kale, Bloomsdale Spinach, Carrots, Radish, Fava Beans, etc.).
- Includes approximate knuckle-depth planting measurements.

### 3. Outdoor Action Guide
- Converts microclimate predictions into a 3-step physical task list.
- Sensory observations for garden soil and outdoor surroundings.
- Companion planting notes (e.g. interplanting garlic and spinach against root cutworms is a commonly said companion planting claim; unverified experimentally).

### 4. Hands-Free Audio Walkthrough
- Built-in audio playback using the browser's native **Web Speech API** (`window.speechSynthesis`).
- Allows gardeners to listen to steps hands-free without looking at a screen.

### 5. Printable Pocket Field Cards & Garden Log
- CSS print styling formats the garden plan onto an index card layout.
- Local session log to record outdoor minutes and soil notes.

## Live Weather Telemetry (Open-Meteo)

FrostSprout supports live microclimate telemetry via the free, open **Open-Meteo Forecast API** (`https://api.open-meteo.com/v1/forecast`, no API key required):

- **Default Location**: Panipat, Haryana, India (`lat=29.39`, `lon=76.97`, elevation ~238m).
- **Endpoint**: `GET /api/live-weather?lat={lat}&lon={lon}`
- **Units**: All temperatures and predictions strictly use **Celsius (°C)**, elevation in meters (m), humidity/clouds in percent (%), and pressure in hPa. The synthetic training data and model feature definitions natively operate in Celsius, so no unit conversion is needed.
- **Real vs. Defaulted Features**:
  - **Real Telemetry (from Open-Meteo query)**:
    - `latitude`: Real (Open-Meteo coordinate response)
    - `elevation_m`: Real (Open-Meteo ground elevation)
    - `day_of_year`: Real (System calendar day of year in `Asia/Kolkata`)
    - `daily_min_temp_c`: Real (48-hour minimum of `temperature_2m`)
    - `daily_max_temp_c`: Real (48-hour maximum of `temperature_2m`)
    - `humidity_pct`: Real (24-hour average of `relative_humidity_2m`)
    - `cloud_cover_pct`: Real (24-hour average of `cloud_cover`)
  - **Defaulted Features (Not provided by the 2-day hourly forecast query)**:
    - `soil_temp_5cm_c`: Defaulted (22.0°C; 5cm soil depth telemetry is not queried)
    - `barometric_pressure_hpa`: Defaulted (1013.25 hPa standard sea-level)
    - `rolling_min_7d_c`: Defaulted to 48-hour minimum (7-day past history is not returned in 2-day forecast query)
- **UI & Simulation Disclosure**: The UI displays: *"Frost scenarios are simulated; live weather is real."* Manual sliders allow what-if exploration (e.g. testing hypothetical freeze drops down to 2°C) and are explicitly tagged as `Mode: What-If (Simulated)`.
- **Training Data Disclosure**: The underlying prediction model is trained on synthetic microclimate data (`backend/data/frost_history.csv`, seed=42) and is not calibrated against real-world agricultural station ground truths.

---

## Benchmark Comparison (Synthetic Data)

Evaluated using `backend/benchmark.py` on 800 synthetic microclimate samples (`backend/data/frost_history.csv`) with a fixed seed (`seed=42`) and a 75/25 train/test split (600 train, 200 test):

| Model | ROC-AUC | Accuracy | Log-Loss | Fit Time | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest** | 0.9987 | 99.00% | 0.0364 | 0.0994s | VERIFIED (sklearn) |
| **XGBoost** | 0.9986 | 99.00% | 0.0435 | 0.0346s | VERIFIED (xgboost) |
| **Prior Labs TabPFN** | 0.9987 | 98.50% | 0.0358 | 0.4460s | VERIFIED (tabpfn) |

> **Data Disclosure**: Data synthetic hai aur label usi formula se bana hai, isliye saare models ke scores lagbhag perfect hain aur ye real-world accuracy nahi dikhate. Previous fallback claims on historical climate data were unverified and have been removed.

---

## Open-Source AI Model Implementation & Fallbacks

### TabPFN (`backend/tabpfn_engine.py`)
- **Class imported**: `tabpfn.classifier.TabPFNClassifier` (package: `tabpfn>=9.1.0`).
- **Weights & Licensing**: TabPFN v2 requires a one-time Prior Labs license acceptance and API key (`TABPFN_TOKEN`) to download weights.
- **Laptop execution status**: Configured and verified via `TABPFN_TOKEN` in `.env`. Foundation model weights successfully downloaded from HuggingFace Hub, running real tabular inference.
- **Fallback Handling**: Agar TabPFN token missing ya unauthenticated ho to UI aur API saaf batate hain ("TabPFN unavailable"), aur active model ka naam response mein "RandomForest (Fallback: TabPFN unavailable)" ke roop mein return hota hai. Token maujood hone par direct "TabPFN (Prior Labs Foundation Model)" active rehta hai.

### Gemma (`backend/gemma_engine.py`)
- **Target model**: Local Ollama (`gemma3:latest`) on `http://127.0.0.1:11434`.
- **Execution status**: Ollama ke sath live inference run hota hai aur response mein `"source": "gemma3 via Ollama"` return hota hai. Agar Ollama band ya unreachable ho to response mein `"source": "offline template"` return hota hai, aur UI use transparently display karta hai.

### Audio Narration
- Uses the browser's native **Web Speech API** (`window.speechSynthesis`).
- No external speech API is called. No API keys are required or committed in the repository.

---

## Quickstart

### Prerequisites
- Python 3.10+
- Modern Web Browser

### 1. Clone & Install
```bash
git clone https://github.com/Shubham-cyber-prog/frostsprout.git
cd frostsprout
pip install -r requirements.txt
```

### 2. Run the Benchmark
```bash
python backend/benchmark.py
```

### 3. Run the Application
```bash
python run.py
```
Open **http://localhost:8000** in your browser.

---

## Project Structure

```
frostsprout/
├── backend/
│   ├── app.py                   # FastAPI server and prediction endpoints
│   ├── benchmark.py             # Reproducible benchmark (seed=42)
│   ├── tabpfn_engine.py         # TabPFN engine with Random Forest fallback
│   ├── gemma_engine.py          # Gemma engine (gemma3) with heuristic fallback
│   └── data/
│       ├── crop_database.json   # Cold-hardy crop agronomy data
│       ├── frost_history.csv    # 800 synthetic microclimate records
│       ├── generate_climate_data.py # Synthetic climate data generator
│       └── journal.json         # Outdoor session logs
├── frontend/
│   ├── index.html               # Semantic HTML5 UI
│   ├── styles.css               # Styling, animations, and print CSS
│   └── app.js                   # UI logic, slider controls, and Web Speech audio
├── run.py                       # Startup script
└── requirements.txt             # Python dependencies
```

---

## Limitations

1. **US-Style Defaults**: Crop lists, planting windows, and temperature calibrations follow North American USDA Plant Hardiness Zones (Zones 4 to 9).
2. **Synthetic Data**: `frost_history.csv` is completely synthetic data generated by formulas in `backend/data/generate_climate_data.py`, not real agricultural sensor recordings.
3. **Manual Inputs**: Weather parameters are adjusted manually via UI sliders; there is no live integration with external meteorological APIs.
4. **Execution Fallbacks**:
   - TabPFN falls back to scikit-learn Random Forest if Prior Labs weights are not downloaded or unauthenticated.
   - Gemma falls back to a deterministic rule-based template if the Ollama daemon is offline.
