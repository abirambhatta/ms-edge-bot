"""Search keywords: today's most-read Wikipedia articles, topped up with random articles.

Stored in search_cache.json as {"timestamp": iso, "keywords": [...]}.
Run directly to refresh:  python keyword_fetcher.py [count]
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import requests

Log = Callable[[str], None]

MAX_AGE = timedelta(hours=18)
HEADERS = {"User-Agent": "EdgeSearchRunner/2.0 (personal use; python-requests)"}
FEATURED_URL = "https://en.wikipedia.org/api/rest_v1/feed/featured/{:%Y/%m/%d}"
API_URL = "https://en.wikipedia.org/w/api.php"

FALLBACK = [
    "climate change", "renewable energy", "space exploration", "quantum computing",
    "electric vehicles", "james webb telescope", "black holes", "nuclear fusion",
    "coral reefs", "marine biology", "volcanoes", "ancient rome", "solar eclipse",
    "honey bees", "deep sea creatures", "northern lights", "mount everest",
    "great barrier reef", "amazon rainforest", "sahara desert", "jazz history",
    "renaissance art", "origami", "sourdough bread", "chess openings",
    "olympic games", "world cup", "photosynthesis", "plate tectonics", "dinosaurs",
]


def _most_read(count: int) -> list[str]:
    # Yesterday (UTC): the most-read list for a day is only complete once that day is over.
    day = datetime.now(timezone.utc) - timedelta(days=1)
    resp = requests.get(FEATURED_URL.format(day), headers=HEADERS, timeout=10)
    resp.raise_for_status()
    articles = resp.json().get("mostread", {}).get("articles", [])
    return [a.get("normalizedtitle") or a.get("title", "") for a in articles][:count]


def _random_titles(count: int) -> list[str]:
    resp = requests.get(API_URL, headers=HEADERS, timeout=10, params={
        "action": "query", "format": "json", "list": "random",
        "rnnamespace": 0, "rnlimit": min(count, 500),
    })
    resp.raise_for_status()
    return [a["title"] for a in resp.json()["query"]["random"]]


def fetch_keywords(count: int, log: Log = print) -> list[str]:
    """Fetch `count` distinct keywords, falling back to a built-in list if Wikipedia is unreachable."""
    keywords: list[str] = []
    try:
        keywords = _most_read(count)
        if len(keywords) < count:
            keywords += _random_titles(count - len(keywords))
    except (requests.RequestException, ValueError, KeyError) as e:
        log(f"Couldn't reach Wikipedia ({e}); using built-in keywords.")
    keywords = [k for k in dict.fromkeys(keywords) if len(k) > 2]
    if len(keywords) < count:
        extra = [k for k in FALLBACK if k not in keywords]
        random.shuffle(extra)
        keywords += extra[: count - len(keywords)]
    return keywords[:count]


class KeywordStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.keywords: list[str] = []
        self.fetched_at: datetime | None = None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.keywords = data["keywords"]
            self.fetched_at = datetime.fromisoformat(data["timestamp"]).astimezone()
        except (OSError, ValueError, KeyError):
            pass

    @property
    def stale(self) -> bool:
        return self.fetched_at is None or datetime.now().astimezone() - self.fetched_at > MAX_AGE

    def refresh(self, count: int, log: Log = print) -> list[str]:
        self.keywords = fetch_keywords(count, log)
        self.fetched_at = datetime.now().astimezone()
        self.path.write_text(json.dumps(
            {"timestamp": self.fetched_at.isoformat(timespec="seconds"), "keywords": self.keywords},
            indent=2, ensure_ascii=False), encoding="utf-8")
        return self.keywords


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    store = KeywordStore(Path(__file__).with_name("search_cache.json"))
    print(f"Saved {len(store.refresh(n))} keywords to {store.path}")
