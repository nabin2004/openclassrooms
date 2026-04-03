"""Unified per-request trace summaries (LangSmith-light)."""

from __future__ import annotations

import json
import logging
from typing import Any

from amoeba.observability import get_trace_id

_trace_log = logging.getLogger("amoeba.trace")


def _truncate(text: str | None, max_chars: int) -> str | None:
    if text is None:
        return None
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


def log_trace_summary(
    *,
    event: str,
    trace_id: str | None = None,
    prompt_version: str | None = None,
    prompt_name: str | None = None,
    input_text: str | None = None,
    input_max_chars: int = 500,
    output: Any = None,
    tokens: dict[str, Any] | None = None,
    latency_ms: float | None = None,
    model: str | None = None,
    cost: float | None = None,
    error: str | None = None,
    **extra: Any,
) -> None:
    """
    Emit one structured log line for a logical request (intent, planner, …).

    ``output`` should be JSON-serializable (e.g. ``model_dump()`` on Pydantic models).
    """
    tid = trace_id if trace_id is not None else get_trace_id()
    payload: dict[str, Any] = {
        "trace_id": tid,
        "event": event,
        "prompt_version": prompt_version,
        "prompt_name": prompt_name,
        "input": _truncate(input_text, input_max_chars),
        "output": output,
        "tokens": tokens,
        "latency_ms": latency_ms,
        "model": model,
        "cost": cost,
        "error": error,
        **extra,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    line = json.dumps(payload, default=str)
    _trace_log.info("%s %s", event, line)
