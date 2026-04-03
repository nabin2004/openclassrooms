"""Structured logging and request correlation for Amoeba."""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

_trace_id: ContextVar[str | None] = ContextVar("amoeba_trace_id", default=None)


def get_logger(name: str = "amoeba") -> logging.Logger:
    return logging.getLogger(name)


def get_trace_id() -> str | None:
    return _trace_id.get()


def set_trace_id(trace_id: str | None) -> None:
    _trace_id.set(trace_id)


def new_trace_id() -> str:
    """Set and return a new trace id for the current async/task context."""
    tid = str(uuid.uuid4())
    _trace_id.set(tid)
    return tid


def log_structured(
    logger: logging.Logger,
    level: int,
    event: str,
    **payload: Any,
) -> None:
    """Emit one log line with a JSON payload (default ``str`` for non-JSON types)."""
    data = {"event": event, **payload}
    tid = get_trace_id()
    if tid is not None:
        data["trace_id"] = tid
    logger.log(level, "%s %s", event, json.dumps(data, default=str))


def log_llm_event(event: str, **data: Any) -> None:
    """INFO-level helper for LLM lifecycle events."""
    log_structured(get_logger(), logging.INFO, event, **data)
