"""Tests for quote card image generation."""

from __future__ import annotations

from pathlib import Path
from PIL import Image

from src.config import PALETTES
from src.generator import generate_quote_image, pick_palette


def test_pick_palette_avoids_repeat() -> None:
    recent = ["cobalt_white", "mustard_ink", "sage_ink", "blush_espresso"]
    for _ in range(20):
        chosen = pick_palette(last_palette="blush_espresso", recent_palettes=recent)
        assert chosen.name not in recent


def test_generate_quote_image_dimensions_and_file(tmp_path: Path) -> None:
    out_file = tmp_path / "card.jpg"
    palette = PALETTES[0]

    result = generate_quote_image(
        quote_text="Some people might try to convince you that you are a basic blue gel pen.",
        output_path=out_file,
        palette=palette,
        signature="-ff",
        width=1080,
        height=1350,
    )

    assert result == out_file
    assert out_file.exists()
    with Image.open(out_file) as img:
        assert img.size == (1080, 1350)
        assert img.mode == "RGB"
