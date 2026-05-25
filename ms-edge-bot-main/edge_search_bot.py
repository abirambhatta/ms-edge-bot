"""
Microsoft Edge Bot - Word Search Automation
This bot opens Microsoft Edge browser and performs word searches.
"""

import time
import random
import os
import argparse
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from search_history import SearchHistoryTracker
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from settings import SettingsManager


class EdgeSearchBot:
    """Microsoft Edge automation bot for performing random word searches."""
    
    def __init__(self, headless=False, profile_name='Default', mobile=False, stop_callback=None):
        """
        Initialize the Edge bot.
        
        Args:
            headless (bool): Run browser in headless mode if True
            profile_name (str): Edge profile to use ('Default', 'Profile 1', etc.)
            mobile (bool): Run in mobile mode if True
            stop_callback (callable): Function to check if bot should stop
        """
        self.driver = None
        self.headless = headless
        self.profile_name = profile_name
        self.mobile = mobile
        self.search_count = 0
        self.stop_callback = stop_callback
        
        # Initialize search history tracker
        script_dir = os.path.dirname(os.path.abspath(__file__))
        history_file = os.path.join(script_dir, 'search_history.json')
        self.history_tracker = SearchHistoryTracker(history_file)
        
        # Initialize settings manager
        settings_file = os.path.join(script_dir, 'settings.json')
        self.settings = SettingsManager(settings_file)
        
    def setup_driver(self):
        """Set up and configure the Edge WebDriver."""
        try:
            edge_options = Options()
            
            # Windows Edge user data directory
            user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Microsoft', 'Edge', 'User Data')
            edge_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            # Use the specified profile
            edge_options.add_argument(f'--profile-directory={self.profile_name}')
            print(f"→ Using profile: {self.profile_name}")
            
            # Mobile mode - simulate mobile browser
            if self.mobile:
                mobile_user_agent = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36 EdgA/131.0.0.0'
                edge_options.add_argument(f'--user-agent={mobile_user_agent}')
                edge_options.add_argument('--window-size=412,915')  # Mobile screen size
                print("→ Running in mobile mode")
            
            # Important: Disable automation detection to maintain login
            edge_options.add_argument('--disable-web-security')
            edge_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            edge_options.add_argument('--disable-site-isolation-trials')
            
            if self.headless:
                edge_options.add_argument('--headless')
                edge_options.add_argument('--disable-gpu')
            
            # Additional options for better stability
            edge_options.add_argument('--disable-blink-features=AutomationControlled')
            edge_options.add_argument('--disable-dev-shm-usage')
            edge_options.add_argument('--no-sandbox')
            edge_options.add_argument('--remote-debugging-port=9222')
            edge_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
            edge_options.add_experimental_option('useAutomationExtension', False)
            
            print("→ Setting up Edge driver...")
            print("→ Loading Microsoft profile...")
            
            # Try multiple ways to initialize the driver to prevent network/offline issues
            self.driver = None
            
            # Method 1: Try local msedgedriver.exe first if it exists (offline friendly)
            local_driver_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'msedgedriver.exe')
            
            if os.path.exists(local_driver_path):
                try:
                    service = Service(local_driver_path)
                    self.driver = webdriver.Edge(service=service, options=edge_options)
                except Exception:
                    pass
            
            # Method 2: Try webdriver_manager
            if self.driver is None:
                try:
                    service = Service(EdgeChromiumDriverManager().install())
                    self.driver = webdriver.Edge(service=service, options=edge_options)
                except Exception as e:
                    if "offline" in str(e).lower() or "reach host" in str(e).lower():
                        # Fallback to native Selenium Manager
                        self.driver = webdriver.Edge(options=edge_options)
                    else:
                        raise e
            
            print("✓ Microsoft Edge browser initialized successfully!")
            return True
            
        except Exception as e:
            print(f"✗ Error setting up Edge driver: {e}")
            return False
    
    def perform_search(self, search_query):
        """
        Perform a search on Bing using Microsoft Edge.
        
        Args:
            search_query (str): The search term to look up
        """
        try:
            # Navigate to Bing
            self.driver.get('https://www.bing.com')
            print(f"→ Navigated to Bing.com")
            
            # Wait for search box to be present
            wait = WebDriverWait(self.driver, 10)
            search_box = wait.until(
                EC.presence_of_element_located((By.NAME, 'q'))
            )
            
            # Clear search box
            search_box.clear()
            
            # Type character by character with random delays (human-like typing)
            for char in search_query:
                search_box.send_keys(char)
                # Random delay between 0.05 and 0.15 seconds per character
                time.sleep(random.uniform(0.05, 0.15))
            
            print(f"→ Searching for: '{search_query}'")
            
            # Small pause before pressing Enter (simulate reading what was typed)
            time.sleep(random.uniform(0.3, 0.7))
            
            # Submit the search
            search_box.send_keys(Keys.RETURN)
            
            # Wait for results to load
            wait.until(EC.presence_of_element_located((By.ID, 'b_results')))
            
            self.search_count += 1
            print(f"✓ Search #{self.search_count} completed successfully!")
            
        except Exception as e:
            print(f"✗ Error performing search: {e}")
    
    def run(self, word_list, delay_between_searches=3, pc_count=None, mobile_count=None):
        """
        Run the bot to perform searches for random words from the list.
        
        Args:
            word_list (list): Word list to search (required)
            delay_between_searches (int): Delay in seconds between searches
            pc_count (int): Number of searches for PC mode (default: from settings)
            mobile_count (int): Number of searches for mobile mode (default: from settings)
        """
        if not self.setup_driver():
            print("✗ Failed to initialize browser. Exiting...")
            return
        
        if not word_list:
            print("✗ Error: No words to search. Please add words to words.txt file.")
            return
        
        # Use settings if counts not provided
        if pc_count is None:
            pc_count = self.settings.get_profile_pc_count(self.profile_name)
        if mobile_count is None:
            mobile_count = self.settings.get_profile_mobile_count(self.profile_name)
        
        # Filter out already searched keywords for this profile
        unsearched_keywords = self.history_tracker.filter_unsearched_keywords(self.profile_name, word_list)
        
        if not unsearched_keywords:
            print(f"⚠ All keywords have been searched for profile '{self.profile_name}'!")
            print(f"→ Total keywords available: {len(word_list)}")
            print(f"→ Already searched: {len(word_list)}")
            print(f"→ Consider updating keywords or clearing search history.")
            self.cleanup()
            return
        
        # Determine how many searches to perform based on mode
        if self.mobile:
            search_count = mobile_count
        else:
            search_count = pc_count
        
        # Get random selection from unsearched keywords
        import random
        if len(unsearched_keywords) <= search_count:
            selected_words = unsearched_keywords.copy()
            random.shuffle(selected_words)
            print(f"⚠ Only {len(selected_words)} unsearched keywords available (need {search_count})")
        else:
            selected_words = random.sample(unsearched_keywords, search_count)
        
        try:
            print(f"\n{'='*60}")
            print(f"Starting Microsoft Edge Search Bot")
            print(f"Profile: {self.profile_name}")
            print(f"Mode: {'Mobile' if self.mobile else 'PC'}")
            print(f"Total keywords available: {len(word_list)}")
            print(f"Already searched: {len(word_list) - len(unsearched_keywords)}")
            print(f"Unsearched keywords: {len(unsearched_keywords)}")
            print(f"Searching: {len(selected_words)} keywords")
            print(f"{'='*60}\n")
            
            # Loop through selected words
            for i, search_word in enumerate(selected_words):
                # Check if stop was requested
                if self.stop_callback and self.stop_callback():
                    print("\n⏹️ Stop requested by user")
                    break
                
                print(f"\n--- Search {i+1}/{len(selected_words)} ---")
                self.perform_search(search_word)
                
                # Mark as searched
                self.history_tracker.add_searched_keyword(self.profile_name, search_word)
                
                if i < len(selected_words) - 1:  # Don't delay after the last search
                    # Check stop during delay too
                    for _ in range(delay_between_searches):
                        if self.stop_callback and self.stop_callback():
                            print("\n⏹️ Stop requested by user")
                            break
                        time.sleep(1)
            
            print(f"\n{'='*60}")
            print(f"✓ Bot completed successfully!")
            print(f"Total searches performed: {self.search_count}")
            stats = self.history_tracker.get_stats(self.profile_name)
            print(f"Total searched for this profile: {stats['total_searched']}")
            print(f"{'='*60}\n")
            
        except KeyboardInterrupt:
            print("\n\n⚠ Bot interrupted by user")
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and close the browser."""
        if self.driver:
            print("\n→ Closing browser...")
            self.driver.quit()
            print("✓ Browser closed successfully!")


def load_word_list_from_file(filename='words.txt'):
    """
    Load word list from a text file.
    
    Args:
        filename (str): Path to the word list file
        
    Returns:
        list: List of words, or None if file doesn't exist
    """
    try:
        # Check if file exists in current directory first
        if not os.path.exists(filename):
            # Try in the script's directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, filename)
        
        with open(filename, 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
        return words
    except FileNotFoundError:
        return None


def main():
    """Main function to run the Edge Search Bot."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microsoft Edge Search Bot - Automated Bing searches')
    parser.add_argument('--profile', '-p', type=str, default='Default',
                        help='Edge profile name (e.g., "Default", "Profile 1", "Profile 2")')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode (no GUI)')
    parser.add_argument('--delay', '-d', type=int, default=3,
                        help='Delay between searches in seconds (default: 3)')
    parser.add_argument('--mobile', '-m', action='store_true',
                        help='Run in mobile mode (simulates mobile browser)')
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Microsoft Edge Search Bot")
    print("="*60)
    
    print(f"→ Using Edge profile: {args.profile}")
    if args.headless:
        print("→ Running in headless mode")
    if args.mobile:
        print("→ Running in mobile mode")
    print()
    
    # Load word list from file (required)
    word_list = load_word_list_from_file('words.txt')
    if not word_list:
        print("✗ Error: words.txt file not found or empty!")
        print("→ Please create a words.txt file with one search term per line.")
        return
    
    print(f"✓ Loaded {len(word_list)} words from words.txt\n")
    
    # Create and run the bot
    bot = EdgeSearchBot(headless=args.headless, profile_name=args.profile, mobile=args.mobile)
    bot.run(
        word_list=word_list,
        delay_between_searches=args.delay
    )


if __name__ == "__main__":
    
    main()
