"""
FrostSprout FastAPI Application
Open-Source AI Garden Planner & Pocket Field Companion
Theme: 'Touch Grass' - Screen in pocket, hands in the soil.
Combines Tabular ML (TabPFN with Random Forest fallback) + Google Gemma (open-weight agent) + Web Speech audio.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Optional
import requests
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# App initialization
app = FastAPI(
    title="FrostSprout AI",
    description="Hyperlocal Garden Intelligence & Pocket Field Companion powered by Tabular ML & Gemma",
    version="1.0.0"
)

# CORS setup for local and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load crop database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CROP_DB_PATH = os.path.join(BASE_DIR, "data", "crop_database.json")
JOURNAL_DB_PATH = os.path.join(BASE_DIR, "data", "journal.json")

crops_data = []
if os.path.exists(CROP_DB_PATH):
    with open(CROP_DB_PATH, "r", encoding="utf-8") as f:
        crops_data = json.load(f).get("crops", [])

# Lazy loaded engines
_predictor = None
_gemma = None

def get_tabpfn():
    global _predictor
    if _predictor is None:
        from backend.tabpfn_engine import get_predictor
        _predictor = get_predictor()
    return _predictor

def get_gemma():
    global _gemma
    if _gemma is None:
        from backend.gemma_engine import get_gemma_engine
        _gemma = get_gemma_engine()
    return _gemma


class MicroclimateInput(BaseModel):
    latitude: float = Field(default=41.2, description="Latitude in degrees")
    elevation_m: float = Field(default=250.0, description="Elevation in meters")
    day_of_year: int = Field(default=284, description="Day of year (1-365)")
    daily_min_temp_c: float = Field(default=3.5, description="Forecast overnight minimum temperature (°C)")
    daily_max_temp_c: float = Field(default=13.0, description="Forecast daytime maximum temperature (°C)")
    soil_temp_5cm_c: float = Field(default=8.0, description="Soil temperature at 5cm depth (°C)")
    humidity_pct: float = Field(default=65.0, description="Relative humidity percentage")
    cloud_cover_pct: float = Field(default=15.0, description="Cloud cover percentage (lower = higher radiative frost)")
    barometric_pressure_hpa: float = Field(default=1020.0, description="Barometric pressure in hPa")
    rolling_min_7d_c: float = Field(default=4.2, description="7-day rolling minimum average temperature (°C)")


class GeneratePlanRequest(BaseModel):
    microclimate: MicroclimateInput
    selected_crop_ids: List[str]


class JournalEntry(BaseModel):
    id: Optional[str] = None
    date: str
    minutes_outside: int
    crops_planted: List[str]
    notes: str
    touch_grass_rating: int = 5 # 1 to 5 stars
    soil_feel: str # "Cool & loamy", "Dry crust", etc.


@app.get("/api/health")
def health_check():
    predictor = get_tabpfn()
    actual_model = getattr(predictor, "last_prediction_model", predictor.model_type)
    return {
        "status": "online",
        "app": "FrostSprout Touch Grass Garden Planner",
        "version": "1.0.0",
        "model_actually_used": actual_model,
        "last_prediction_model": actual_model,
        "open_source_models": {
            "tabular_foundation_model": actual_model,
            "tabular_model_active": actual_model,
            "last_prediction_model": actual_model,
            "tabpfn_status": predictor.tabpfn_status,
            "companion_language_model": "Google Gemma (gemma3 via Ollama)",
            "voice_audio": "Web Speech API (Browser Synthesis)"
        },
        "crops_count": len(crops_data)
    }


@app.get("/api/live-weather")
def get_live_weather(lat: float = 29.39, lon: float = 76.97):
    """
    Fetch live real-world weather from Open-Meteo (free, no API key required)
    for coordinates (default: Panipat, Haryana, India).
    Maps hourly telemetry to tabular model microclimate features.
    """
    base_url = os.getenv("OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast")
    url = (
        f"{base_url}?latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,wind_speed_10m,cloud_cover"
        f"&forecast_days=2&timezone=Asia%2FKolkata"
    )
    try:
        resp = requests.get(url, timeout=5.0)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as net_err:
        raise HTTPException(
            status_code=502,
            detail=f"Open-Meteo unreachable (network error/timeout): {type(net_err).__name__}: {str(net_err)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Open-Meteo unreachable (network error/timeout): {str(e)}"
        )

    if resp.status_code == 400:
        raise HTTPException(
            status_code=400,
            detail=f"Open-Meteo bad request (HTTP 400): {resp.text[:200]}"
        )
    elif resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Open-Meteo error (HTTP {resp.status_code}): {resp.text[:200]}"
        )

    data = resp.json()

    elevation = float(data.get("elevation", 238.0))
    hourly = data.get("hourly", {})
    temps = hourly.get("temperature_2m", [])
    humidities = hourly.get("relative_humidity_2m", [])
    clouds = hourly.get("cloud_cover", [])

    if not temps:
        raise HTTPException(status_code=502, detail="Incomplete telemetry data from Open-Meteo")

    # Real features from Open-Meteo
    daily_min_temp_c = round(float(min(temps)), 1)
    daily_max_temp_c = round(float(max(temps)), 1)
    humidity_pct = round(float(sum(humidities[:24]) / max(1, len(humidities[:24]))), 1)
    cloud_cover_pct = round(float(sum(clouds[:24]) / max(1, len(clouds[:24]))), 1)
    day_of_year = int(datetime.now().timetuple().tm_yday)

    # Clearly labeled defaults for features without Open-Meteo equivalents in this query
    soil_temp_5cm_c = 22.0
    barometric_pressure_hpa = 1013.25
    rolling_min_7d_c = daily_min_temp_c

    features = {
        "latitude": round(lat, 4),
        "elevation_m": elevation,
        "day_of_year": day_of_year,
        "daily_min_temp_c": daily_min_temp_c,
        "daily_max_temp_c": daily_max_temp_c,
        "soil_temp_5cm_c": soil_temp_5cm_c,
        "humidity_pct": humidity_pct,
        "cloud_cover_pct": cloud_cover_pct,
        "barometric_pressure_hpa": barometric_pressure_hpa,
        "rolling_min_7d_c": rolling_min_7d_c
    }

    feature_metadata = {
        "latitude": {"source": "real", "label": "Real (Open-Meteo query)"},
        "elevation_m": {"source": "real", "label": "Real (Open-Meteo elevation)"},
        "day_of_year": {"source": "real", "label": "Real (System calendar day)"},
        "daily_min_temp_c": {"source": "real", "label": "Real (Open-Meteo 48h min)"},
        "daily_max_temp_c": {"source": "real", "label": "Real (Open-Meteo 48h max)"},
        "humidity_pct": {"source": "real", "label": "Real (Open-Meteo 24h average)"},
        "cloud_cover_pct": {"source": "real", "label": "Real (Open-Meteo 24h average)"},
        "soil_temp_5cm_c": {"source": "defaulted", "label": "22.0°C (default, not measured)"},
        "barometric_pressure_hpa": {"source": "defaulted", "label": "1013.25 hPa (default, not measured)"},
        "rolling_min_7d_c": {"source": "defaulted", "label": f"{daily_min_temp_c}°C (default, not measured)"}
    }

    loc_name = "Panipat, Haryana, India" if abs(lat - 29.39) < 0.1 and abs(lon - 76.97) < 0.1 else f"Custom Coordinates ({lat}, {lon})"

    return {
        "status": "success",
        "source": "Open-Meteo Forecast API (free, no API key)",
        "location": {
            "name": loc_name,
            "latitude": lat,
            "longitude": lon,
            "elevation_m": elevation,
            "timezone": data.get("timezone", "Asia/Kolkata")
        },
        "fetched_at": datetime.now().isoformat(),
        "features": features,
        "feature_metadata": feature_metadata,
        "note": "Frost scenarios are simulated; live weather is real."
    }


@app.get("/api/crops")
def get_crops():
    """Return all cold-hardy autumn/winter crops with requirements and tips."""
    return {"crops": crops_data}


@app.post("/api/predict/frost")
def predict_frost(data: MicroclimateInput):
    """
    Run tabular model to forecast frost probability,
    days until killing frost, and radiative freeze anomalies.
    """
    try:
        predictor = get_tabpfn()
        result = predictor.predict_frost_risk(data.dict())
        
        # Calculate suitability scores for each crop
        crop_suitability = []
        days_to_frost = result.get("days_until_frost", 14)
        soil_temp = data.soil_temp_5cm_c
        
        for crop in crops_data:
            # Check soil temp requirement
            temp_ok = soil_temp >= crop.get("min_soil_temp_c", 4)
            # Check weeks before frost
            ideal_weeks = crop.get("ideal_weeks_before_frost", 4)
            days_needed = ideal_weeks * 7
            frost_fit = 100 if days_to_frost >= days_needed else max(20, int(100 - (days_needed - days_to_frost) * 4))
            
            suitability_score = int(frost_fit * 0.7 + (100 if temp_ok else 40) * 0.3)
            
            status = "Recommended to Plant Now"
            if suitability_score < 50:
                status = "High Frost Risk - Mulch or Overwinter"
            elif suitability_score < 75:
                status = "Window Closing - Plant This Weekend"

            crop_suitability.append({
                "id": crop["id"],
                "name": crop["name"],
                "category": crop["category"],
                "suitability_score": suitability_score,
                "status": status,
                "min_soil_temp_c": crop["min_soil_temp_c"],
                "current_soil_temp_c": soil_temp,
                "soil_temp_label": f"{soil_temp}°C (default, not measured)",
                "frost_tolerance": crop["frost_tolerance"],
                "outdoor_action": crop["outdoor_action"],
                "touch_grass_tip": crop["touch_grass_tip"]
            })
            
        # Sort by best suitability score
        crop_suitability.sort(key=lambda x: x["suitability_score"], reverse=True)

        return {
            "prediction": result,
            "crop_recommendations": crop_suitability
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/api/generate/plan")
def generate_garden_plan(req: GeneratePlanRequest):
    """
    Gemma transforms tabular predictions into a tangible, hands-on outdoor action plan.
    """
    try:
        predictor = get_tabpfn()
        frost_data = predictor.predict_frost_risk(req.microclimate.dict())
        
        # Filter selected crops
        chosen_crops = [c for c in crops_data if c["id"] in req.selected_crop_ids]
        if not chosen_crops and crops_data:
            chosen_crops = crops_data[:2]

        gemma = get_gemma()
        plan = gemma.generate_garden_action_plan(frost_data, chosen_crops)
        
        return {
            "frost_summary": frost_data,
            "selected_crops": chosen_crops,
            "gemma_plan": plan
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemma plan generation error: {str(e)}")


@app.get("/api/benchmark")
def get_model_benchmark():
    """
    Benchmark TabPFN vs Random Forest vs XGBoost on historical microclimate tabular data.
    Provides reproducible benchmark comparison on synthetic microclimate data.
    """
    try:
        predictor = get_tabpfn()
        benchmark_results = predictor.benchmark_comparison()
        return {
            "title": "Tabular Microclimate Frost Benchmark",
            "description": "TabPFN vs Gradient Boosting and Random Forest baselines evaluated on synthetic microclimate data",
            "models": benchmark_results,
            "synthetic_data_note": "Evaluated strictly on synthetic data (seed=42). TabPFN model weights require one-time license auth on Prior Labs."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark calculation error: {str(e)}")


@app.get("/api/journal")
def get_journal_entries():
    """Get saved 'Touch Grass' outdoor gardening journal entries."""
    if os.path.exists(JOURNAL_DB_PATH):
        try:
            with open(JOURNAL_DB_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
                return {"entries": entries}
        except Exception:
            pass
    return {"entries": []}


@app.post("/api/journal")
def add_journal_entry(entry: JournalEntry):
    """Save an outdoor garden session and streak."""
    entries = []
    if os.path.exists(JOURNAL_DB_PATH):
        try:
            with open(JOURNAL_DB_PATH, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except Exception:
            entries = []

    new_id = f"entry-{int(time.time())}"
    entry_dict = entry.dict()
    entry_dict["id"] = new_id
    entries.insert(0, entry_dict)

    with open(JOURNAL_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

    return {"status": "success", "entry": entry_dict, "total_sessions": len(entries)}



# Mount static frontend
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

