import asyncio
from playwright.sync_api import sync_playwright
import os

def save_session():
    """
    Opens a browser for manual login and saves the auth state.
    """
    with sync_playwright() as p:
        print("\n--- 🌐 Threads Session Manager ---")
        print("1. A browser window will open.")
        print("2. Log in to your SHADOW Threads account manually.")
        print("3. Once you are on the home feed, come back here and press Enter.")
        
        # Open visible browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.threads.net/login")
        
        input("\nPress Enter AFTER you have successfully logged in...")
        
        # Save state to file
        context.storage_state(path="data/auth_state.json")
        print("✅ Session saved to data/auth_state.json")
        
        browser.close()

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    save_session()
