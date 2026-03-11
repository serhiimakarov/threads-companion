import asyncio
import sys
import os
from playwright.async_api import async_playwright

async def run():
    print("🚀 PI BROWSER FIX: Starting...")
    async with async_playwright() as p:
        try:
            # Add Pi flags
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(storage_state="data/auth_state.json")
            page = await context.new_page()
            
            url = "https://www.threads.net/t/DVk2Mc3CMgQ"
            print(f"👉 Navigating to: {url}")
            await page.goto(url, timeout=60000)
            await asyncio.sleep(5)
            
            # Look for like button
            like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
            if await like_btn.is_visible():
                await like_btn.click()
                print("❤️ SUCCESS: Clicked Like via Playwright!")
                await asyncio.sleep(2)
            else:
                print("⚠️ Like button not found or already liked.")
                
            await browser.close()
        except Exception as e:
            print(f"❌ Playwright Fatal Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
