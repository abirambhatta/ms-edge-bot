"""
Quick script to check which Edge profile has Microsoft Rewards signed in
"""

import time
import subprocess
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import os

def check_profile(profile_name):
    """Check if a profile has Microsoft Rewards signed in."""
    print(f"\n{'='*60}")
    print(f"Checking profile: {profile_name}")
    print(f"{'='*60}\n")
    
    try:
        edge_options = Options()
        
        user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Microsoft', 'Edge', 'User Data')
        edge_options.add_argument(f'--user-data-dir={user_data_dir}')
        edge_options.add_argument(f'--profile-directory={profile_name}')
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--remote-debugging-port=9222')
        edge_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=edge_options)
        
        print(f"[OK] Browser opened with profile: {profile_name}")
        print("-> Navigating to Microsoft Rewards...")
        
        # Navigate to Rewards page
        driver.get('https://rewards.bing.com/')
        
        # Wait for page to load
        time.sleep(3)
        
        print("\n" + "="*60)
        print("PLEASE CHECK THE BROWSER WINDOW:")
        print("- Are you signed in to Microsoft Rewards?")
        print("- Can you see your points balance?")
        print(f"- If YES, use this profile with the bot: --profile \"{profile_name}\"")
        print("="*60)
        
        input("\nPress Enter to close browser and try next profile...")
        
        driver.quit()
        print(f"[OK] Browser closed")
        
        # Force kill all Edge processes to ensure clean state
        print("-> Killing all Edge processes...")
        subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # Wait for processes to fully terminate
        print("[OK] All Edge processes killed\n")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}\n")
        # Try to kill processes even on error
        subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)


def main():
    print("\n" + "="*60)
    print("Microsoft Edge Profile Checker")
    print("This will help you find which profile has Rewards signed in")
    print("="*60)
    print("\n⚠️  IMPORTANT: Close Microsoft Edge before running this!")
    print("   (The script cannot access profiles while Edge is running)\n")
    
    input("Press Enter when Edge is closed...")
    
    profiles = ['Default', 'Profile 1', 'Profile 2', 'Profile 4']
    
    for profile in profiles:
        check_profile(profile)
    
    print("\n" + "="*60)
    print("✓ Profile check complete!")
    print("Run the bot with: python edge_search_bot.py -p \"YourProfile\"")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
