"""Quote fetching, deduplication, and caption formatting."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import requests

from src.config import HISTORY_FILE

ZENQUOTES_BATCH_URL = "https://zenquotes.io/api/quotes"
MAX_QUOTE_CHARS = 240
MIN_QUOTE_CHARS = 20

FALLBACK_QUOTES: list[tuple[str, str]] = [
    (
        "The quieter you become, the more you are able to hear.",
        "Rumi",
    ),
    (
        "Do not wait for the storms of life to pass. Learn to dance in the rain.",
        "Vivian Greene",
    ),
    (
        "You do not have to be great to start, but you have to start to be great.",
        "Zig Ziglar",
    ),
    (
        "In the middle of difficulty lies opportunity.",
        "Albert Einstein",
    ),
]


@dataclass(frozen=True)
class Quote:
    """A single quote and its attribution."""

    text: str
    author: str

    @property
    def digest(self) -> str:
        normalized = " ".join(self.text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def load_history(history_path: Path = HISTORY_FILE) -> dict:
    """Load posted quote digests and last palette from JSON."""
    if not history_path.exists():
        return {"posted": [], "last_palette": None}
    with history_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {
        "posted": list(data.get("posted", [])),
        "last_palette": data.get("last_palette"),
    }


def save_history(
    quote: Quote,
    palette_name: str,
    history_path: Path = HISTORY_FILE,
) -> None:
    """Record a posted quote digest and palette name."""
    history = load_history(history_path)
    if quote.digest not in history["posted"]:
        history["posted"].append(quote.digest)
    history["last_palette"] = palette_name
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)
        fh.write("\n")


def fetch_zenquotes(timeout: int = 15) -> list[Quote]:
    """Fetch a batch of quotes from ZenQuotes API."""
    response = requests.get(ZENQUOTES_BATCH_URL, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    quotes: list[Quote] = []
    for item in payload:
        text = str(item.get("q", "")).strip()
        author = str(item.get("a", "Unknown")).strip()
        if not text or author.lower() == "zenquotes.io":
            continue
        if MIN_QUOTE_CHARS <= len(text) <= MAX_QUOTE_CHARS:
            quotes.append(Quote(text=text, author=author))
    return quotes


def pick_next_quote(history_path: Path = HISTORY_FILE) -> Quote:
    """Pick an unposted quote from ZenQuotes, falling back to local quotes."""
    history = load_history(history_path)
    seen = set(history["posted"])

    candidates: list[Quote] = []
    try:
        candidates = fetch_zenquotes()
    except Exception:
        candidates = []

    unseen = [q for q in candidates if q.digest not in seen]
    if unseen:
        return random.choice(unseen)

    fallback = [Quote(text=t, author=a) for t, a in FALLBACK_QUOTES]
    unseen_fallback = [q for q in fallback if q.digest not in seen]
    if unseen_fallback:
        return random.choice(unseen_fallback)

    return random.choice(candidates or fallback)


def format_caption(quote: Quote) -> str:
    """Build an Instagram caption for the post."""
    return (
        f'"{quote.text}"\n'
        f"— {quote.author}\n\n"
        "#quotes #dailyquotes #mindset #wisdom #reflection"
    )
