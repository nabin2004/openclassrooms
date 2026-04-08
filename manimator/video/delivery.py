"""Combine scene MP4s into one deliverable with transcript in the same folder."""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from amoeba.subprocess import run_subprocess
from manimator.contracts.scene_spec import SceneSpec


def _ffprobe_has_audio(path: Path) -> bool:
    r = run_subprocess(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=False,
    )
    return bool(r.stdout.strip())


def _normalize_segment(src: Path, dst: Path, height: int = 720) -> None:
    """H.264 + AAC stereo 48 kHz; add silent audio if the clip has no audio stream."""
    vf = f"scale=-2:{height},fps=30,format=yuv420p"
    if _ffprobe_has_audio(src):
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            str(dst),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000",
            "-filter_complex",
            f"[0:v]{vf}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-shortest",
            str(dst),
        ]
    run_subprocess(cmd, check=True)


def _concat_demuxer_copy(segments: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        for seg in segments:
            p = seg.resolve().as_posix().replace("'", r"'\''")
            f.write(f"file '{p}'\n")
        list_path = f.name
    try:
        run_subprocess(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                list_path,
                "-c",
                "copy",
                str(output),
            ],
            check=True,
        )
    finally:
        Path(list_path).unlink(missing_ok=True)


def ordered_scene_video_sources(
    scene_specs: list[SceneSpec],
    narrated_paths: dict[int, str],
    rendered_paths: dict[int, str],
) -> list[Path]:
    """Prefer narrated clip per scene, else rendered; scene order from specs."""
    out: list[Path] = []
    for spec in sorted(scene_specs, key=lambda s: s.scene_id):
        sid = spec.scene_id
        raw = narrated_paths.get(sid) or rendered_paths.get(sid)
        if not raw:
            continue
        p = Path(raw)
        if p.is_file():
            out.append(p)
    return out


def build_delivery_package(
    scene_specs: list[SceneSpec],
    narrated_paths: dict[int, str],
    rendered_paths: dict[int, str],
    full_transcript: str,
    outputs_root: Path | None = None,
) -> dict[str, str | None]:
    """
    Create a delivery folder with transcript.txt and final.mp4 (all scenes).

    - If ``outputs_root`` is the global ``outputs/`` folder, we keep the historical
      timestamped layout: ``outputs/delivery/<timestamp>/`` and also write
      ``outputs/transcript.txt`` for backward compatibility.
    - If ``outputs_root`` is a per-run folder (e.g. ``outputs/runs/<run_id>/``),
      we write to ``<outputs_root>/delivery/`` (no timestamp) so everything for a
      run is easy to find in one place.
    """
    outputs_root = outputs_root or Path("outputs")
    outputs_root.mkdir(parents=True, exist_ok=True)

    if outputs_root.name == "outputs":
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        delivery_dir = outputs_root / "delivery" / stamp
    else:
        delivery_dir = outputs_root / "delivery"
    delivery_dir.mkdir(parents=True, exist_ok=True)

    transcript_delivery = delivery_dir / "transcript.txt"
    transcript_delivery.write_text(full_transcript, encoding="utf-8")

    legacy_transcript: Path | None = None
    if outputs_root.name == "outputs":
        legacy_transcript = outputs_root / "transcript.txt"
        legacy_transcript.write_text(full_transcript, encoding="utf-8")

    sources = ordered_scene_video_sources(scene_specs, narrated_paths, rendered_paths)
    final_mp4 = delivery_dir / "final.mp4"
    output_video_path: str | None = None

    if sources:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                normalized: list[Path] = []
                for i, src in enumerate(sources):
                    n = tmp_path / f"n{i:04d}.mp4"
                    _normalize_segment(src, n)
                    normalized.append(n)
                _concat_demuxer_copy(normalized, final_mp4)
            if final_mp4.is_file():
                output_video_path = str(final_mp4.resolve())
        except OSError:
            output_video_path = None

    return {
        "output_video_path": output_video_path,
        "transcript_path": str(transcript_delivery.resolve()),
        "delivery_dir": str(delivery_dir.resolve()),
        "legacy_transcript_path": str(legacy_transcript.resolve()) if legacy_transcript else None,
    }
