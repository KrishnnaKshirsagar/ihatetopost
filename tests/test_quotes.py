"""Tests for quote selection, deduplication, and history persistence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.quotes import (
    Quote,
    format_caption,
    load_curated_quotes,
    load_history,
    pick_next_quote,
    save_history,
)


def test_history_roundtrip(tmp_path: Path) -> None:
    history_file = tmp_path / "posted_quotes.json"
    quote = Quote(text="Simplicity is the ultimate sophistication.", author="Leonardo da Vinci")

    save_history(quote, "cobalt_white", history_file)
    loaded = load_history(history_file)

    assert quote.digest in loaded["posted"]
    assert loaded["last_palette"] == "cobalt_white"


def test_pick_next_quote_skips_seen(tmp_path: Path) -> None:
    history_file = tmp_path / "posted_quotes.json"
    seen_quote = Quote(text="Already posted quote.", author="Author A")
    fresh_quote = Quote(text="Fresh unseen quote for today.", author="Author B")
    save_history(seen_quote, "mustard_ink", history_file)

    with patch("src.quotes.fetch_zenquotes", return_value=[seen_quote, fresh_quote]):
        picked = pick_next_quote(history_file, quotes_path=tmp_path / "missing_quotes.json")

    assert picked == fresh_quote


def test_curated_quotes_bank(tmp_path: Path) -> None:
    history_file = tmp_path / "posted_quotes.json"
    quotes_file = tmp_path / "quotes.json"
    quotes_file.write_text(
        json.dumps([{"text": "Curated quote one.", "author": ""}]),
        encoding="utf-8",
    )

    loaded = load_curated_quotes(quotes_file)
    assert len(loaded) == 1
    assert loaded[0].text == "Curated quote one."

    with patch("src.quotes.fetch_zenquotes", return_value=[]):
        picked = pick_next_quote(history_file, quotes_path=quotes_file)
    assert picked.text == "Curated quote one."


def test_format_caption() -> None:
    quote = Quote(text="Stay hungry, stay foolish.", author="Steve Jobs")
    caption = format_caption(quote)
    assert '"Stay hungry, stay foolish."' in caption
    assert "— Steve Jobs" in caption


def test_format_caption_without_author() -> None:
    quote = Quote(text="Just a standalone quote.", author="")
    caption = format_caption(quote)
    assert '"Just a standalone quote."' in caption
    assert "—" not in caption
