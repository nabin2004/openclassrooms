import subprocess
from pathlib import Path


def ffprobe_duration_seconds(media: Path) -> float:
    r = subprocess.run(
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
        capture_output=True,
        text=True,
        check=True,
    )
    return float(r.stdout.strip())


def mux_video_stretched_to_audio(video: Path, wav: Path, output: Path) -> None:
    """
    Mux narration with scene video. Video timeline is uniformly scaled so that
    visual duration matches the WAV duration (animations track wall-clock with speech).
    """
    v_dur = ffprobe_duration_seconds(video)
    a_dur = ffprobe_duration_seconds(wav)
    if v_dur <= 0.01:
        raise ValueError(f"Video duration too small or unknown: {video} ({v_dur}s)")
    if a_dur <= 0.01:
        raise ValueError(f"Audio duration too small or unknown: {wav} ({a_dur}s)")

    ratio = a_dur / v_dur
    output.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = f"[0:v]setpts=PTS*{ratio}[v]"

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
        "1:a:0",
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
    subprocess.run(cmd, capture_output=True, text=True, check=True)
