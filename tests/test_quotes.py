"""Tests for quote selection, deduplication, and history persistence."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.quotes import Quote, format_caption, load_history, pick_next_quote, save_history


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
        picked = pick_next_quote(history_file)

    assert picked == fresh_quote


def test_format_caption() -> None:
    quote = Quote(text="Stay hungry, stay foolish.", author="Steve Jobs")
    caption = format_caption(quote)
    assert '"Stay hungry, stay foolish."' in caption
    assert "— Steve Jobs" in caption
