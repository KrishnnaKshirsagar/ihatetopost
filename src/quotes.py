"""Quote fetching, deduplication, and caption formatting."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import requests

from src.config import HISTORY_FILE, QUOTES_BANK_FILE

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


def load_curated_quotes(quotes_path: Path = QUOTES_BANK_FILE) -> list[Quote]:
    """Load curated quotes from data/quotes.json if present."""
    if not quotes_path.exists():
        return []
    with quotes_path.open("r", encoding="utf-8") as fh:
        items = json.load(fh)
    quotes: list[Quote] = []
    for item in items:
        text = str(item.get("text", "")).strip()
        author = str(item.get("author", "")).strip()
        if text:
            quotes.append(Quote(text=text, author=author))
    return quotes


def pick_next_quote(
    history_path: Path = HISTORY_FILE,
    quotes_path: Path = QUOTES_BANK_FILE,
) -> Quote:
    """Pick an unposted quote, mixing curated quotes (data/quotes.json) with ZenQuotes."""
    history = load_history(history_path)
    seen = set(history["posted"])

    unseen_curated = [q for q in load_curated_quotes(quotes_path) if q.digest not in seen]

    api_candidates: list[Quote] = []
    try:
        api_candidates = fetch_zenquotes()
    except Exception:
        api_candidates = []
    unseen_api = [q for q in api_candidates if q.digest not in seen]

    if unseen_curated and unseen_api:
        return random.choice(random.choice([unseen_curated, unseen_api]))
    if unseen_curated:
        return random.choice(unseen_curated)
    if unseen_api:
        return random.choice(unseen_api)

    fallback = [Quote(text=t, author=a) for t, a in FALLBACK_QUOTES]
    unseen_fallback = [q for q in fallback if q.digest not in seen]
    if unseen_fallback:
        return random.choice(unseen_fallback)

    return random.choice(api_candidates or load_curated_quotes(quotes_path) or fallback)


def format_caption(quote: Quote) -> str:
    """Build an Instagram caption for the post."""
    author = quote.author.strip()
    tags = "#quotes #dailyquotes #mindset #wisdom #reflection"
    if author and author.lower() != "unknown":
        return f'"{quote.text}"\n— {author}\n\n{tags}'
    return f'"{quote.text}"\n\n{tags}'
