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
        # Fallback: many models wrap JSON with a short preamble/epilogue.
        # Try to extract the first balanced JSON object/array and parse that.
        extracted = _extract_first_json(cleaned)
        if extracted is not None:
            try:
                return json.loads(extracted)
            except json.JSONDecodeError:
                pass
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


def _extract_first_json(text: str) -> str | None:
    """
    Return the first balanced JSON object/array substring, if any.

    This is a best-effort extractor to tolerate harmless preambles like
    "Sure, here's the JSON:" while keeping strict JSON decoding.
    """
    s = text.strip()
    if not s:
        return None
    start_candidates = []
    for ch in ("{", "["):
        idx = s.find(ch)
        if idx != -1:
            start_candidates.append(idx)
    if not start_candidates:
        return None
    start = min(start_candidates)
    opener = s[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if in_str:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            continue
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None