import os
import json
import subprocess
import re
import time
import tempfile

class BrowserEngine:
    def __init__(self, state_path=None):
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.state_path = os.path.join(base_dir, "data", "auth_state.json")
        else:
            self.state_path = state_path

    def is_authenticated(self):
        return os.path.exists(self.state_path)

    def _create_curl_cookie_file(self):
        """Converts Playwright JSON cookies to Netscape format for curl."""
        if not self.is_authenticated(): return None
        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            
            tmp_cookie_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
            # Netscape cookie format header
            tmp_cookie_file.write("# Netscape HTTP Cookie File\n")
            for c in state.get('cookies', []):
                domain = c['domain']
                path = c['path']
                secure = "TRUE" if c['secure'] else "FALSE"
                expires = int(c['expires']) if c['expires'] > 0 else 0
                name = c['name']
                value = c['value']
                tmp_cookie_file.write(f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
            tmp_cookie_file.close()
            return tmp_cookie_file.name
        except:
            return None

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        
        cookie_jar = self._create_curl_cookie_file()
        if not cookie_jar: return []
        
        liked_urls = []
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        for url in post_urls:
            try:
                print(f"👉 Target: {url}")
                
                # 1. GET page and UPDATE cookie jar
                get_cmd = [
                    "curl", "-s", "-L",
                    "-b", cookie_jar, "-c", cookie_jar,
                    "-H", f"User-Agent: {user_agent}",
                    url
                ]
                html = subprocess.run(get_cmd, capture_output=True, text=True).stdout
                
                # Extract Media ID and LSD from fresh HTML
                m_id = None
                m_id_match = re.search(r'\"(?:post_id|media_id|target_id|id)\":\"?(\d{17,20})\"?', html)
                if m_id_match: m_id = m_id_match.group(1)
                
                lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', html)
                lsd = lsd_match.group(1) if lsd_match else ""
                
                if m_id:
                    print(f"❤️ Liking Media ID: {m_id}...")
                    
                    # 2. POST like using UPDATED cookie jar
                    post_cmd = [
                        "curl", "-s", "-X", "POST",
                        "https://www.threads.net/api/v1/web/threads/like/",
                        "-b", cookie_jar, "-c", cookie_jar,
                        "-H", f"User-Agent: {user_agent}",
                        "-H", "X-IG-App-ID: 238280524082381",
                        "-H", f"X-FB-LSD: {lsd}",
                        "-H", "X-Requested-With: XMLHttpRequest",
                        "-H", "Origin: https://www.threads.net",
                        "-H", f"Referer: {url}",
                        "-H", "Content-Type: application/x-www-form-urlencoded",
                        "--data-raw", f"media_id={m_id}&lsd={lsd}"
                    ]
                    
                    resp = subprocess.run(post_cmd, capture_output=True, text=True).stdout
                    if '"status":"ok"' in resp:
                        print(f"✅ SUCCESS: Like recorded!")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Rejection: {resp[:100]}")
                else:
                    print("⚠️ Media ID not found.")
                
                time.sleep(5)
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Cleanup
        if os.path.exists(cookie_jar): os.remove(cookie_jar)
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
