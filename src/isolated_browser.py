import sys
import os
import time
import json
import asyncio
from playwright.async_api import async_playwright

async def run_isolated_batch(urls, state_path):
    print(f"🌐 Isolated Browser (Async): Starting batch for {len(urls)} posts...")
    liked = []
    
    if not os.path.exists(state_path):
        print(f"❌ State file not found at {state_path}")
        return

    try:
        async with async_playwright() as p:
            print("🚀 Launching Chromium (Async Mode)...")
            # aarch64 often needs specific flags to behave
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox", 
                    "--disable-setuid-sandbox", 
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )
            
            context = await browser.new_context(
                storage_state=state_path,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            for url in urls:
                try:
                    print(f"👉 Visiting: {url}")
                    # Extended timeout for RPi processing
                    await page.goto(url, timeout=120000, wait_until="domcontentloaded")
                    await asyncio.sleep(7) # Extra time for Threads JS to settle
                    
                    # Detection logic
                    like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                    unlike_btn = page.locator('svg[aria-label="Unlike"]').first
                    
                    if await unlike_btn.is_visible():
                        print("✅ Already liked.")
                        liked.append(url)
                    elif await like_btn.is_visible():
                        await like_btn.click()
                        print("❤️ Clicked Like.")
                        await asyncio.sleep(3)
                        liked.append(url)
                    else:
                        print("⚠️ UI not matching (Like button missing).")
                        
                except Exception as e:
                    print(f"⚠️ Error on {url}: {e}")
            
            await browser.close()
    except Exception as e:
        print(f"❌ Fatal isolated error: {e}")
    
    print(f"RESULT_JSON:{json.dumps(liked)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    state_file = sys.argv[1]
    post_urls = sys.argv[2:]
    
    # Run the async loop
    try:
        asyncio.run(run_isolated_batch(post_urls, state_file))
    except KeyboardInterrupt:
        pass
