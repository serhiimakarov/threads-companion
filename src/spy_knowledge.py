import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        """
        Final reliable strategy: Target specific leaders in the niche.
        """
        niche_targets = {
            "python": ["python.learning", "realpython", "python_tips", "talkpython"],
            "diy": ["raspberrypi", "hackaday", "arduino.cc", "makezine"],
            "indiehacker": ["levelsio", "pieterlevels", "indiehackers", "robwalling"],
            "cybersecurity": ["mikko_hypponen", "schneierblog", "troyhunt"]
        }
        
        usernames = niche_targets.get(tag, ["raspberrypi", "python.learning"])
        target_username = random.choice(usernames)
        
        print(f"🎯 SpyKnowledge: Targeting niche leader @{target_username} for #{tag}...")
        
        try:
            url = f"https://www.threads.net/@{target_username}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=20)
            
            # Extract post links from the profile page
            # Links in profile look like: /@username/post/CODE
            pattern = rf'\/@{target_username.replace(".", "\.")}\/post\/([a-zA-Z0-9_-]{11})'
            shortcodes = re.findall(pattern, res.text)
            
            if shortcodes:
                links = [f"https://www.threads.net/t/{s}" for s in set(shortcodes)]
                print(f"✅ FOUND {len(links)} posts from @{target_username}.")
                return links
            else:
                # Emergency fallback: find ANY post link on the page
                any_posts = re.findall(r'\/@[a-zA-Z0-9._]+\/post\/([a-zA-Z0-9_-]{11})', res.text)
                if any_posts:
                    links = [f"https://www.threads.net/t/{s}" for s in set(any_posts)]
                    print(f"✅ FOUND {len(links)} general posts from the page.")
                    return links
                
                print(f"⚠️ No posts found in profile of @{target_username}.")
        except Exception as e:
            print(f"❌ Target extraction failed: {e}")

        return []

    def get_post_text_lightweight(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "A trending discussion in the tech community."
