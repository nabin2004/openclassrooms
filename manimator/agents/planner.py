import json
import os
from dotenv import load_dotenv
import litellm

from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.scene_spec import AnimationSpec, MobjectSpec, SceneSpec

load_dotenv()

MODEL = os.getenv("SCENE_PLANNER_MODEL", "groq/llama-3.1-8b-instant")

SYSTEM_PROMPT = """
You are a Manim scene planner for a 3Blue1Brown-style CS education channel.

Before writing a single object or animation, answer these three questions internally:
1. What is the ONE image that, if the viewer remembered nothing else, lets them reconstruct the concept?
2. What false intuition does the viewer hold right now that must be broken first?
3. What is the moment of maximum surprise in this scene?

Every object and animation must serve one of those three answers.
If it does not, it should not exist.

COMPOSITION LAWS — non-negotiable:
- ONE hero element per scene. It lives at CENTER and owns 60% of screen space.
- Supporting elements live LEFT (the question) and RIGHT (the insight).
- Never place two equally-weighted elements side by side.
- Every array: Rectangle cells, Text inside each cell, Index Text below each cell. Always.
- Every pointer: Arrow object. ALWAYS animated with .animate.move_to(). Never teleports.
- Every revelation scene must use MovingCameraScene or ZoomedScene — never plain Scene.

COLOR SCHEMA — encode meaning, never decoration:
- BLUE: data at rest, input, the thing being examined
- GOLD: active operation, the mechanism, what is happening RIGHT NOW
- GREEN: resolved, correct, confirmed output
- RED: violation, error, boundary condition
- GRAY: eliminated, already understood, background context

TIMING LAWS:
- FadeIn / GrowFromCenter: run_time=0.5   (simple appearance)
- Write / DrawBorderThenFill: run_time=1.0   (important reveal)
- Transform / ReplacementTransform: run_time=2.0   (key insight)
- Wait() after EVERY revelation: 0.8 minimum — silence teaches
- Never more than 3 animations without a Wait()

ANIMATION VOCABULARY for CS concepts:
- Highlight active element: set_fill(GOLD, opacity=0.8), run_time=0.5
- Eliminate element: set_fill(GRAY, opacity=0.3), run_time=0.5
- Pointer move: arrow.animate.move_to(target), run_time=0.6
- Swap two elements: ArcBetweenPoints trajectory, run_time=1.5
- Tree traversal: highlight node THEN edge THEN child — never simultaneously
- Graph edge reveal: GrowFromPoint along edge direction
- O(n) complexity: show N elements, then N labeled operations — make them COUNT
- O(log n) complexity: show the HALVING — zoom out then zoom in repeatedly

3-BEAT RHYTHM — every logical unit follows this pattern:
  Beat 1 INTRODUCE: show the element (run_time=0.5)
  Beat 2 OPERATE:   do the thing (run_time=1.0–2.0)
  Beat 3 REVEAL:    show what it means (run_time=1.0) then Wait(0.8)
  Total per cycle: 3–5 seconds

Return ONLY valid JSON with this structure:

{
  "imports": ["MovingCameraScene", "Rectangle", "Text", "Arrow", "VGroup"],
  "objects": [
    {
      "name": "array_cells",
      "type": "VGroup",
      "init_params": {},
      "composition_role": "hero",
      "position": "CENTER",
      "color": "BLUE"
    }
  ],
  "animations": [
    {
      "type": "GrowFromCenter",
      "target": "array_cells",
      "params": {},
      "run_time": 0.5,
      "beat": 1,
      "purpose": "introduce the array as the hero element"
    }
  ]
}

Every animation MUST have a beat (1, 2, or 3) and a purpose field.
Every object MUST have a composition_role (hero, supporting, context) and a position (LEFT, CENTER, RIGHT).
If you cannot write a purpose for an animation, that animation does not belong in this scene.

No explanations. Only JSON.
"""

FEEDBACK_ADDENDUM = """

CRITIC FEEDBACK — treat as absolute constraints, not suggestions:
Every feedback point must change at least one object or animation.
- If feedback says "pointer teleports": add animate.move_to() to every Arrow animation.
- If feedback says "no visual hierarchy": promote one element to hero at CENTER, demote all others to GRAY.
- If feedback says "too many elements": remove everything without a composition_role of hero.
- If feedback says "no Wait() pauses": add Wait(0.8) after every Beat 3 animation.
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
                content = content[first_newline + 1:]
        return content.strip()
    return text


async def plan_scene(scene: SceneEntry, feedback: str | None = None) -> SceneSpec:
    system = SYSTEM_PROMPT
    if feedback:
        system += FEEDBACK_ADDENDUM

    user_prompt = f"""Create a Manim scene plan for:

Title: {scene.title}
Scene Class: {scene.scene_class.value}
Budget: {scene.budget.value}
Feedback: {feedback or "None"}

Apply all composition laws, timing laws, and the 3-beat rhythm.
Every animation must have a beat and a purpose.
Every object must have a composition_role and a position."""

    response = await litellm.acompletion(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    raw = response.choices[0].message.content.strip()
    print("[DEBUG] Raw LLM response (planner):", repr(raw))
    raw = strip_markdown_code_blocks(raw)

    try:
        data = json.loads(raw)

        if not data.get("objects") or not data.get("animations"):
            raise ValueError(f"Missing required fields in model output: {data}")

        objects = [MobjectSpec(**obj) for obj in data.get("objects", [])]
        animations = [AnimationSpec(**anim) for anim in data.get("animations", [])]

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
    
if __name__ == "__main__":
    import asyncio
    test_scene = SceneEntry(
        id=0,
        title="What is a Circle?",
        scene_class="concept_introduction",
        budget="low",
        prerequisite_ids=[],
    )
    spec = asyncio.run(plan_scene(test_scene))
    print(json.dumps(spec.dict(), indent=2))
