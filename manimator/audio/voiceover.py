import re

from manimator.contracts.scene_plan import SceneEntry
from manimator.contracts.scene_spec import SceneSpec


def fallback_scene_transcript(scene_id: int, scene_title: str, animation_count: int) -> str:
    return (
        f"Scene {scene_id}, {scene_title}. "
        f"In this scene we build intuition using {animation_count} visual steps. "
        "Notice what changes, what stays fixed, and how those changes explain the core idea."
    )


def prepare_text_for_tts(text: str) -> str:
    """Normalize planner markers and whitespace for speech synthesis."""
    t = text.strip()
    t = re.sub(r"\[pause\]", " ... ", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def voiceover_text_for_scene(spec: SceneSpec, scene: SceneEntry | None) -> str:
    raw = (spec.voiceover_script or "").strip()
    if raw:
        return prepare_text_for_tts(raw)
    scene_title = scene.title if scene else spec.class_name
    return prepare_text_for_tts(
        fallback_scene_transcript(spec.scene_id, scene_title, len(spec.animations))
    )
