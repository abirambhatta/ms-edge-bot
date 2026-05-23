"""
Search History Tracker
Tracks searched keywords per profile to avoid duplicates
"""

import json
import os
from datetime import datetime


class SearchHistoryTracker:
    """Track search history per profile to avoid duplicate searches."""
    
    def __init__(self, history_file='search_history.json'):
        self.history_file = history_file
        self.history = self.load_history()
    
    def load_history(self):
        """Load search history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading history: {e}")
            return {}
    
    def save_history(self):
        """Save search history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_searched_keywords(self, profile):
        """Get list of already searched keywords for a profile."""
        if profile not in self.history:
            self.history[profile] = {
                'searched': [],
                'last_updated': datetime.now().isoformat()
            }
        return set(self.history[profile]['searched'])
    
    def add_searched_keyword(self, profile, keyword):
        """Add a keyword to the searched list for a profile."""
        if profile not in self.history:
            self.history[profile] = {
                'searched': [],
                'last_updated': datetime.now().isoformat()
            }
        
        if keyword not in self.history[profile]['searched']:
            self.history[profile]['searched'].append(keyword)
            self.history[profile]['last_updated'] = datetime.now().isoformat()
            self.save_history()
    
    def filter_unsearched_keywords(self, profile, keywords):
        """Filter out already searched keywords for a profile."""
        searched = self.get_searched_keywords(profile)
        unsearched = [kw for kw in keywords if kw not in searched]
        return unsearched
    
    def clear_profile_history(self, profile):
        """Clear search history for a specific profile."""
        if profile in self.history:
            self.history[profile]['searched'] = []
            self.history[profile]['last_updated'] = datetime.now().isoformat()
            self.save_history()
    
    def clear_all_history(self):
        """Clear all search history."""
        self.history = {}
        self.save_history()
    
    def get_stats(self, profile):
        """Get statistics for a profile."""
        if profile not in self.history:
            return {'total_searched': 0, 'last_updated': 'Never'}
        
        return {
            'total_searched': len(self.history[profile]['searched']),
            'last_updated': self.history[profile]['last_updated']
        }
