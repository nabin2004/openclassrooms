import asyncio
import os

import logging
from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.exceptions import AmoebaError
from amoeba.runtime import load_agent_env
from manimator.config.video_config import get_video_config, apply_config_limits
from manimator.contracts.intent import ConceptType, IntentResult, Modality
from manimator.contracts.llm_outputs import LLMScenePlanPayload
from manimator.contracts.scene_plan import Budget, SceneEntry, ScenePlan, TransitionStyle, SceneClass
from manimator.prompts.registry import get_scene_decomposer_prompt

load_agent_env()

MODEL = os.getenv("SCENE_DECOMPOSER_MODEL", "groq/llama-3.1-8b-instant")
log = logging.getLogger(__name__)

_ACTIVE_PROMPT = get_scene_decomposer_prompt()


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

    agent = Agent(
        name="scene_decomposer",
        role=_ACTIVE_PROMPT.system,
        model_env_key="SCENE_DECOMPOSER_MODEL",
        default_model=MODEL,
        temperature=0.3,
        memory=StatelessMemoryAdapter(),
    )
    agent.reset_history()
    try:
        payload = await agent.think_and_parse(
            user_prompt,
            schema=LLMScenePlanPayload,
            max_tokens=2048,
        )
    except AmoebaError as e:
        log.error("Scene decomposer failed: %s", e.format_detail())
        raise

    scenes = [
        SceneEntry(
            id=s.id,
            title=s.title,
            scene_class=SceneClass(s.scene_class),
            budget=Budget((s.budget or "high")),
            prerequisite_ids=list(s.prerequisite_ids or []),
        )
        for s in payload.scenes
    ]

    return ScenePlan(
        scene_count=payload.scene_count,
        scenes=scenes,
        transition_style=TransitionStyle(payload.transition_style),
        total_duration_target=payload.total_duration_target,
    )


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