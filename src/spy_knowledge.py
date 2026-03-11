import requests
import re
import time
import random
import urllib.parse

class SpyKnowledge:
    def __init__(self, threads_client):
        self.client = threads_client

    def find_posts_by_tag(self, tag):
        print(f"🕵️ SpyKnowledge: Searching Google for fresh Threads posts about #{tag}...")
        
        try:
            # Search for specific post patterns in Google
            # We look for /post/ links which are guaranteed to be interactive
            search_query = f"site:threads.net \"#{tag}\" inurl:post"
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://www.google.com/search?q={encoded_query}"
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=15)
            
            # Extract links like threads.net/@user/post/CODE
            # Google often encodes links, so we look for raw patterns
            links = re.findall(r'https://www\.threads\.net/@[a-zA-Z0-9._]+/post/[a-zA-Z0-9_-]+', res.text)
            
            if not links:
                # Try to find encoded links in Google's redirect format
                encoded_links = re.findall(r'url\?q=(https://www\.threads\.net/@[a-zA-Z0-9._]+/post/[a-zA-Z0-9_-]+)', res.text)
                links = encoded_links

            if links:
                unique_links = list(set(links))
                print(f"✅ Google Proxy found {len(unique_links)} fresh posts.")
                return unique_links
        except Exception as e:
            print(f"⚠️ Google Proxy failed: {e}")

        # Emergency Fallback: If Google is blocking us, use a few static reliable posts 
        # (or just skip to avoid detected automation patterns)
        print("💡 No links found. Google might be throttling or no fresh posts indexed.")
        return []

    def get_post_text_lightweight(self, url):
        try:
            # We can often get the post text from the page title or meta tags
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=10)
            
            # Threads often puts the post content in the <title> or og:description
            match = re.search(r'<meta property=\"og:description\" content=\"(.*?)\"', res.text)
            if match:
                return match.group(1)
            
            title_match = re.search(r'<title>(.*?)<\/title>', res.text)
            if title_match:
                return title_match.group(1).replace("Threads", "").strip()
        except: pass
        return "A technical discussion on Threads."
