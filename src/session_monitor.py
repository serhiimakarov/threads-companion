import requests
import json
import os
from src.browser_engine import BrowserEngine
from src.notifications import send_telegram_notification

class SessionMonitor:
    def __init__(self):
        self.browser = BrowserEngine()

    def check_session_health(self):
        """
        Verifies if the current cookie session is still valid.
        Returns: True (Healthy), False (Expired/Invalid)
        """
        if not self.browser.is_authenticated():
            print("❌ Session Monitor: No auth file found.")
            return False

        cookies = self.browser._get_cookies_dict()
        headers = self.browser._get_headers(cookies)
        
        # We use the current_user endpoint which returns 404/401 if not logged in
        url = "https://www.threads.net/api/v1/web/accounts/current_user/"
        
        try:
            res = requests.get(url, cookies=cookies, headers=headers, timeout=15)
            
            # If we get a JSON with user info, we are good
            if res.status_code == 200:
                data = res.json()
                if data.get('user'):
                    print(f"✅ Session Healthy: @{data['user']['username']}")
                    return True
            
            # If we are redirected to login or get error
            print(f"⚠️ Session Invalid. Status: {res.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Session Monitor Error: {e}")
            return False

    def run_health_check(self):
        """
        Runs check and notifies user if session died.
        """
        is_healthy = self.check_session_health()
        
        # Check if we already notified about failure to avoid spam
        # We can use a simple flag file
        flag_file = "data/session_dead.flag"
        
        if not is_healthy:
            if not os.path.exists(flag_file):
                send_telegram_notification("🚨 *CRITICAL: Threads Session Expired!*\n\nThe bot cannot like or comment. Please refresh cookies via SSH Tunnel immediately.")
                with open(flag_file, 'w') as f: f.write("dead")
        else:
            # If healthy, remove flag if it exists
            if os.path.exists(flag_file):
                os.remove(flag_file)
                send_telegram_notification("✅ *System Restored:* Threads Session is back online.")
        
        return is_healthy

if __name__ == "__main__":
    monitor = SessionMonitor()
    monitor.run_health_check()
