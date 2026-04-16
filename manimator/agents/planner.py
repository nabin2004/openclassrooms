import asyncio
import os
import re

import logging
from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.exceptions import AmoebaError, JSONParseError, LLMError, StructuredOutputError
from amoeba.runtime import load_agent_env
from manimator.agents.json_llm import response_format_json_object
from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.llm_outputs import LLMPlannerPayload
from manimator.contracts.scene_spec import AnimationSpec, CameraOp, MobjectSpec, SceneSpec
from manimator.prompts.registry import get_scene_planner_prompt

load_agent_env()

MODEL = os.getenv("SCENE_PLANNER_MODEL", "groq/llama-3.1-8b-instant")
log = logging.getLogger(__name__)

_ACTIVE_PROMPT = get_scene_planner_prompt()

async def _plan_scene_think_parse_with_retries(
    *,
    agent: Agent,
    user_prompt: str,
    scene_id: int,
) -> LLMPlannerPayload:
    """
    Retry transient JSON / schema / empty failures (``SCENE_PLANNER_TRANSIENT_RETRIES``,
    default 1 → up to 2 attempts per scene).
    """
    retries = max(0, int(os.getenv("SCENE_PLANNER_TRANSIENT_RETRIES", "1")))
    extra = response_format_json_object(disable_env_var="SCENE_PLANNER_DISABLE_JSON_MODE")
    last: BaseException | None = None
    for attempt in range(retries + 1):
        agent.reset_history()
        try:
            return await agent.think_and_parse(
                user_prompt,
                schema=LLMPlannerPayload,
                max_tokens=2048,
                **extra,
            )
        except (LLMError, JSONParseError, StructuredOutputError) as e:
            last = e
            if attempt >= retries:
                raise
            delay = min(5.0, 0.4 * (2**attempt))
            log.warning(
                "scene_planner.transient_retry scene_id=%s attempt=%s/%s delay_s=%.2f err=%s",
                scene_id,
                attempt + 1,
                retries + 1,
                delay,
                e,
            )
            await asyncio.sleep(delay)
    assert last is not None
    raise last


FEEDBACK_ADDENDUM = """

CRITIC FEEDBACK — treat as absolute constraints, not suggestions:
Every feedback point must change at least one object or animation.
- If feedback says "pointer teleports": add animate.move_to() to every Arrow animation.
- If feedback says "no visual hierarchy": promote one element to hero at CENTER, demote all others to GRAY.
- If feedback says "too many elements": remove everything without a composition_role of hero.
- If feedback says "no Wait() pauses": add Wait(0.8) after every Beat 3 animation.
"""


async def plan_scene(scene: SceneEntry, feedback: str | None = None) -> SceneSpec:
    system = _ACTIVE_PROMPT.system
    if feedback:
        system += FEEDBACK_ADDENDUM

    user_prompt = f"""Create a Manim scene plan for:

Title: {scene.title}
Scene Class: {scene.scene_class.value}
Budget: {scene.budget.value}
Feedback: {feedback or "None"}

Apply all composition laws, timing laws, and the 3-beat rhythm.
Every animation must have a beat and a purpose.
Every object must have a composition_role and a position.
Return voiceover_script for TTS."""

    agent = Agent(
        name="scene_planner",
        role=system,
        model_env_key="SCENE_PLANNER_MODEL",
        default_model=MODEL,
        temperature=0.3,
        memory=StatelessMemoryAdapter(),
    )
    try:
        payload = await _plan_scene_think_parse_with_retries(
            agent=agent,
            user_prompt=user_prompt,
            scene_id=scene.id,
        )
    except AmoebaError as e:
        log.error("Planner failed: %s", e.format_detail())
        raise

    objects = [MobjectSpec(name=o.name, type=o.type, init_params=o.init_params) for o in payload.objects]
    animations = [
        AnimationSpec(
            type=a.type,
            target=a.target,
            run_time=a.run_time or 1.0,
            params=a.params,
        )
        for a in payload.animations
    ]
    camera_ops = [
        CameraOp(type=op.type, phi=op.phi, theta=op.theta, zoom=op.zoom)
        for op in payload.camera_ops
    ]

    raw_title = scene.title
    class_name = re.sub(r"[^a-zA-Z0-9]", "", raw_title)
    if class_name:
        class_name = class_name[0].upper() + class_name[1:]
    else:
        class_name = "SceneAuto"

    voiceover_script = payload.voiceover_script
    if voiceover_script is not None and not isinstance(voiceover_script, str):
        voiceover_script = str(voiceover_script)

    return SceneSpec(
        scene_id=scene.id,
        class_name=class_name,
        scene_class=scene.scene_class,
        budget=scene.budget,
        imports=payload.imports or [],
        objects=objects,
        animations=animations,
        camera_ops=camera_ops,
        voiceover_script=voiceover_script,
    )
    
if __name__ == "__main__":
    import asyncio
    import json

    test_scene = SceneEntry(
        id=0,
        title="What is a Circle?",
        scene_class="concept_introduction",
        budget="low",
        prerequisite_ids=[],
    )
    spec = asyncio.run(plan_scene(test_scene))
    print(json.dumps(spec.dict(), indent=2))
