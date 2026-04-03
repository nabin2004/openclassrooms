"""Intent classifier prompt — version 2 (stricter JSON-only emphasis for experiments)."""

from manimator.prompts.intent_classifier.v1 import INTENT as _INTENT_V1
from manimator.prompts.types import Prompt

VERSION = "v2"

INTENT = Prompt(
    name="intent_classifier",
    version=VERSION,
    system=_INTENT_V1.system
    + "\n\nHard rule: respond with a single JSON object only — no markdown fences, no commentary.\n",
)
