"""Load PipelineState from persisted IR JSON under outputs/runs/<run_id>/ir/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manimator.contracts.critic import CriticResult
from manimator.contracts.intent import IntentResult
from manimator.contracts.scene_plan import ScenePlan
from manimator.contracts.scene_spec import SceneSpec
from manimator.contracts.validation import ValidationResult
from manimator.pipeline.state import PipelineState


def _read_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _int_key_dict(d: dict[Any, Any] | None) -> dict[int, Any]:
    if not d:
        return {}
    out: dict[int, Any] = {}
    for k, v in d.items():
        out[int(k)] = v
    return out


def load_pipeline_state(
    ir_dir: Path,
    *,
    run_id: str | None = None,
) -> PipelineState:
    """
    Best-effort hydrate ``PipelineState`` from ``ir_dir``.

    Reads ``run_summary.json`` for ``raw_query`` and optional ``run_id``;
    loads optional stage artifacts when present.
    """
    ir_dir = ir_dir.resolve()
    summary = _read_json(ir_dir / "run_summary.json")
    if not isinstance(summary, dict):
        raise FileNotFoundError(f"Missing or invalid run_summary.json under {ir_dir}")

    raw_query = summary.get("raw_query") or ""
    rid = run_id or summary.get("run_id") or ""

    state = PipelineState(raw_query=str(raw_query), run_id=str(rid) if rid else None)

    intent_data = _read_json(ir_dir / "intent.json")
    if intent_data is not None:
        state.intent = IntentResult.model_validate(intent_data)

    plan_data = _read_json(ir_dir / "scene_plan.json")
    if plan_data is not None:
        state.scene_plan = ScenePlan.model_validate(plan_data)

    specs_data = _read_json(ir_dir / "scene_specs.json")
    if isinstance(specs_data, list):
        state.scene_specs = [SceneSpec.model_validate(x) for x in specs_data]

    codes = _read_json(ir_dir / "generated_codes.json")
    if isinstance(codes, dict):
        state.generated_codes = {int(k): str(v) for k, v in codes.items()}

    paths = _read_json(ir_dir / "code_paths.json")
    if isinstance(paths, dict):
        state.code_paths = {int(k): str(v) for k, v in paths.items()}

    val = _read_json(ir_dir / "validation_results.json")
    if isinstance(val, list):
        results: dict[int, ValidationResult] = {}
        for item in val:
            vr = ValidationResult.model_validate(item)
            results[vr.scene_id] = vr
        state.validation_results = results

    rendered = _read_json(ir_dir / "rendered_paths.json")
    if isinstance(rendered, dict):
        state.rendered_paths = _int_key_dict(rendered)

    narrated = _read_json(ir_dir / "narrated_paths.json")
    if isinstance(narrated, dict):
        state.narrated_paths = _int_key_dict(narrated)

    critic_data = _read_json(ir_dir / "critic_result.json")
    if critic_data is not None:
        state.critic_result = CriticResult.model_validate(critic_data)

    transcripts = _read_json(ir_dir / "scene_transcripts.json")
    if isinstance(transcripts, dict):
        state.scene_transcripts = _int_key_dict(transcripts)

    full = _read_json(ir_dir / "full_transcript.json")
    if isinstance(full, dict) and "full_transcript" in full:
        state.full_transcript = str(full["full_transcript"])

    return state
