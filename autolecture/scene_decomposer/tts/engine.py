"""Abstract base for all TTS providers.

Every speech provider must subclass TTSEngine and implement the three
required methods.  The rest of the system talks to this interface only,
making providers hot-swappable at runtime.
"""

from abc import ABC, abstractmethod
from typing import List
import numpy as np


class TTSEngine(ABC):
    """Uniform contract that every TTS backend must satisfy."""

    @abstractmethod
    def generate(self, text: str, voice: str = "default", speed: float = 1.0) -> np.ndarray:
        """Return a 1-D float32 numpy array of audio samples."""
        ...

    @abstractmethod
    def available_voices(self) -> List[str]:
        """Return the list of voice names the backend supports."""
        ...

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Audio sample rate in Hz (e.g. 24000)."""
        ...

    def generate_to_file(self, text: str, output_path: str, voice: str = "default",
                         speed: float = 1.0) -> str:
        """Convenience: synthesise then write to a wav file. Returns *output_path*."""
        import soundfile as sf
        audio = self.generate(text, voice=voice, speed=speed)
        sf.write(output_path, audio, self.sample_rate)
        return output_path
