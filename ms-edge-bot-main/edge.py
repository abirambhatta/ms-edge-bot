"""Everything that touches Microsoft Edge itself: profiles, the driver, and launching a browser.

Run directly to make msedgedriver.exe match the installed Edge:  python edge.py --update-driver
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import time
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

import requests
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

Log = Callable[[str], None]

REPO_ROOT = Path(__file__).resolve().parent.parent
DRIVER_PATH = REPO_ROOT / "msedgedriver.exe"
DRIVER_HOST = "https://msedgedriver.microsoft.com"

# Only the files the bot needs to stay signed in. Copying them into a throwaway
# user-data dir avoids fighting Edge's lock on the real one.
PROFILE_FILES = ("Login Data", "Preferences", "Secure Preferences", "Web Data",
                 "Cookies", "Network/Cookies")  # Edge 96+ keeps cookies under Network/

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def user_data_dir() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Edge" / "User Data"


# ── Profiles ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EdgeProfile:
    folder: str        # what Edge calls it on disk, e.g. "Profile 1"
    name: str          # what the user sees in Edge's profile menu
    signed_in: bool    # a Microsoft account is attached to the profile


def list_profiles() -> list[EdgeProfile]:
    """Profiles Edge knows about, read from its Local State file."""
    try:
        state = json.loads((user_data_dir() / "Local State").read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError):
        return []
    cache = state.get("profile", {}).get("info_cache", {})
    return [
        EdgeProfile(folder, info.get("name") or folder, bool(info.get("user_name")))
        for folder, info in sorted(cache.items())
    ]


# ── Edge processes ───────────────────────────────────────────────────────────

def edge_is_running() -> bool:
    out = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq msedge.exe", "/NH"],
        capture_output=True, text=True, creationflags=_NO_WINDOW,
    ).stdout
    return "msedge.exe" in out


def close_edge(timeout: float = 6.0) -> None:
    """Force-close every Edge window and any leftover driver, then wait until they are gone."""
    for image in ("msedge.exe", "msedgedriver.exe"):
        subprocess.run(["taskkill", "/F", "/IM", image],
                       capture_output=True, creationflags=_NO_WINDOW)
    deadline = time.monotonic() + timeout
    while edge_is_running() and time.monotonic() < deadline:
        time.sleep(0.3)


# ── Driver ───────────────────────────────────────────────────────────────────

def installed_edge_version() -> str | None:
    out = subprocess.run(
        ["reg", "query", r"HKCU\Software\Microsoft\Edge\BLBeacon", "/v", "version"],
        capture_output=True, text=True, creationflags=_NO_WINDOW,
    ).stdout
    for line in out.splitlines():
        if "version" in line and "REG_SZ" in line:
            return line.split()[-1]
    return None


def driver_version(path: Path = DRIVER_PATH) -> str | None:
    if not path.exists():
        return None
    out = subprocess.run([str(path), "--version"], capture_output=True, text=True,
                         creationflags=_NO_WINDOW).stdout
    # "Microsoft Edge WebDriver 158.0.4370.33 (hash)"
    parts = out.split()
    return parts[3] if len(parts) > 3 else None


def major(version: str | None) -> str | None:
    return version.split(".")[0] if version else None


def ensure_driver(log: Log = print) -> Path:
    """Make msedgedriver.exe match the installed Edge, downloading from Microsoft if needed."""
    edge = installed_edge_version()
    current = driver_version()
    if edge is None:
        log("Couldn't read the installed Edge version; using the driver as is.")
        return DRIVER_PATH
    if major(current) == major(edge):
        return DRIVER_PATH

    log(f"Driver {current or 'missing'} doesn't match Edge {edge}. Downloading a matching driver.")
    latest = requests.get(f"{DRIVER_HOST}/LATEST_RELEASE_{major(edge)}_WINDOWS", timeout=15)
    latest.raise_for_status()
    version = latest.content.decode("utf-16" if latest.content[:2] in (b"\xff\xfe", b"\xfe\xff")
                                    else "utf-8").strip()
    archive = requests.get(f"{DRIVER_HOST}/{version}/edgedriver_win64.zip", timeout=120)
    archive.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(archive.content)) as zf:
        DRIVER_PATH.write_bytes(zf.read("msedgedriver.exe"))
    log(f"Driver updated to {version}.")
    return DRIVER_PATH


# ── Browser ──────────────────────────────────────────────────────────────────

def _copy_profile(profile: str, dest: Path) -> None:
    src_root = user_data_dir()
    src, dst = src_root / profile, dest / profile
    for name in PROFILE_FILES:
        if (src / name).exists():
            (dst / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src / name, dst / name)
    # Local State holds the key Edge needs to decrypt the copied cookies.
    if (src_root / "Local State").exists():
        shutil.copy2(src_root / "Local State", dest / "Local State")


def _mobile_user_agent() -> str:
    v = f"{major(installed_edge_version()) or '158'}.0.0.0"
    return (f"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{v} Mobile Safari/537.36 EdgA/{v}")


@contextmanager
def open_browser(profile: str, mobile: bool = False, headless: bool = False,
                 log: Log = print) -> Iterator[webdriver.Edge]:
    """Close Edge, start a copy of `profile` under WebDriver, and clean everything up afterwards.

    The copy contains the profile's cookies and saved logins, so it is always deleted on exit.
    """
    driver_path = ensure_driver(log)
    close_edge()
    workdir = Path(tempfile.mkdtemp(prefix="edge_search_"))
    driver = None
    try:
        _copy_profile(profile, workdir)
        options = Options()
        options.add_argument(f"--user-data-dir={workdir}")
        options.add_argument(f"--profile-directory={profile}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        if mobile:
            options.add_argument(f"--user-agent={_mobile_user_agent()}")
            options.add_argument("--window-size=412,915")
        if headless:
            options.add_argument("--headless=new")
        driver = webdriver.Edge(service=Service(str(driver_path)), options=options)
        yield driver
    finally:
        if driver is not None:
            driver.quit()
        shutil.rmtree(workdir, ignore_errors=True)


def rewards_signed_in(driver: webdriver.Edge) -> bool:
    """True when the Rewards dashboard opens without bouncing to a Microsoft login page."""
    driver.get("https://rewards.bing.com/")
    time.sleep(5)
    host = driver.current_url.split("/")[2]
    return host.endswith("rewards.bing.com")


if __name__ == "__main__":
    import sys
    if "--update-driver" in sys.argv:
        ensure_driver()
        print(f"Edge {installed_edge_version()}, driver {driver_version()}")
    else:
        for p in list_profiles():
            print(f"{p.folder:12} {p.name:20} {'signed in' if p.signed_in else 'no account'}")
