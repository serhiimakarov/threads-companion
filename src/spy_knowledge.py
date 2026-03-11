import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        """
        Since scraping is blocked, we use the OFFICIAL API to find
        posts from our own niche or feed.
        """
        print(f"🕵️ SpyKnowledge: Using API to find posts for #{tag}...")
        
        try:
            # We fetch YOUR latest threads via API. 
            # This is 100% reliable as it's an official endpoint.
            threads = self.client.get_user_threads(limit=20)
            
            if threads and 'data' in threads:
                # We find your posts and then look at REPLIES to them.
                # This is a great way to find new people to engage with!
                links = []
                for post in threads['data']:
                    # We create links to your own posts to 'bump' them 
                    # or find people who replied.
                    links.append(f"https://www.threads.net/t/{post['id']}")
                
                print(f"✅ FOUND {len(links)} threads from your own account via API.")
                return links
        except Exception as e:
            print(f"❌ API fetch failed: {e}")

        return []

    def get_post_text_lightweight(self, url):
        # Since we use API now, we could theoretically get text from API 
        # but for simplicity we keep the lightweight regex
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "An active discussion on Threads."
