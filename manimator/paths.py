from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunPaths:
    run_dir: Path
    ir_dir: Path
    code_dir: Path
    renders_dir: Path
    narrated_dir: Path
    audio_dir: Path
    delivery_dir: Path
    manim_media_dir: Path


def get_run_paths(run_id: str, *, outputs_root: Path | None = None) -> RunPaths:
    """
    Standardize Manimator output structure for one pipeline run.

    Layout:
      outputs/runs/<run_id>/
        code/
        renders/
        narrated/
        audio/
        delivery/
        manim_media/     (isolated manim --media_dir)
    """
    root = (outputs_root or Path("outputs")).resolve()
    run_dir = root / "runs" / run_id
    ir_dir = run_dir / "ir"
    code_dir = run_dir / "code"
    renders_dir = run_dir / "renders"
    narrated_dir = run_dir / "narrated"
    audio_dir = run_dir / "audio"
    delivery_dir = run_dir / "delivery"
    manim_media_dir = run_dir / "manim_media"

    for p in [ir_dir, code_dir, renders_dir, narrated_dir, audio_dir, delivery_dir, manim_media_dir]:
        p.mkdir(parents=True, exist_ok=True)

    return RunPaths(
        run_dir=run_dir,
        ir_dir=ir_dir,
        code_dir=code_dir,
        renders_dir=renders_dir,
        narrated_dir=narrated_dir,
        audio_dir=audio_dir,
        delivery_dir=delivery_dir,
        manim_media_dir=manim_media_dir,
    )

