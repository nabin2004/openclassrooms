"""
Per-scene codegen → validate → repair → render pipeline.

The inner validate/repair loop lives here (not on LangGraph edges). Scenes run in
parallel up to ``MAX_PARALLEL_SCENES`` (default 3).
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amoeba.subprocess import run_subprocess

from manimator.agents.codegen import generate_code
from manimator.agents.repair import repair_code
from manimator.agents.validator import validate_code
from manimator.config.video_config import get_video_config
from manimator.contracts.scene_spec import SceneSpec
from manimator.contracts.validation import MAX_RETRIES, ErrorType, ValidationResult
from manimator.ir import write_ir_bundle
from manimator.logging import get_logger, log_exception
from manimator.paths import RunPaths, get_run_paths
from amoeba.observability import get_logger as get_amoeba_logger
from amoeba.observability import log_structured


def _max_repair_attempts() -> int:
    cfg = get_video_config()
    return min(MAX_RETRIES, cfg.max_retries)


@dataclass
class ScenePipelineResult:
    scene_id: int
    code: str
    code_path: str
    validation: ValidationResult
    rendered_path: str
    exc: BaseException | None = None


def _render_one_sync(
    spec: SceneSpec,
    code_path: str,
    paths: RunPaths,
    run_id: str,
) -> str:
    """Run manim subprocess; return intended output mp4 path (may not exist if manim failed)."""
    scene_log = get_logger(__name__, run_id=run_id, node="render", scene_id=spec.scene_id)
    output_file = paths.renders_dir / f"scene_{spec.scene_id}.mp4"
    scene_class = spec.class_name

    if not Path(code_path).exists():
        Path(code_path).write_text("", encoding="utf-8")

    try:
        cmd = [
            "manim",
            code_path,
            scene_class,
            "-qm",
            "--output_file",
            f"scene_{spec.scene_id}",
            "--media_dir",
            str(paths.manim_media_dir),
        ]
        result = run_subprocess(cmd, check=False)
        if result.returncode == 0:
            media_dir = paths.manim_media_dir / "videos"
            if media_dir.exists():
                for file in media_dir.rglob(f"*scene_{spec.scene_id}*.mp4"):
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    file.replace(output_file)
                    break
                else:
                    for file in media_dir.rglob(f"*{scene_class}*.mp4"):
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        file.replace(output_file)
                        break
            if output_file.exists():
                scene_log.info("Rendered to %s", str(output_file))
            else:
                scene_log.warning("Manim succeeded but output not found at %s", str(output_file))
        else:
            scene_log.error(
                "Manim failed (exit=%s). stderr=%s",
                result.returncode,
                (result.stderr or "").strip(),
            )
    except Exception as e:
        log_exception(scene_log, "Exception while rendering scene.", exc=e)
        return str((paths.renders_dir / f"scene_{spec.scene_id}.mp4").resolve())

    return str(output_file.resolve())


async def run_scene_subagent(spec: SceneSpec, paths: RunPaths, run_id: str) -> ScenePipelineResult:
    """
    One scene: template codegen → validate/repair loop → manim render.

    Matches previous graph semantics: after ``max_repair_attempts`` failed validations,
    proceed to render with the last code (may still fail at manim).
    """
    scene_log = get_logger(__name__, run_id=run_id, node="codegen_render", scene_id=spec.scene_id)
    out_py = paths.code_dir / f"scene_{spec.scene_id}.py"
    code = await generate_code(spec)
    out_py.write_text(code or "", encoding="utf-8")
    code_path = str(out_py.resolve())

    max_attempts = _max_repair_attempts()
    retry = 0
    last_vr: ValidationResult | None = None

    while retry <= max_attempts:
        vr = await validate_code(code, spec, retry_count=retry)
        last_vr = vr
        if vr.passed:
            scene_log.info("Validation passed after %s attempt(s).", retry)
            break
        if retry >= max_attempts:
            scene_log.warning(
                "Validation still failing after %s attempts; proceeding to render. type=%s",
                retry,
                getattr(vr.error_type, "value", None),
            )
            break
        code = await repair_code(vr)
        out_py.write_text(code or "", encoding="utf-8")
        retry += 1
        scene_log.info("Repaired code (%s chars). retry=%s", len(code or ""), retry)

    assert last_vr is not None
    rendered = await asyncio.to_thread(_render_one_sync, spec, code_path, paths, run_id)
    return ScenePipelineResult(
        scene_id=spec.scene_id,
        code=code,
        code_path=code_path,
        validation=last_vr,
        rendered_path=rendered,
    )


async def node_codegen_render(state: Any) -> dict:
    """
    LangGraph node: parallel per-scene subagents (codegen + validate/repair + render).
    """
    from manimator.pipeline.state import PipelineState

    assert isinstance(state, PipelineState)
    log = get_logger(__name__, run_id=state.run_id, node="codegen_render")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="codegen_render")

    max_parallel = int(os.getenv("MAX_PARALLEL_SCENES", "3"))
    sem = asyncio.Semaphore(max_parallel)

    async def guarded(spec: SceneSpec) -> ScenePipelineResult:
        async with sem:
            try:
                return await run_scene_subagent(spec, paths, run_id)
            except Exception as e:
                scene_log = get_logger(__name__, run_id=state.run_id, scene_id=spec.scene_id)
                log_exception(scene_log, "Scene subagent failed.", exc=e)
                p = paths.code_dir / f"scene_{spec.scene_id}.py"
                fallback_code = p.read_text(encoding="utf-8") if p.is_file() else ""
                return ScenePipelineResult(
                    scene_id=spec.scene_id,
                    code=fallback_code,
                    code_path=str(p.resolve()),
                    validation=ValidationResult(
                        passed=False,
                        scene_id=spec.scene_id,
                        failing_code=fallback_code,
                        error_type=ErrorType.TIMEOUT,
                        error_message=str(e),
                        error_line=1,
                        retry_count=0,
                        original_spec=spec,
                    ),
                    rendered_path=str((paths.renders_dir / f"scene_{spec.scene_id}.mp4").resolve()),
                    exc=e,
                )

    results = await asyncio.gather(*[guarded(spec) for spec in state.scene_specs])

    codes: dict[int, str] = {}
    code_paths: dict[int, str] = {}
    validation_results: dict[int, ValidationResult] = {}
    rendered_paths: dict[int, str] = {}
    failed: list[int] = []

    for r in results:
        codes[r.scene_id] = r.code
        code_paths[r.scene_id] = r.code_path
        validation_results[r.scene_id] = r.validation
        rendered_paths[r.scene_id] = r.rendered_path
        if not r.validation.passed:
            failed.append(r.scene_id)

    log.info(
        "Codegen+render complete. scenes=%s failed_validation=%s",
        sorted(codes.keys()),
        failed,
    )
    log_structured(
        get_amoeba_logger(),
        20,
        "pipeline.node.completed",
        run_id=run_id,
        node="codegen_render",
        scenes=len(codes),
        failed_validation=failed,
    )

    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=state.scene_plan,
        scene_specs=state.scene_specs,
        generated_codes=codes,
        code_paths=code_paths,
        validation_results=validation_results,
        rendered_paths=rendered_paths,
    )

    return {
        "generated_codes": codes,
        "code_paths": code_paths,
        "validation_results": validation_results,
        "rendered_paths": rendered_paths,
        "failed_scene_ids": failed,
        "run_dir": str(paths.run_dir),
    }


async def _render_one_scene_async(spec: SceneSpec, state: Any) -> tuple[int, str]:
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    code_path = state.code_paths.get(spec.scene_id) or str(
        (paths.code_dir / f"scene_{spec.scene_id}.py").resolve()
    )
    if not Path(code_path).exists():
        Path(code_path).write_text(state.generated_codes.get(spec.scene_id, ""), encoding="utf-8")
    out = await asyncio.to_thread(_render_one_sync, spec, code_path, paths, run_id)
    return spec.scene_id, out


async def node_render(state: Any) -> dict:
    """
    Render all scenes in parallel (for tests and batch ``render`` stage resume).

    Expects ``scene_specs`` and ``generated_codes`` (and optionally ``code_paths``).
    """
    from manimator.pipeline.state import PipelineState

    assert isinstance(state, PipelineState)
    log = get_logger(__name__, run_id=state.run_id, node="render")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="render")

    max_parallel = int(os.getenv("MAX_PARALLEL_SCENES", "3"))
    sem = asyncio.Semaphore(max_parallel)

    async def one(spec: SceneSpec) -> tuple[int, str]:
        async with sem:
            return await _render_one_scene_async(spec, state)

    pairs = await asyncio.gather(*[one(s) for s in state.scene_specs])
    rendered = {sid: p for sid, p in pairs}

    log.info("Render step complete. rendered_scenes=%s", sorted(rendered.keys()))
    log_structured(
        get_amoeba_logger(),
        20,
        "pipeline.node.completed",
        run_id=run_id,
        node="render",
        rendered_scenes=sorted(rendered.keys()),
    )
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=state.scene_plan,
        scene_specs=state.scene_specs,
        generated_codes=state.generated_codes,
        code_paths=state.code_paths,
        validation_results=state.validation_results,
        rendered_paths=rendered,
    )
    return {"rendered_paths": rendered, "run_dir": str(paths.run_dir)}


async def node_validate(state: Any) -> dict:
    """Validate all scenes in parallel (batch resume / legacy)."""
    from manimator.pipeline.state import PipelineState

    assert isinstance(state, PipelineState)
    log = get_logger(__name__, run_id=state.run_id, node="validate")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="validate")

    max_parallel = int(os.getenv("MAX_PARALLEL_SCENES", "3"))
    sem = asyncio.Semaphore(max_parallel)

    async def one(spec: SceneSpec) -> tuple[int, ValidationResult]:
        async with sem:
            code = state.generated_codes[spec.scene_id]
            retry_count = state.retry_counts.get(spec.scene_id, 0)
            scene_log = get_logger(__name__, run_id=state.run_id, node="validate", scene_id=spec.scene_id)
            result = await validate_code(code, spec, retry_count=retry_count)
            if not result.passed:
                scene_log.warning(
                    "Validation failed (type=%s line=%s): %s",
                    getattr(result.error_type, "value", None),
                    result.error_line,
                    result.error_message,
                )
            else:
                scene_log.info("Validation passed.")
            return spec.scene_id, result

    pairs = await asyncio.gather(*[one(s) for s in state.scene_specs])
    results = {sid: vr for sid, vr in pairs}
    failed = [sid for sid, vr in results.items() if not vr.passed]

    log.info("Validation complete. failed_scene_ids=%s", failed)
    log_structured(
        get_amoeba_logger(),
        20,
        "pipeline.node.completed",
        run_id=run_id,
        node="validate",
        failed_scene_ids=failed,
    )
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=state.scene_plan,
        scene_specs=state.scene_specs,
        generated_codes=state.generated_codes,
        code_paths=state.code_paths,
        validation_results=results,
    )
    return {"validation_results": results, "failed_scene_ids": failed}


async def node_repair(state: Any) -> dict:
    """Repair failed scenes (batch resume / legacy)."""
    from manimator.pipeline.state import PipelineState

    assert isinstance(state, PipelineState)
    log = get_logger(__name__, run_id=state.run_id, node="repair")
    run_id = state.run_id or "unknown"
    log_structured(
        get_amoeba_logger(),
        20,
        "pipeline.node.start",
        run_id=run_id,
        node="repair",
        failed_scene_ids=state.failed_scene_ids,
    )
    new_codes = dict(state.generated_codes)
    new_retries = dict(state.retry_counts)

    for scene_id in state.failed_scene_ids:
        validation = state.validation_results[scene_id]
        scene_log = get_logger(__name__, run_id=state.run_id, node="repair", scene_id=scene_id)
        repaired = await repair_code(validation)
        new_codes[scene_id] = repaired
        out_py = get_run_paths(run_id).code_dir / f"scene_{scene_id}.py"
        out_py.write_text(repaired or "", encoding="utf-8")
        new_retries[scene_id] = new_retries.get(scene_id, 0) + 1
        scene_log.info("Repaired code (%s chars). retry_count=%s", len(repaired or ""), new_retries[scene_id])

    log_structured(
        get_amoeba_logger(),
        20,
        "pipeline.node.completed",
        run_id=run_id,
        node="repair",
        repaired_scenes=list(state.failed_scene_ids),
    )
    return {"generated_codes": new_codes, "retry_counts": new_retries}
