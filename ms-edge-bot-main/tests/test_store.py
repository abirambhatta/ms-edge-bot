import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from search_history import SearchHistory  # noqa: E402
from settings import Settings  # noqa: E402


def test_override_falls_back_to_default_and_is_dropped_when_equal(tmp_path):
    s = Settings(tmp_path / "settings.json")
    assert s.target("P1", mobile=False) == 34
    s.set_override("P1", False, 10)
    assert s.target("P1", mobile=False) == 10
    assert s.target("P1", mobile=True) == 24
    s.set_override("P1", False, 34)  # same as default -> no override stored
    assert s.data["profile_settings"] == {}


def test_profiles_json_is_migrated_into_settings(tmp_path):
    (tmp_path / "profiles.json").write_text(json.dumps({"profiles": ["Default", "Profile 2"]}))
    (tmp_path / "settings.json").write_text(json.dumps({"global_pc_count": 30}))
    s = Settings(tmp_path / "settings.json")
    assert s.profiles == ["Default", "Profile 2"]
    assert s.default_count(False) == 30
    assert not (tmp_path / "profiles.json").exists()
    assert Settings(tmp_path / "settings.json").profiles == ["Default", "Profile 2"]


def test_remove_profile_drops_its_overrides(tmp_path):
    s = Settings(tmp_path / "settings.json")
    s.add_profile("P1")
    s.set_override("P1", True, 5)
    s.remove_profile("P1")
    assert "P1" not in s.profiles and "P1" not in s.data["profile_settings"]


def test_record_counts_today_by_mode_and_persists(tmp_path):
    path = tmp_path / "h.json"
    h = SearchHistory(path)
    h.record("P1", "alpha", mobile=False)
    h.record("P1", "beta", mobile=True)
    h.record("P1", "gamma", mobile=False)
    reloaded = SearchHistory(path)
    assert reloaded.done_today("P1", mobile=False) == 2
    assert reloaded.done_today("P1", mobile=True) == 1
    assert reloaded.unsearched("P1", ["alpha", "delta"]) == ["delta"]
    assert reloaded.unsearched("P2", ["alpha"]) == ["alpha"]


def test_old_history_without_daily_counts_still_loads(tmp_path):
    path = tmp_path / "h.json"
    path.write_text(json.dumps({"P1": {"searched": ["x"], "last_updated": "2026-01-01T00:00:00"}}))
    h = SearchHistory(path)
    assert h.done_today("P1", mobile=False) == 0
    assert h.unsearched("P1", ["x", "y"]) == ["y"]
    h.record("P1", "y", mobile=False)
    assert h.done_today("P1", mobile=False) == 1


def test_daily_counts_older_than_two_weeks_are_pruned(tmp_path):
    path = tmp_path / "h.json"
    old = (date.today() - timedelta(days=30)).isoformat()
    path.write_text(json.dumps({"P1": {"searched": [], "last_updated": None,
                                       "daily": {old: {"pc": 5, "mobile": 0}}}}))
    h = SearchHistory(path)
    h.record("P1", "z", mobile=False)
    assert old not in json.loads(path.read_text())["P1"]["daily"]
