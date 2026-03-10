from playwright.sync_api import sync_playwright
import os
import time

class BrowserEngine:
    def __init__(self, state_path=None):
        if state_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.state_path = os.path.join(base_dir, "data", "auth_state.json")
        else:
            self.state_path = state_path

    def is_authenticated(self):
        return os.path.exists(self.state_path)

    def like_post(self, post_url):
        if not self.is_authenticated(): 
            print("❌ Browser: Session not found.")
            return False
            
        playwright_cm = sync_playwright()
        try:
            p = playwright_cm.start()
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=self.state_path)
            page = context.new_page()
            
            page.goto(post_url)
            time.sleep(3)
            like_button = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
            if like_button.is_visible():
                like_button.click()
                print(f"❤️ Successfully liked via browser: {post_url}")
                time.sleep(1)
                browser.close()
                playwright_cm.stop()
                return True
            
            browser.close()
            playwright_cm.stop()
        except Exception as e:
            print(f"❌ Like error: {e}")
            try: playwright_cm.stop()
            except: pass
        return False

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        if not self.is_authenticated(): return 0
        
        playwright_cm = sync_playwright()
        count = 0
        try:
            p = playwright_cm.start()
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=self.state_path)
            page = context.new_page()
            
            print(f"🔎 Exploring #{tag}...")
            page.goto(f"https://www.threads.net/search?q=%23{tag}")
            time.sleep(6)
            
            # Extract post URLs
            links = page.locator('a[href*="/post/"]').all()
            urls = []
            for l in links:
                href = l.get_attribute('href')
                if href:
                    full_url = f"https://www.threads.net{href}" if href.startswith("/") else href
                    if full_url not in urls: urls.append(full_url)
            
            for url in urls[:limit]:
                try:
                    page.goto(url)
                    time.sleep(4)
                    
                    # Try to like
                    like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                    if like_btn.is_visible():
                        like_btn.click()
                        time.sleep(1)

                    txt_elem = page.locator('div[data-testid="post-text-container"]').first
                    if txt_elem.is_visible():
                        comment = comment_callback(txt_elem.inner_text())
                        if comment:
                            reply_btn = page.locator('div[role="button"]:has(svg[aria-label="Reply"])').first
                            if reply_btn.is_visible():
                                reply_btn.click()
                                time.sleep(2)
                                page.keyboard.type(comment)
                                time.sleep(1)
                                post_btn = page.locator('div[role="button"]:has-text("Post")').first
                                if post_btn.is_visible():
                                    post_btn.click()
                                    count += 1
                                    print(f"✅ Commented on {url}")
                                    time.sleep(5)
                except Exception as post_err:
                    print(f"⚠️ Error on post {url}: {post_err}")
            
            browser.close()
            playwright_cm.stop()
        except Exception as e:
            print(f"❌ Outbound error: {e}")
            try: playwright_cm.stop()
            except: pass
            
        return count
