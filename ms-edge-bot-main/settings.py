"""User settings, persisted to settings.json: search counts and which Edge profiles to run."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {
    "api_keyword_count": 100,
    "global_pc_count": 34,
    "global_mobile_count": 24,
    "profiles": ["Default"],
    "profile_settings": {},  # {"Profile 1": {"pc_count": 30, "mobile_count": 20}}
}


class Settings:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = {**DEFAULTS, **self._load()}
        self._migrate_profiles_file()

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _migrate_profiles_file(self) -> None:
        """Older versions kept the profile list in a separate profiles.json."""
        legacy = self.path.with_name("profiles.json")
        if "profiles" in self._load() or not legacy.exists():
            return
        try:
            self.data["profiles"] = json.loads(legacy.read_text(encoding="utf-8"))["profiles"]
            self.save()
            legacy.unlink()
        except (OSError, ValueError, KeyError):
            pass

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    # ── Keywords ──
    @property
    def keyword_count(self) -> int:
        return self.data["api_keyword_count"]

    @keyword_count.setter
    def keyword_count(self, n: int) -> None:
        self.data["api_keyword_count"] = n

    # ── Search counts ──
    def default_count(self, mobile: bool) -> int:
        return self.data["global_mobile_count" if mobile else "global_pc_count"]

    def set_default_count(self, mobile: bool, n: int) -> None:
        self.data["global_mobile_count" if mobile else "global_pc_count"] = n

    def override(self, profile: str, mobile: bool) -> int | None:
        key = "mobile_count" if mobile else "pc_count"
        return self.data["profile_settings"].get(profile, {}).get(key)

    def set_override(self, profile: str, mobile: bool, n: int | None) -> None:
        """Set a per-profile count; None (or the default value) removes the override."""
        key = "mobile_count" if mobile else "pc_count"
        overrides = self.data["profile_settings"].setdefault(profile, {})
        if n is None or n == self.default_count(mobile):
            overrides.pop(key, None)
        else:
            overrides[key] = n
        if not overrides:
            del self.data["profile_settings"][profile]

    def target(self, profile: str, mobile: bool) -> int:
        """How many searches `profile` should do per day in this mode."""
        o = self.override(profile, mobile)
        return self.default_count(mobile) if o is None else o

    # ── Profiles ──
    @property
    def profiles(self) -> list[str]:
        return list(self.data["profiles"])

    def add_profile(self, folder: str) -> None:
        if folder not in self.data["profiles"]:
            self.data["profiles"].append(folder)

    def remove_profile(self, folder: str) -> None:
        if folder in self.data["profiles"]:
            self.data["profiles"].remove(folder)
        self.data["profile_settings"].pop(folder, None)
