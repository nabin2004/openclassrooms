"""Central registry for versioned prompts (select via env or explicit version)."""

from __future__ import annotations

import os

from amoeba.exceptions import ConfigurationError

from manimator.prompts.intent_classifier import v1 as intent_v1
from manimator.prompts.intent_classifier import v2 as intent_v2
from manimator.prompts.scene_decomposer import v1 as decompose_v1
from manimator.prompts.scene_planner import v1 as planner_v1
from manimator.prompts.code_repair import v1 as repair_v1
from manimator.prompts.types import Prompt

INTENT_PROMPTS: dict[str, Prompt] = {
    intent_v1.INTENT.version: intent_v1.INTENT,
    intent_v2.INTENT.version: intent_v2.INTENT,
}

SCENE_DECOMPOSER_PROMPTS: dict[str, Prompt] = {
    decompose_v1.SCENE_DECOMPOSER.version: decompose_v1.SCENE_DECOMPOSER,
}

SCENE_PLANNER_PROMPTS: dict[str, Prompt] = {
    planner_v1.SCENE_PLANNER.version: planner_v1.SCENE_PLANNER,
}

CODE_REPAIR_PROMPTS: dict[str, Prompt] = {
    repair_v1.CODE_REPAIR.version: repair_v1.CODE_REPAIR,
}


def get_intent_prompt(version: str | None = None) -> Prompt:
    """
    Resolve the intent classifier prompt.

    Uses ``INTENT_CLASSIFIER_PROMPT_VERSION`` (default ``v1``) when ``version`` is omitted.
    """
    key = (version or os.getenv("INTENT_CLASSIFIER_PROMPT_VERSION", "v1")).strip()
    try:
        return INTENT_PROMPTS[key]
    except KeyError as e:
        raise ConfigurationError(
            f"Unknown intent prompt version {key!r}",
            context={
                "available_versions": sorted(INTENT_PROMPTS),
                "env": "INTENT_CLASSIFIER_PROMPT_VERSION",
            },
        ) from e


def get_scene_decomposer_prompt(version: str | None = None) -> Prompt:
    key = (version or os.getenv("SCENE_DECOMPOSER_PROMPT_VERSION", "v1")).strip()
    try:
        return SCENE_DECOMPOSER_PROMPTS[key]
    except KeyError as e:
        raise ConfigurationError(
            f"Unknown scene decomposer prompt version {key!r}",
            context={
                "available_versions": sorted(SCENE_DECOMPOSER_PROMPTS),
                "env": "SCENE_DECOMPOSER_PROMPT_VERSION",
            },
        ) from e


def get_scene_planner_prompt(version: str | None = None) -> Prompt:
    key = (version or os.getenv("SCENE_PLANNER_PROMPT_VERSION", "v1")).strip()
    try:
        return SCENE_PLANNER_PROMPTS[key]
    except KeyError as e:
        raise ConfigurationError(
            f"Unknown scene planner prompt version {key!r}",
            context={
                "available_versions": sorted(SCENE_PLANNER_PROMPTS),
                "env": "SCENE_PLANNER_PROMPT_VERSION",
            },
        ) from e


def get_code_repair_prompt(version: str | None = None) -> Prompt:
    key = (version or os.getenv("CODE_REPAIR_PROMPT_VERSION", "v1")).strip()
    try:
        return CODE_REPAIR_PROMPTS[key]
    except KeyError as e:
        raise ConfigurationError(
            f"Unknown code repair prompt version {key!r}",
            context={
                "available_versions": sorted(CODE_REPAIR_PROMPTS),
                "env": "CODE_REPAIR_PROMPT_VERSION",
            },
        ) from e
