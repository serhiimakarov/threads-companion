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
        if not self.is_authenticated(): return False
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=self.state_path)
            page = context.new_page()
            try:
                page.goto(post_url)
                time.sleep(3)
                like_button = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                if like_button.is_visible():
                    like_button.click()
                    time.sleep(1)
                    browser.close()
                    return True
            except: pass
            browser.close()
            return False

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        if not self.is_authenticated(): return 0
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(storage_state=self.state_path)
            page = context.new_page()
            count = 0
            try:
                page.goto(f"https://www.threads.net/search?q=%23{tag}")
                time.sleep(5)
                # Filter for unique post URLs
                links = page.locator('a[href*="/post/"]').all()
                urls = list(set([f"https://www.threads.net{l.get_attribute('href')}" for l in links if l.get_attribute('href')]))
                
                for url in urls[:limit]:
                    page.goto(url)
                    time.sleep(3)
                    
                    # 1. LIKE THE POST FIRST (Visibility)
                    try:
                        like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                        if like_btn.is_visible():
                            like_btn.click()
                            print(f"❤️ Liked stranger's post: {url}")
                            time.sleep(1)
                    except: pass

                    txt_elem = page.locator('div[data-testid="post-text-container"]').first
                    if not txt_elem.is_visible(): continue
                    
                    comment = comment_callback(txt_elem.inner_text())
                    if not comment: continue
                    
                    reply_btn = page.locator('div[role="button"]:has(svg[aria-label="Reply"])').first
                    if reply_btn.is_visible():
                        reply_btn.click()
                        time.sleep(2)
                        page.keyboard.type(comment)
                        time.sleep(1)
                        # Click the "Post" button explicitly
                        post_btn = page.locator('div[role="button"]:has-text("Post")').first
                        if post_btn.is_visible():
                            post_btn.click()
                            count += 1
                            print(f"✅ Commented on {url}")
                            time.sleep(5)
            except Exception as e:
                print(f"Error in tag commenting: {e}")
            browser.close()
            return count
