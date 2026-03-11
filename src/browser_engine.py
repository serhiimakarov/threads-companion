import os
import json
import requests
import time
import re
import random

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
        # Precise mimicry of Threads Web 2025
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "238280524082381",
            "X-FB-LSD": lsd_token if lsd_token else cookies.get('lsd', ''),
            "X-ASBD-ID": "129477",
            "X-IG-WWW-Claim": "0",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.threads.net",
            "Referer": "https://www.threads.net/",
            "Content-Type": "application/x-www-form-urlencoded",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        csrf = cookies.get('csrftoken')
        if csrf: headers["X-CSRFToken"] = csrf
        return headers

    def _extract_media_id(self, url, html_content):
        # Format /t/ID
        if "/t/" in url:
            parts = url.split("/t/")[1].split("/")[0].split("?")[0]
            if parts.isdigit(): return parts
        
        # Format /post/ID
        if "/post/" in url:
            parts = url.split("/post/")[1].split("/")[0].split("?")[0]
            if parts.isdigit(): return parts

        # Regex fallback
        match = re.search(r'\"post_id\":\"(\d+)\"', html_content)
        if match: return match.group(1)
        return None

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated() or not post_urls: return []
        
        session = requests.Session()
        cookies = self._get_cookies_dict()
        for n, v in cookies.items():
            session.cookies.set(n, v, domain=".threads.net")

        liked_urls = []
        for url in post_urls:
            try:
                print(f"👉 Visiting: {url}")
                res = session.get(url, headers=self._get_headers(cookies), timeout=15)
                
                m_id = self._extract_media_id(url, res.text)
                # Extract fresh LSD from page
                lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', res.text)
                lsd_t = lsd_match.group(1) if lsd_match else cookies.get('lsd', '')
                
                if m_id:
                    print(f"❤️ Liking Media ID {m_id}...")
                    like_url = "https://www.threads.net/api/v1/web/threads/like/"
                    
                    # Essential payload for Web Like
                    payload = {
                        "media_id": m_id,
                        "lsd": lsd_t
                    }
                    
                    headers = self._get_headers(cookies, lsd_t)
                    resp = session.post(like_url, data=payload, headers=headers, timeout=15)
                    
                    if resp.status_code == 200 and '"status":"ok"' in resp.text:
                        print(f"✅ SUCCESS: {url}")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Failed. Code: {resp.status_code}. Msg: {resp.text[:100]}")
                
                time.sleep(random.randint(5, 10))
            except Exception as e:
                print(f"❌ Error: {e}")
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        # Commenting is similar but with "comment_text" in payload
        return False
