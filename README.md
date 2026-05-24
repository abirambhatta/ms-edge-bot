# Microsoft Edge Search Automator

A GUI automation tool for running Microsoft Edge Rewards searches across multiple profiles.

## Requirements

- **Windows 10 or 11**
- **Python 3.11+** — if not installed, `setup.bat` will install it automatically

---

## Setup (One Time)

Just double-click:

```
setup.bat
```

This will:
1. Check if Python is installed — if not, it installs it automatically via Windows Package Manager (`winget`)
2. Create a virtual environment (`.venv`)
3. Install all required dependencies

If your system doesn't support `winget` (older Windows), it will display a direct link to download Python manually.

---

## Launch

```
run_gui.bat
```

---

## GUI Overview

### Left Panel — Run Controls

- **Run All (PC + Mobile / PC Only / Mobile Only)** — runs searches across all profiles in one click
- **Individual Profiles** — run searches per profile with three modes: Both, PC, Mobile
- **Remove** button on each profile card to instantly remove it from the list
- **Stop Run** button to cancel any running session
- **Status indicator** showing current state (Ready / Running / Stopped / etc.)

### Right Panel — Tabs

#### Activity Log
- Real-time log output from all running sessions
- **Clear** button to wipe the log

#### Settings
- **Global Settings**:
  - Wikipedia API Keywords — how many keywords to fetch (default: 100)
  - PC Searches per Profile — default PC count (default: 34)
  - Mobile Searches per Profile — default mobile count (default: 24)
  - All Save buttons ask for confirmation before applying
- **Per-Profile Settings**:
  - Override global defaults for individual profiles
  - Each profile can have its own PC and mobile search count

### Toolbar Buttons

| Button | Action |
|---|---|
| Close Edge | Force-close all Edge windows |
| Check Profiles | Open each Edge profile to verify Rewards login |
| Clear History | Reset search history for all profiles |
| Add Profile | Add a new Edge profile to the list |
| Update Keywords | Fetch fresh trending topics from Wikipedia |

---

## How It Works

1. **Keywords** are fetched from Wikipedia's "Most Read" API and cached in `search_cache.json`
2. The cache is automatically refreshed on startup if older than **18 hours**
3. Each search session randomly selects keywords from the pool
4. **Search history** is tracked per profile in `search_history.json` to prevent duplicate searches
5. Settings are saved to `settings.json` and persist across sessions

---

## Files

| File | Description |
|---|---|
| `gui.py` | Main GUI application |
| `edge_search_bot.py` | Core Selenium automation logic |
| `keyword_fetcher.py` | Wikipedia API integration |
| `settings.py` | Persistent settings manager |
| `search_history.py` | Per-profile search history tracker |
| `profile_manager.py` | Profile list management |
| `check_profile.py` | Profile checker utility |
| `words.txt` | Cached keywords (auto-generated) |
| `search_cache.json` | Keyword cache with timestamp |
| `settings.json` | User settings (auto-generated) |
| `search_history.json` | Search history per profile (auto-generated) |

---

## Default Settings

| Setting | Default |
|---|---|
| Total Keywords | 100 |
| PC Searches per Profile | 34 |
| Mobile Searches per Profile | 24 |
| Cache Duration | 18 hours |

---

## Troubleshooting

**Python not found after auto-install**
- Close `setup.bat` and run it again — the new window will pick up the updated PATH

**Keywords not updating**
- Click "Update Keywords" in the GUI toolbar
- Check your internet connection
- Or run `update_keywords.bat` manually

**Bot not launching / profile errors**
- Click "Close Edge" first to close all Edge windows
- Click "Check Profiles" to verify which profiles have Rewards signed in
- Make sure the profile name matches exactly (e.g. `Default`, `Profile 1`)

**Settings not saving**
- Ensure write permissions on the `ms-edge-bot-main` folder
- Check that `settings.json` is not open in another program

**Search history / duplicates**
- Click "Clear History" in the toolbar to reset all search history
- This allows re-searching the same keywords again

---

## Quick Start

1. Double-click `setup.bat` — Python and all dependencies will be installed automatically
2. Double-click `run_gui.bat` to open the app
3. (Optional) Go to the Settings tab to customize search counts
4. Click any run button to start searching
