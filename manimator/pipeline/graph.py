import asyncio

from langgraph.graph import StateGraph, END
from manimator.pipeline.state import PipelineState
from manimator.logging import get_logger, log_exception
from manimator.paths import get_run_paths
from amoeba.observability import get_logger as get_amoeba_logger
from amoeba.observability import log_structured
from manimator.ir import write_ir_bundle
from manimator.agents.intent_classifier import classify_intent
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.codegen import generate_code
from manimator.agents.validator import validate_code
from manimator.agents.repair import repair_code
from manimator.agents.critic import critique_render
from manimator.contracts.validation import MAX_RETRIES
from manimator.contracts.critic import MAX_REPLANS
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

async def node_generate_code(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="codegen")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="codegen")
    codes = {}
    code_paths: dict[int, str] = {}
    for spec in state.scene_specs:
        scene_log = get_logger(__name__, run_id=state.run_id, node="codegen", scene_id=spec.scene_id)
        code = await generate_code(spec)
        codes[spec.scene_id] = code
        out_py = paths.code_dir / f"scene_{spec.scene_id}.py"
        out_py.write_text(code or "", encoding="utf-8")
        code_paths[spec.scene_id] = str(out_py.resolve())
        scene_log.info("Generated code (%s chars).", len(code or ""))
    log.info("Wrote scene code to %s", str(paths.code_dir))
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="codegen", scenes=len(code_paths))
    write_ir_bundle(
        ir_dir=paths.ir_dir,
        run_id=run_id,
        raw_query=state.raw_query,
        intent=state.intent,
        scene_plan=state.scene_plan,
        scene_specs=state.scene_specs,
        generated_codes=codes,
        code_paths=code_paths,
    )
    return {"generated_codes": codes, "code_paths": code_paths, "run_dir": str(paths.run_dir)}


async def node_validate(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="validate")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="validate")
    results = {}
    failed = []
    for spec in state.scene_specs:
        code = state.generated_codes[spec.scene_id]
        retry_count = state.retry_counts.get(spec.scene_id, 0)
        scene_log = get_logger(__name__, run_id=state.run_id, node="validate", scene_id=spec.scene_id)
        result = await validate_code(code, spec, retry_count=retry_count)
        results[spec.scene_id] = result
        if not result.passed:
            failed.append(spec.scene_id)
            scene_log.warning(
                "Validation failed (type=%s line=%s): %s",
                getattr(result.error_type, "value", None),
                result.error_line,
                result.error_message,
            )
        else:
            scene_log.info("Validation passed.")
    log.info("Validation complete. failed_scene_ids=%s", failed)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="validate", failed_scene_ids=failed)
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

async def node_repair(state: PipelineState) -> dict:
    log = get_logger(__name__, run_id=state.run_id, node="repair")
    run_id = state.run_id or "unknown"
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="repair", failed_scene_ids=state.failed_scene_ids)
    new_codes = dict(state.generated_codes)
    new_retries = dict(state.retry_counts)
    for scene_id in state.failed_scene_ids:
        validation = state.validation_results[scene_id]
        scene_log = get_logger(__name__, run_id=state.run_id, node="repair", scene_id=scene_id)
        repaired = await repair_code(validation)
        new_codes[scene_id] = repaired
        new_retries[scene_id] = new_retries.get(scene_id, 0) + 1
        scene_log.info("Repaired code (%s chars). retry_count=%s", len(repaired or ""), new_retries[scene_id])
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="repair", repaired_scenes=list(state.failed_scene_ids))
    return {"generated_codes": new_codes, "retry_counts": new_retries}


async def node_render(state: PipelineState) -> dict:
    import os
    from pathlib import Path

    from amoeba.subprocess import run_subprocess

    log = get_logger(__name__, run_id=state.run_id, node="render")
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)
    log_structured(get_amoeba_logger(), 20, "pipeline.node.start", run_id=run_id, node="render")
    
    rendered = {}
    
    for spec in state.scene_specs:
        scene_log = get_logger(__name__, run_id=state.run_id, node="render", scene_id=spec.scene_id)
        code_path = state.code_paths.get(spec.scene_id) or str((paths.code_dir / f"scene_{spec.scene_id}.py").resolve())
        if not Path(code_path).exists():
            Path(code_path).write_text(state.generated_codes.get(spec.scene_id, ""), encoding="utf-8")
        
        try:
            # Render the scene using Manim
            scene_class = spec.class_name
            output_file = paths.renders_dir / f"scene_{spec.scene_id}.mp4"
            
            cmd = [
                "manim", 
                code_path,
                scene_class,
                "-qm",  # medium quality
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
                    rendered[spec.scene_id] = str(output_file.resolve())
                    scene_log.info("Rendered to %s", str(output_file))
                else:
                    scene_log.warning("Manim succeeded but output not found at %s", str(output_file))
                    rendered[spec.scene_id] = str(output_file.resolve())  # still return the path
            else:
                scene_log.error("Manim failed (exit=%s). stderr=%s", result.returncode, (result.stderr or "").strip())
                rendered[spec.scene_id] = str(output_file.resolve())  # fallback path
                
        except Exception as e:
            log_exception(scene_log, "Exception while rendering scene.", exc=e)
            rendered[spec.scene_id] = str((paths.renders_dir / f"scene_{spec.scene_id}.mp4").resolve())  # fallback path
    
    log.info("Render step complete. rendered_scenes=%s", sorted(rendered.keys()))
    log_structured(get_amoeba_logger(), 20, "pipeline.node.completed", run_id=run_id, node="render", rendered_scenes=sorted(rendered.keys()))
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
    from pathlib import Path

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


def edge_after_validate(state: PipelineState) -> str:
    if not state.failed_scene_ids:
        return "render"
    # Check if any failed scene has hit the retry cap
    for scene_id in state.failed_scene_ids:
        retry = state.retry_counts.get(scene_id, 0)
        if retry >= MAX_RETRIES:
            # Exceeded retry budget: skip repair, proceed with broken scene
            return "render"
    return "repair"


def edge_after_critique(state: PipelineState) -> str:
    if state.critic_result.replan_required and state.replan_count < MAX_REPLANS:
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
    graph.add_node("codegen", node_generate_code)
    graph.add_node("validate", node_validate)
    graph.add_node("repair", node_repair)
    graph.add_node("render", node_render)
    graph.add_node("critique", node_critique)
    graph.add_node("narrate", node_add_narration)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("classify")

    graph.add_conditional_edges("classify", edge_after_intent, {
        "decompose": "decompose",
        "end": END,
    })
    graph.add_edge("decompose", "plan")
    graph.add_edge("plan", "codegen")
    graph.add_edge("codegen", "validate")
    graph.add_conditional_edges("validate", edge_after_validate, {
        "render": "render",
        "repair": "repair",
    })
    graph.add_edge("repair", "validate")
    graph.add_edge("render", "critique")
    graph.add_conditional_edges("critique", edge_after_critique, {
        "narrate": "narrate",
        "replan": "plan",
    })
    graph.add_edge("narrate", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


pipeline = build_pipeline()
# graph = pipeline.get_graph()

# png_bytes = graph.draw_mermaid_png()

# with open("pipeline_graph.png", "wb") as f:
#     f.write(png_bytes)