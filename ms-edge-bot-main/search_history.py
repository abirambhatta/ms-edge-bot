"""Which keywords each profile has already searched, and how many searches it did per day.

Persisted to search_history.json:
    {"Profile 1": {"searched": [...], "last_updated": "...", "daily": {"2026-11-22": {"pc": 3, "mobile": 0}}}}
"""

from __future__ import annotations

import json
import threading
from datetime import date, datetime, timedelta
from pathlib import Path

DAYS_KEPT = 14


class SearchHistory:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.Lock()  # the GUI reads while a worker thread writes
        try:
            self._data: dict = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._data = {}

    def _profile(self, profile: str) -> dict:
        entry = self._data.setdefault(profile, {"searched": [], "last_updated": None})
        entry.setdefault("daily", {})
        return entry

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def unsearched(self, profile: str, keywords: list[str]) -> list[str]:
        with self._lock:
            done = set(self._profile(profile)["searched"])
        return [k for k in keywords if k not in done]

    def record(self, profile: str, keyword: str, mobile: bool) -> None:
        """Record one successful search."""
        with self._lock:
            entry = self._profile(profile)
            if keyword not in entry["searched"]:
                entry["searched"].append(keyword)
            today = entry["daily"].setdefault(date.today().isoformat(), {"pc": 0, "mobile": 0})
            today["mobile" if mobile else "pc"] += 1
            entry["last_updated"] = datetime.now().isoformat(timespec="seconds")
            cutoff = (date.today() - timedelta(days=DAYS_KEPT)).isoformat()
            entry["daily"] = {d: c for d, c in entry["daily"].items() if d >= cutoff}
            self._save()

    def done_today(self, profile: str, mobile: bool) -> int:
        with self._lock:
            day = self._data.get(profile, {}).get("daily", {}).get(date.today().isoformat(), {})
            return day.get("mobile" if mobile else "pc", 0)

    def total_searched(self, profile: str) -> int:
        with self._lock:
            return len(self._data.get(profile, {}).get("searched", []))

    def clear(self) -> None:
        with self._lock:
            self._data = {}
            self._save()
