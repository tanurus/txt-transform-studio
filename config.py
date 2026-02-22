# Centralized configuration — clean transform-only version
import json
import os
import uuid
from typing import Any, Dict, List
from pathlib import Path

PARENT_DIR = Path(__file__).resolve().parent
PROMPT_PATH = str(PARENT_DIR / "SYSTEM_PROMPT.txt")

DEFAULT_TEXT_FOLDER = str(PARENT_DIR / "Data" / "Source")
PROCESSED_FOLDER = os.path.join(PARENT_DIR, "Processed Database")
SETTINGS_FILE = os.path.join(PARENT_DIR, "user_settings.json")

MODEL_CATALOG = {
    "gpt-4.1": {
        "name": "GPT-4.1",
        "input_price_per_1m": 2.0,
        "output_price_per_1m": 8.0,
        "notes": "Flagship model, best quality.",
    },
    "gpt-4.1-mini": {
        "name": "GPT-4.1 Mini",
        "input_price_per_1m": 0.6,
        "output_price_per_1m": 2.4,
        "notes": "Faster and cheaper, good for most tasks.",
    },
    "gpt-4.1-nano": {
        "name": "GPT-4.1 Nano",
        "input_price_per_1m": 0.2,
        "output_price_per_1m": 0.8,
        "notes": "Fastest, lowest cost.",
    },
}
SUPPORTED_MODELS: tuple[str, ...] = tuple(MODEL_CATALOG.keys())
DEFAULT_MODEL = SUPPORTED_MODELS[0]
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0
DEFAULT_PROMPT_ID = "default"
DEFAULT_OUTPUT_FORMAT = ".txt"


def _normalize_text_folder(path: str | None) -> str | None:
    if not path or not isinstance(path, str):
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (PARENT_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return str(candidate)


_text_folder = _normalize_text_folder(DEFAULT_TEXT_FOLDER)


def _load_settings() -> Dict[str, Any]:
    """Load persisted settings from disk, returning an empty dict on error."""
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
            return loaded if isinstance(loaded, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_settings(settings: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(SETTINGS_FILE) or ".", exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)


def get_text_folder() -> str:
    return _text_folder


def set_text_folder(new_path: str) -> None:
    """Persist the folder the UI should monitor for .txt files."""
    normalized = _normalize_text_folder(new_path)
    if not normalized:
        raise ValueError("Text folder path cannot be empty.")
    if not os.path.isdir(normalized):
        raise ValueError("Provided text folder does not exist.")
    global _text_folder
    _text_folder = normalized
    current = _load_settings()
    current["text_folder"] = _text_folder
    _save_settings(current)


def get_model_catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": model_id,
            "name": payload.get("name", model_id),
            "input_price_per_1m": payload.get("input_price_per_1m", 0.0),
            "output_price_per_1m": payload.get("output_price_per_1m", 0.0),
            "notes": payload.get("notes"),
        }
        for model_id, payload in MODEL_CATALOG.items()
    ]


def get_model_settings() -> Dict[str, Any]:
    settings = _load_settings()
    model = settings.get("model", DEFAULT_MODEL)
    if model not in SUPPORTED_MODELS:
        model = DEFAULT_MODEL
    temperature = settings.get("temperature", DEFAULT_TEMPERATURE)
    top_p = settings.get("top_p", DEFAULT_TOP_P)
    output_format = settings.get("output_format", DEFAULT_OUTPUT_FORMAT)
    try:
        temperature = float(temperature)
    except (TypeError, ValueError):
        temperature = DEFAULT_TEMPERATURE
    try:
        top_p = float(top_p)
    except (TypeError, ValueError):
        top_p = DEFAULT_TOP_P
    if output_format not in (".txt", ".md"):
        output_format = DEFAULT_OUTPUT_FORMAT
    return {
        "model": model,
        "temperature": round(temperature, 4),
        "top_p": round(top_p, 4),
        "output_format": output_format,
    }


def set_model_settings(
    model: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    output_format: str | None = None,
) -> Dict[str, Any]:
    settings = _load_settings()
    if model is not None:
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")
        settings["model"] = model
    if temperature is not None:
        temperature = float(temperature)
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        settings["temperature"] = temperature
    if top_p is not None:
        top_p = float(top_p)
        if not 0 <= top_p <= 1:
            raise ValueError("top_p must be between 0 and 1")
        settings["top_p"] = top_p
    if output_format is not None:
        if output_format not in (".txt", ".md"):
            raise ValueError("output_format must be '.txt' or '.md'")
        settings["output_format"] = output_format
    _save_settings(settings)
    return get_model_settings()


