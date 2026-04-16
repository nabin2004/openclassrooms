import asyncio
import os

import logging
from typing import Any

from amoeba.core.agent import Agent
from amoeba.core.memory import StatelessMemoryAdapter
from amoeba.exceptions import AmoebaError, StructuredOutputError
from amoeba.runtime import load_agent_env
from amoeba.utils import safe_parse_json
from pydantic import ValidationError
from manimator.config.video_config import get_video_config, apply_config_limits
from manimator.agents.json_llm import response_format_json_object
from manimator.contracts.intent import ConceptType, IntentResult, Modality
from manimator.contracts.llm_outputs import LLMScenePlanPayload
from manimator.contracts.scene_plan import Budget, SceneClass, SceneEntry, ScenePlan, coerce_transition_style
from manimator.prompts.registry import get_scene_decomposer_prompt

load_agent_env()

MODEL = os.getenv("SCENE_DECOMPOSER_MODEL", "groq/llama-3.1-8b-instant")
log = logging.getLogger(__name__)

_ACTIVE_PROMPT = get_scene_decomposer_prompt()


def _normalize_llm_scene_plan_data(data: Any) -> dict[str, Any]:
    """
    Models sometimes return a JSON array of scenes instead of the full object envelope.
    Wrap that shape into the dict expected by :class:`LLMScenePlanPayload`.
    """
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        scenes: list[dict[str, Any]] = []
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise StructuredOutputError(
                    "Scene plan JSON root was a list but an element was not an object",
                    context={"agent": "scene_decomposer", "index": i, "element_type": type(item).__name__},
                    user_message="The model returned a scene list with invalid entries.",
                )
            scenes.append(item)
        return {
            "scene_count": len(scenes),
            "scenes": scenes,
            "transition_style": "continuation",
            "total_duration_target": None,
        }
    raise StructuredOutputError(
        "Scene plan JSON must be an object or a list of scene objects",
        context={"agent": "scene_decomposer", "parsed_type": type(data).__name__},
        user_message="The model returned JSON that was not an object or scene list.",
    )


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
    llm_kwargs = {"max_tokens": 2048, **response_format_json_object(disable_env_var="SCENE_DECOMPOSER_DISABLE_JSON_MODE")}
    try:
        raw = await agent.think(user_prompt, **llm_kwargs)
        data = safe_parse_json(raw)
        data = _normalize_llm_scene_plan_data(data)
        try:
            payload = LLMScenePlanPayload(**data)
        except ValidationError as e:
            raise StructuredOutputError(
                "Model output failed validation for LLMScenePlanPayload",
                context={"agent": "scene_decomposer", "pydantic_errors": e.errors(), "raw_preview": raw[:2000]},
                user_message="The model returned JSON that did not match the expected scene plan shape.",
            ) from e
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
        transition_style=coerce_transition_style(payload.transition_style),
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