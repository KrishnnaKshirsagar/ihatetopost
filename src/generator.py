"""Generate textured quote card images matching the reference aesthetic."""

from __future__ import annotations

from pathlib import Path
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import DEFAULT_FONT_PATH, PALETTES, Palette


def pick_palette(
    palette_name: str | None = None,
    last_palette: str | None = None,
) -> Palette:
    """Select a palette by name or pick one different from last_palette."""
    if palette_name:
        for palette in PALETTES:
            if palette.name == palette_name:
                return palette
        available = ", ".join(p.name for p in PALETTES)
        raise ValueError(f"Unknown palette '{palette_name}'. Available: {available}")

    choices = [p for p in PALETTES if p.name != last_palette] or list(PALETTES)
    return random.choice(choices)


def _create_textured_background(
    width: int,
    height: int,
    bg_rgb: tuple[int, int, int],
    grain_strength: float,
) -> np.ndarray:
    """Create a tactile matte paper / film-grain background array (H, W, 3)."""
    rng = np.random.default_rng()
    base = np.zeros((height, width, 3), dtype=np.float32)
    base[:, :] = bg_rgb

    # Fine monochrome grain + very subtle chromatic cardstock variation.
    mono_grain = rng.normal(0.0, grain_strength, size=(height, width, 1)).astype(np.float32)
    chroma_grain = rng.normal(0.0, grain_strength * 0.18, size=(height, width, 3)).astype(
        np.float32
    )

    # Gentle radial vignette (edges ~4% darker) for organic print depth.
    y = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    x = np.linspace(-1.0, 1.0, width, dtype=np.float32)[None, :]
    vignette = 1.0 - 0.04 * (x * x + y * y)

    textured = base * vignette[:, :, None] + mono_grain + chroma_grain
    return np.clip(textured, 0, 255).astype(np.uint8)


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines


def _fit_quote_layout(
    draw: ImageDraw.ImageDraw,
    quote_text: str,
    font_path: Path,
    max_width: int,
    max_height: int,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Choose the largest font size that fits comfortably inside the target box."""
    for size in range(56, 26, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        lines = _wrap_text(draw, quote_text, font, max_width)
        line_height = int(size * 1.42)
        total_height = len(lines) * line_height
        if total_height <= max_height:
            return font, lines, line_height

    font = ImageFont.truetype(str(font_path), size=28)
    lines = _wrap_text(draw, quote_text, font, max_width)
    return font, lines, int(28 * 1.42)


def _blend_color(
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    alpha: float,
) -> tuple[int, int, int]:
    """Blend foreground color toward background color."""
    return tuple(int(fg[i] * alpha + bg[i] * (1.0 - alpha)) for i in range(3))


def generate_quote_image(
    quote_text: str,
    output_path: Path,
    palette: Palette,
    signature: str = "-BL",
    width: int = 1080,
    height: int = 1350,
    font_path: Path = DEFAULT_FONT_PATH,
) -> Path:
    """Render a quote card image and save it as a high-quality JPEG/PNG."""
    if not font_path.exists():
        raise FileNotFoundError(f"Font file not found: {font_path}")

    bg_array = _create_textured_background(
        width=width,
        height=height,
        bg_rgb=palette.bg_rgb,
        grain_strength=palette.grain_strength,
    )
    image = Image.fromarray(bg_array, mode="RGB")
    draw = ImageDraw.Draw(image)

    margin_x = int(width * 0.105)
    max_text_width = width - (2 * margin_x)
    max_text_height = int(height * 0.56)

    font, lines, line_height = _fit_quote_layout(
        draw=draw,
        quote_text=quote_text,
        font_path=font_path,
        max_width=max_text_width,
        max_height=max_text_height,
    )

    total_block_height = len(lines) * line_height
    # Optical center: slightly above exact vertical midpoint.
    start_y = int((height - total_block_height) * 0.46)

    for idx, line in enumerate(lines):
        y = start_y + idx * line_height
        draw.text((margin_x, y), line, font=font, fill=palette.text_rgb)

    if signature:
        sig_size = max(26, min(32, int(font.size * 0.62)))
        sig_font = ImageFont.truetype(str(font_path), size=sig_size)
        sig_bbox = draw.textbbox((0, 0), signature, font=sig_font)
        sig_w = sig_bbox[2] - sig_bbox[0]
        sig_h = sig_bbox[3] - sig_bbox[1]
        sig_x = width - int(width * 0.08) - sig_w
        sig_y = height - int(height * 0.06) - sig_h
        sig_color = _blend_color(palette.text_rgb, palette.bg_rgb, alpha=0.88)
        draw.text((sig_x, sig_y), signature, font=sig_font, fill=sig_color)

    # Light final ink-on-paper grain pass so text integrates with the cardstock.
    rng = np.random.default_rng()
    final_arr = np.asarray(image, dtype=np.float32)
    ink_grain = rng.normal(0.0, palette.grain_strength * 0.25, size=(height, width, 1)).astype(
        np.float32
    )
    image = Image.fromarray(np.clip(final_arr + ink_grain, 0, 255).astype(np.uint8), mode="RGB")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() in (".jpg", ".jpeg"):
        image.save(output_path, format="JPEG", quality=95)
    else:
        image.save(output_path, format="PNG")
    return output_path
