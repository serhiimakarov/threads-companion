import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        print(f"🕵️ SpyKnowledge: Scraping Threads for #{tag}...")
        
        try:
            # The most reliable way: go to the tag search page and find shortcodes in JSON
            url = f"https://www.threads.net/search?q=%23{tag}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.threads.net/"
            }
            
            res = requests.get(url, headers=headers, timeout=20)
            
            # Extract shortcodes from the large JSON blobs inside HTML
            # Pattern: "code":"DVk2Mc3CMgQ"
            shortcodes = re.findall(r'\"code\":\"([a-zA-Z0-9_-]{11})\"', res.text)
            
            if shortcodes:
                # Filter out unique and format as full URLs
                links = [f"https://www.threads.net/t/{s}" for s in set(shortcodes)]
                print(f"✅ FOUND {len(links)} posts via Direct Scraping.")
                return links
            else:
                print("⚠️ No shortcodes found in HTML blob.")
        except Exception as e:
            print(f"❌ Scraping failed: {e}")

        return []

    def get_post_text_lightweight(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            # Threads puts content in og:description
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "A trending discussion in the tech community."
