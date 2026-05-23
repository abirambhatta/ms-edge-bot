# Microsoft Edge Search Bot

An automated bot that performs random word searches in Microsoft Edge browser using Selenium WebDriver with your Microsoft profile.

## Features

- Performs automated searches on Bing using Microsoft Edge
- Uses your Microsoft profile (maintains Rewards login)
- Random word selection from built-in or custom word lists
- Configurable delays between searches to simulate human behavior
- Progress tracking and detailed logging
- Headless mode support for background operation
- Easy configuration and customization

## Prerequisites

- Python 3.7 or higher
- Microsoft Edge browser installed
- Edge driver at `/usr/local/bin/msedgedriver/msedgedriver`

## Installation

1. **Navigate to the project directory:**

   ```bash
   cd /home/aryan/Desktop/project/ms-edge-bot
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the bot with default settings (5 searches):

```bash
.venv/bin/python edge_search_bot.py
```

Or simply:

```bash
python3 edge_search_bot.py
```

### Configuration

Edit the configuration variables in the `main()` function of `edge_search_bot.py` (around line 218):

```python
NUM_SEARCHES = 5              # Number of searches to perform
HEADLESS_MODE = False         # Set to True to run without GUI
DELAY_BETWEEN_SEARCHES = 3    # Seconds between searches
PROFILE_NAME = 'Default'      # Change to 'Profile 1' if needed
```

### Using Custom Word Lists

The bot comes with a `words.txt` file containing 45 tech-related search terms. You can customize it with one search term per line:

```text
artificial intelligence
machine learning
web development
data science
cloud computing
```

The bot will automatically load and use this custom word list if the file exists.

## Project Structure

```
ms-edge-bot/
├── edge_search_bot.py    # Main bot script
├── requirements.txt      # Python dependencies
├── words.txt            # Custom word list (45 tech terms)
└── README.md           # This file
```

## How It Works

1. **Profile Loading**: Loads your Microsoft Edge profile with saved login credentials
2. **Initialization**: Sets up Edge WebDriver with your profile settings
3. **Navigation**: Opens Bing.com in the Edge browser
4. **Search**: Enters a random word from the list and performs the search
5. **Wait**: Simulates human behavior with random delays (2-5 seconds)
6. **Repeat**: Continues for the specified number of searches
7. **Cleanup**: Closes the browser and releases resources

## Example Output

```
============================================================
Microsoft Edge Random Search Bot
============================================================
→ Using default word list
✓ Microsoft Edge browser initialized successfully!

============================================================
Starting Microsoft Edge Search Bot
Number of searches: 5
============================================================

--- Search 1/5 ---
→ Navigated to Bing.com
→ Searching for: 'artificial intelligence'
✓ Search #1 completed successfully!
→ Waiting 3.4 seconds before next action...

--- Search 2/5 ---
→ Navigated to Bing.com
→ Searching for: 'cloud computing'
✓ Search #2 completed successfully!
...

============================================================
✓ Bot completed successfully!
Total searches performed: 5
============================================================
```

## Customization Options

Edit these settings in `edge_search_bot.py` (lines 221-225):

```python
NUM_SEARCHES = 10              # Change number of searches
HEADLESS_MODE = True           # Run without browser window
DELAY_BETWEEN_SEARCHES = 5     # Adjust delay between searches
PROFILE_NAME = 'Profile 1'     # Change Edge profile
```

## Troubleshooting 🔍

### Not Signed Into Microsoft Rewards

If the bot opens Edge but you're not signed into Microsoft Rewards:

1. Check which Edge profile has your Rewards account signed in
2. Update `PROFILE_NAME` variable in code (line 225)
3. Common profiles: `'Default'`, `'Profile 1'`, `'Profile 2'`

### Browser Not Opening

- Verify Edge is installed: `microsoft-edge --version`
- Check driver exists: `ls -la /usr/local/bin/msedgedriver/msedgedriver`
- Make driver executable: `chmod +x /usr/local/bin/msedgedriver/msedgedriver`

## Notes

- Uses random delays (2-5 seconds) to simulate human behavior
- Loads your Microsoft Edge profile automatically
- Searches performed on Bing.com
- Press `Ctrl+C` to stop the bot at any time
