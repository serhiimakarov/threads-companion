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

    def _extract_media_id(self, url, html_content):
        # 1. From URL if it's a direct ID link
        if "/t/" in url:
            m_id = url.split("/t/")[1].split("/")[0].split("?")[0]
            if m_id.isdigit(): return m_id
        
        # 2. From HTML JSON blobs
        match = re.search(r'"post_id":"(\d+)"', html_content)
        if match: return match.group(1)
        
        match = re.search(r'"media_id":"(\d+)"', html_content)
        if match: return match.group(1)
        
        # 3. From any ID pattern
        match = re.search(r'"id":"(\d+)"', html_content)
        if match: return match.group(1)
        
        return None

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated() or not post_urls: return []
        cookies = self._get_cookies_dict()
        liked_urls = []
        for url in post_urls:
            try:
                res = requests.get(url, cookies=cookies, timeout=15)
                m_id = self._extract_media_id(url, res.text)
                lsd_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', res.text)
                lsd_t = lsd_match.group(1) if lsd_match else cookies.get('lsd', '')
                
                if m_id:
                    like_url = "https://www.threads.net/api/v1/web/threads/like/"
                    requests.post(like_url, data={"media_id": m_id, "lsd": lsd_t}, cookies=cookies, headers=self._get_headers(cookies, lsd_t), timeout=15)
                    liked_urls.append(url)
                    print(f"❤️ Liked Media ID {m_id}: {url}")
                time.sleep(2)
            except: pass
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        if not self.is_authenticated(): return False
        cookies = self._get_cookies_dict()
        try:
            res = requests.get(post_url, cookies=cookies, timeout=15)
            m_id = self._extract_media_id(post_url, res.text)
            lsd_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', res.text)
            
            if m_id:
                lsd_t = lsd_match.group(1) if lsd_match else cookies.get('lsd', '')
                print(f"💬 Posting comment to Media ID: {m_id}...")
                
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
                print(f"⚠️ Could not find Media ID for {post_url}")
        except Exception as e:
            print(f"❌ Web Comment Error: {e}")
        return False

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        # Outbound logic is handled by outbound.py using SpyKnowledge
        return 0
