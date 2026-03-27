import json
import os
from dotenv import load_dotenv
import litellm

from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.scene_spec import AnimationSpec, MobjectSpec, SceneSpec

load_dotenv()

MODEL = os.getenv("SCENE_PLANNER_MODEL", "groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """
You are a scene planner for Manim.

Return ONLY valid JSON with this structure:

{
  "imports": ["Scene", "Circle"],
  "objects": [
    {"name": "circle", "type": "Circle"}
  ],
  "animations": [
    {"type": "Create", "target": "circle"}
  ]
}

Rules:
- Keep animations within budget
- Use valid Manim primitives
- Keep names consistent between objects and animations
- No explanations, only JSON
"""


def strip_markdown_code_blocks(text: str) -> str:
    text = text.strip()

    if not text.startswith("```"):
        return text

    parts = text.split("```")
    if len(parts) >= 2:
        content = parts[1].strip()
        first_newline = content.find("\n")

        if first_newline != -1:
            maybe_lang = content[:first_newline].strip().lower()
            if maybe_lang in {"json", "python", "js"}:
                content = content[first_newline + 1 :]

        return content.strip()

    return text


async def plan_scene(scene: SceneEntry, feedback: str | None = None) -> SceneSpec:
    user_payload = {
        "scene": scene.model_dump(),
        "feedback": feedback,
    }

    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        temperature=0.2,  # small creativity but not chaos
    )

    raw = response.choices[0].message.content.strip()
    raw = strip_markdown_code_blocks(raw)

    try:
        data = json.loads(raw)
        
        if not data.get("objects") or not data.get("animations"):
            raise ValueError(f"Missing required fields in model output: {data}")

        objects = [
            MobjectSpec(**obj)
            for obj in data.get("objects", [])
        ]

        animations = [
            AnimationSpec(**anim)
            for anim in data.get("animations", [])
        ]

        return SceneSpec(
            scene_id=scene.id,
            class_name=scene.title.replace(" ", ""),
            scene_class=scene.scene_class,
            budget=scene.budget,
            imports=data.get("imports", []),
            objects=objects,
            animations=animations,
        )

    except Exception as e:
        raise ValueError(f"Failed to parse SceneSpec: {e}\nRaw output:\n{raw}")