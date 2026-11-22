# Edge Searches

A Windows desktop app that runs a daily quota of Bing searches in each of your Microsoft Edge profiles and shows how far each profile has got today.

> Automated searches are against the Microsoft Rewards terms. Accounts used with this tool can lose points or be suspended.

## Requirements

- Windows 10 or 11 with Microsoft Edge
- Python 3.11+ (`setup.bat` installs it with `winget` if it's missing)

## Setup and launch

| Step | Run |
|---|---|
| Once | `setup.bat` (creates `.venv` and installs dependencies) |
| Every time | `run_gui.bat` |

## Using the app

**Today** shows one row per profile with today's PC and mobile progress (for example `12 / 34`). Bars turn green when a profile hits its target.

- **Run** on a row, or **Run all profiles**, does only the searches still missing today. Pick *PC and mobile*, *PC only* or *Mobile only* first.
- **Stop** finishes the current search, then stops.
- **Check sign-in** opens each profile's Rewards page in the background and marks profiles that aren't signed in.
- **Refresh keywords** fetches new topics from Wikipedia. This also happens on launch when keywords are older than 18 hours.

Running a search or a sign-in check **closes every Edge window**: the app asks first if Edge is open.

**Settings** holds the daily targets (a default plus optional per-profile overrides), which Edge profiles to run, how many keywords to fetch, and a button to clear search history.

## Command line

```
python ms-edge-bot-main\edge_search_bot.py --profile "Profile 1" [--mobile] [--count N]
python ms-edge-bot-main\keyword_fetcher.py [count]      # refresh keywords
python ms-edge-bot-main\edge.py                         # list Edge profiles
python ms-edge-bot-main\edge.py --update-driver         # same as update_driver.bat
```

`--profile` takes Edge's folder name (`Default`, `Profile 1`, ...), which can differ from the name Edge shows. `python edge.py` prints both.

## How it works

1. Edge is closed, and the profile's sign-in files (cookies, saved logins, preferences) are copied to a temporary folder. WebDriver can't use a profile Edge has locked.
2. Edge starts on that copy under `msedgedriver.exe`, types each keyword into Bing with human-like delays (3 s between searches), and waits for results.
3. Only successful searches are recorded. Each profile skips keywords it has searched before.
4. The temporary copy, which contains login data, is deleted when the browser closes.

`msedgedriver.exe` must match Edge's major version. The app checks on every run and downloads a matching driver from Microsoft when Edge has updated.

## Files

| File | Purpose |
|---|---|
| `ms-edge-bot-main/gui.py` | Desktop app |
| `ms-edge-bot-main/edge_search_bot.py` | Search runner and command line |
| `ms-edge-bot-main/edge.py` | Edge profiles, driver updates, browser launch |
| `ms-edge-bot-main/keyword_fetcher.py` | Wikipedia keywords (`search_cache.json`) |
| `ms-edge-bot-main/settings.py` | Targets and profile list (`settings.json`) |
| `ms-edge-bot-main/search_history.py` | Searched keywords and daily counts (`search_history.json`) |
| `ms-edge-bot-main/tests/` | Unit tests: `python -m pytest ms-edge-bot-main\tests` |

## Troubleshooting

| Problem | Fix |
|---|---|
| A profile shows "Not signed in to Rewards" | Open Edge in that profile, sign in at rewards.bing.com, then **Check sign-in** again |
| "Profile not found in Edge" | The folder in Settings no longer exists. Remove it and add the right one |
| Driver errors after an Edge update | Run `update_driver.bat` |
| "Every keyword has been searched" | **Refresh keywords**, or **Clear search history** in Settings |
