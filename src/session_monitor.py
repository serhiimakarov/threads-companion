import subprocess
import json
import os
import re
from src.browser_engine import BrowserEngine
from src.notifications import send_telegram_notification

class SessionMonitor:
    def __init__(self):
        self.browser = BrowserEngine()

    def check_session_health(self):
        """
        Verifies if the current cookie session is still valid using curl.
        """
        if not self.browser.is_authenticated():
            print("❌ Session Monitor: No auth file found.")
            return False

        # We use curl because requests is often blocked or gets 404
        cookie_jar = self.browser._create_curl_cookie_file()
        if not cookie_jar: return False
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        url = "https://www.threads.com/api/v1/web/accounts/current_user/"
        
        try:
            cmd = [
                "curl", "-s", "-L", "--http2",
                "-b", cookie_jar,
                "-H", f"User-Agent: {user_agent}",
                "-H", "X-Requested-With: XMLHttpRequest",
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
            
            # Clean up cookie jar immediately
            if os.path.exists(cookie_jar): os.remove(cookie_jar)

            if result.returncode == 0 and '"username"' in output:
                try:
                    data = json.loads(output)
                    if data.get('user'):
                        print(f"✅ Session Healthy: @{data['user']['username']}")
                        return True
                except:
                    # If it's not JSON but has username, it might be valid HTML with data
                    print("✅ Session Healthy (Found username in output)")
                    return True
            
            print(f"⚠️ Session Invalid or Response Error. Output sample: {output[:100]}")
            return False
            
        except Exception as e:
            print(f"❌ Session Monitor Error: {e}")
            if os.path.exists(cookie_jar): os.remove(cookie_jar)
            return False

    def run_health_check(self):
        is_healthy = self.check_session_health()
        flag_file = "data/session_dead.flag"
        
        if not is_healthy:
            if not os.path.exists(flag_file):
                send_telegram_notification("🚨 *CRITICAL: Threads Session Expired!*\n\nThe bot cannot like or comment. Please refresh cookies via SSH Tunnel.")
                with open(flag_file, 'w') as f: f.write("dead")
        else:
            if os.path.exists(flag_file):
                os.remove(flag_file)
                send_telegram_notification("✅ *System Restored:* Threads Session is back online.")
        
        return is_healthy

if __name__ == "__main__":
    monitor = SessionMonitor()
    monitor.run_health_check()
