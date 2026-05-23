# Microsoft Edge Search Bot - Enhanced Version

## 🚀 New Features

### Automatic Keyword Fetching
- Fetches **100 trending topics** from Wikipedia API automatically
- Keywords are cached and auto-refresh every **18 hours**
- Random keyword selection for each search session
- **PC Mode**: Uses 34 random keywords
- **Mobile Mode**: Uses 24 random keywords

### GUI Application
- Easy-to-use graphical interface
- Real-time activity logs
- Individual profile controls (Default, Profile 1, Profile 2)
- Batch operations for all profiles
- Manual keyword update button

## 📦 Setup

1. **Run setup** (one time):
   ```
   setup.bat
   ```

2. **Launch the GUI**:
   ```
   run_gui.bat
   ```

## 🎮 GUI Features

### Individual Profile Controls
For each profile (Default, Profile 1, Profile 2):
- **PC + Mobile**: Runs PC search (34 keywords) then Mobile search (24 keywords)
- **PC Only**: Runs only PC search (34 keywords)
- **Mobile Only**: Runs only mobile search (24 keywords)

### Run All Profiles
- **Run All (PC + Mobile)**: Executes PC + Mobile for all 3 profiles sequentially
- **Run All (PC Only)**: Executes PC search for all 3 profiles
- **Run All (Mobile Only)**: Executes Mobile search for all 3 profiles

### Update Keywords Button
- Click "🔄 Update Keywords" to fetch fresh topics from Wikipedia
- Automatically updates if cache is older than 18 hours
- Shows keyword count and search limits

## 📁 Files

- `gui.py` - Main GUI application
- `edge_search_bot.py` - Core bot logic
- `keyword_fetcher.py` - Wikipedia API integration
- `check_profile.py` - Profile checker utility
- `words.txt` - Cached keywords (auto-generated)
- `search_cache.json` - Keyword cache with timestamp

## 🔧 Manual Operations

### Update Keywords Manually
```
update_keywords.bat
```

### Check Edge Profiles
```
check_profile.bat
```

### Run Bot via Command Line
```
.venv\Scripts\activate
python ms-edge-bot-main\edge_search_bot.py --profile "Default" --mobile
```

## 🎯 How It Works

1. **Keyword Fetching**:
   - Fetches trending articles from Wikipedia's "Most Read" API
   - Supplements with random Wikipedia articles
   - Falls back to curated tech topics if API fails
   - Saves to cache with timestamp

2. **Random Selection**:
   - Each search session randomly selects keywords
   - PC mode: 34 random keywords from the 100 available
   - Mobile mode: 24 random keywords from the 100 available
   - No duplicate searches in the same session

3. **Auto-Update**:
   - Checks cache age on GUI startup
   - Auto-updates if older than 18 hours
   - Manual update available via button

## 📊 Search Counts

- **Total Keywords**: 100 (fetched from Wikipedia)
- **PC Searches**: 34 random keywords per session
- **Mobile Searches**: 24 random keywords per session
- **Cache Duration**: 18 hours

## 🛠️ Troubleshooting

### Keywords Not Updating
- Click "🔄 Update Keywords" button in GUI
- Or run: `update_keywords.bat`
- Check internet connection

### Bot Not Finding Keywords
- Ensure `words.txt` exists in `ms-edge-bot-main` folder
- Run `update_keywords.bat` to regenerate

### Profile Issues
- Run `check_profile.bat` to verify which profile has Rewards signed in
- Use the correct profile name in GUI

## 📝 Notes

- Keywords are randomized for each search session
- Cache automatically refreshes every 18 hours
- All searches use human-like typing delays
- Supports headless mode (via command line)
- Logs all activity in real-time

## 🎉 Quick Start

1. Double-click `setup.bat`
2. Double-click `run_gui.bat`
3. Click any button to start searching!

The bot will automatically fetch fresh keywords from Wikipedia and start searching with random selections!
