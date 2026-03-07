import time
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.analytics import analyze_user_profile
from src.notifications import send_telegram_notification
from src.database import is_interaction_processed, mark_interaction_processed

def process_interactions():
    print("🤝 Checking for new interactions on the Target account...")
    
    if not THREADS_ACCESS_TOKEN_TARGET:
        return

    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)
    brain = AIBrain()
    
    # 1. Get Persona from Source
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = source_client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
    except Exception as e:
        print(f"Failed to get persona: {e}")
        return

    # 2. Get recent posts from TARGET account
    try:
        target_threads = client.get_user_threads(limit=5)
        for post in target_threads.get('data', []):
            post_id = post['id']
            post_text = post.get('text', '')
            
            # Check for replies
            replies_data = client.get_replies(post_id)
            for reply in replies_data.get('data', []):
                reply_id = reply['id']
                
                # SKIP if already processed
                if is_interaction_processed(reply_id):
                    continue

                reply_text = reply.get('text', '')
                reply_user = reply.get('username')
                
                # Don't interact with yourself
                if reply_user == client.get_user_profile()['username']:
                    continue
                
                print(f"New reply from @{reply_user}: \"{reply_text[:30]}...\"")
                
                # Ask AI what to do
                decision = brain.evaluate_interaction(persona, post_text, reply_text)
                
                actions_taken = []
                reply_msg_taken = None
                if decision.get('like'):
                    try:
                        client.like_post(reply_id)
                        actions_taken.append("liked")
                    except Exception as e:
                        print(f"Failed to like: {e}")
                
                if decision.get('reply'):
                    reply_msg = decision['reply']
                    try:
                        container_id = client.create_reply_container(reply_id, reply_msg)
                        time.sleep(2) 
                        client.publish_container(container_id)
                        actions_taken.append("replied")
                        reply_msg_taken = reply_msg
                    except Exception as e:
                        print(f"Failed to reply: {e}")
                
                if actions_taken:
                    mark_interaction_processed(reply_id, ", ".join(actions_taken))
                    notification = f"🤝 *New Interaction with @{reply_user}*\n"
                    if "liked" in actions_taken: notification += "❤️ Liked their reply.\n"
                    if "replied" in actions_taken: notification += f"💬 Replied: \"{reply_msg_taken}\""
                    send_telegram_notification(notification)
                        
    except Exception as e:
        print(f"Interaction processing error: {e}")

if __name__ == "__main__":
    process_interactions()
