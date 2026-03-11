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

    def _get_media_id_via_json(self, url, cookie_jar):
        """Uses the __a=1 endpoint to get structured JSON data for a post."""
        shortcode = None
        if "/t/" in url: shortcode = url.split("/t/")[1].split("/")[0].split("?")[0]
        elif "/post/" in url: shortcode = url.split("/post/")[1].split("/")[0].split("?")[0]
        
        if not shortcode: return None
        
        # Threads internal JSON data endpoint
        json_url = f"https://www.threads.net/t/{shortcode}/?__a=1&__d=dis"
        headers = ["-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "-H", "X-Requested-With: XMLHttpRequest"]
        
        cmd = ["curl", "-s", "-L", "-b", cookie_jar] + headers + [json_url]
        res = subprocess.run(cmd, capture_output=True, text=True).stdout
        
        try:
            data = json.loads(res)
            # Media ID is in graphql -> shortcode_media -> id
            m_id = data.get('graphql', {}).get('shortcode_media', {}).get('id')
            if m_id: return m_id
        except: pass
        
        # Regex fallback on the JSON response
        m_id_match = re.search(r'\"id\":\"(\d{17,20})\"', res)
        return m_id_match.group(1) if m_id_match else None

    def like_posts_batch(self, post_urls):
        if not self.is_authenticated(): return []
        cookie_jar = self._create_curl_cookie_file()
        if not cookie_jar: return []
        
        liked_urls = []
        for url in post_urls:
            try:
                print(f"👉 Resolving ID for: {url}")
                m_id = self._get_media_id_via_json(url, cookie_jar)
                
                if m_id:
                    print(f"❤️ Liking Media ID: {m_id}...")
                    # Get LSD from the regular page (JSON endpoint might not have it)
                    page_html = subprocess.run(["curl", "-s", "-b", cookie_jar, url], capture_output=True, text=True).stdout
                    lsd_match = re.search(r'\"LSD\",\[\],{\"token\":\"(.*?)\"}', page_html)
                    lsd = lsd_match.group(1) if lsd_match else ""
                    
                    post_cmd = [
                        "curl", "-s", "-X", "POST",
                        "https://www.threads.net/api/v1/web/threads/like/",
                        "-b", cookie_jar, "-c", cookie_jar,
                        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
                        print(f"✅ SUCCESS!")
                        liked_urls.append(url)
                    else: print(f"⚠️ Rejection: {resp[:50]}")
                else: print("⚠️ Media ID Resolution failed.")
                
                time.sleep(5)
            except Exception as e: print(f"❌ Error: {e}")
        
        if os.path.exists(cookie_jar): os.remove(cookie_jar)
        return liked_urls

    def post_comment_web(self, post_url, comment_text):
        return False
