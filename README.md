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

---

## Benchmark Comparison (Synthetic Data)

Evaluated using `backend/benchmark.py` on 800 synthetic microclimate samples (`backend/data/frost_history.csv`) with a fixed seed (`seed=42`) and a 75/25 train/test split (600 train, 200 test):

| Model | ROC-AUC | Accuracy | Log-Loss | Fit Time | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest** | 0.9987 | 99.00% | 0.0364 | 0.1266s | VERIFIED (sklearn) |
| **XGBoost** | 0.9986 | 99.00% | 0.0435 | 0.0312s | VERIFIED (xgboost) |
| **Prior Labs TabPFN** | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | FAILED (TabPFNLicenseError: model weights require Prior Labs license auth) |

> **Data Disclosure**: Data synthetic hai aur label usi formula se bana hai, isliye saare models ke scores lagbhag perfect hain aur ye real-world accuracy nahi dikhate. Previous fallback claims on historical climate data were unverified and have been removed.

---

## Open-Source AI Model Implementation & Fallbacks

### TabPFN (`backend/tabpfn_engine.py`)
- **Class imported**: `tabpfn.classifier.TabPFNClassifier` (package: `tabpfn>=9.1.0`).
- **Weights & Licensing**: TabPFN v2 requires a one-time Prior Labs license acceptance and API key (`TABPFN_TOKEN`) to download weights.
- **Laptop execution status**: Weights download did not run in this IDE environment due to missing interactive authentication / `TABPFN_TOKEN`.
- **Fallback Handling**: Silent fallback hata diya gaya hai. Agar TabPFN unavailable ya unauthenticated ho to UI aur API saaf batate hain ("TabPFN unavailable"), aur active model ka naam response mein "RandomForest (Fallback: TabPFN unavailable)" ke roop mein return hota hai.

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
