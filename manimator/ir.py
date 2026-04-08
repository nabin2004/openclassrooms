from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _json_default(obj: Any) -> Any:
    # Pydantic models
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Dataclasses / misc
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=_json_default) + "\n")


def write_ir_bundle(
    *,
    ir_dir: Path,
    run_id: str,
    raw_query: str,
    intent: Any | None = None,
    scene_plan: Any | None = None,
    scene_specs: list[Any] | None = None,
    generated_codes: dict[int, str] | None = None,
    code_paths: dict[int, str] | None = None,
    validation_results: dict[int, Any] | None = None,
    rendered_paths: dict[int, str] | None = None,
    narrated_paths: dict[int, str] | None = None,
    critic_result: Any | None = None,
    scene_transcripts: dict[int, str] | None = None,
    full_transcript: str | None = None,
) -> None:
    """
    Persist a run's Intermediate Representation (IR) as stable artifacts.

    These files are designed to be:
    - easy to inspect
    - usable as a caching key/value layer later
    - usable as training/finetuning datasets later
    """
    ir_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()

    write_json(
        ir_dir / "run_summary.json",
        {
            "schema_version": "1.0.0",
            "run_id": run_id,
            "ts_utc": stamp,
            "raw_query": raw_query,
            "has_intent": intent is not None,
            "has_scene_plan": scene_plan is not None,
            "scene_spec_count": len(scene_specs or []),
            "scene_ids": [getattr(s, "scene_id", None) for s in (scene_specs or [])],
        },
    )

    if intent is not None:
        write_json(ir_dir / "intent.json", intent)
    if scene_plan is not None:
        write_json(ir_dir / "scene_plan.json", scene_plan)
    if scene_specs is not None:
        write_json(ir_dir / "scene_specs.json", scene_specs)
    if generated_codes is not None:
        write_json(ir_dir / "generated_codes.json", generated_codes)
    if code_paths is not None:
        write_json(ir_dir / "code_paths.json", code_paths)
    if validation_results is not None:
        # store as list for deterministic ordering
        ordered = [validation_results[k] for k in sorted(validation_results)]
        write_json(ir_dir / "validation_results.json", ordered)
    if rendered_paths is not None:
        write_json(ir_dir / "rendered_paths.json", rendered_paths)
    if narrated_paths is not None:
        write_json(ir_dir / "narrated_paths.json", narrated_paths)
    if critic_result is not None:
        write_json(ir_dir / "critic_result.json", critic_result)
    if scene_transcripts is not None:
        write_json(ir_dir / "scene_transcripts.json", scene_transcripts)
    if full_transcript is not None:
        write_json(ir_dir / "full_transcript.json", {"full_transcript": full_transcript})

