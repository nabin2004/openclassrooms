"""Batch manifest JSON under outputs/batches/<batch_id>/batch_manifest.json."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MANIFEST_SCHEMA = "1.0.0"


@dataclass(frozen=True, slots=True)
class BatchSampleRef:
    row_id: str
    run_id: str
    raw_query_hash: str


def raw_query_hash(raw_query: str) -> str:
    return hashlib.sha256(raw_query.encode("utf-8")).hexdigest()[:32]


def batch_dir(outputs_root: Path, batch_id: str) -> Path:
    return outputs_root.resolve() / "batches" / batch_id


def manifest_path(outputs_root: Path, batch_id: str) -> Path:
    return batch_dir(outputs_root, batch_id) / "batch_manifest.json"


def progress_path(outputs_root: Path, batch_id: str) -> Path:
    return batch_dir(outputs_root, batch_id) / "progress.jsonl"


def write_batch_manifest(
    *,
    outputs_root: Path,
    batch_id: str,
    pipeline_fingerprint: str,
    prompt_versions: dict[str, str],
    samples: list[BatchSampleRef],
) -> Path:
    out = manifest_path(outputs_root, batch_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": MANIFEST_SCHEMA,
        "batch_id": batch_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline_fingerprint": pipeline_fingerprint,
        "prompt_versions": prompt_versions,
        "samples": [
            {
                "row_id": s.row_id,
                "run_id": s.run_id,
                "raw_query_hash": s.raw_query_hash,
            }
            for s in samples
        ],
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def read_batch_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid manifest: {path}")
    return data


def load_samples_from_manifest(manifest: dict[str, Any]) -> list[BatchSampleRef]:
    raw = manifest.get("samples") or []
    out: list[BatchSampleRef] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(
            BatchSampleRef(
                row_id=str(item.get("row_id", "")),
                run_id=str(item["run_id"]),
                raw_query_hash=str(item.get("raw_query_hash", "")),
            )
        )
    return out
