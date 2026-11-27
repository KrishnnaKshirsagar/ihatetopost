"""Tests for Reel video generation."""

from __future__ import annotations

from pathlib import Path
import shutil
import pytest

from src.config import PALETTES
from src.generator import generate_quote_image
from src.video import create_reel_video, pick_music_track


def test_pick_music_track_empty_dir(tmp_path: Path) -> None:
    assert pick_music_track(tmp_path) is None


def test_pick_music_track_finds_mp3(tmp_path: Path) -> None:
    track = tmp_path / "lofi.mp3"
    track.write_bytes(b"fake")
    assert pick_music_track(tmp_path) == track


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_create_reel_video_silent(tmp_path: Path) -> None:
    img_path = tmp_path / "card.jpg"
    mp4_path = tmp_path / "reel.mp4"
    generate_quote_image(
        quote_text="Simplicity is the ultimate sophistication.",
        output_path=img_path,
        palette=PALETTES[0],
        signature="-ff",
        width=1080,
        height=1920,
    )

    result = create_reel_video(
        image_path=img_path,
        output_path=mp4_path,
        duration_seconds=2.0,
        music_path=None,
    )
    assert result == mp4_path
    assert mp4_path.exists()
    assert mp4_path.stat().st_size > 0
