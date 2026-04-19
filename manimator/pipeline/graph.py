import asyncio

from langgraph.graph import StateGraph, END
from manimator.pipeline.state import PipelineState
from manimator.logging import get_logger
from manimator.paths import get_run_paths
from amoeba.observability import get_logger as get_amoeba_logger
from amoeba.observability import log_structured
from manimator.ir import write_ir_bundle
from manimator.agents.intent_classifier import classify_intent
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.scene_subagent import node_codegen_render, node_render
from manimator.agents.critic import critique_render
from manimator.contracts.critic import MAX_REPLANS as CRITIC_MAX_REPLANS
from manimator.audio.narration import build_narrated_scene_paths
from manimator.audio.voiceover import voiceover_text_for_scene
from manimator.video.delivery import build_delivery_package

##################################################
#                NODES
#################################################


async def node_classify_intent(state: PipelineState) -> dict:
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log = get_logger(__name__, run_id=state.run_id, node="classify")
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="classify")
    intent = await classify_intent(state.raw_query)
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=intent,
    )
    if not intent.in_scope:
        log.info("Intent rejected: %s", intent.reject_reason)
        log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="classify", ok=False)
        return {"intent": intent, "error": intent.reject_reason, "run_dir": str(paths.run_dir)}
    log.info("Intent accepted.")
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="classify", ok=True)
    return {"intent": intent, "run_dir": str(paths.run_dir)}


async def node_decompose_scenes(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="decompose")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="decompose")
    plan = await decompose_scenes(state.intent)
    log.info("Decomposed into %s scenes.", getattr(plan, "scene_count", "?"))
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="decompose", scene_count=getattr(plan, "scene_count", None))
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=plan,
    )
    return {"scene_plan": plan}


async def node_bump_replan(state: PipelineState) -> dict:
    """Increment replan counter when critique sends us back to planning."""
    return {"replan_count": state.replan_count + 1}


async def node_plan_scenes(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="plan")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="plan")
    specs = []
    for scene in state.scene_plan.scenes:
        # Pass critic feedback if this is a re-plan
        feedback = None
        if state.critic_result and scene.id in state.failed_scene_ids:
            idx = state.failed_scene_ids.index(scene.id)
            if idx < len(state.critic_result.critic_feedback):
                feedback = state.critic_result.critic_feedback[idx]
        scene_log = get_logger(__name__, run_id=state.run_id, node="plan", scene_id=scene.id)
        spec = await plan_scene(scene, feedback=feedback)
        scene_log.info("Planned scene %s (%s).", scene.id, spec.class_name)
        specs.append(spec)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="plan", scene_specs=len(specs))
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=state.scene_plan,
        scene_specs=specs,
    )
    return {"scene_specs": specs}


async def node_critique(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="critique")
    run_id = state.run_id or "unknown"
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="critique")
    scene_ids = list(state.rendered_paths.keys())
    keyframes = list(state.rendered_paths.values())
    result = await critique_render(
        scene_ids=scene_ids,
        keyframe_paths=keyframes,
        replan_count=state.replan_count,
    )
    log.info(
        "Critique complete. combined=%s replan_required=%s failed_scene_ids=%s",
        result.combined_score,
        result.replan_required,
        result.failed_scene_ids,
    )
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="critique", combined_score=result.combined_score, replan_required=result.replan_required)
    paths = get_run_paths(run_id)
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
        rendered_paths=state.rendered_paths,
        critic_result=result,
    )
    return {
        "critic_result": result,
        "failed_scene_ids": result.failed_scene_ids,
    }


async def node_finalize(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="finalize")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="finalize")

    scene_lookup = {}
    if state.scene_plan:
        scene_lookup = {scene.id: scene for scene in state.scene_plan.scenes}

    scene_transcripts = {}
    transcript_blocks = []

    for spec in sorted(state.scene_specs, key=lambda s: s.scene_id):
        scene = scene_lookup.get(spec.scene_id)
        scene_title = scene.title if scene else spec.class_name

        transcript = voiceover_text_for_scene(spec, scene)

        scene_transcripts[spec.scene_id] = transcript
        transcript_blocks.append(f"[Scene {spec.scene_id}: {scene_title}]\n{transcript}")

    full_transcript = "\n\n".join(transcript_blocks)

    pkg = await asyncio.to_thread(
        build_delivery_package,
        state.scene_specs,
        dict(state.narrated_paths),
        dict(state.rendered_paths),
        full_transcript,
        paths.run_dir,
    )

    log.info("Delivery package built. delivery_dir=%s output_video_path=%s", pkg["delivery_dir"], pkg["output_video_path"])
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="finalize", delivery_dir=pkg["delivery_dir"], output_video_path=pkg["output_video_path"])
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
        rendered_paths=state.rendered_paths,
        narrated_paths=state.narrated_paths,
        critic_result=state.critic_result,
        scene_transcripts=scene_transcripts,
        full_transcript=full_transcript,
    )
    return {
        "output_video_path": pkg["output_video_path"],
        "delivery_dir": pkg["delivery_dir"],
        "scene_transcripts": scene_transcripts,
        "full_transcript": full_transcript,
        "transcript_path": pkg["transcript_path"],
        "narrated_paths": dict(state.narrated_paths),
        "run_dir": str(paths.run_dir),
    }


##################################################
#                CONDITIONAL EDGES
#################################################


def edge_after_intent(state: PipelineState) -> str:
    if state.error:
        return "end"
    return "decompose"


def edge_after_critique(state: PipelineState) -> str:
    if state.critic_result and state.critic_result.replan_required and state.replan_count < CRITIC_MAX_REPLANS:
        return "replan"
    return "narrate"


async def node_add_narration(state: PipelineState) -> dict:
    """Synthesize KittenTTS from scene voiceovers and mux with rendered MP4s."""
    narrated = await asyncio.to_thread(build_narrated_scene_paths, state)
    return {"narrated_paths": narrated}


##################################################
#                Build Graph
#################################################


def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("classify", node_classify_intent)
    graph.add_node("decompose", node_decompose_scenes)
    graph.add_node("plan", node_plan_scenes)
    graph.add_node("bump_replan", node_bump_replan)
    graph.add_node("codegen_render", node_codegen_render)
    graph.add_node("critique", node_critique)
    graph.add_node("narrate", node_add_narration)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("classify")

    graph.add_conditional_edges("classify", edge_after_intent, {
        "decompose": "decompose",
        "end": END,
    })
    graph.add_edge("decompose", "plan")
    graph.add_edge("plan", "codegen_render")
    graph.add_edge("codegen_render", "critique")
    graph.add_conditional_edges("critique", edge_after_critique, {
        "narrate": "narrate",
        "replan": "bump_replan",
    })
    graph.add_edge("bump_replan", "plan")
    graph.add_edge("narrate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


pipeline = build_pipeline()
