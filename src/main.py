"""CLI entry point for generating a quote image and posting it to Instagram."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from src.config import HISTORY_FILE, OUTPUT_DIR, Settings
from src.generator import generate_quote_image, pick_palette
from src.instagram import publish_photo
from src.quotes import Quote, format_caption, load_history, pick_next_quote, save_history
from src.uploader import upload_image


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a textured quote card and post it to Instagram."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate image and caption locally without uploading or posting.",
    )
    parser.add_argument(
        "--palette",
        type=str,
        default=None,
        help="Force a specific palette name (e.g., cobalt_white, mustard_ink, charcoal_red).",
    )
    parser.add_argument(
        "--quote",
        type=str,
        default=None,
        help="Override quote text instead of fetching from ZenQuotes.",
    )
    parser.add_argument(
        "--author",
        type=str,
        default="Unknown",
        help="Author attribution when --quote is provided.",
    )
    parser.add_argument(
        "--signature",
        type=str,
        default=None,
        help="Bottom-right signature (default: -BL).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Custom output file path (default: output/quote_<timestamp>.jpg).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = Settings.from_env()
    dry_run = args.dry_run or settings.dry_run
    signature = args.signature if args.signature is not None else settings.signature

    history = load_history(HISTORY_FILE)
    quote = (
        Quote(text=args.quote.strip(), author=args.author.strip())
        if args.quote
        else pick_next_quote(HISTORY_FILE)
    )
    palette = pick_palette(
        palette_name=args.palette,
        last_palette=history.get("last_palette"),
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = args.output or (OUTPUT_DIR / f"quote_{timestamp}.jpg")

    generate_quote_image(
        quote_text=quote.text,
        output_path=output_path,
        palette=palette,
        signature=signature,
        width=settings.image_width,
        height=settings.image_height,
        font_path=settings.font_path,
    )
    caption = format_caption(quote)

    print(f"Generated image: {output_path}")
    print(f"Palette: {palette.name}")
    print(f"Signature: {signature}")
    print(f"Caption:\n{caption}\n")

    if dry_run:
        print("Dry run enabled — skipping upload and Instagram publish.")
        return 0

    image_url = upload_image(output_path, settings)
    print(f"Uploaded public image URL: {image_url}")

    media_id = publish_photo(
        ig_user_id=settings.ig_user_id,
        access_token=settings.ig_access_token,
        image_url=image_url,
        caption=caption,
    )
    print(f"Published to Instagram! Media ID: {media_id}")

    save_history(quote=quote, palette_name=palette.name, history_path=HISTORY_FILE)
    print(f"Updated history: {HISTORY_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
