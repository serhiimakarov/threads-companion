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
        """Converts Playwright cookies to a single string for curl's --cookie flag."""
        if not self.is_authenticated(): return ""
        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            return "; ".join([f"{c['name']}={c['value']}" for c in state.get('cookies', [])])
        except:
            return ""

    def _get_lsd_token(self, url):
        """Uses curl to get the page and extract the LSD token."""
        cookie_str = self._get_cookies_str()
        cmd = [
            "curl", "-s", "-L",
            "--cookie", cookie_str,
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        html = result.stdout
        
        m_id_match = re.search(r'"post_id":"(\d+)"', html)
        lsd_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', html)
        
        m_id = m_id_match.group(1) if m_id_match else None
        if not m_id and "/t/" in url:
            m_id = url.split("/t/")[1].split("/")[0].split("?")[0]
            
        return m_id, lsd_match.group(1) if lsd_match else ""

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        
        cookie_str = self._get_cookies_str()
        liked_urls = []
        
        for url in post_urls:
            try:
                print(f"👉 Processing via Curl: {url}")
                m_id, lsd = self._get_lsd_token(url)
                
                if m_id:
                    print(f"❤️ Sending REAL Curl Like for Media ID {m_id}...")
                    
                    # Construct the CURL command for POST
                    cmd = [
                        "curl", "-s", "-X", "POST",
                        "https://www.threads.net/api/v1/web/threads/like/",
                        "--cookie", cookie_str,
                        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                        "-H", "X-IG-App-ID: 238280524082381",
                        "-H", f"X-FB-LSD: {lsd}",
                        "-H", "Origin: https://www.threads.net",
                        "-H", f"Referer: {url}",
                        "-H", "Content-Type: application/x-www-form-urlencoded",
                        "--data-raw", f"media_id={m_id}&lsd={lsd}"
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if '"status":"ok"' in result.stdout:
                        print(f"✅ CURL LIKE SUCCESS: {url}")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Curl failed. Response: {result.stdout[:100]}")
                
                time.sleep(5)
            except Exception as e:
                print(f"❌ Curl Error: {e}")
                
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
