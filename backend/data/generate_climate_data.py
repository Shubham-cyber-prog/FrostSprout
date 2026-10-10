"""
Generate realistic historical tabular microclimate and frost observation data
representing diverse hardiness zones (Zones 4 through 9) across multiple autumn seasons.
Used by TabPFN (Prior Labs' tabular foundation model) for tabular frost risk forecasting.
"""

import numpy as np
import pandas as pd
import os

def generate_frost_dataset(num_samples=800, seed=42):
    np.random.seed(seed)
    
    # Define microclimate archetypes
    zones = [
        {"name": "Northern Valley (Zone 4b)", "lat": 44.5, "base_elev": 450, "mean_first_frost_doy": 268}, # late Sep
        {"name": "Appalachian Foothills (Zone 5b)", "lat": 41.2, "base_elev": 320, "mean_first_frost_doy": 280}, # early Oct
        {"name": "Midwest Prairie (Zone 6a)", "lat": 39.8, "base_elev": 220, "mean_first_frost_doy": 288}, # mid Oct
        {"name": "Coastal Lowland (Zone 7b)", "lat": 36.8, "base_elev": 45, "mean_first_frost_doy": 305}, # early Nov
        {"name": "Pacific Maritime (Zone 8b)", "lat": 47.6, "base_elev": 80, "mean_first_frost_doy": 320}, # mid Nov
    ]
    
    rows = []
    
    for _ in range(num_samples):
        zone = np.random.choice(zones)
        # Random autumn day of year (doy 250 to 330: Sep 7 to Nov 26)
        doy = int(np.random.uniform(250, 335))
        elev = zone["base_elev"] + np.random.normal(0, 40)
        
        # Days relative to the typical first frost
        days_from_typical = doy - zone["mean_first_frost_doy"]
        
        # Atmospheric cooling curve: min temp drops as season progresses
        expected_min = 12.0 - (days_from_typical * 0.35) - (elev / 300.0)
        daily_min_temp = round(expected_min + np.random.normal(0, 3.2), 1)
        
        # Diurnal range is higher when cloud cover is low (radiative cooling)
        cloud_cover = round(np.random.uniform(5, 95), 1)
        humidity = round(np.clip(70 - (daily_min_temp * 0.8) + np.random.normal(0, 10), 30, 98), 1)
        
        diurnal_spread = 8.0 + (100 - cloud_cover) * 0.08 + np.random.normal(0, 2)
        daily_max_temp = round(daily_min_temp + max(3.0, diurnal_spread), 1)
        
        # Soil temp lags air temp but cools steadily
        soil_temp_5cm = round(max(0.5, daily_min_temp * 0.4 + 6.5 + np.random.normal(0, 1.2)), 1)
        
        pressure = round(1013.25 + np.random.normal(0, 8.5) + (5.0 if cloud_cover < 30 else -3.0), 1)
        
        # 7-day rolling minimum temp trend
        rolling_min_7d = round(daily_min_temp + np.random.uniform(-2.5, 3.0), 1)
        
        # Clear nights (cloud < 25%) with high pressure and low humidity accelerate freeze
        radiative_frost_bonus = 1.8 if (cloud_cover < 30 and pressure > 1018) else 0.0
        effective_frost_temp = daily_min_temp - radiative_frost_bonus
        
        # Ground frost occurs when min temp <= 0.0 C (or <= 1.0 C under radiative open sky)
        frost_imminent = 1 if effective_frost_temp <= 0.5 else 0
        
        # Days until first frost occurs
        days_until_frost = max(0, int(round((daily_min_temp - 0.5) / 0.38 + np.random.normal(0, 2.5))))
        if frost_imminent == 1:
            days_until_frost = 0
            
        rows.append({
            "zone_name": zone["name"],
            "latitude": round(zone["lat"], 2),
            "elevation_m": round(elev, 1),
            "day_of_year": doy,
            "daily_min_temp_c": daily_min_temp,
            "daily_max_temp_c": daily_max_temp,
            "soil_temp_5cm_c": soil_temp_5cm,
            "humidity_pct": humidity,
            "cloud_cover_pct": cloud_cover,
            "barometric_pressure_hpa": pressure,
            "rolling_min_7d_c": rolling_min_7d,
            "frost_imminent": frost_imminent,
            "days_until_frost": days_until_frost
        })
        
    df = pd.DataFrame(rows)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "frost_history.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} climate records successfully at {out_path}")
    return out_path

if __name__ == "__main__":
    generate_frost_dataset()
