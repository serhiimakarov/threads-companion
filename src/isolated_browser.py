import sys
import os
import time
import json
from playwright.sync_api import sync_playwright

def run_isolated_batch(urls, state_path):
    print(f"🌐 Isolated Browser: Starting batch for {len(urls)} posts...")
    liked = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=state_path)
            page = context.new_page()
            
            for url in urls:
                try:
                    print(f"👉 Liking: {url}")
                    page.goto(url, timeout=60000)
                    time.sleep(5)
                    
                    like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                    if like_btn.is_visible():
                        like_btn.click()
                        liked.append(url)
                        print("✅ Done.")
                        time.sleep(2)
                    elif page.locator('svg[aria-label="Unlike"]').is_visible():
                        print("✅ Already liked.")
                        liked.append(url)
                except Exception as e:
                    print(f"⚠️ Error on {url}: {e}")
            
            browser.close()
    except Exception as e:
        print(f"❌ Fatal isolated error: {e}")
    
    # Return JSON of liked URLs so the main bot can track them
    print(f"RESULT_JSON:{json.dumps(liked)}")

if __name__ == "__main__":
    # Args: state_path, url1, url2, ...
    if len(sys.argv) < 3:
        sys.exit(1)
    
    state_file = sys.argv[1]
    post_urls = sys.argv[2:]
    run_isolated_batch(post_urls, state_file)
