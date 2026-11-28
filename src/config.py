"""Configuration and defaults for the quote-to-Instagram pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
HISTORY_FILE = DATA_DIR / "posted_quotes.json"
QUOTES_BANK_FILE = DATA_DIR / "quotes.json"

DEFAULT_FONT_PATH = FONTS_DIR / "ShortStack-Regular.ttf"


@dataclass(frozen=True)
class Palette:
    """Color and texture configuration for a quote card."""

    name: str
    bg_rgb: tuple[int, int, int]
    text_rgb: tuple[int, int, int]
    grain_strength: float = 10.0


# Curated palettes inspired directly by the reference images + cohesive extras.
PALETTES: tuple[Palette, ...] = (
    Palette(
        name="cobalt_white",
        bg_rgb=(17, 65, 142),       # Deep royal/cobalt blue
        text_rgb=(244, 246, 250),   # Crisp off-white
        grain_strength=9.0,
    ),
    Palette(
        name="mustard_ink",
        bg_rgb=(229, 172, 56),      # Warm mustard yellow
        text_rgb=(26, 24, 20),      # Deep ink black
        grain_strength=5.5,
    ),
    Palette(
        name="charcoal_red",
        bg_rgb=(30, 30, 30),        # Matte charcoal
        text_rgb=(232, 24, 24),     # Vibrant red
        grain_strength=9.0,
    ),
    Palette(
        name="forest_cream",
        bg_rgb=(39, 64, 48),        # Deep forest green
        text_rgb=(245, 239, 228),   # Warm cream
        grain_strength=8.0,
    ),
    Palette(
        name="terracotta_cream",
        bg_rgb=(184, 74, 50),       # Warm terracotta
        text_rgb=(250, 244, 235),   # Soft cream
        grain_strength=7.0,
    ),
    Palette(
        name="paper_ink",
        bg_rgb=(239, 233, 221),     # Textured warm paper
        text_rgb=(28, 28, 28),      # Ink black
        grain_strength=5.5,
    ),
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    signature: str
    image_width: int
    image_height: int
    font_path: Path
    ig_access_token: str
    ig_user_id: str
    imgbb_api_key: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    dry_run: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            signature=os.getenv("QUOTE_SIGNATURE", "-ff"),
            image_width=int(os.getenv("IMAGE_WIDTH", "1080")),
            image_height=int(os.getenv("IMAGE_HEIGHT", "1350")),
            font_path=Path(os.getenv("FONT_PATH", str(DEFAULT_FONT_PATH))),
            ig_access_token=os.getenv("IG_ACCESS_TOKEN", "").strip(),
            ig_user_id=os.getenv("IG_USER_ID", "").strip(),
            imgbb_api_key=os.getenv("IMGBB_API_KEY", "").strip(),
            cloudinary_cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "").strip(),
            cloudinary_api_key=os.getenv("CLOUDINARY_API_KEY", "").strip(),
            cloudinary_api_secret=os.getenv("CLOUDINARY_API_SECRET", "").strip(),
            dry_run=os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes"),
        )
