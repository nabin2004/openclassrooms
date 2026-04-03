"""Central registry for versioned prompts (select via env or explicit version)."""

from __future__ import annotations

import os

from amoeba.exceptions import ConfigurationError

from manimator.prompts.intent_classifier import v1 as intent_v1
from manimator.prompts.intent_classifier import v2 as intent_v2
from manimator.prompts.types import Prompt

INTENT_PROMPTS: dict[str, Prompt] = {
    intent_v1.INTENT.version: intent_v1.INTENT,
    intent_v2.INTENT.version: intent_v2.INTENT,
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
