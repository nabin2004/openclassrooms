"""Versioned LLM prompts for Manimator."""

from manimator.prompts.registry import INTENT_PROMPTS, get_intent_prompt
from manimator.prompts.types import Prompt

__all__ = [
    "INTENT_PROMPTS",
    "Prompt",
    "get_intent_prompt",
]
