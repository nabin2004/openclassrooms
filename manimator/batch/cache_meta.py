"""Per-run IR fingerprint sidecar for batch resume skip semantics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_BATCH_CACHE = "batch_cache.json"


def batch_cache_path(ir_dir: Path) -> Path:
    return ir_dir / _BATCH_CACHE


def read_batch_cache_fingerprint(ir_dir: Path) -> str | None:
    p = batch_cache_path(ir_dir)
    if not p.is_file():
        return None
    try:
        data: Any = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        fp = data.get("pipeline_fingerprint")
        if isinstance(fp, str):
            return fp
    return None


def write_batch_cache(ir_dir: Path, *, pipeline_fingerprint: str) -> None:
    ir_dir.mkdir(parents=True, exist_ok=True)
    batch_cache_path(ir_dir).write_text(
        json.dumps({"pipeline_fingerprint": pipeline_fingerprint}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
