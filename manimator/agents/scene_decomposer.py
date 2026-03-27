import json 
import os
from dotenv import load_dotenv
import litellm 

from manimator.contracts.intent import IntentResult
from manimator.contracts.scene_plan import Budget, SceneClass, SceneEntry, ScenePlan, TransitionStyle
from manim_utils import strip_markdown_code_blocks

load_dotenv()

MODEL = os.getenv("SCENE_DECOMPOSER_MODEL","groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """

"""

async def decompose_scenes(intent: IntentResult) -> ScenePlan:
    response = await litellm.acompletion(
        model = MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":f"XXXXXXXXXX"}
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()
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