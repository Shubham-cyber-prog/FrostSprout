"""
FrostSprout FastAPI Application
Open-Source AI Garden Planner & Pocket Field Companion
Theme: 'Touch Grass' - Screen in pocket, hands in the soil.
Combines Prior Labs' TabPFN (tabular foundation model) + Google Gemma (open-weight agent) + Web Speech audio.
"""

import os
import json
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# App initialization
app = FastAPI(
    title="FrostSprout AI",
    description="Hyperlocal Garden Intelligence & Pocket Field Companion powered by TabPFN & Gemma",
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
    return {
        "status": "online",
        "app": "FrostSprout Touch Grass Garden Planner",
        "version": "1.0.0",
        "open_source_models": {
            "tabular_foundation_model": "TabPFN (Prior Labs)",
            "companion_language_model": "Google Gemma (gemma3 via Ollama)",
            "voice_audio": "Web Speech API (Browser Synthesis)"
        },
        "crops_count": len(crops_data)
    }


@app.get("/api/crops")
def get_crops():
    """Return all cold-hardy autumn/winter crops with requirements and tips."""
    return {"crops": crops_data}


@app.post("/api/predict/frost")
def predict_frost(data: MicroclimateInput):
    """
    Run TabPFN tabular foundation model to forecast frost probability,
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
    Gemma transforms TabPFN tabular predictions into a tangible, hands-on outdoor action plan.
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

