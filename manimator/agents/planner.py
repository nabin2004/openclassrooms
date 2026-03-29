import json
import os
from dotenv import load_dotenv
import litellm

from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.scene_spec import AnimationSpec, MobjectSpec, SceneSpec

load_dotenv()

MODEL = os.getenv("SCENE_PLANNER_MODEL", "groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """
You are a scene planner for Manim animations.

Given a scene request, create a detailed plan with objects and animations.

Return ONLY valid JSON with this structure:

{
  "imports": ["Scene", "Circle", "Dot", "Line", "Axes", "Text"],
  "objects": [
    {"name": "axes", "type": "Axes", "init_params": {"x_range": [-5, 5], "y_range": [-5, 5]}},
    {"name": "circle", "type": "Circle", "init_params": {"radius": 1, "color": "BLUE"}},
    {"name": "title_text", "type": "Text", "init_params": {"text": "My Title", "font_size": 36}}
  ],
  "animations": [
    {"type": "Create", "target": "axes", "params": {}, "run_time": 1},
    {"type": "Create", "target": "circle", "params": {}, "run_time": 1},
    {"type": "Write", "target": "title_text", "params": {}, "run_time": 1}
  ]
}

Rules:
- Create as many objects and animations as needed for the scene
- Use valid Manim primitives (Circle, Square, Line, Dot, Text, Axes, etc.)
- No budget limitations - create comprehensive animations
- Use consistent object names between objects and animations
- For graph scenes, include Axes objects
- For mathematical concepts, include relevant geometric objects
- For text, create Text objects first, then animate them with Write or Create
- No explanations, only JSON
- init_params and params should be valid Python dictionaries
- Text objects use "text" parameter in init_params, not in the object name
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
    user_prompt = f"""Create a comprehensive Manim scene plan for:
    
Title: {scene.title}
Scene Class: {scene.scene_class.value}
Budget: {scene.budget.value} (no animation limits)
Feedback: {feedback or "None"}

Create as many objects and animations as needed to fully explain this concept.
Focus on comprehensive coverage of the topic."""
    
    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # Allow more creativity for comprehensive scenes
    )
    raw = response.choices[0].message.content.strip()
    print("[DEBUG] Raw LLM response (planner):", repr(raw))
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

        # Sanitize class_name: remove non-alphanumeric, capitalize first letter
        import re
        raw_title = scene.title
        class_name = re.sub(r'[^a-zA-Z0-9]', '', raw_title)
        if class_name:
            class_name = class_name[0].upper() + class_name[1:]
        else:
            class_name = "SceneAuto"
        return SceneSpec(
            scene_id=scene.id,
            class_name=class_name,
            scene_class=scene.scene_class,
            budget=scene.budget,
            imports=data.get("imports", []),
            objects=objects,
            animations=animations,
        )

    except Exception as e:
        raise ValueError(f"Failed to parse SceneSpec: {e}\nRaw output:\n{raw}")