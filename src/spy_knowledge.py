import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        """
        Final strategy: Extract ANY post link from high-traffic niche profiles.
        """
        niche_targets = {
            "python": ["python.learning", "realpython", "python_tips", "talkpython"],
            "diy": ["raspberrypi", "hackaday", "arduino.cc", "makezine"],
            "indiehacker": ["levelsio", "pieterlevels", "indiehackers", "robwalling"],
            "cybersecurity": ["mikko_hypponen", "schneierblog", "troyhunt"]
        }
        
        usernames = niche_targets.get(tag, ["raspberrypi", "python.learning"])
        target_username = random.choice(usernames)
        
        print(f"🎯 SpyKnowledge: Scraping @{target_username} for #{tag}...")
        
        try:
            url = f"https://www.threads.net/@{target_username}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=20)
            
            # BROAD REGEX: Find any string that looks like /post/CODE or /t/CODE
            # This is much more reliable as it doesn't depend on the username prefix
            shortcodes = re.findall(r'\/post\/([a-zA-Z0-9_-]{11})', res.text)
            if not shortcodes:
                shortcodes = re.findall(r'\/t\/([a-zA-Z0-9_-]{11})', res.text)
            
            if shortcodes:
                links = [f"https://www.threads.net/t/{s}" for s in set(shortcodes)]
                print(f"✅ SUCCESS! Found {len(links)} posts on the page.")
                return links
            else:
                print(f"⚠️ No post links found on @{target_username} page.")
                # Log a bit of HTML for debugging (first 500 chars)
                # print(res.text[:500])
        except Exception as e:
            print(f"❌ Scraping failed: {e}")

        return []

    def get_post_text_lightweight(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "A technical discussion on Threads."
