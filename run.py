"""
FrostSprout Runner Script
Launches FastAPI backend and static frontend server on http://localhost:8000
"""

import os
import sys
import uvicorn

# Automatically load .env if present
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("=" * 65)
    print("[FrostSprout] Touch Grass Garden Intelligence")
    print("   Powered by Tabular ML & Google Gemma")
    print("   Starting fullstack server on http://localhost:8000")
    print("=" * 65)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
