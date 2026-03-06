# utils/save_manager.py
import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.path.join(PROJECT_ROOT, "save_data.json")

DEFAULT_SAVE_DATA = {
    "tutorial_dialogue_completed": False,
    "completed_careers": [],
    "skills": {
        "debugging": 0,
        "logic": 0,
        "efficiency": 0,
        "speed": 0,
    },
    "career_reports": {},
}


def _merge_defaults(data, defaults):
    merged = dict(defaults)
    for key, value in data.items():
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            merged[key] = _merge_defaults(value, defaults[key])
        else:
            merged[key] = value
    return merged

def load_save():
    if not os.path.exists(SAVE_FILE):
        return _merge_defaults({}, DEFAULT_SAVE_DATA)

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _merge_defaults({}, DEFAULT_SAVE_DATA)

    return _merge_defaults(data, DEFAULT_SAVE_DATA)

def save_data(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(_merge_defaults(data, DEFAULT_SAVE_DATA), f, indent=4)