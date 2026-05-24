"""
Profile Manager for Edge Search Bot
Manage Edge profiles dynamically
"""

import json
import os


class ProfileManager:
    """Manage Edge profiles list."""
    
    def __init__(self, profiles_file='profiles.json'):
        self.profiles_file = profiles_file
        self.default_profiles = ['Default', 'Profile 1', 'Profile 2', 'Profile 4']
        self.profiles = self.load_profiles()
    
    def load_profiles(self):
        """Load profiles from file or create defaults."""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('profiles', self.default_profiles)
        except Exception as e:
            print(f"Error loading profiles: {e}")
        return self.default_profiles.copy()
    
    def save_profiles(self):
        """Save profiles to file."""
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump({'profiles': self.profiles}, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profiles: {e}")
            return False
    
    def get_profiles(self):
        """Get list of profiles."""
        return self.profiles.copy()
    
    def add_profile(self, profile_name):
        """Add a new profile."""
        if profile_name and profile_name not in self.profiles:
            self.profiles.append(profile_name)
            self.save_profiles()
            return True
        return False
    
    def remove_profile(self, profile_name):
        """Remove a profile."""
        if profile_name in self.profiles:
            self.profiles.remove(profile_name)
            self.save_profiles()
            return True
        return False
    
    def profile_exists(self, profile_name):
        """Check if profile exists."""
        return profile_name in self.profiles
