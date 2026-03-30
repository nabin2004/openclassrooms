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
    import os
    import subprocess
    import tempfile
    from pathlib import Path
    
    # Create outputs directory
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    
    rendered = {}
    
    for spec in state.scene_specs:
        code = state.generated_codes[spec.scene_id]
        
        # Write the Manim code to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Render the scene using Manim
            scene_class = spec.class_name
            output_file = f"outputs/scene_{spec.scene_id}.mp4"
            
            cmd = [
                "manim", 
                temp_file, 
                scene_class,
                "-qm",  # medium quality
                "--output_file", f"scene_{spec.scene_id}"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                # Manim creates files in media/videos/ by default
                # Look for the generated file in common locations
                media_dir = Path("media/videos")
                if media_dir.exists():
                    # Find the video file
                    for file in media_dir.rglob(f"*scene_{spec.scene_id}*.mp4"):
                        file.rename(output_file)
                        break
                    else:
                        # Try alternative naming
                        for file in media_dir.rglob(f"*{scene_class}*.mp4"):
                            file.rename(output_file)
                            break
                
                if Path(output_file).exists():
                    rendered[spec.scene_id] = output_file
                    print(f"✅ Successfully rendered scene {spec.scene_id} to {output_file}")
                else:
                    print(f"⚠️  Manim ran but output file not found at {output_file}")
                    rendered[spec.scene_id] = output_file  # still return the path
            else:
                print(f"❌ Failed to render scene {spec.scene_id}: {result.stderr}")
                rendered[spec.scene_id] = output_file  # fallback path
                
        except Exception as e:
            print(f"❌ Error rendering scene {spec.scene_id}: {e}")
            rendered[spec.scene_id] = f"outputs/scene_{spec.scene_id}.mp4"  # fallback path
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
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
# graph = pipeline.get_graph()

# png_bytes = graph.draw_mermaid_png()

# with open("pipeline_graph.png", "wb") as f:
#     f.write(png_bytes)