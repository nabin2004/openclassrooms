import re
import json
from typing import Any

def strip_fences(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    parts = text.split("```")
    if len(parts) >= 2:
        content = parts[1].strip()
        first_newline = content.find("\n")
        if first_newline != -1:
            maybe_lang = content[:first_newline].strip().lower()
            if maybe_lang in {"json", "python", "py", "js", "typescript"}:
                content = content[first_newline + 1:]
        return content.strip()
    return text

def to_class_name(raw: str, fallback: str = "SceneAuto") -> str:
    name = re.sub(r'[^a-zA-Z0-9]', '', raw)
    if not name:
        return fallback
    return name[0].upper() + name[1:]

def safe_parse_json(raw: str) -> Any:
    cleaned = strip_fences(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parse failed: {e}\nRaw:\n{cleaned}")