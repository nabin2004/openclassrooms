"""Logical batch stages mapped to existing LangGraph node functions."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from manimator.batch.state_merge import merge_updates
from manimator.pipeline.graph import (
    edge_after_validate,
    node_add_narration,
    node_classify_intent,
    node_critique,
    node_decompose_scenes,
    node_finalize,
    node_generate_code,
    node_plan_scenes,
    node_render,
    node_repair,
    node_validate,
)
from manimator.pipeline.state import PipelineState


class LogicalStage(str, Enum):
    intent = "intent"
    scene_plan = "scene_plan"
    scene_specs = "scene_specs"
    codegen = "codegen"
    validation = "validation"
    render = "render"
    critic = "critic"
    narrate = "narrate"
    finalize = "finalize"


# Primary artifact used for resume skip detection
STAGE_ARTIFACT: dict[LogicalStage, str] = {
    LogicalStage.intent: "intent.json",
    LogicalStage.scene_plan: "scene_plan.json",
    LogicalStage.scene_specs: "scene_specs.json",
    LogicalStage.codegen: "generated_codes.json",
    LogicalStage.validation: "validation_results.json",
    LogicalStage.render: "rendered_paths.json",
    LogicalStage.critic: "critic_result.json",
    LogicalStage.narrate: "narrated_paths.json",
    LogicalStage.finalize: "full_transcript.json",
}

STAGES_THROUGH_CRITIC: tuple[LogicalStage, ...] = (
    LogicalStage.intent,
    LogicalStage.scene_plan,
    LogicalStage.scene_specs,
    LogicalStage.codegen,
    LogicalStage.validation,
    LogicalStage.render,
    LogicalStage.critic,
)

STAGES_FULL_DELIVERY: tuple[LogicalStage, ...] = STAGES_THROUGH_CRITIC + (
    LogicalStage.narrate,
    LogicalStage.finalize,
)


def resolve_stage_list(
    names: list[str] | None,
    *,
    profile: str,
) -> tuple[LogicalStage, ...]:
    """Resolve ``--stages`` names or use profile defaults."""
    if names:
        out: list[LogicalStage] = []
        for n in names:
            out.append(LogicalStage(n.strip()))
        return tuple(out)
    if profile == "full_delivery":
        return STAGES_FULL_DELIVERY
    return STAGES_THROUGH_CRITIC


def artifact_ready(ir_dir: Path, stage: LogicalStage) -> bool:
    name = STAGE_ARTIFACT[stage]
    return (ir_dir / name).is_file()


async def run_validation_bundle(state: PipelineState) -> None:
    """Validate / repair loop matching ``edge_after_validate`` semantics."""
    while True:
        merge_updates(state, await node_validate(state))
        nxt = edge_after_validate(state)
        if nxt == "render":
            break
        merge_updates(state, await node_repair(state))


async def run_critic_with_optional_replans(
    state: PipelineState,
    *,
    max_critic_replans: int,
) -> None:
    """
    Run critique; optionally re-run plan → codegen → validation (bounded).

    ``max_critic_replans`` counts how many replan *tails* may execute after the first critique.
    """
    replans_done = 0
    while True:
        merge_updates(state, await node_critique(state))
        cr = state.critic_result
        if cr is None or not cr.replan_required:
            return
        if replans_done >= max_critic_replans:
            return
        replans_done += 1
        state.replan_count = replans_done
        merge_updates(state, await node_plan_scenes(state))
        merge_updates(state, await node_generate_code(state))
        await run_validation_bundle(state)


async def run_logical_stage(
    state: PipelineState,
    stage: LogicalStage,
    *,
    max_critic_replans: int,
) -> None:
    if stage is LogicalStage.intent:
        merge_updates(state, await node_classify_intent(state))
        return
    if stage is LogicalStage.scene_plan:
        merge_updates(state, await node_decompose_scenes(state))
        return
    if stage is LogicalStage.scene_specs:
        merge_updates(state, await node_plan_scenes(state))
        return
    if stage is LogicalStage.codegen:
        merge_updates(state, await node_generate_code(state))
        return
    if stage is LogicalStage.validation:
        await run_validation_bundle(state)
        return
    if stage is LogicalStage.render:
        merge_updates(state, await node_render(state))
        return
    if stage is LogicalStage.critic:
        await run_critic_with_optional_replans(state, max_critic_replans=max_critic_replans)
        return
    if stage is LogicalStage.narrate:
        merge_updates(state, await node_add_narration(state))
        return
    if stage is LogicalStage.finalize:
        merge_updates(state, await node_finalize(state))
        return
    raise ValueError(f"Unknown stage: {stage}")
