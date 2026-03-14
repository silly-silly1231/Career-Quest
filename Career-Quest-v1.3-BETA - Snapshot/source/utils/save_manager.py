# utils/save_manager.py
import json
import os
import tempfile
from copy import deepcopy

SOURCE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_FILE = os.path.join(SOURCE_ROOT, "save_data.json")

DEFAULT_SAVE_DATA = {
    "tutorial_dialogue_completed": False,
    "completed_careers": [],
    "skills": {
        "debugging": 0,
        "logic": 0,
        "efficiency": 0,
        "speed": 0,
        "timing": 0,
        "precision": 0,
        "organization": 0,
        "composure": 0,
        "triage": 0,
        "diagnosis": 0,
        "accuracy": 0,
        "empathy": 0,
    },
    "career_reports": {},
}


def _default_save_data():
    return deepcopy(DEFAULT_SAVE_DATA)


def _clamp_score(value):
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, min(5, int(value)))
    return 0


def _sanitize_skills(skills):
    sanitized = _default_save_data()["skills"]
    if not isinstance(skills, dict):
        return sanitized

    for key in sanitized:
        sanitized[key] = _clamp_score(skills.get(key, sanitized[key]))
    return sanitized


def _sanitize_career_reports(reports):
    if not isinstance(reports, dict):
        return {}

    sanitized = {}
    for career_name, values in reports.items():
        if not isinstance(career_name, str) or not isinstance(values, dict):
            continue

        cleaned_values = {}
        for skill_name, skill_value in values.items():
            if isinstance(skill_name, str):
                cleaned_values[skill_name] = _clamp_score(skill_value)

        sanitized[career_name] = cleaned_values
    return sanitized


def _sanitize_save_data(data):
    sanitized = _default_save_data()
    if not isinstance(data, dict):
        return sanitized

    sanitized["tutorial_dialogue_completed"] = bool(data.get("tutorial_dialogue_completed", False))

    completed_careers = data.get("completed_careers", [])
    if isinstance(completed_careers, list):
        sanitized["completed_careers"] = []
        seen = set()
        for career in completed_careers:
            if not isinstance(career, str) or career in seen:
                continue
            seen.add(career)
            sanitized["completed_careers"].append(career)

    sanitized["skills"] = _sanitize_skills(data.get("skills"))
    sanitized["career_reports"] = _sanitize_career_reports(data.get("career_reports"))
    return sanitized


def load_save():
    if not os.path.exists(SAVE_FILE):
        return _default_save_data()

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return _default_save_data()

    return _sanitize_save_data(data)


def save_data(data):
    sanitized_data = _sanitize_save_data(data)
    save_directory = os.path.dirname(SAVE_FILE)

    try:
        os.makedirs(save_directory, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=save_directory,
            delete=False,
            prefix="save_data_",
            suffix=".tmp",
        ) as temp_file:
            json.dump(sanitized_data, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = temp_file.name
        os.replace(temp_path, SAVE_FILE)
        return True
    except OSError:
        temp_path = locals().get("temp_path")
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False


def delete_save_data():
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
        return True
    except OSError:
        return False