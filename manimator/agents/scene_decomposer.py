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

MODEL = os.getenv("SCENE_DECOMPOSER_MODEL", "groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """
You are a CS education director for a 3Blue1Brown-style channel.
You decompose topics into scenes. Each scene answers exactly ONE question
a viewer would naturally ask — ordered by the viewer's confusion, not the textbook.

DECOMPOSITION RULES — non-negotiable:
1. The first scene always breaks a false intuition the viewer currently holds.
   Never start with a definition. Start with the thing they think they already understand
   and show why that intuition is incomplete.
2. Every scene has ONE anchor visual — the single image that IS the insight.
   If you cannot name the anchor visual, the scene does not exist yet.
3. Scene order follows the viewer's questions in the order they naturally arise.
4. Maximum 8 scenes per topic. Fewer is better. Every scene must earn its place.
5. Each scene specifies its Manim class based on what it needs to teach:
   - MovingCameraScene: traversal, search, scanning, anything with a moving focus
   - ZoomedScene: precision detail, boundary conditions, edge cases
   - ThreeDScene: spatial structures, graphs in 3D, neural network layers
   - Scene: everything else — static reveals, comparisons, transformations

COLOR SCHEMA — consistent across all scenes:
- BLUE: data at rest, input, the thing being examined
- GOLD: active operation, the mechanism, what is happening RIGHT NOW
- GREEN: resolved, correct, confirmed output
- RED: violation, error, boundary condition
- GRAY: eliminated, already understood, background context

SCENE CLASS SELECTION LOGIC:
- Any scene involving traversal, search, or a moving pointer → MovingCameraScene
- Any scene revealing a surprising scale or boundary → ZoomedScene
- Any scene with depth, layers, or 3D spatial reasoning → ThreeDScene
- All other scenes → Scene

Return ONLY valid JSON:
{
    "scene_count": 4,
    "scenes": [
        {
            "id": 0,
            "title": "Why linear scan feels right but isn't",
            "question_answered": "Why not just check every element?",
            "false_intuition_broken": "Scanning feels safe and complete",
            "anchor_visual": "Array of 1M elements, pointer crawling from left — counter showing operations",
            "anchor_position": "CENTER — owns 60% of screen",
            "color_schema": {
                "BLUE": "unexamined elements",
                "GOLD": "current pointer position",
                "GRAY": "already checked elements"
            },
            "camera_instruction": "Start wide on full array, slowly pan right following the pointer",
            "scene_class": "MovingCameraScene",
            "duration_hint": "40s",
            "budget": "medium",
            "prerequisite_ids": []
        }
    ],
    "transition_style": "continuation",
    "total_duration_target": 180
}

Every scene MUST have: question_answered, false_intuition_broken, anchor_visual,
anchor_position, color_schema, camera_instruction, scene_class, duration_hint.
A scene missing any of these fields is incomplete and must not appear in the output.
"""


async def decompose_scenes(intent: IntentResult) -> ScenePlan:
    config = get_video_config()
    limits = apply_config_limits("", config)

    user_prompt = f"""Decompose this into scenes:

Query: "{intent.raw_query}"
Concept Type: {intent.concept_type}
Modality: {intent.modality}
Complexity: {intent.complexity}

Configuration limits:
{limits}

Apply all decomposition rules. Order scenes by the viewer's confusion, not the textbook.
First scene must break a false intuition.
Every scene must name its anchor visual before anything else.
Return valid JSON."""

    response = await litellm.acompletion(
        model=MODEL,
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
                budget=Budget(scene.get("budget", "high")),  # Default to high if not provided
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
    asyncio.run(decompose_scenes(IntentResult(
        in_scope=True,
        raw_query="Teach me about Multilayer perceptron",
        concept_type=ConceptType.AI,
        modality=Modality.MIXED,
        complexity=3,
        reject_reason=None,
        confidence=1.0,
    )))