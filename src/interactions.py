import time
import requests
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.notifications import send_telegram_notification
from src.database import is_interaction_processed, mark_interaction_processed
from src.browser_engine import BrowserEngine

def process_interactions():
    print("🤝 Checking for new interactions...")
    
    if not THREADS_ACCESS_TOKEN_TARGET:
        return

    target_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE) if THREADS_ACCESS_TOKEN_SOURCE else None
    browser = BrowserEngine()
    brain = AIBrain()
    
    # --- 1. STALK THE HUMAN (Batch Mode) ---
    if source_client:
        try:
            print("🕵️ Analyzing Source account for new posts...")
            url = f"https://graph.threads.net/v1.0/me/threads?fields=id,permalink&access_token={THREADS_ACCESS_TOKEN_SOURCE}"
            source_threads = requests.get(url).json()
            
            # 1. Collect all unliked posts
            to_like = []
            post_id_map = {} # Map permalink to post_id for database tracking
            
            for post in source_threads.get('data', []):
                post_id = post['id']
                permalink = post.get('permalink', '').replace('threads.com', 'threads.net')
                
                if permalink and not is_interaction_processed(f"stalk_{post_id}"):
                    to_like.append(permalink)
                    post_id_map[permalink] = post_id
            
            # 2. Process all likes in ONE browser session
            if to_like:
                print(f"📦 Found {len(to_like)} posts to like. Starting batch browser session...")
                # We limit to last 5 to avoid long sessions
                liked_urls = browser.like_posts_batch(to_like[:5])
                
                for url in liked_urls:
                    p_id = post_id_map.get(url)
                    if p_id:
                        mark_interaction_processed(f"stalk_{p_id}", "liked_human_browser")
                
                if liked_urls:
                    send_telegram_notification(f"🤝 *Support Mode:* Liked {len(liked_urls)} of your latest posts via Batch Browser.")
            else:
                print("No new posts to support.")
                        
        except Exception as e:
            print(f"Stalking failed: {e}")

    # --- 2. RESPOND TO REPLIES ---
    try:
        source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
        persona_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
        threads_data = persona_client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
        
        target_threads = target_client.get_user_threads(limit=5)
        for post in target_threads.get('data', []):
            post_id = post['id']
            post_text = post.get('text', '')
            
            try:
                replies_data = target_client.get_replies(post_id)
            except Exception as e:
                print(f"⚠️ Could not fetch replies for post {post_id}: {e}")
                continue
            
            for reply in replies_data.get('data', []):
                reply_id = reply['id']
                if is_interaction_processed(reply_id): continue
                
                reply_text = reply.get('text', '')
                reply_user = reply.get('username')
                
                try: me = target_client.get_user_profile()['username']
                except: me = None
                if reply_user == me: continue

                print(f"New reply from @{reply_user}: \"{reply_text[:30]}...\"")
                decision = brain.evaluate_interaction(persona, post_text, reply_text)
                
                if decision.get('like'):
                    try: target_client.like_post(reply_id)
                    except: pass
                
                if decision.get('reply'):
                    reply_msg = decision['reply']
                    try:
                        container_id = target_client.create_reply_container(reply_id, reply_msg)
                        time.sleep(2) 
                        target_client.publish_container(container_id)
                        mark_interaction_processed(reply_id, f"replied: {reply_msg}")
                        send_telegram_notification(f"💬 *Replied to @{reply_user}:* {reply_msg}")
                    except: pass
    except Exception as e:
        print(f"Interaction error: {e}")

if __name__ == "__main__":
    process_interactions()
