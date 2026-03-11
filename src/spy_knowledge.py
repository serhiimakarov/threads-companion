import requests
import re
import time
import random
import urllib.parse

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        """
        Exploits Google Search to find fresh Threads posts from external people.
        """
        print(f"🕵️ SpyKnowledge: Hunting for external posts about #{tag} via Google...")
        
        try:
            # Search pattern that forces Google to show individual posts
            search_query = f"site:threads.net \"#{tag}\" \"post/\""
            url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}"
            
            # Masking as a real desktop browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/"
            }
            
            res = requests.get(url, headers=headers, timeout=15)
            
            # Regex to find threads.net post links in Google's HTML
            # We look for /t/ or /post/ patterns
            links = re.findall(r'https://www\.threads\.net/t/[a-zA-Z0-9_-]+', res.text)
            links += re.findall(r'https://www\.threads\.net/@[a-zA-Z0-9._]+/post/[a-zA-Z0-9_-]+', res.text)
            
            if links:
                # Remove duplicates and avoid our own accounts
                external_links = [l for l in set(links) if "@serhiimakarov" not in l and "@serhii.makarov" not in l]
                print(f"✅ Google found {len(external_links)} EXTERNAL targets.")
                return external_links
            else:
                print("⚠️ Google found no fresh links. Trying fallback targets...")
        except Exception as e:
            print(f"❌ Google Proxy Error: {e}")

        # Strategy 2: Target Niche Leaders directly (They always have posts)
        leaders = ["raspberrypi", "python.learning", "zuck", "indiehackers"]
        target = random.choice(leaders)
        print(f"🎯 Falling back to niche leader: @{target}")
        
        return [f"https://www.threads.net/@{target}"]

    def get_post_text_lightweight(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}
            res = requests.get(url, headers=headers, timeout=10)
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match: return match.group(1)
        except: pass
        return "A technical discussion about software and DIY."
