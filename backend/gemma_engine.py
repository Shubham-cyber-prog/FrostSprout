"""
Google Gemma Open-Weight Model Integration Engine for FrostSprout.
Gemma transforms tabular frost and crop predictions into actionable, hands-on outdoor
gardening activities, companion planting blueprints, and audio walkthrough scripts.
Prioritizes keeping screen time minimal: 'Touch Grass - Eyes on the Soil, Screen in Pocket'.
"""

import os
import json
import time
import requests

class GemmaEngine:
    def __init__(self):
        self.ollama_model = os.environ.get("OLLAMA_MODEL", "gemma3:latest")
        self.ollama_host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        self.hf_token = os.environ.get("HF_TOKEN", "")

    def generate_garden_action_plan(self, frost_data: dict, selected_crops: list) -> dict:
        """
        Generate physical, hands-on outdoor garden action plan using gemma3 via Ollama,
        with offline template fallback if Ollama is unreachable.
        """
        frost_prob = frost_data.get("frost_probability_percent", 25)
        risk_level = frost_data.get("risk_level", "Safe Planting Window")
        days_to_frost = frost_data.get("days_until_frost", 14)
        crop_names = [c.get("name", "Crops") for c in selected_crops] or ["Garlic", "Kale"]

        prompt = (
            f"You are the FrostSprout Outdoor Garden Mentor powered by Gemma.\n"
            f"Context: Frost risk is {frost_prob}% ({risk_level}). Days until frost: ~{days_to_frost} days. "
            f"Target autumn crops: {', '.join(crop_names)}.\n"
            f"Respond ONLY with valid JSON in this exact structure, with no markdown backticks and no conversational intro:\n"
            f'{{"chores": ['
            f'{{"step": 1, "title": "Trench & Loosen Soil Bed", "duration": "15 mins", "action": "Loosen topsoil 15cm deep with garden fork.", "tools": ["Hand trowel", "Mulch"]}}, '
            f'{{"step": 2, "title": "Plant Target Crops", "duration": "15 mins", "action": "Press cloves or seeds into soil at proper depth.", "tools": ["Watering can"]}}, '
            f'{{"step": 3, "title": "Thermal Leaf Blanket", "duration": "10 mins", "action": "Cover beds with shredded autumn leaves.", "tools": ["Rake"]}}'
            f'], '
            f'"touch_grass_sensory": "Sensory observation of the cold damp earth and air.", '
            f'"audio_script": "Short 60-second conversational voice guide for hands-free gardening.", '
            f'"companion_synergy": [{{"pair": "Garlic + Spinach", "benefit": "(Commonly said / unverified) Mutual cold-hardy companion pair"}}]'
            f'}}'
        )

        # Call live Ollama model
        raw_text, latency = self._call_llm(prompt)
        if raw_text:
            # Parse JSON from model output
            clean = raw_text.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

            try:
                parsed = json.loads(clean)
                return {
                    "source": "gemma3 via Ollama",
                    "chores": parsed.get("chores", []),
                    "touch_grass_sensory": parsed.get("touch_grass_sensory", "Press fingertips into the cool earth and breathe."),
                    "audio_script": parsed.get("audio_script", "Welcome outside. Pocket your phone and begin digging."),
                    "companion_synergy": parsed.get("companion_synergy", []),
                    "raw_model_output": raw_text,
                    "latency_seconds": round(latency, 2)
                }
            except Exception as e:
                # Format failure test handling
                print(f"Gemma output JSON parse failed ({e}), extracting fallback structure from raw text.")
                return {
                    "source": "gemma3 via Ollama",
                    "chores": self._extract_chores_from_text(raw_text),
                    "touch_grass_sensory": self._extract_sensory_from_text(raw_text),
                    "audio_script": self._extract_audio_script(raw_text, selected_crops, days_to_frost),
                    "companion_synergy": [{"pair": "Garlic + Spinach", "benefit": "(Commonly said / unverified) Pest deterring companion pair"}],
                    "raw_model_output": raw_text,
                    "latency_seconds": round(latency, 2),
                    "format_warning": f"JSON parse error: {str(e)}"
                }

        # Offline template fallback when Ollama is offline/unreachable
        return self._generate_offline_gemma_plan(frost_data, selected_crops)

    def _call_llm(self, prompt: str) -> tuple:
        # Check Ollama
        try:
            t0 = time.time()
            r = requests.post(f"{self.ollama_host}/api/generate", json={
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }, timeout=60)
            latency = time.time() - t0
            if r.status_code == 200:
                return r.json().get("response", ""), latency
        except Exception:
            pass

        return None, 0.0

    def _extract_chores_from_text(self, text: str) -> list:
        lines = [line.strip("- *• ") for line in text.split("\n") if len(line.strip()) > 10]
        chores = []
        for i, line in enumerate(lines[:3]):
            chores.append({
                "step": i + 1,
                "title": f"Garden Task {i+1}",
                "duration": "15 mins",
                "action": line,
                "tools": ["Hand trowel", "Mulch"]
            })
        return chores or [
            {"step": 1, "title": "Trench & Loosen Soil", "duration": "15 mins", "action": "Work soil with garden fork", "tools": ["Garden fork"]}
        ]

    def _extract_sensory_from_text(self, text: str) -> str:
        for line in text.split("\n"):
            if any(k in line.lower() for k in ["sensory", "smell", "feel", "soil", "touch"]):
                return line.strip("- *• :")
        return "Kneel down, touch the cold autumn soil with your fingertips."

    def _generate_offline_gemma_plan(self, frost_data: dict, selected_crops: list) -> dict:
        days = frost_data.get("days_until_frost", 12)
        frost_prob = frost_data.get("frost_probability_percent", 30)
        crop_names = [c.get("name", "") for c in selected_crops] or ["Hardneck Garlic", "Lacinato Kale"]
        
        is_urgent = frost_prob > 50

        chores = []
        if any("Garlic" in c for c in crop_names) or any("Shallot" in c for c in crop_names):
            chores.append({
                "step": 1,
                "title": "Trench & Plant Alliums (Garlic & Shallots)",
                "duration": "15 mins",
                "action": "Loosen topsoil 15cm deep with a garden fork. Press cloves pointed end up, 5cm deep, spaced 15cm apart.",
                "tools": ["Hand trowel", "Organic straw mulch", "Bone meal or compost"]
            })
        
        if any(c in ["Lacinato 'Dino' Kale", "Rustic Wild Arugula (Rocket)", "Bloomsdale Long Standing Spinach"] for c in crop_names):
            chores.append({
                "step": len(chores) + 1,
                "title": "Sow Cold-Hardy Greens & Seed Firming",
                "duration": "10 mins",
                "action": "Make 1cm furrows with your finger. Sprinkle seeds lightly. Firm down soil with your palm for tight seed contact.",
                "tools": ["Watering can with fine rose", "Seed packets"]
            })

        chores.append({
            "step": len(chores) + 1,
            "title": "Thermal Leaf Blanket Topdress",
            "duration": "10 mins",
            "action": f"{'Urgent: Apply 10cm dry shredded leaves tonight' if is_urgent else 'Spread a 5cm protective leaf layer'} over open root beds to insulate soil microbes.",
            "tools": ["Rake", "Autumn leaves or clean straw"]
        })

        touch_grass_sensory = (
            "Take 60 seconds before you start: Kneel down, press your bare fingertips 5cm into the soil. "
            f"At {frost_data.get('soil_temperature_status', 'cool')}, cold soil smells rich and fungal. "
            "Listen to the autumn wind through the bare branches. Your boots are in the grass and your screen is done."
        )

        audio_walkthrough = (
            f"Welcome outside to your garden. Step out into the fresh air, take a deep breath, and let's get your hands dirty. "
            f"According to our TabPFN microclimate analysis, you have about {days} days before the first true frost. "
            f"Today we are planting {', '.join(crop_names[:2])}. "
            f"First: grab your garden fork. Loosen the soil bed about six inches down. "
            f"If you're planting garlic, separate your cloves now. Keep the papery skins on! Plant each clove pointy end up, about two inches down. "
            f"Give the bed a good drink of water, then tuck your soil in with a blanket of fallen autumn leaves. "
            f"That's it for today. Look around, enjoy the quiet earth, and wash up when you're ready. You touched grass today."
        )

        return {
            "source": "Offline Heuristic Fallback (Ollama offline/not running)",
            "chores": chores,
            "touch_grass_sensory": touch_grass_sensory,
            "audio_script": audio_walkthrough,
            "companion_synergy": [
                {
                    "pair": "Garlic + Spinach",
                    "benefit": "(Commonly said / unverified) Garlic sulfur volatiles are said to deter aphids & cutworms while spinach shades garlic root zones from winter heaving."
                },
                {
                    "pair": "Kale + Beets / Carrots",
                    "benefit": "Brassicas and deep taproot crops utilize distinct soil strata without competing for autumn nitrogen."
                }
            ]
        }

    def _extract_pocket_summary(self, text: str) -> list:
        lines = [line.strip("- *• ") for line in text.split("\n") if len(line.strip()) > 10][:3]
        return lines or ["Prep soil bed with compost", "Plant root crops at recommended depth", "Mulch beds thoroughly"]

    def _extract_audio_script(self, text: str, selected_crops: list, days: int) -> str:
        return (
            f"Welcome to your garden session. We have approximately {days} days before the frost arrives. "
            f"Put your phone away, grab your trowel, and let's work the soil. "
            f"{text[:350]}..."
        )

# Singleton instance
gemma_engine = None

def get_gemma_engine():
    global gemma_engine
    if gemma_engine is None:
        gemma_engine = GemmaEngine()
    return gemma_engine
