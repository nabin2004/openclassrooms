from pathlib import Path

from amoeba.subprocess import run_subprocess

# Ignore sub-frame disagreements between ffprobe and filters.
_DURATION_EPS = 0.06


def ffprobe_duration_seconds(media: Path) -> float:
    r = run_subprocess(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(media),
        ],
        check=True,
    )
    return float(r.stdout.strip())


def mux_video_with_narration(video: Path, wav: Path, output: Path) -> None:
    """
    Mux TTS WAV with a Manim scene without slowing the animation down.

    - If speech is longer than the video: keep playback at native speed, then hold
      the last frame (clone) until the audio ends.
    - If the video is longer than the speech: pad the audio with trailing silence
      so the full animation plays without time-stretching either stream.

    This avoids the “laggy / hanging” look caused by uniform setpts stretching.
    """
    v_dur = ffprobe_duration_seconds(video)
    a_dur = ffprobe_duration_seconds(wav)
    if v_dur <= 0.01:
        raise ValueError(f"Video duration too small or unknown: {video} ({v_dur}s)")
    if a_dur <= 0.01:
        raise ValueError(f"Audio duration too small or unknown: {wav} ({a_dur}s)")

    output.parent.mkdir(parents=True, exist_ok=True)

    if a_dur > v_dur + _DURATION_EPS:
        pad_v = a_dur - v_dur
        filter_complex = (
            f"[0:v]tpad=stop_mode=clone:stop_duration={pad_v:.6f},format=yuv420p[v];"
            "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a]"
        )
    elif v_dur > a_dur + _DURATION_EPS:
        filter_complex = (
            "[0:v]format=yuv420p[v];"
            f"[1:a]apad=whole_dur={v_dur:.6f},aformat=sample_rates=48000:channel_layouts=stereo[a]"
        )
    else:
        filter_complex = (
            "[0:v]format=yuv420p[v];"
            "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[a]"
        )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-i",
        str(wav),
        "-filter_complex",
        filter_complex,
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output),
    ]
    run_subprocess(cmd, check=True)


# Backward-compatible name
def mux_video_stretched_to_audio(video: Path, wav: Path, output: Path) -> None:
    mux_video_with_narration(video, wav, output)
