import random
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE, THREADS_ACCESS_TOKEN_TARGET
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.browser_engine import BrowserEngine
from src.spy_knowledge import SpyKnowledge
from src.notifications import send_telegram_notification

def run_outbound_engagement():
    print("🚀 Starting Smart Outbound Engagement Session...")
    
    tags = ["indiehacker", "python", "diy", "raspberrypi", "cybersecurity", "softwareengineering", "solopreneur"]
    selected_tag = random.choice(tags)
    
    brain = AIBrain()
    # We use source token to identify persona
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    spy = SpyKnowledge(client)
    browser = BrowserEngine() # For liking via cookies
    
    try:
        threads_data = client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
    except:
        persona = "A technical DIY enthusiast and software engineer."

    print(f"🏷️ Seeking interaction for: #{selected_tag}")
    post_urls = spy.find_posts_by_tag(selected_tag)
    
    comment_count = 0
    if post_urls:
        # 1. Bulk Like via Cookie Engine
        print(f"❤️ Mass liking {len(post_urls)} found posts...")
        browser.like_posts_batch(post_urls[:5])
        
        # 2. Smart commenting on top 2 posts
        for url in post_urls[:2]:
            try:
                post_text = spy.get_post_text_lightweight(url)
                comment = brain.generate_external_comment(persona, post_text)
                
                if comment:
                    print(f"💬 Attempting to post REAL comment on {url}...")
                    success = browser.post_comment_web(url, comment)
                    if success:
                        print(f"✅ Comment posted: {comment[:50]}...")
                        comment_count += 1
                    else:
                        print(f"❌ Failed to post comment on {url}")
            except Exception as e:
                print(f"⚠️ Error processing post {url}: {e}")
    
    if comment_count > 0 or post_urls:
        send_telegram_notification(f"🌍 *Smart Outbound:* Found and engaged with {len(post_urls[:5])} posts about #{selected_tag}.")
    else:
        print("No interaction targets found.")

if __name__ == "__main__":
    run_outbound_engagement()
