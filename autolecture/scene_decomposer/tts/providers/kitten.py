"""KittenTTS provider — lightweight ONNX-based TTS that runs on CPU."""

from __future__ import annotations
from typing import List

import numpy as np

from ..engine import TTSEngine
from ..registry import register_provider


_MODEL_VARIANTS = {
    "mini": "KittenML/kitten-tts-mini-0.8",
    "micro": "KittenML/kitten-tts-micro-0.8",
    "nano": "KittenML/kitten-tts-nano-0.8",
    "nano-int8": "KittenML/kitten-tts-nano-0.8-int8",
}

DEFAULT_VARIANT = "mini"


class KittenTTSProvider(TTSEngine):
    """Wraps the ``kittentts`` library behind the common TTSEngine interface.

    Parameters
    ----------
    model_variant : str
        One of ``mini``, ``micro``, ``nano``, ``nano-int8``,
        **or** a full Hugging Face repo id.
    cache_dir : str | None
        Where to cache downloaded ONNX files.
    """

    def __init__(self, model_variant: str = DEFAULT_VARIANT, cache_dir: str | None = None):
        from kittentts import KittenTTS
        from huggingface_hub import hf_hub_download, list_repo_files

        repo = _MODEL_VARIANTS.get(model_variant, model_variant)
        
        files = list_repo_files(repo)
        onnx_file = next(f for f in files if f.endswith(".onnx"))
        npz_file = next(f for f in files if f.endswith(".npz"))
        
        model_path = hf_hub_download(repo, onnx_file, cache_dir=cache_dir)
        voices_path = hf_hub_download(repo, npz_file, cache_dir=cache_dir)

        self._model = KittenTTS(model_path=model_path, voices_path=voices_path)
        
        # fix: kitten-tts-mini 0.8 voices are (400, 256), but model expects (1, 256)
        import numpy as np
        voices_dict = dict(self._model._voices)
        for k, v in voices_dict.items():
            if len(v.shape) == 2 and v.shape[0] > 1:
                voices_dict[k] = np.mean(v, axis=0, keepdims=True)
        self._model._voices = voices_dict

        self._variant = model_variant

    def generate(self, text: str, voice: str = "default", speed: float = 1.0) -> np.ndarray:
        available = self.available_voices()
        if voice in ("default", "Bella") or voice not in available:
            voice = available[0] if available else voice
        return self._model.generate(text, voice=voice, speed=speed)
    def available_voices(self) -> List[str]:
        return self._model.available_voices

    @property
    def sample_rate(self) -> int:
        return 24_000


register_provider("kitten", KittenTTSProvider)
