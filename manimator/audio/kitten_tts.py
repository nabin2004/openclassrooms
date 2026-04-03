import os
from pathlib import Path

_model = None


def _load_model():
    from kittentts import KittenTTS

    model_name = os.getenv("KITTEN_TTS_MODEL", "KittenML/kitten-tts-nano-0.8")
    cache_dir = os.getenv("KITTEN_TTS_CACHE_DIR") or None
    backend = os.getenv("KITTEN_TTS_BACKEND", "").strip()
    kwargs = {}
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    if backend.lower() in ("cuda", "gpu"):
        kwargs["backend"] = "cuda"
    return KittenTTS(model_name, **kwargs)


def get_kitten_model():
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def synthesize_voiceover_to_wav(text: str, out_path: Path) -> None:
    """Write 24 kHz WAV using KittenTTS."""
    if not text:
        raise ValueError("Cannot synthesize empty voiceover text")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model = get_kitten_model()
    voice = os.getenv("KITTEN_TTS_VOICE", "Jasper")
    speed = float(os.getenv("KITTEN_TTS_SPEED", "1.0"))
    # Wrapper in kittentts.get_model only accepts voice/speed/sample_rate (no clean_text).
    # Underlying ONNX model still preprocesses via generate() defaults.
    model.generate_to_file(
        text,
        str(out_path),
        voice=voice,
        speed=speed,
        sample_rate=24000,
    )
