import importlib.util
import os
import shutil


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def kittentts_available() -> bool:
    return importlib.util.find_spec("kittentts") is not None


def is_tts_enabled() -> bool:
    """
    MANIMATOR_ENABLE_TTS:
      unset / empty → auto (on if kittentts is installed)
      0/false/no/off → off
      1/true/yes/on → on (requires kittentts)
    """
    raw = os.getenv("MANIMATOR_ENABLE_TTS", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    return kittentts_available()
