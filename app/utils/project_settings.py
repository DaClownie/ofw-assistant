# app/utils/project_settings.py
import json
from pathlib import Path

SETTINGS_PATH = Path("data/project_settings.json")

def load_project_settings():
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r') as f:
            return json.load(f)
    return {
        "instructions": "Focus on parenting concerns, safety issues, and behavioral patterns. Identify potential manipulation, coaching, or fabricated symptoms."
    }

def save_project_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f, indent=2)