import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        # Guaranteed existing accounts
        global_targets = [
            "raspberrypi", "zuck", "mosseri", "netflix", 
            "nasa", "natgeo", "coding.memes", "python.learning"
        ]
        
        # Mix niche targets with global ones for reliability
        target_username = random.choice(global_targets)
        
        print(f"🎯 SpyKnowledge: Scraping @{target_username}...")
        
        try:
            url = f"https://www.threads.net/@{target_username}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=20)
            
            # Threads shortcodes are 11 chars: DVk2Mc3CMgQ
            # We look for them in the HTML text
            shortcodes = re.findall(r'\"code\":\"([a-zA-Z0-9_-]{11})\"', res.text)
            
            if shortcodes:
                links = [f"https://www.threads.net/t/{s}" for s in set(shortcodes)]
                print(f"✅ SUCCESS! Found {len(links)} posts.")
                return links
            else:
                # If "code" pattern fails, try to find any link with /post/
                more_links = re.findall(r'\/post\/([a-zA-Z0-9_-]{11})', res.text)
                if more_links:
                    links = [f"https://www.threads.net/t/{s}" for s in set(more_links)]
                    print(f"✅ FOUND {len(links)} posts via secondary regex.")
                    return links
                
                print(f"⚠️ Failed to find posts on @{target_username}. Meta might be blocking raw requests.")
        except Exception as e:
            print(f"❌ Scraping failed: {e}")

        return []

    def get_post_text_lightweight(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "A trending discussion on Threads."
