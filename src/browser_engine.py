import os
import json
import subprocess
import re
import time
import tempfile
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

    def _create_curl_cookie_file(self):
        if not self.is_authenticated(): return None
        try:
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            tmp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.txt')
            tmp_file.write("# Netscape HTTP Cookie File\n")
            for c in state.get('cookies', []):
                domain = c['domain']
                secure = "TRUE" if c['secure'] else "FALSE"
                expires = int(c['expires']) if c['expires'] > 0 else 0
                tmp_file.write(f"{domain}\tTRUE\t{c['path']}\t{secure}\t{expires}\t{c['name']}\t{c['value']}\n")
            tmp_file.close()
            return tmp_file.name
        except: return None

    def _get_csrf_from_jar(self, jar_path):
        try:
            with open(jar_path, 'r') as f:
                content = f.read()
                match = re.search(r'csrftoken\t(\S+)', content)
                if match: return match.group(1)
        except: pass
        return ""

    def _extract_media_id(self, url, html_content):
        # 1. From URL if it's a direct ID link
        if "/t/" in url:
            m_id = url.split("/t/")[1].split("/")[0].split("?")[0]
            if m_id.isdigit(): return m_id
        
        if "/post/" in url:
            m_id = url.split("/post/")[1].split("/")[0].split("?")[0]
            if m_id.isdigit(): return m_id

        # 2. Aggressive search for any 17-19 digit number in JSON blobs or HTML
        # Look for "id":"337..." or "post_id":"337..." or just any quoted number
        matches = re.findall(r'\"(?:post_id|media_id|id|target_id)\":\"?(\d{17,20})\"?', html_content)
        if matches: return matches[0]
        
        # 3. Fallback: look for the first long numeric sequence that looks like a Media ID
        # (usually starts with 3 or 1 and is 18-19 digits)
        standalone_matches = re.findall(r'(\d{18,19})', html_content)
        if standalone_matches: return standalone_matches[0]
        
        return None

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated() or not post_urls: return []
        cookie_jar = self._create_curl_cookie_file()
        if not cookie_jar: return []
        
        liked_urls = []
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        for url in post_urls:
            try:
                print(f"👉 Target: {url}")
                
                # 1. GET page to refresh tokens
                get_cmd = ["curl", "-s", "-L", "--http2", "-b", cookie_jar, "-c", cookie_jar, "-H", f"User-Agent: {user_agent}", url]
                html = subprocess.run(get_cmd, capture_output=True, text=True).stdout
                
                # Extract Media ID and LSD
                m_id = self._extract_media_id(url, html)
                lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', html)
                lsd = lsd_match.group(1) if lsd_match else ""
                csrf = self._get_csrf_from_jar(cookie_jar)
                
                if m_id:
                    print(f"🎯 ID: {m_id} | LSD: {lsd[:5]}... | CSRF: {csrf[:5]}...")
                    print(f"❤️ Sending POST like...")
                    
                    post_cmd = [
                        "curl", "-s", "--http2", "-X", "POST",
                        "https://www.threads.com/api/v1/web/threads/like/",
                        "-b", cookie_jar, "-c", cookie_jar,
                        "-H", f"User-Agent: {user_agent}",
                        "-H", "X-IG-App-ID: 238280524082381",
                        "-H", f"X-FB-LSD: {lsd}",
                        "-H", f"X-CSRFToken: {csrf}",
                        "-H", "X-Requested-With: XMLHttpRequest",
                        "-H", "Origin: https://www.threads.com",
                        "-H", f"Referer: {url}",
                        "-H", "Content-Type: application/x-www-form-urlencoded",
                        "--data-raw", f"media_id={m_id}&lsd={lsd}"
                    ]
                    
                    resp = subprocess.run(post_cmd, capture_output=True, text=True).stdout
                    if '"status":"ok"' in resp:
                        print(f"✅ SUCCESS: Like confirmed!")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Rejection: {resp[:100]}")
                else:
                    print("⚠️ Could not find Numeric Media ID on page.")
                
                time.sleep(random.randint(5, 10))
            except Exception as e:
                print(f"❌ Error: {e}")
        
        if os.path.exists(cookie_jar): os.remove(cookie_jar)
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        # Outbound logic is handled by Mentions for now
        return False
