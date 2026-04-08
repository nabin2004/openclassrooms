from __future__ import annotations

from pathlib import Path

from manimator.audio.kitten_tts import synthesize_voiceover_to_wav
from manimator.audio.mux import mux_video_with_narration
from manimator.audio.tts_config import ffmpeg_available, is_tts_enabled, kittentts_available
from manimator.audio.voiceover import voiceover_text_for_scene
from manimator.paths import get_run_paths
from manimator.pipeline.state import PipelineState


def build_narrated_scene_paths(state: PipelineState) -> dict[int, str]:
    """
    For each rendered scene, optionally synthesize speech from the same text used
    for transcripts and mux it into a new MP4. Video keeps natural timing; if
    speech is longer, the last frame is held instead of slowing the whole scene.
    """
    run_id = state.run_id or "unknown"
    paths = get_run_paths(run_id)

    scene_lookup = {}
    if state.scene_plan:
        scene_lookup = {s.id: s for s in state.scene_plan.scenes}

    want_tts = is_tts_enabled()
    if want_tts and not kittentts_available():
        raise RuntimeError(
            "MANIMATOR_ENABLE_TTS requests TTS but `kittentts` is not installed. "
            "Install with: uv sync --package manimator --extra tts"
        )
    if want_tts and not ffmpeg_available():
        raise RuntimeError(
            "TTS mux requires ffmpeg and ffprobe on PATH (install your OS ffmpeg package)."
        )

    narrated: dict[int, str] = {}
    for spec in sorted(state.scene_specs, key=lambda s: s.scene_id):
        scene_id = spec.scene_id
        video_path = state.rendered_paths.get(scene_id)
        if not video_path:
            continue
        video = Path(video_path)
        if not video.is_file():
            narrated[scene_id] = str(video)
            continue

        if not want_tts:
            narrated[scene_id] = str(video)
            continue

        scene = scene_lookup.get(scene_id)
        text = voiceover_text_for_scene(spec, scene)
        wav_path = paths.audio_dir / f"scene_{scene_id}_narration.wav"
        out_path = paths.narrated_dir / f"scene_{scene_id}.mp4"

        synthesize_voiceover_to_wav(text, wav_path)
        mux_video_with_narration(video, wav_path, out_path)
        narrated[scene_id] = str(out_path)

    return narrated
