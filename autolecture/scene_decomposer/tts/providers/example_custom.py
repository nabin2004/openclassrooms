"""Skeleton showing how to plug in your own TTS backend.

Copy this file, implement the three methods, and call ``register_provider``.
See SPEECH_PROVIDERS.md at the project root for the full walkthrough.
"""

from __future__ import annotations
from typing import List
import numpy as np

from manimator.tts.engine import TTSEngine
from manimator.tts.registry import register_provider


class MyCustomTTSProvider(TTSEngine):
    def __init__(self, **kwargs):
        # Load your model / API client here
        ...

    def generate(self, text: str, voice: str = "default", speed: float = 1.0) -> np.ndarray:
        raise NotImplementedError("Replace with your synthesis logic")

    def available_voices(self) -> List[str]:
        return ["default"]

    @property
    def sample_rate(self) -> int:
        return 24_000


# Uncomment to make the provider available at runtime:
# register_provider("my_custom", MyCustomTTSProvider)
