"""Run Bing searches in an Edge profile until it reaches today's target.

Command line:  python edge_search_bot.py --profile "Profile 1" [--mobile] [--count N]
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import edge
from keyword_fetcher import KeywordStore
from search_history import SearchHistory
from settings import Settings

HERE = Path(__file__).resolve().parent
DELAY_SECONDS = 3


@dataclass
class Progress:
    profile: str
    mobile: bool
    done: int      # searches finished in this run
    planned: int   # searches this run will attempt
    keyword: str


def search(driver, query: str) -> bool:
    """Type `query` into Bing like a person would and wait for results. False on failure."""
    try:
        driver.get("https://www.bing.com")
        wait = WebDriverWait(driver, 10)
        box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        box.clear()
        for ch in query:
            box.send_keys(ch)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.3, 0.7))
        box.submit()
        wait.until(EC.presence_of_element_located((By.ID, "b_results")))
        return True
    except WebDriverException:
        return False


def run_searches(profile: str, mobile: bool, keywords: list[str], history: SearchHistory,
                 count: int, label: str | None = None, log: edge.Log = print,
                 on_progress: Callable[[Progress], None] = lambda p: None,
                 should_stop: Callable[[], bool] = lambda: False) -> int:
    """Search up to `count` keywords this profile hasn't searched yet. Returns successful searches.

    `label` is how the profile is named in log lines (defaults to its folder name).
    """
    mode = "mobile" if mobile else "PC"
    name = label or profile
    fresh = history.unsearched(profile, keywords)
    if count <= 0:
        log(f"{name}: {mode} searches already done for today.")
        return 0
    if not fresh:
        log(f"{name}: every keyword has been searched. Refresh keywords or clear history.")
        return 0
    picks = random.sample(fresh, min(count, len(fresh)))
    if len(picks) < count:
        log(f"{name}: only {len(picks)} unsearched keywords left (wanted {count}).")

    log(f"{name}: starting {len(picks)} {mode} searches.")
    done = 0
    with edge.open_browser(profile, mobile=mobile, log=log) as driver:
        for i, keyword in enumerate(picks):
            if should_stop():
                break
            on_progress(Progress(profile, mobile, done, len(picks), keyword))
            if search(driver, keyword):
                history.record(profile, keyword, mobile)
                done += 1
                log(f"  {i + 1}/{len(picks)}  {keyword}")
            else:
                log(f"  {i + 1}/{len(picks)}  {keyword}  (failed, will retry another day)")
            if i < len(picks) - 1:
                for _ in range(DELAY_SECONDS * 10):
                    if should_stop():
                        break
                    time.sleep(0.1)
    on_progress(Progress(profile, mobile, done, len(picks), ""))
    log(f"{name}: {done} of {len(picks)} {mode} searches done.")
    return done


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run Bing searches in one Edge profile.")
    parser.add_argument("--profile", "-p", default="Default", help='Edge profile folder, e.g. "Profile 1"')
    parser.add_argument("--mobile", "-m", action="store_true", help="search as a mobile browser")
    parser.add_argument("--count", "-n", type=int, help="number of searches (default: what's left for today)")
    args = parser.parse_args()

    settings = Settings(HERE / "settings.json")
    history = SearchHistory(HERE / "search_history.json")
    store = KeywordStore(HERE / "search_cache.json")
    if store.stale or not store.keywords:
        store.refresh(settings.keyword_count)

    count = args.count
    if count is None:
        count = settings.target(args.profile, args.mobile) - history.done_today(args.profile, args.mobile)
    run_searches(args.profile, args.mobile, store.keywords, history, count)


if __name__ == "__main__":
    main()
