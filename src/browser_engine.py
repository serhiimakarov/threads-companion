import os
import json
import requests
import time
import re

class BrowserEngine:
    def __init__(self, state_path=None):
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.state_path = os.path.join(base_dir, "data", "auth_state.json")
        else:
            self.state_path = state_path

    def is_authenticated(self):
        return os.path.exists(self.state_path)

    def _get_cookies_dict(self):
        if not self.is_authenticated(): return {}
        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            return {c['name']: c['value'] for c in state.get('cookies', [])}
        except:
            return {}

    def _get_headers(self, cookies, lsd_token=''):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "X-IG-App-ID": "238280524082381",
            "X-FB-LSD": lsd_token if lsd_token else cookies.get('lsd', ''),
            "Origin": "https://www.threads.net",
            "Referer": "https://www.threads.net/",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        csrf_token = cookies.get('csrftoken')
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
        return headers

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated() or not post_urls: return []
        cookies = self._get_cookies_dict()
        liked_urls = []
        for url in post_urls:
            try:
                res = requests.get(url, cookies=cookies, timeout=15)
                media_id = re.search(r'"post_id":"(\d+)"', res.text)
                lsd = re.search(r'"LSD",\[\],{"token":"(.*?)"}', res.text)
                if media_id:
                    m_id = media_id.group(1)
                    lsd_t = lsd.group(1) if lsd else cookies.get('lsd', '')
                    like_url = "https://www.threads.net/api/v1/web/threads/like/"
                    requests.post(like_url, data={"media_id": m_id, "lsd": lsd_t}, cookies=cookies, headers=self._get_headers(cookies, lsd_t), timeout=15)
                    liked_urls.append(url)
                    print(f"❤️ Liked: {url}")
                time.sleep(2)
            except: pass
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        """
        Actually posts a comment via Web API.
        """
        if not self.is_authenticated(): return False
        cookies = self._get_cookies_dict()
        try:
            # 1. Get tokens from the post page
            res = requests.get(post_url, cookies=cookies, timeout=15)
            media_id_match = re.search(r'"post_id":"(\d+)"', res.text)
            lsd_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', res.text)
            
            if media_id_match:
                m_id = media_id_match.group(1)
                lsd_t = lsd_match.group(1) if lsd_match else cookies.get('lsd', '')
                
                # Double check m_id (it must be long numeric string)
                if not m_id.isdigit() or len(m_id) < 10:
                    # Alternative: extract from metadata
                    alt_id = re.search(r'\"media_id\":\"(\d+)\"', res.text)
                    if alt_id: m_id = alt_id.group(1)
                
                print(f"💬 Posting real comment to Media ID: {m_id}...")
                
                # Threads Web Reply API
                reply_url = "https://www.threads.net/api/v1/web/threads/reply/"
                data = {
                    "comment_text": comment_text,
                    "media_id": m_id,
                    "lsd": lsd_t
                }
                
                response = requests.post(reply_url, data=data, cookies=cookies, headers=self._get_headers(cookies, lsd_t), timeout=15)
                
                if response.status_code == 200:
                    print(f"✅ COMMENT SUCCESS for {post_url}")
                    return True
                else:
                    print(f"⚠️ Comment failed ({response.status_code}): {response.text[:100]}")
            else:
                print(f"⚠️ Could not find Media ID for commenting on {post_url}")
        except Exception as e:
            print(f"❌ Web Comment Error: {e}")
        return False

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        """
        Finds posts and engages with them using REAL web actions.
        """
        from src.spy_knowledge import SpyKnowledge
        # We need to initialize SpyKnowledge here or pass it
        # For simplicity, we'll use regex on search page as fallback
        cookies = self._get_cookies_dict()
        headers = self._get_headers(cookies)
        
        search_url = f"https://www.threads.net/search?q=%23{tag}"
        try:
            res = requests.get(search_url, cookies=cookies, headers=headers, timeout=20)
            post_paths = re.findall(r'\/@[a-zA-Z0-9._]+\/post\/[a-zA-Z0-9_-]+', res.text)
            urls = list(set([f"https://www.threads.net{p}" for p in post_paths]))
            
            if not urls:
                # Use SpyKnowledge if regex fails
                return 0 # Let outbound.py handle the spy logic
            
            count = 0
            for url in urls[:limit]:
                # 1. Like
                self.like_posts_batch([url])
                # 2. Comment
                success = self.post_comment_web(url, comment_callback(tag))
                if success: count += 1
                time.sleep(5)
            return count
        except: return 0
