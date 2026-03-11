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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "238280524082381",
            "X-FB-LSD": lsd_token if lsd_token else cookies.get('lsd', ''),
            "Origin": "https://www.threads.com",
            "Referer": "https://www.threads.com/",
            "X-Requested-With": "XMLHttpRequest"
        }
        csrf = cookies.get('csrftoken')
        if csrf: headers["X-CSRFToken"] = csrf
        return headers

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

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        cookie_jar = self._create_curl_cookie_file()
        if not cookie_jar: return []
        
        liked_urls = []
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        for url in post_urls:
            try:
                print(f"👉 Target: {url}")
                # 1. GET page with HTTP/2
                get_cmd = ["curl", "-s", "-L", "--http2", "-b", cookie_jar, "-c", cookie_jar, "-H", f"User-Agent: {user_agent}", url]
                html = subprocess.run(get_cmd, capture_output=True, text=True).stdout
                
                m_id = None
                m_match = re.search(r'BarcelonaPostLegacyPathController.*?(\d{17,20})', html)
                if not m_match: m_match = re.search(r'\"post_id\":\"?(\d{17,20})\"?', html)
                if m_match: m_id = m_match.group(1)
                
                lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', html)
                lsd = lsd_match.group(1) if lsd_match else ""
                csrf = self._get_csrf_from_jar(cookie_jar)
                
                if m_id:
                    print(f"🎯 ID: {m_id} | LSD: {lsd[:5]}... | CSRF: {csrf[:5]}...")
                    
                    # 2. POST like with HTTP/2 and ALL headers
                    post_cmd = [
                        "curl", "-s", "--http2", "-X", "POST",
                        "https://www.threads.com/api/v1/web/threads/like/",
                        "-b", cookie_jar, "-c", cookie_jar,
                        "-H", f"User-Agent: {user_agent}",
                        "-H", "X-IG-App-ID: 238280524082381",
                        "-H", "X-ASBD-ID: 129477",
                        "-H", "X-IG-WWW-Claim: 0",
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
                        print(f"✅ SUCCESS: CURL-HTTP2 Like Confirmed!")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Rejection: {resp[:100]}")
                else: print("⚠️ ID not found.")
                time.sleep(5)
            except Exception as e: print(f"❌ Error: {e}")
        
        if os.path.exists(cookie_jar): os.remove(cookie_jar)
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
