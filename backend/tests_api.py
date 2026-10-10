import unittest
from fastapi.testclient import TestClient
from backend.app import app

class TestFrostSproutAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "online")
        self.assertIn("open_source_models", data)
        self.assertGreater(data.get("crops_count", 0), 0)
        print("PASS: /api/health ->", data["open_source_models"])

    def test_02_crops(self):
        resp = self.client.get("/api/crops")
        self.assertEqual(resp.status_code, 200)
        crops = resp.json().get("crops", [])
        self.assertGreaterEqual(len(crops), 10)
        self.assertTrue(any(c["id"] == "garlic-hardneck" for c in crops))
        print(f"PASS: /api/crops -> {len(crops)} crops loaded successfully")

    def test_03_predict_frost_normal(self):
        payload = {
            "latitude": 29.39,
            "elevation_m": 238.0,
            "day_of_year": 284,
            "daily_min_temp_c": 14.0,
            "daily_max_temp_c": 28.0,
            "soil_temp_5cm_c": 22.0,
            "humidity_pct": 55.0,
            "cloud_cover_pct": 40.0,
            "barometric_pressure_hpa": 1013.25,
            "rolling_min_7d_c": 14.0
        }
        resp = self.client.post("/api/predict/frost", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("prediction", data)
        self.assertIn("crop_recommendations", data)
        pred = data["prediction"]
        self.assertIn("frost_probability_percent", pred)
        self.assertIn("risk_level", pred)
        print(f"PASS: /api/predict/frost (normal) -> Risk: {pred['risk_level']}, Prob: {pred['frost_probability_percent']}%")

    def test_04_predict_frost_cold_radiative(self):
        payload = {
            "latitude": 41.2,
            "elevation_m": 250.0,
            "day_of_year": 300,
            "daily_min_temp_c": 1.0,
            "daily_max_temp_c": 8.0,
            "soil_temp_5cm_c": 3.0,
            "humidity_pct": 80.0,
            "cloud_cover_pct": 10.0,  # low cloud cover (< 20%) + cold temp triggers radiative chill anomaly
            "barometric_pressure_hpa": 1025.0,
            "rolling_min_7d_c": 1.5
        }
        resp = self.client.post("/api/predict/frost", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        pred = data["prediction"]
        self.assertTrue(pred.get("radiative_chill_anomaly", False))
        print(f"PASS: /api/predict/frost (radiative) -> Prob: {pred['frost_probability_percent']}%, Radiative Alert: {pred['radiative_chill_anomaly']}")

    def test_05_live_weather(self):
        resp = self.client.get("/api/live-weather?lat=29.39&lon=76.97")
        self.assertIn(resp.status_code, [200, 502])
        if resp.status_code == 200:
            data = resp.json()
            self.assertEqual(data.get("status"), "success")
            features = data.get("features", {})
            self.assertIn("daily_min_temp_c", features)
            self.assertIn("daily_max_temp_c", features)
            self.assertIn("feature_metadata", data)
            # Check source labels
            self.assertEqual(data["feature_metadata"]["daily_min_temp_c"]["source"], "real")
            self.assertEqual(data["feature_metadata"]["soil_temp_5cm_c"]["source"], "defaulted")
            print(f"PASS: /api/live-weather -> Location: {data['location']['name']}, Min: {features['daily_min_temp_c']}°C, Max: {features['daily_max_temp_c']}°C")
        else:
            data = resp.json()
            self.assertIn("Open-Meteo", data.get("detail", ""))
            print(f"PASS: /api/live-weather (502 error handling verified) -> {data.get('detail')}")

    def test_06_generate_plan(self):
        payload = {
            "microclimate": {
                "latitude": 29.39,
                "elevation_m": 238.0,
                "day_of_year": 284,
                "daily_min_temp_c": 10.0,
                "daily_max_temp_c": 22.0,
                "soil_temp_5cm_c": 15.0,
                "humidity_pct": 60.0,
                "cloud_cover_pct": 20.0,
                "barometric_pressure_hpa": 1013.25,
                "rolling_min_7d_c": 10.0
            },
            "selected_crop_ids": ["garlic-hardneck", "kale-lacinato"]
        }
        resp = self.client.post("/api/generate/plan", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("gemma_plan", data)
        plan = data["gemma_plan"]
        self.assertIn("chores", plan)
        self.assertIn("touch_grass_sensory", plan)
        print(f"PASS: /api/generate/plan -> Source: {plan.get('source')}, Chores count: {len(plan.get('chores', []))}")

    def test_07_benchmark(self):
        resp = self.client.get("/api/benchmark")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("models", data)
        models = data["models"]
        self.assertIn("Random Forest", models)
        self.assertIn("XGBoost", models)
        print(f"PASS: /api/benchmark -> RF Acc: {models['Random Forest']['accuracy']}, XGB Acc: {models['XGBoost']['accuracy']}")

    def test_08_journal(self):
        entry_payload = {
            "date": "2026-10-11",
            "minutes_outside": 45,
            "crops_planted": ["Hardneck Garlic", "Spinach"],
            "notes": "Crisp autumn morning, mulched beds with dry leaves.",
            "touch_grass_rating": 5,
            "soil_feel": "Cool & loamy"
        }
        resp = self.client.post("/api/journal", json=entry_payload)
        self.assertEqual(resp.status_code, 200)
        post_data = resp.json()
        self.assertEqual(post_data.get("status"), "success")

        get_resp = self.client.get("/api/journal")
        self.assertEqual(get_resp.status_code, 200)
        entries = get_resp.json().get("entries", [])
        self.assertGreaterEqual(len(entries), 1)
        self.assertEqual(entries[0]["minutes_outside"], 45)
        print(f"PASS: /api/journal -> Total entries: {len(entries)}, latest: {entries[0]['crops_planted']}")

    def test_09_static_frontend(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("FrostSprout", resp.text)
        print("PASS: / (static index.html) served properly")

if __name__ == "__main__":
    unittest.main()
