import sys
import os
import time
import json
from playwright.sync_api import sync_playwright

def run_isolated_batch(urls, state_path):
    print(f"🌐 Isolated Browser: Starting batch for {len(urls)} posts...")
    liked = []
    
    # Check if state file exists
    if not os.path.exists(state_path):
        print(f"❌ State file not found at {state_path}")
        return

    try:
        with sync_playwright() as p:
            print("🚀 Launching Chromium with Pi-optimized flags...")
            # We add --no-sandbox because RPi/Linux often needs it
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            
            context = browser.new_context(
                storage_state=state_path,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            for url in urls:
                try:
                    print(f"👉 Visiting: {url}")
                    # Increase timeout for slow RPi
                    page.goto(url, timeout=90000, wait_until="networkidle")
                    time.sleep(5)
                    
                    # Try to find Like button
                    like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                    unlike_btn = page.locator('svg[aria-label="Unlike"]').first
                    
                    if unlike_btn.is_visible():
                        print("✅ Already liked.")
                        liked.append(url)
                    elif like_btn.is_visible():
                        like_btn.click()
                        print("❤️ Clicked Like.")
                        time.sleep(2)
                        liked.append(url)
                    else:
                        print("⚠️ Could not find like button UI.")
                        
                except Exception as e:
                    print(f"⚠️ Error on {url}: {e}")
            
            browser.close()
    except Exception as e:
        print(f"❌ Fatal isolated error: {e}")
        # Detailed diagnostic for user
        if "executable" in str(e).lower():
            print("💡 Hint: Playwright browser binaries not found. Try: playwright install chromium")
    
    # Return JSON of liked URLs
    print(f"RESULT_JSON:{json.dumps(liked)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    state_file = sys.argv[1]
    post_urls = sys.argv[2:]
    run_isolated_batch(post_urls, state_file)
