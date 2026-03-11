import requests
import re
import time
import random

class SpyKnowledge:
    """
    Module for finding interesting content on Threads without a heavy browser.
    """
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        """
        Tries to find posts using different strategies.
        """
        print(f"🕵️ SpyKnowledge: Searching for content related to #{tag}...")
        
        # Strategy 1: Official API (requires threads_keyword_search)
        try:
            results = self.client.search_posts(tag, limit=5)
            if results and 'data' in results:
                print("✅ Found posts via official API search.")
                return [f"https://www.threads.net/@{p['username']}/post/{p['id']}" for p in results['data']]
        except:
            print("⚠️ Official API search failed or restricted.")

        # Strategy 2: Google Search Scraper (Lightweight)
        # Search for: site:threads.net "#python"
        try:
            search_query = f"site:threads.net \"#{tag}\""
            url = f"https://www.google.com/search?q={search_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=15)
            
            # Find threads.net post links in Google results
            links = re.findall(r'https://www.threads.net/@[a-zA-Z0-9._]+/post/[a-zA-Z0-9_-]+', res.text)
            if links:
                print(f"✅ Found {len(set(links))} posts via Google Proxy.")
                return list(set(links))
        except Exception as e:
            print(f"⚠️ Google Proxy search failed: {e}")

        # Strategy 3: Niche Leaders (Safe fallback)
        # Instead of searching, we just visit known profiles in the niche
        niche_profiles = {
            "python": ["@python.learning", "@realpython"],
            "diy": ["@hackaday", "@raspberrypi"],
            "indiehacker": ["@levelsio", "@pieterlevels"]
        }
        
        target_profiles = niche_profiles.get(tag, ["@raspberrypi"])
        print(f"💡 Strategy 3: Falling back to niche leaders: {target_profiles}")
        
        fallback_links = []
        for profile in target_profiles:
            fallback_links.append(f"https://www.threads.net/{profile}")
            
        return fallback_links

    def get_post_text_lightweight(self, url):
        """
        Extracts at least some context from a post URL without a browser.
        """
        try:
            res = requests.get(url, timeout=10)
            # Try to get meta description or title which usually contains post text
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match:
                return match.group(1)
        except: pass
        return "A technical post on Threads."