def _read_system_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as pf:
            return pf.read()
    except OSError:
        return ""


def get_prompt_presets() -> List[Dict[str, str]]:
    settings = _load_settings()
    presets = settings.get("prompts", [])
    if not isinstance(presets, list):
        presets = []
    unique = []
    seen_ids = set()
    for entry in presets:
        if not isinstance(entry, dict):
            continue
        prompt_id = str(entry.get("id", "")).strip()
        if not prompt_id:
            prompt_id = str(uuid.uuid4())
        if prompt_id in seen_ids:
            continue
        seen_ids.add(prompt_id)
        name = str(entry.get("name", prompt_id)).strip() or prompt_id
        content = str(entry.get("content", "")).strip()
        unique.append({"id": prompt_id, "name": name, "content": content})
    if DEFAULT_PROMPT_ID not in seen_ids:
        unique.insert(
            0,
            {
                "id": DEFAULT_PROMPT_ID,
                "name": "Default (SYSTEM_PROMPT.txt)",
                "content": _read_system_prompt(),
            },
        )
    return unique


def get_default_prompt_id() -> str:
    settings = _load_settings()
    prompt_id = str(settings.get("default_prompt_id", DEFAULT_PROMPT_ID)).strip()
    if not prompt_id:
        return DEFAULT_PROMPT_ID
    if not any(entry["id"] == prompt_id for entry in get_prompt_presets()):
        return DEFAULT_PROMPT_ID
    return prompt_id


def set_default_prompt_id(prompt_id: str) -> None:
    if not prompt_id:
        raise ValueError("Prompt id cannot be empty.")
    if prompt_id not in {entry["id"] for entry in get_prompt_presets()}:
        raise ValueError(f"Unknown prompt id: {prompt_id}")
    settings = _load_settings()
    settings["default_prompt_id"] = prompt_id
    _save_settings(settings)


def get_prompt(prompt_id: str | None = None) -> Dict[str, str]:
    prompts = get_prompt_presets()
    if prompt_id:
        for entry in prompts:
            if entry["id"] == prompt_id:
                return entry.copy()
    active_id = get_default_prompt_id()
    for entry in prompts:
        if entry["id"] == active_id:
            return entry.copy()
    return prompts[0]


def upsert_prompt(
    preset_id: str | None, name: str, content: str, set_default: bool = False
) -> Dict[str, str]:
    if not name or not name.strip():
        raise ValueError("Prompt name cannot be empty.")
    if not content or not str(content).strip():
        raise ValueError("Prompt content cannot be empty.")
    preset_id = (preset_id or "").strip() or str(uuid.uuid4())
    settings = _load_settings()
    prompts = settings.get("prompts", [])
    if not isinstance(prompts, list):
        prompts = []
    updated = False
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        if str(prompt.get("id", "")).strip() == preset_id:
            prompt["name"] = name.strip()
            prompt["content"] = str(content)
            updated = True
            break
    if not updated:
        prompts.append(
            {"id": preset_id, "name": name.strip(), "content": str(content)}
        )
    settings["prompts"] = prompts
    if set_default:
        settings["default_prompt_id"] = preset_id
    _save_settings(settings)
    return get_prompt(preset_id)


def get_theme() -> str:
    """Return 'dark' or 'light'."""
    settings = _load_settings()
    theme = settings.get("theme", "dark")
    return theme if theme in ("dark", "light") else "dark"


def set_theme(theme: str) -> None:
    if theme not in ("dark", "light"):
        raise ValueError("Theme must be 'dark' or 'light'.")
    settings = _load_settings()
    settings["theme"] = theme
    _save_settings(settings)


# ---------- Initialize text folder preference ----------
settings = _load_settings()
if "text_folder" in settings and settings["text_folder"]:
    normalized_from_settings = _normalize_text_folder(settings["text_folder"])
    if normalized_from_settings and os.path.isdir(normalized_from_settings):
        _text_folder = normalized_from_settings

if not _text_folder:
    _text_folder = str(PARENT_DIR)

if not os.path.isdir(_text_folder):
    os.makedirs(_text_folder, exist_ok=True)

os.makedirs(PROCESSED_FOLDER, exist_ok=True)
