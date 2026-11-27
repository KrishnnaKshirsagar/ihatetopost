"""Convert a static quote card image into an MP4 Reel with optional background music."""

from __future__ import annotations

from pathlib import Path
import random
import shutil
import subprocess

from src.config import ASSETS_DIR

MUSIC_DIR = ASSETS_DIR / "music"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac"}


def pick_music_track(music_dir: Path = MUSIC_DIR) -> Path | None:
    """Return a random audio track from music_dir, or None if none exist."""
    if not music_dir.exists():
        return None
    tracks = [
        p
        for p in sorted(music_dir.iterdir())
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return random.choice(tracks) if tracks else None


def create_reel_video(
    image_path: Path,
    output_path: Path,
    duration_seconds: float = 6.0,
    music_path: Path | None = None,
) -> Path:
    """Render an MP4 Reel from a quote image and optional audio track using ffmpeg."""
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg is required to create Reel videos but was not found on PATH.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fade_out_start = max(0.0, duration_seconds - 0.8)

    cmd: list[str] = [
        ffmpeg_bin,
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
    ]

    if music_path is not None:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])
        audio_filter = f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_out_start:.2f}:d=0.8"
        cmd.extend(["-af", audio_filter])
    else:
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])

    cmd.extend(
        [
            "-t",
            f"{duration_seconds:.2f}",
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({result.returncode}): {result.stderr}")
    return output_path
