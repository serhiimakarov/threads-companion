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
        Verifies session health by checking if the home page contains the user's name.
        """
        if not self.browser.is_authenticated():
            return False

        cookie_jar = self.browser._create_curl_cookie_file()
        if not cookie_jar: return False
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        url = "https://www.threads.com/"
        
        try:
            cmd = [
                "curl", "-s", "-L", "--http2",
                "-b", cookie_jar,
                "-H", f"User-Agent: {user_agent}",
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
            
            if os.path.exists(cookie_jar): os.remove(cookie_jar)

            # Check if shadow username is in the HTML
            if 'serhii.makarov' in output or 'serhiimakarov' in output:
                print(f"✅ Session Healthy: User found in home page HTML.")
                return True
            
            if 'not-logged-in' in output or 'login' in url.lower() or 'Oops' in output:
                print(f"⚠️ Session Invalid. Found indications of being logged out.")
                return False
            
            print(f"⚠️ Session status unclear. Output length: {len(output)}")
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
                send_telegram_notification("🚨 *CRITICAL: Threads Session Expired!*\n\nPlease refresh cookies via SSH Tunnel.")
                with open(flag_file, 'w') as f: f.write("dead")
        else:
            if os.path.exists(flag_file):
                os.remove(flag_file)
                send_telegram_notification("✅ *System Restored:* Threads Session is active.")
        
        return is_healthy

if __name__ == "__main__":
    monitor = SessionMonitor()
    monitor.run_health_check()
