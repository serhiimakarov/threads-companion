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

    def _get_headers(self, cookies):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-IG-App-ID": "238280524082381",
            "X-ASBD-ID": "129477",
            "X-FB-LSD": cookies.get('lsd', ''),
            "Origin": "https://www.threads.net",
            "Referer": "https://www.threads.net/",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        csrf_token = cookies.get('csrftoken')
        if csrf_token:
            headers["X-CSRFToken"] = csrf_token
        return headers

    def like_posts_batch(self, post_urls):
        """
        Actually likes posts using the internal Web API.
        """
        if not self.is_authenticated() or not post_urls:
            return []

        cookies = self._get_cookies_dict()
        liked_urls = []

        print(f"📡 Deep Request Engine: Processing {len(post_urls)} REAL likes...")
        
        for url in post_urls:
            try:
                # 1. Get the post page to extract the media_id and internal tokens
                res = requests.get(url, cookies=cookies, timeout=15)
                
                # Extract media_id (often found in the URL or in metadata)
                # Threads media IDs look like numbers: 337...
                media_id_match = re.search(r'"post_id":"(\d+)"', res.text)
                lsd_token_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', res.text)
                
                if not media_id_match:
                    # Fallback media id detection from script blobs
                    media_id_match = re.search(r'"id":"(\d+)"', res.text)

                if media_id_match:
                    media_id = media_id_match.group(1)
                    lsd_token = lsd_token_match.group(1) if lsd_token_match else cookies.get('lsd', '')
                    
                    print(f"👉 Extracted Media ID: {media_id}. Sending POST like...")
                    
                    like_url = f"https://www.threads.net/api/v1/web/threads/like/"
                    data = {
                        "media_id": media_id,
                        "lsd": lsd_token
                    }
                    
                    headers = self._get_headers(cookies)
                    headers["X-FB-LSD"] = lsd_token
                    
                    post_res = requests.post(like_url, data=data, cookies=cookies, headers=headers, timeout=15)
                    
                    if post_res.status_code == 200:
                        print(f"✅ REAL LIKE SUCCESS for {url}")
                        liked_urls.append(url)
                    else:
                        print(f"⚠️ Like POST failed ({post_res.status_code}): {post_res.text[:100]}")
                else:
                    print(f"⚠️ Could not find Media ID for {url}. Skipping.")
                
                time.sleep(3) # Be human
            except Exception as e:
                print(f"❌ HTTP Like error: {e}")
        
        return liked_urls

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        # Implementation for real comments would be similar (using /api/v1/web/threads/reply/)
        print("⚠️ Outbound commenting via Deep Engine pending.")
        return 0
