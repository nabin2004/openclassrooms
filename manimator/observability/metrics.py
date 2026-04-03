"""Append-only JSONL metrics for offline analysis (dashboards later)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


def append_metrics_jsonl(record: dict[str, Any]) -> None:
    """
    If ``MANIMATOR_METRICS_JSONL`` is set, append one JSON object per line.

    The path should be writable by the process (e.g. under ``outputs/``).
    """
    path = os.getenv("MANIMATOR_METRICS_JSONL")
    if not path:
        return
    line = {
        "ts": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(line, default=str) + "\n")
