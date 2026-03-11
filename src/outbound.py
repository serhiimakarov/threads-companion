import random
import re
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE, THREADS_ACCESS_TOKEN_TARGET
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.browser_engine import BrowserEngine
from src.spy_knowledge import SpyKnowledge
from src.notifications import send_telegram_notification

def run_outbound_engagement():
    print("🚀 Starting Smart Outbound Mention Session...")
    
    tags = ["indiehacker", "python", "diy", "raspberrypi", "cybersecurity", "softwareengineering", "solopreneur"]
    selected_tag = random.choice(tags)
    
    brain = AIBrain()
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    spy = SpyKnowledge(client)
    browser = BrowserEngine()
    
    try:
        threads_data = client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
    except:
        persona = "A technical DIY enthusiast and software engineer."

    print(f"🏷️ Seeking interaction for: #{selected_tag}")
    post_urls = spy.find_posts_by_tag(selected_tag)
    
    engaged_count = 0
    if post_urls:
        # 1. Bulk Like via Cookie Engine
        print(f"❤️ Mass liking {len(post_urls)} found posts...")
        browser.like_posts_batch(post_urls[:5])
        
        # 2. Smart Mention Strategy
        for url in post_urls[:2]:
            try:
                # Extract username from URL: threads.net/@USERNAME/post/ID
                username_match = re.search(r'@([a-zA-Z0-9._]+)', url)
                if username_match:
                    target_username = username_match.group(1)
                    
                    if target_username not in ['serhiimakarov', 'serhii.makarov'] and random.random() > 0.3:
                        print(f"🗣️ Decided to MENTION @{target_username}...")
                        post_context = spy.get_post_text_lightweight(url)
                        mention_text = brain.generate_mention_post(persona, target_username, post_context)
                        
                        if mention_text:
                            # Use TARGET client to post
                            target_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)
                            published_id = target_client.post_text(mention_text)
                            print(f"✅ Mention post published! ID: {published_id}")
                            send_telegram_notification(f"🗣️ *Mention Post Published:*\n\n\"{mention_text}\"\n\nTargeting: @{target_username}")
                            engaged_count += 1
                            continue

            except Exception as e:
                print(f"⚠️ Error in mention logic for {url}: {e}")
    
    if engaged_count > 0 or post_urls:
        send_telegram_notification(f"🌍 *Outbound Growth:* Found {len(post_urls[:5])} targets. Engaged with {engaged_count} via Mentions.")
    else:
        print("No interaction targets found.")

if __name__ == "__main__":
    run_outbound_engagement()
