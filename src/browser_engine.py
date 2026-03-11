import os
import json
import subprocess
import re
import time
import requests

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
        except: return {}

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        
        cookies = self._get_cookies_dict()
        session = requests.Session()
        for n, v in cookies.items():
            session.cookies.set(n, v, domain=".threads.net")

        liked_urls = []
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        for url in post_urls:
            try:
                print(f"👉 Target: {url}")
                # 1. Use curl to get the latest page context (reliable GET)
                cookie_str = "; ".join([f"{k}={v}" for k,v in cookies.items()])
                get_cmd = ["curl", "-s", "-L", "--cookie", cookie_str, "-H", f"User-Agent: {user_agent}", url]
                html = subprocess.run(get_cmd, capture_output=True, text=True).stdout
                
                # Extract tokens
                m_id = None
                m_match = re.search(r'BarcelonaPostLegacyPathController.*?(\d{17,20})', html)
                if not m_match: m_match = re.search(r'\"post_id\":\"?(\d{17,20})\"?', html)
                if m_match: m_id = m_match.group(1)
                
                lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', html)
                lsd = lsd_match.group(1) if lsd_match else cookies.get('lsd', '')
                
                if m_id:
                    print(f"🎯 ID Found: {m_id}. Sending Hybrid POST like...")
                    # Update session with any fresh cookies from curl (if we had a jar, but let's try raw)
                    
                    headers = {
                        "User-Agent": user_agent,
                        "X-IG-App-ID": "238280524082381",
                        "X-FB-LSD": lsd,
                        "X-CSRFToken": cookies.get('csrftoken', ''),
                        "X-Requested-With": "XMLHttpRequest",
                        "Origin": "https://www.threads.net",
                        "Referer": url,
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                    
                    payload = {"media_id": m_id, "lsd": lsd}
                    
                    resp = session.post("https://www.threads.net/api/v1/web/threads/like/", data=payload, headers=headers, timeout=15)
                    
                    if resp.status_code == 200 and '"status":"ok"' in resp.text:
                        print(f"✅ SUCCESS: Hybrid Like Recorded!")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Hybrid rejection ({resp.status_code}): {resp.text[:100]}")
                else:
                    print("⚠️ ID Resolution failed.")
                
                time.sleep(5)
            except Exception as e:
                print(f"❌ Hybrid Error: {e}")
                
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
