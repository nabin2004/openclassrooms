from langgraph.graph import StateGraph, END
from manimator.pipeline.state import PipelineState
from manimator.agents.intent_classifier import classify_intent
from manimator.agents.scene_decomposer import decompose_scenes
from manimator.agents.planner import plan_scene
from manimator.agents.codegen import generate_code
from manimator.agents.validator import validate_code
from manimator.agents.repair import repair_code
from manimator.agents.critic import critique_render
from manimator.contracts.validation import MAX_RETRIES
from manimator.contracts.critic import MAX_REPLANS

##################################################
#                NODES 
#################################################

async def node_classify_intent(state: PipelineState) -> dict:
    intent = await classify_intent(state.raw_query)
    if not intent.in_scope:
        return {"intent": intent, "error": intent.reject_reason}
    return {"intent": intent}


async def node_decompose_scenes(state: PipelineState) -> dict:
    plan = await decompose_scenes(state.intent)
    return {"scene_plan": plan}


async def node_plan_scenes(state: PipelineState) -> dict:
    specs = []
    for scene in state.scene_plan.scenes:
        # Pass critic feedback if this is a re-plan
        feedback = None
        if state.critic_result and scene.id in state.failed_scene_ids:
            idx = state.failed_scene_ids.index(scene.id)
            if idx < len(state.critic_result.critic_feedback):
                feedback = state.critic_result.critic_feedback[idx]
        spec = await plan_scene(scene, feedback=feedback)
        specs.append(spec)
    return {"scene_specs": specs}

async def node_generate_code(state: PipelineState) -> dict:
    codes = {}
    for spec in state.scene_specs:
        code = await generate_code(spec)
        codes[spec.scene_id] = code
    return {"generated_codes": codes}


async def node_validate(state: PipelineState) -> dict:
    results = {}
    failed = []
    for spec in state.scene_specs:
        code = state.generated_codes[spec.scene_id]
        retry_count = state.retry_counts.get(spec.scene_id, 0)
        result = await validate_code(code, spec, retry_count=retry_count)
        results[spec.scene_id] = result
        if not result.passed:
            failed.append(spec.scene_id)
    return {"validation_results": results, "failed_scene_ids": failed}

async def node_repair(state: PipelineState) -> dict:
    new_codes = dict(state.generated_codes)
    new_retries = dict(state.retry_counts)
    for scene_id in state.failed_scene_ids:
        validation = state.validation_results[scene_id]
        repaired = await repair_code(validation)
        new_codes[scene_id] = repaired
        new_retries[scene_id] = new_retries.get(scene_id, 0) + 1
    return {"generated_codes": new_codes, "retry_counts": new_retries}


async def node_render(state: PipelineState) -> dict:
    # STUB — real Manim render goes here in Phase 1
    rendered = {}
    for spec in state.scene_specs:
        rendered[spec.scene_id] = f"outputs/scene_{spec.scene_id}.mp4"
    return {"rendered_paths": rendered}

async def node_critique(state: PipelineState) -> dict:
    scene_ids = list(state.rendered_paths.keys())
    keyframes = list(state.rendered_paths.values())
    result = await critique_render(
        scene_ids=scene_ids,
        keyframe_paths=keyframes,
        replan_count=state.replan_count,
    )
    return {
        "critic_result": result,
        "failed_scene_ids": result.failed_scene_ids,
    }


async def node_finalize(state: PipelineState) -> dict:
    # STUB: real video concatenation goes here
    return {"output_video_path": "outputs/final.mp4"}

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
    if not state.critic_result.replan_required:
        return "finalize"
    if state.replan_count >= MAX_REPLANS:
        return "finalize"
    return "replan"

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
        "finalize": "finalize",
        "replan": "plan",
    })
    graph.add_edge("finalize", END)

    return graph.compile()


pipeline = build_pipeline()