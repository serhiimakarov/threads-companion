import random
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE, THREADS_ACCESS_TOKEN_TARGET
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.browser_engine import BrowserEngine
from src.notifications import send_telegram_notification

def run_outbound_engagement():
    print("🚀 Starting Outbound Engagement Session...")
    
    tags = ["indiehacker", "python", "diy", "raspberrypi", "cybersecurity", "softwareengineering", "solopreneur"]
    selected_tag = random.choice(tags)
    
    brain = AIBrain()
    browser = BrowserEngine()
    
    # Get persona from source
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
    except:
        persona = "A technical DIY enthusiast and software engineer."

    def comment_creator(post_text):
        return brain.generate_external_comment(persona, post_text)

    print(f"🏷️ Exploring tag: #{selected_tag}")
    count = browser.find_and_comment_on_tag(selected_tag, comment_creator, limit=2)
    
    if count > 0:
        send_telegram_notification(f"🌍 *Outbound Growth:* Left {count} smart comments on #{selected_tag} posts.")
    else:
        print("No comments left this session.")

if __name__ == "__main__":
    run_outbound_engagement()
