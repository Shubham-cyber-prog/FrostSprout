"""
FrostSprout Runner Script
Launches FastAPI backend and static frontend server on http://localhost:8000
"""

import sys
import uvicorn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

if __name__ == "__main__":
    print("=" * 65)
    print("[FrostSprout] Touch Grass Garden Intelligence")
    print("   Powered by Prior Labs TabPFN & Google Gemma")
    print("   Starting fullstack server on http://localhost:8000")
    print("=" * 65)
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
