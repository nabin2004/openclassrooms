import os
import json
import asyncio
from dotenv import load_dotenv
from litellm import acompletion
import litellm

from manimator.contracts.intent import IntentResult
from manimator.contracts.scene_plan import Budget, SceneEntry, ScenePlan, TransitionStyle, SceneClass
from manimator.manim_utils import strip_markdown_code_blocks
from manimator.config.video_config import get_video_config, apply_config_limits
from manimator.contracts.intent import ConceptType, IntentResult, Modality

load_dotenv()

MODEL = os.getenv("SCENE_DECOMPOSER_MODEL","groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are a scene decomposition expert for an AI math animation system.
Given a user's intent and query, break it down into a logical sequence of scenes for animation.

You must respond with a JSON object containing:
{
    "scene_count": integer (no limit),
    "scenes": [
        {
            "id": integer (starting from 0),
            "title": string (no character limit),
            "scene_class": "Scene" | "ThreeDScene" | "MovingCameraScene" | "ZoomedScene",
            "budget": "low" | "medium" | "high",
            "prerequisite_ids": array of integers (scenes that must come before this one)
        }
    ],
    "transition_style": "cut" | "fade" | "continuation" | "wipe",
    "total_duration_target": integer (no limit - seconds)
}

Scene classes:
- "Scene": Basic 2D animations (including graphs with Axes)
- "ThreeDScene": 3D animations and camera movement
- "MovingCameraScene": Complex camera movements
- "ZoomedScene": Zoomed-in detailed views

Budget levels:
- "low": basic animations (no strict limit)
- "medium": moderate animations (no strict limit)  
- "high": complex animations (no strict limit)

Scene titles: No character limit - be descriptive and clear
Scene count: No limit - create as many scenes as needed
Duration: No limit - set total_duration_target as needed

Keep scenes focused and logical. Each scene should build upon previous ones."""

async def decompose_scenes(intent: IntentResult) -> ScenePlan:
    config = get_video_config()
    
    # Build dynamic prompt based on configuration
    limits = apply_config_limits("", config)
    
    user_prompt = f"""Decompose this animation request into scenes:
    
Query: "{intent.raw_query}"
Concept Type: {intent.concept_type}
Modality: {intent.modality}
Complexity: {intent.complexity}

Configuration limits:
{limits}

Return a valid JSON scene plan."""
    
    response = await litellm.acompletion(
        model = MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()
    print("[DEBUG] Raw LLM response (scene_decomposer):", repr(raw))
    raw = strip_markdown_code_blocks(raw)
    data = json.loads(raw)
    
    try:
        scenes_data = data["scenes"]

        scenes = [
            SceneEntry(
                id=scene["id"],
                title=scene["title"],
                scene_class=SceneClass(scene["scene_class"]),
                budget=Budget(scene["budget"]),
                prerequisite_ids=scene.get("prerequisite_ids", []),
            )
            for scene in scenes_data
        ]

        scene_plan = ScenePlan(
            scene_count=data["scene_count"],
            scenes=scenes,
            transition_style=TransitionStyle(data["transition_style"]),
            total_duration_target=data.get("total_duration_target"),
        )
        return scene_plan

    except Exception as e:
        raise ValueError(f"Failed to parse ScenePlan: {e}\nRaw output:\n{raw}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(decompose_scenes(IntentResult(
        in_scope=True,
        raw_query="Teach me about Multilayer perceptron",
        concept_type=ConceptType.AI,
        modality=Modality.MIXED,
        complexity=3,
        reject_reason=None,
        confidence=1.0,
    )))
