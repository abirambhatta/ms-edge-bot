"""
Wikipedia Trending Topics Fetcher
Fetches trending and popular topics from Wikipedia API
"""

import requests
import json
import random
from datetime import datetime, timedelta
import os


class WikipediaKeywordFetcher:
    """Fetch trending topics and keywords from Wikipedia."""
    
    def __init__(self, cache_file='search_cache.json'):
        self.cache_file = cache_file
        self.cache_duration_hours = 18
        
    def fetch_trending_topics(self, count=100):
        """
        Fetch trending topics from Wikipedia.
        
        Args:
            count (int): Number of topics to fetch
            
        Returns:
            list: List of search keywords
        """
        keywords = []
        
        try:
            print(f"-> Fetching {count} trending topics from Wikipedia...")
            
            # Set proper headers to avoid 403 errors
            headers = {
                'User-Agent': 'EdgeSearchBot/1.0 (Educational Project; Python/Requests)'
            }
            
            # Get most viewed articles from Wikipedia
            # Using Wikipedia REST API for most read articles
            url = "https://en.wikipedia.org/api/rest_v1/feed/featured/today"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract article titles
                if 'mostread' in data and 'articles' in data['mostread']:
                    for article in data['mostread']['articles'][:count]:
                        title = article.get('normalizedtitle', article.get('title', ''))
                        if title and len(title) > 2:
                            keywords.append(title)
            
            # If we need more keywords, fetch from random articles
            if len(keywords) < count:
                print(f"-> Fetching additional random topics...")
                keywords.extend(self._fetch_random_articles(count - len(keywords)))
            
            # If still not enough, add some general search terms
            if len(keywords) < count:
                general_terms = self._get_general_search_terms()
                random.shuffle(general_terms)
                keywords.extend(general_terms[:count - len(keywords)])
            
            # Remove duplicates and limit to count
            keywords = list(dict.fromkeys(keywords))[:count]
            
            print(f"[OK] Successfully fetched {len(keywords)} keywords")
            return keywords
            
        except Exception as e:
            print(f"[ERROR] Error fetching from Wikipedia: {e}")
            print("-> Using fallback keywords...")
            return self._get_general_search_terms()[:count]
    
    def _fetch_random_articles(self, count):
        """Fetch random article titles from Wikipedia."""
        keywords = []
        
        try:
            # Set proper headers
            headers = {
                'User-Agent': 'EdgeSearchBot/1.0 (Educational Project; Python/Requests)'
            }
            
            # Wikipedia API for random articles
            url = "https://en.wikipedia.org/w/api.php"
            
            # Fetch in batches of 10 (API limit)
            batches = (count // 10) + 1
            
            for _ in range(batches):
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'random',
                    'rnnamespace': 0,  # Main namespace only
                    'rnlimit': 10
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'query' in data and 'random' in data['query']:
                        for article in data['query']['random']:
                            title = article.get('title', '')
                            if title and len(title) > 2:
                                keywords.append(title)
                
                if len(keywords) >= count:
                    break
            
        except Exception as e:
            print(f"[ERROR] Error fetching random articles: {e}")
        
        return keywords[:count]
    
    def _get_general_search_terms(self):
        """Get general fallback search terms."""
        return [
            "artificial intelligence", "machine learning", "climate change",
            "renewable energy", "space exploration", "quantum computing",
            "cryptocurrency", "blockchain technology", "virtual reality",
            "augmented reality", "5G technology", "internet of things",
            "cybersecurity", "data science", "cloud computing",
            "electric vehicles", "autonomous driving", "robotics",
            "biotechnology", "gene editing", "nanotechnology",
            "solar energy", "wind power", "nuclear fusion",
            "mars mission", "james webb telescope", "black holes",
            "gravitational waves", "particle physics", "string theory",
            "neural networks", "deep learning", "natural language processing",
            "computer vision", "speech recognition", "recommendation systems",
            "big data", "data analytics", "business intelligence",
            "digital transformation", "industry 4.0", "smart cities",
            "sustainable development", "circular economy", "green technology",
            "mental health", "telemedicine", "personalized medicine",
            "3D printing", "additive manufacturing", "materials science",
            "quantum cryptography", "edge computing", "serverless computing",
            "microservices", "containerization", "kubernetes",
            "devops", "agile methodology", "software engineering",
            "web development", "mobile apps", "user experience",
            "digital marketing", "social media", "content creation",
            "streaming services", "online education", "remote work",
            "gig economy", "fintech", "insurtech",
            "healthtech", "edtech", "proptech",
            "supply chain", "logistics", "e-commerce",
            "digital payments", "mobile banking", "open banking",
            "artificial general intelligence", "neural interfaces", "brain computer interface",
            "synthetic biology", "crispr", "immunotherapy",
            "quantum sensors", "photonics", "metamaterials",
            "hydrogen fuel", "carbon capture", "battery technology",
            "smart grid", "energy storage", "power electronics",
            "satellite internet", "low earth orbit", "space tourism",
            "asteroid mining", "lunar base", "interplanetary travel",
            "exoplanets", "astrobiology", "search for extraterrestrial intelligence",
            "dark matter", "dark energy", "cosmology",
            "evolutionary biology", "ecology", "conservation",
            "ocean exploration", "marine biology", "coral reefs",
            "biodiversity", "endangered species", "wildlife conservation"
        ]
    
    def save_cache(self, keywords):
        """
        Save keywords to cache file with timestamp.
        
        Args:
            keywords (list): List of keywords to cache
        """
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'keywords': keywords
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Cache saved to {self.cache_file}")
            
        except Exception as e:
            print(f"[ERROR] Error saving cache: {e}")
    
    def load_cache(self):
        """
        Load keywords from cache if valid.
        
        Returns:
            list or None: Cached keywords if valid, None otherwise
        """
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            timestamp = datetime.fromisoformat(cache_data['timestamp'])
            age = datetime.now() - timestamp
            
            if age.total_seconds() / 3600 < self.cache_duration_hours:
                hours_old = age.total_seconds() / 3600
                print(f"[OK] Using cached keywords (age: {hours_old:.1f} hours)")
                return cache_data['keywords']
            else:
                print(f"-> Cache expired (age: {age.total_seconds() / 3600:.1f} hours)")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error loading cache: {e}")
            return None
    
    def get_keywords(self, count=100, force_refresh=False):
        """
        Get keywords, using cache if valid or fetching new ones.
        
        Args:
            count (int): Number of keywords to get
            force_refresh (bool): Force refresh even if cache is valid
            
        Returns:
            list: List of search keywords
        """
        if not force_refresh:
            cached = self.load_cache()
            if cached and len(cached) >= count:
                return cached[:count]
        
        # Fetch new keywords
        keywords = self.fetch_trending_topics(count)
        
        # Save to cache
        self.save_cache(keywords)
        
        return keywords
    
    def get_random_keywords(self, count, keywords=None):
        """
        Get random keywords from the list.
        
        Args:
            count (int): Number of keywords to return
            keywords (list): Source keyword list (uses cache if None)
            
        Returns:
            list: Random selection of keywords
        """
        if keywords is None:
            keywords = self.get_keywords()
        
        if len(keywords) <= count:
            random.shuffle(keywords)
            return keywords
        
        return random.sample(keywords, count)


def update_words_file(force_refresh=False, keyword_count=100):
    """
    Update words.txt file with fresh keywords.
    
    Args:
        force_refresh (bool): Force refresh even if cache is valid
        keyword_count (int): Number of keywords to fetch
    """
    print("\n" + "="*60)
    print("Updating Search Keywords")
    print("="*60 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cache_file = os.path.join(script_dir, 'search_cache.json')
    
    fetcher = WikipediaKeywordFetcher(cache_file=cache_file)
    keywords = fetcher.get_keywords(count=keyword_count, force_refresh=force_refresh)
    
    # Save to words.txt (REPLACE old content)
    try:
        words_file = os.path.join(script_dir, 'words.txt')
        
        # Write mode 'w' will replace the entire file
        with open(words_file, 'w', encoding='utf-8') as f:
            for keyword in keywords:
                f.write(keyword + '\n')
        
        print(f"[OK] Replaced words.txt with {len(keywords)} new keywords")
        print(f"[OK] File location: {words_file}")
        
    except Exception as e:
        print(f"[ERROR] Error updating words.txt: {e}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Test the fetcher
    update_words_file(force_refresh=True)
