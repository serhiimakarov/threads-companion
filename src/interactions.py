import time
import requests
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.notifications import send_telegram_notification
from src.database import is_interaction_processed, mark_interaction_processed
from src.browser_engine import BrowserEngine

def process_interactions():
    print("🤝 Checking for new interactions (Recursive Mode)...")
    
    if not THREADS_ACCESS_TOKEN_TARGET: return

    target_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE) if THREADS_ACCESS_TOKEN_SOURCE else None
    browser = BrowserEngine()
    brain = AIBrain()
    
    try:
        my_profile = target_client.get_user_profile()
        my_username = my_profile.get('username')
    except:
        my_username = None

    # --- 1. STALK THE HUMAN (Batch Mode) ---
    if source_client:
        try:
            print("🕵️ Analyzing Source account...")
            url = f"https://graph.threads.com/v1.0/me/threads?fields=id,permalink&access_token={THREADS_ACCESS_TOKEN_SOURCE}"
            source_threads = requests.get(url).json()
            to_like = []
            post_id_map = {}
            for post in source_threads.get('data', []):
                post_id = post['id']
                permalink = post.get('permalink', '').replace('threads.com', 'threads.net')
                if permalink and not is_interaction_processed(f"stalk_{post_id}"):
                    to_like.append(permalink)
                    post_id_map[permalink] = post_id
            if to_like:
                liked_urls = browser.like_posts_batch(to_like[:5])
                for url in liked_urls:
                    p_id = post_id_map.get(url)
                    if p_id: mark_interaction_processed(f"stalk_{p_id}", "liked_human_browser")
                if liked_urls: send_telegram_notification(f"🤝 *Support Mode:* Liked {len(liked_urls)} posts.")
        except Exception as e: print(f"Stalking failed: {e}")

    # --- 2. RESPOND TO REPLIES (Recursive Engine) ---
    def process_node_recursive(parent_id, parent_text, depth=1, max_depth=5):
        if depth > max_depth: return
        
        try:
            replies_data = target_client.get_replies(parent_id)
            replies = replies_data.get('data', [])
        except Exception as e:
            print(f"⚠️ Could not fetch replies for {parent_id}: {e}")
            return

        for reply in replies:
            reply_id = reply['id']
            reply_text = reply.get('text', '')
            reply_user = reply.get('username')

            # 1. If it's US, we just go deeper to see if anyone replied to US
            if reply_user == my_username:
                process_node_recursive(reply_id, reply_text, depth + 1, max_depth)
                continue

            # 2. If already processed, we still go deeper (maybe there are NEW replies to this old node)
            if is_interaction_processed(reply_id):
                process_node_recursive(reply_id, reply_text, depth + 1, max_depth)
                continue

            # 3. New interaction found!
            print(f"[{'  '*depth}↳] New reply from @{reply_user} at depth {depth}: \"{reply_text[:30]}...\"")
            
            # Generate Persona dynamically or use cache
            # (For speed, we could cache this once per process_interactions run)
            source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
            persona_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
            persona_posts = persona_client.get_user_threads(limit=10).get('data', [])
            persona_text = "\n---\n".join([p.get('text', '') for p in persona_posts if p.get('text')])
            persona = brain.generate_persona(persona_text)

            decision = brain.evaluate_interaction(persona, parent_text, reply_text)
            
            if decision.get('like'):
                try: target_client.like_post(reply_id)
                except: pass
            
            if decision.get('reply'):
                reply_msg = decision['reply']
                try:
                    container_id = target_client.create_reply_container(reply_id, reply_msg)
                    time.sleep(15) 
                    published_id = target_client.publish_container(container_id)
                    print(f"{'  '*depth}✅ SUCCESS: Replied to @{reply_user}. ID: {published_id}")
                    mark_interaction_processed(reply_id, f"replied: {reply_msg}")
                    send_telegram_notification(f"💬 *Deep Reply (Lvl {depth}) to @{reply_user}:*\n\n\"{reply_msg}\"")
                    
                    # After our reply, we could potentially check for replies to THIS new message in the next run
                except Exception as re:
                    print(f"❌ Failed to post reply to @{reply_user}: {re}")

    # Start recursion from recent top-level threads
    try:
        target_threads = target_client.get_user_threads(limit=5)
        for post in target_threads.get('data', []):
            process_node_recursive(post['id'], post.get('text', ''), depth=1)
    except Exception as e:
        print(f"Main interaction loop error: {e}")

if __name__ == "__main__":
    process_interactions()
