"""
Settings Manager for Edge Search Bot
"""

import json
import os


class SettingsManager:
    """Manage bot settings with JSON persistence."""
    
    def __init__(self, settings_file='settings.json'):
        self.settings_file = settings_file
        self.default_settings = {
            'api_keyword_count': 100,
            'global_pc_count': 34,
            'global_mobile_count': 24,
            'profile_settings': {}
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from file or create defaults."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
        return self.default_settings.copy()
    
    def save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_api_keyword_count(self):
        """Get API keyword count."""
        return self.settings.get('api_keyword_count', 100)
    
    def set_api_keyword_count(self, count):
        """Set API keyword count."""
        self.settings['api_keyword_count'] = count
        self.save_settings()
    
    def get_global_pc_count(self):
        """Get global PC search count."""
        return self.settings.get('global_pc_count', 34)
    
    def set_global_pc_count(self, count):
        """Set global PC search count."""
        self.settings['global_pc_count'] = count
        self.save_settings()
    
    def get_global_mobile_count(self):
        """Get global mobile search count."""
        return self.settings.get('global_mobile_count', 24)
    
    def set_global_mobile_count(self, count):
        """Set global mobile search count."""
        self.settings['global_mobile_count'] = count
        self.save_settings()
    
    def get_profile_pc_count(self, profile):
        """Get PC count for specific profile (falls back to global)."""
        profile_settings = self.settings.get('profile_settings', {})
        if profile in profile_settings and 'pc_count' in profile_settings[profile]:
            return profile_settings[profile]['pc_count']
        return self.get_global_pc_count()
    
    def get_profile_mobile_count(self, profile):
        """Get mobile count for specific profile (falls back to global)."""
        profile_settings = self.settings.get('profile_settings', {})
        if profile in profile_settings and 'mobile_count' in profile_settings[profile]:
            return profile_settings[profile]['mobile_count']
        return self.get_global_mobile_count()
    
    def set_profile_pc_count(self, profile, count):
        """Set PC count for specific profile."""
        if 'profile_settings' not in self.settings:
            self.settings['profile_settings'] = {}
        if profile not in self.settings['profile_settings']:
            self.settings['profile_settings'][profile] = {}
        self.settings['profile_settings'][profile]['pc_count'] = count
        self.save_settings()
    
    def set_profile_mobile_count(self, profile, count):
        """Set mobile count for specific profile."""
        if 'profile_settings' not in self.settings:
            self.settings['profile_settings'] = {}
        if profile not in self.settings['profile_settings']:
            self.settings['profile_settings'][profile] = {}
        self.settings['profile_settings'][profile]['mobile_count'] = count
        self.save_settings()
    
    def clear_profile_settings(self, profile):
        """Clear custom settings for a profile (revert to global)."""
        if 'profile_settings' in self.settings and profile in self.settings['profile_settings']:
            del self.settings['profile_settings'][profile]
            self.save_settings()
