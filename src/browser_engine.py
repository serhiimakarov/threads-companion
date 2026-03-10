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

    def like_posts_batch(self, post_urls):
        """
        Likes multiple posts in a single browser session. 
        MUCH better for Raspberry Pi resources.
        """
        if not self.is_authenticated() or not post_urls:
            return []

        liked_urls = []
        try:
            with sync_playwright() as p:
                print(f"🚀 Launching browser for batch liking ({len(post_urls)} posts)...")
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(storage_state=self.state_path)
                page = context.new_page()
                
                for url in post_urls:
                    try:
                        print(f"🕵️ Liking: {url}")
                        page.goto(url, timeout=60000)
                        time.sleep(4)
                        
                        like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                        if like_btn.is_visible():
                            like_btn.click()
                            liked_urls.append(url)
                            print(f"✅ Success.")
                            time.sleep(2)
                        else:
                            # Check if already liked
                            if page.locator('svg[aria-label="Unlike"]').is_visible():
                                print("✅ Already liked.")
                                liked_urls.append(url)
                            else:
                                print("⚠️ Like button not found.")
                    except Exception as e:
                        print(f"❌ Failed to like {url}: {e}")
                
                browser.close()
        except Exception as e:
            print(f"❌ Batch like fatal error: {e}")
        
        return liked_urls

    def find_and_comment_on_tag(self, tag, comment_callback, limit=2):
        if not self.is_authenticated(): return 0
        
        count = 0
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(storage_state=self.state_path)
                page = context.new_page()
                
                print(f"🔎 Exploring #{tag}...")
                page.goto(f"https://www.threads.net/search?q=%23{tag}", timeout=60000)
                time.sleep(7)
                
                links = page.locator('a[href*="/post/"]').all()
                urls = []
                for l in links:
                    href = l.get_attribute('href')
                    if href:
                        full_url = f"https://www.threads.net{href}" if href.startswith("/") else href
                        if full_url not in urls: urls.append(full_url)
                
                for url in urls[:limit]:
                    try:
                        page.goto(url, timeout=60000)
                        time.sleep(5)
                        
                        # Try to like
                        like_btn = page.locator('div[role="button"]:has(svg[aria-label="Like"])').first
                        if like_btn.is_visible():
                            like_btn.click()
                            time.sleep(2)

                        txt_elem = page.locator('div[data-testid="post-text-container"]').first
                        if txt_elem.is_visible():
                            comment = comment_callback(txt_elem.inner_text())
                            if comment:
                                reply_btn = page.locator('div[role="button"]:has(svg[aria-label="Reply"])').first
                                if reply_btn.is_visible():
                                    reply_btn.click()
                                    time.sleep(2)
                                    page.keyboard.type(comment)
                                    time.sleep(2)
                                    post_btn = page.locator('div[role="button"]:has-text("Post")').first
                                    if post_btn.is_visible():
                                        post_btn.click()
                                        count += 1
                                        print(f"✅ Commented on {url}")
                                        time.sleep(5)
                    except Exception as post_err:
                        print(f"⚠️ Error on post {url}: {post_err}")
                
                browser.close()
        except Exception as e:
            print(f"❌ Batch outbound fatal error: {e}")
            
        return count
