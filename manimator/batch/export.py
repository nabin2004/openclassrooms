"""CLI: emit per-stage JSONL datasets from completed batch runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from manimator.batch.manifest import load_samples_from_manifest, manifest_path, read_batch_manifest
from manimator.batch.stages import STAGES_FULL_DELIVERY, LogicalStage, STAGE_ARTIFACT
from manimator.paths import get_run_paths


def _read(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build_row(
    stage: LogicalStage,
    *,
    run_id: str,
    batch_id: str,
    fingerprint: str | None,
    ir_dir: Path,
) -> dict[str, Any] | None:
    """One JSONL record, or None if stage artifact missing."""
    artifact = STAGE_ARTIFACT[stage]
    out_raw = _read(ir_dir / artifact)
    if out_raw is None:
        return None

    summary = _read(ir_dir / "run_summary.json") or {}
    raw_query = str(summary.get("raw_query", ""))

    intent = _read(ir_dir / "intent.json")
    scene_plan = _read(ir_dir / "scene_plan.json")
    scene_specs = _read(ir_dir / "scene_specs.json")
    generated_codes = _read(ir_dir / "generated_codes.json")
    code_paths = _read(ir_dir / "code_paths.json")
    validation_results = _read(ir_dir / "validation_results.json")
    rendered_paths = _read(ir_dir / "rendered_paths.json")

    input_payload: dict[str, Any]
    if stage is LogicalStage.intent:
        input_payload = {"raw_query": raw_query}
    elif stage is LogicalStage.scene_plan:
        input_payload = {"raw_query": raw_query, "intent": intent}
    elif stage is LogicalStage.scene_specs:
        input_payload = {"raw_query": raw_query, "intent": intent, "scene_plan": scene_plan}
    elif stage is LogicalStage.codegen:
        input_payload = {"scene_specs": scene_specs}
    elif stage is LogicalStage.validation:
        input_payload = {"scene_specs": scene_specs, "generated_codes": generated_codes}
    elif stage is LogicalStage.render:
        input_payload = {
            "scene_specs": scene_specs,
            "generated_codes": generated_codes,
            "code_paths": code_paths,
            "validation_results": validation_results,
        }
    elif stage is LogicalStage.critic:
        input_payload = {
            "scene_specs": scene_specs,
            "rendered_paths": rendered_paths,
        }
    elif stage is LogicalStage.narrate:
        input_payload = {
            "scene_specs": scene_specs,
            "rendered_paths": rendered_paths,
        }
    elif stage is LogicalStage.finalize:
        input_payload = {
            "scene_specs": scene_specs,
            "narrated_paths": _read(ir_dir / "narrated_paths.json"),
            "rendered_paths": rendered_paths,
        }
    else:
        input_payload = {}

    return {
        "input": input_payload,
        "output": out_raw,
        "metadata": {
            "run_id": run_id,
            "batch_id": batch_id,
            "stage": stage.value,
            "pipeline_fingerprint": fingerprint,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
    }


def export_batch(
    *,
    outputs_root: Path,
    batch_id: str,
    stages: tuple[LogicalStage, ...] | None = None,
) -> dict[str, Path]:
    outputs_root = outputs_root.resolve()
    mpath = manifest_path(outputs_root, batch_id)
    manifest = read_batch_manifest(mpath)
    fingerprint = manifest.get("pipeline_fingerprint")
    samples = load_samples_from_manifest(manifest)
    stage_list = STAGES_FULL_DELIVERY if stages is None else stages

    out_dir = outputs_root / "datasets" / batch_id
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for stage in stage_list:
        out_path = out_dir / f"{stage.value}.jsonl"
        out_path.write_text("", encoding="utf-8")
        with open(out_path, "w", encoding="utf-8") as f:
            for ref in samples:
                paths = get_run_paths(ref.run_id, outputs_root=outputs_root)
                row = _build_row(
                    stage,
                    run_id=ref.run_id,
                    batch_id=batch_id,
                    fingerprint=str(fingerprint) if fingerprint else None,
                    ir_dir=paths.ir_dir,
                )
                if row is not None:
                    f.write(json.dumps(row, default=str) + "\n")
        written[stage.value] = out_path
    return written


def main() -> None:
    p = argparse.ArgumentParser(description="Export per-stage JSONL datasets from a batch manifest.")
    p.add_argument("--batch-id", required=True)
    p.add_argument("--outputs-root", type=Path, default=Path("outputs"))
    p.add_argument(
        "--stages",
        default=None,
        help="Comma-separated stages to export (default: all known stages).",
    )
    args = p.parse_args()
    stages_arg = args.stages
    stages: tuple[LogicalStage, ...] | None
    if stages_arg:
        stages = tuple(LogicalStage(s.strip()) for s in stages_arg.split(","))
    else:
        stages = tuple(STAGES_FULL_DELIVERY)
    written = export_batch(outputs_root=args.outputs_root, batch_id=args.batch_id, stages=stages)
    print(json.dumps({k: str(v) for k, v in written.items()}, indent=2))


if __name__ == "__main__":
    main()
