import os
import subprocess
import json
import sys

class BrowserEngine:
    def __init__(self, state_path=None):
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.state_path = os.path.join(base_dir, "data", "auth_state.json")
        else:
            self.state_path = state_path

    def is_authenticated(self):
        return os.path.exists(self.state_path)

    def like_posts_batch(self, post_urls):
        """
        Runs browser liking in an ISOLATED process via subprocess.
        Fixes PlaywrightContextManager errors on Raspberry Pi.
        """
        if not self.is_authenticated() or not post_urls:
            return []

        print(f"📡 Launching isolated browser process for {len(post_urls)} posts...")
        
        # Build command: python3 src/isolated_browser.py [state_path] [urls...]
        # We use sys.executable to ensure we use the same venv
        cmd = [sys.executable, "src/isolated_browser.py", self.state_path] + post_urls
        
        try:
            # Run and capture output
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Print isolated logs for debugging
            if result.stdout:
                print(f"--- Isolated Logs ---\n{result.stdout}\n---")
            if result.stderr:
                print(f"--- Isolated Errors ---\n{result.stderr}\n---")
                
            # Parse results from stdout (looking for RESULT_JSON: prefix)
            liked_urls = []
            for line in result.stdout.splitlines():
                if line.startswith("RESULT_JSON:"):
                    json_str = line.replace("RESULT_JSON:", "").strip()
                    liked_urls = json.loads(json_str)
            
            return liked_urls
        except Exception as e:
            print(f"❌ Subprocess execution failed: {e}")
            return []

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        """
        For now, this is still using API or simple logic.
        Ideally, outbound should also be moved to isolated_browser.py
        if it also fails on RPi.
        """
        print("⚠️ Outbound via browser currently using isolated script logic not yet implemented.")
        # We could create another isolated script for outbound if needed
        return 0
