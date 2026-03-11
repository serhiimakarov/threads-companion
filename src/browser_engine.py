import os
import json
import subprocess
import re
import time

class BrowserEngine:
    def __init__(self, state_path=None):
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.state_path = os.path.join(base_dir, "data", "auth_state.json")
        else:
            self.state_path = state_path

    def is_authenticated(self):
        return os.path.exists(self.state_path)

    def _get_cookies_str(self):
        if not self.is_authenticated(): return ""
        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            return "; ".join([f"{c['name']}={c['value']}" for c in state.get('cookies', [])])
        except:
            return ""

    def _get_lsd_token(self, url):
        cookie_str = self._get_cookies_str()
        cmd = [
            "curl", "-s", "-L",
            "--cookie", cookie_str,
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        html = result.stdout
        
        # SUPER PERMISSIVE EXTRACTION
        # Threads/IG Media IDs are usually 17-19 digits long and start with 3... or 1...
        m_id = None
        
        # Priority 1: Explicit JSON keys
        match = re.search(r'\"(?:post_id|media_id|target_id|id)\":\"?(\d{17,20})\"?', html)
        if match:
            m_id = match.group(1)
        
        # Priority 2: Barcelona Legacy pattern we just saw
        if not m_id:
            match = re.search(r'BarcelonaPostLegacyPathController.*?(\d{17,20})', html)
            if match: m_id = match.group(1)
            
        # Priority 3: First long number on page (risky but effective)
        if not m_id:
            match = re.search(r'(\d{17,20})', html)
            if match: m_id = match.group(1)
        
        # Extract LSD
        lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', html)
        lsd = lsd_match.group(1) if lsd_match else ""
        
        return m_id, lsd

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        cookie_str = self._get_cookies_str()
        liked_urls = []
        
        for url in post_urls:
            try:
                print(f"👉 Target: {url}")
                m_id, lsd = self._get_lsd_token(url)
                
                if m_id:
                    print(f"❤️ Liking Media ID: {m_id}...")
                    cmd = [
                        "curl", "-s", "-X", "POST",
                        "https://www.threads.net/api/v1/web/threads/like/",
                        "--cookie", cookie_str,
                        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "-H", "X-IG-App-ID: 238280524082381",
                        "-H", f"X-FB-LSD: {lsd}",
                        "-H", "X-Requested-With: XMLHttpRequest",
                        "-H", "Origin: https://www.threads.net",
                        "-H", f"Referer: {url}",
                        "-H", "Content-Type: application/x-www-form-urlencoded",
                        "--data-raw", f"media_id={m_id}&lsd={lsd}"
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if '"status":"ok"' in result.stdout:
                        print(f"✅ SUCCESS: Like recorded!")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ API Rejection: {result.stdout[:100]}")
                else:
                    print("⚠️ Media ID not found.")
                
                time.sleep(5)
            except Exception as e:
                print(f"❌ Curl Like Error: {e}")
                
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
