import json
import logging
import re
from typing import Any

from amoeba.exceptions import JSONParseError
from amoeba.observability import get_trace_id

_json_log = logging.getLogger("amoeba.json")


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

def safe_parse_json(raw: str, *, preview_chars: int = 500) -> Any:
    """
    Strip markdown fences, parse JSON, raise :class:`~amoeba.exceptions.JSONParseError` on failure.

    Logs a debug preview before parse and a warning on failure (truncate long text).
    """
    cleaned = strip_fences(raw)
    tid = get_trace_id()
    _json_log.debug(
        "json.parse.attempt trace_id=%s preview=%s",
        tid,
        cleaned[:preview_chars],
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        _json_log.warning(
            "json.parse.failed trace_id=%s error=%s preview=%s",
            tid,
            e,
            cleaned[:preview_chars],
        )
        raise JSONParseError(
            "Failed to parse LLM JSON output",
            context={
                "json_error": str(e),
                "text_preview": cleaned[:preview_chars],
                "trace_id": tid,
            },
            user_message="The model returned invalid JSON.",
        ) from e