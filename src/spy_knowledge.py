import requests
import re
import time
import random

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        print(f"🕵️ SpyKnowledge: Searching for content related to #{tag}...")
        
        # Strategy 1: Google Proxy (Very reliable for finding post links)
        try:
            search_query = f"site:threads.net \"#{tag}\""
            url = f"https://www.google.com/search?q={search_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=15)
            # Find threads.net post links (NOT profiles)
            links = re.findall(r'https://www.threads.net/@[a-zA-Z0-9._]+/post/[a-zA-Z0-9_-]+', res.text)
            if links:
                return list(set(links))
        except: pass

        # Strategy 2: Niche Leaders (Extraction of latest post)
        niche_profiles = {
            "python": ["python.learning", "realpython"],
            "diy": ["hackaday", "raspberrypi"],
            "indiehacker": ["levelsio", "pieterlevels"]
        }
        
        target_usernames = niche_profiles.get(tag, ["raspberrypi"])
        found_posts = []
        
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
        
        for username in target_usernames:
            try:
                profile_url = f"https://www.threads.net/@{username}"
                print(f"🧐 Visiting profile: {profile_url} to find latest post...")
                res = requests.get(profile_url, headers=headers, timeout=15)
                # Regex to find any post link in the profile HTML
                post_links = re.findall(rf'\/@{username}\/post\/[a-zA-Z0-9_-]+', res.text)
                if post_links:
                    full_url = f"https://www.threads.net{post_links[0]}"
                    print(f"📍 Found latest post: {full_url}")
                    found_posts.append(full_url)
            except: pass
            
        return found_posts

    def get_post_text_lightweight(self, url):
        try:
            res = requests.get(url, timeout=10)
            # Try to get meta description or title which usually contains post text
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match:
                return match.group(1)
        except: pass
        return "A technical post on Threads."
