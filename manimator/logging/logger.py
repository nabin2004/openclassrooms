from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Mapping


_DEFAULT_FORMAT = (
    "%(asctime)s %(levelname)s %(name)s "
    "run_id=%(run_id)s node=%(node)s scene_id=%(scene_id)s - %(message)s"
)


class _MissingContextFilter(logging.Filter):
    """Ensure formatter fields always exist (so logs never crash formatting)."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 (filter name is stdlib)
        if not hasattr(record, "run_id"):
            record.run_id = "-"
        if not hasattr(record, "node"):
            record.node = "-"
        if not hasattr(record, "scene_id"):
            record.scene_id = "-"
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "run_id": getattr(record, "run_id", "-"),
            "node": getattr(record, "node", "-"),
            "scene_id": getattr(record, "scene_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(
    *,
    level: str | int | None = None,
    json_logs: bool | None = None,
    log_file: str | None = None,
) -> None:
    """
    Configure process-wide logging for Manimator.

    - Respects env vars: MANIMATOR_LOG_LEVEL, MANIMATOR_LOG_JSON, MANIMATOR_LOG_FILE.
    - Safe to call multiple times (idempotent-ish).
    """
    env_level = os.getenv("MANIMATOR_LOG_LEVEL")
    env_json = os.getenv("MANIMATOR_LOG_JSON")
    env_file = os.getenv("MANIMATOR_LOG_FILE")

    if level is None:
        level = env_level or "INFO"
    if json_logs is None:
        json_logs = (env_json or "").strip().lower() in {"1", "true", "yes", "on"}
    if log_file is None:
        log_file = env_file

    resolved_level = level
    if isinstance(level, str):
        resolved_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(int(resolved_level))

    # Avoid duplicate handlers if configure_logging is called again.
    if getattr(root, "_manimator_configured", False):
        return

    handlers: list[logging.Handler] = []

    stream_handler = logging.StreamHandler(stream=sys.stderr)
    handlers.append(stream_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(file_handler)

    formatter: logging.Formatter
    if json_logs:
        formatter = _JsonFormatter()
    else:
        formatter = logging.Formatter(_DEFAULT_FORMAT)

    for h in handlers:
        h.setLevel(int(resolved_level))
        h.addFilter(_MissingContextFilter())
        h.setFormatter(formatter)
        root.addHandler(h)

    root._manimator_configured = True  # type: ignore[attr-defined]


def get_logger(
    name: str,
    *,
    run_id: str | None = None,
    node: str | None = None,
    scene_id: int | str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> logging.LoggerAdapter:
    base = logging.getLogger(name)
    merged: dict[str, Any] = {}
    if extra:
        merged.update(dict(extra))
    if run_id is not None:
        merged["run_id"] = run_id
    if node is not None:
        merged["node"] = node
    if scene_id is not None:
        merged["scene_id"] = scene_id
    return logging.LoggerAdapter(base, merged)


def log_exception(
    logger: logging.Logger | logging.LoggerAdapter,
    message: str,
    *,
    exc: BaseException | None = None,
    level: int = logging.ERROR,
) -> None:
    if exc is None:
        logger.log(level, message, exc_info=True)
    else:
        logger.log(level, message, exc_info=(type(exc), exc, exc.__traceback__))
