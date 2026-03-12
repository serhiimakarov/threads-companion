import time
import os
import schedule
import requests
from datetime import datetime
from src.database import init_db, get_pending_posts, mark_post_status, log_stat
from src.threads_client import ThreadsClient
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH
from src.interactions import process_interactions
from src.outbound import run_outbound_engagement
from src.notifications import send_telegram_notification

def update_env_token(key, new_token):
    """Updates a specific key in the .env file."""
    try:
        env_path = ".env"
        if not os.path.exists(env_path): return
        
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        with open(env_path, 'w') as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={new_token}\n")
                else:
                    f.write(line)
        print(f"✅ Updated {key} in .env file.")
    except Exception as e:
        print(f"❌ Failed to update .env: {e}")

def run_scheduler():
    init_db()
    
    if not THREADS_ACCESS_TOKEN_TARGET:
        print("Error: THREADS_ACCESS_TOKEN_TARGET is missing.")
        return

    # We use a factory-like approach or refresh the client inside jobs to use latest tokens
    def get_client(token):
        return ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, token)

    def job_check_posts():
        print(f"[{datetime.now()}] Checking for pending posts...")
        # Reload env to get latest tokens if they were refreshed
        from dotenv import load_dotenv
        load_dotenv(override=True)
        token = os.getenv('THREADS_ACCESS_TOKEN_TARGET')
        client = get_client(token)
        
        posts = get_pending_posts()
        if not posts: return

        for post in posts:
            post_id, content, platform, image_url = post
            try:
                if platform == 'threads':
                    published_id = client.post_image(image_url, content) if image_url else client.post_text(content)
                    print(f"Successfully published post {post_id}. ID: {published_id}")
                    send_telegram_notification(f"🚀 *Post Published!*\n\n{content[:100]}...")
                    mark_post_status(post_id, 'posted')
            except Exception as e:
                print(f"Failed to publish post {post_id}: {e}")
                mark_post_status(post_id, 'failed')

    def job_refresh_tokens():
        print(f"[{datetime.now()}] 🔄 Attempting to refresh Long-Lived tokens...")
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        tokens_to_refresh = {
            'THREADS_ACCESS_TOKEN_TARGET': os.getenv('THREADS_ACCESS_TOKEN_TARGET'),
            'THREADS_ACCESS_TOKEN_SOURCE': os.getenv('THREADS_ACCESS_TOKEN_SOURCE')
        }
        
        refreshed_count = 0
        for key, token in tokens_to_refresh.items():
            if not token: continue
            try:
                client = get_client(token)
                new_data = client.refresh_long_lived_token()
                new_token = new_data['access_token']
                update_env_token(key, new_token)
                refreshed_count += 1
                print(f"✅ Successfully refreshed {key}.")
            except Exception as e:
                print(f"❌ Failed to refresh {key}: {e}")
        
        if refreshed_count > 0:
            send_telegram_notification(f"🔄 *Token Refresh:* Successfully refreshed {refreshed_count} tokens on RPi.")

    def job_process_interactions():
        print(f"[{datetime.now()}] Checking for new replies...")
        try: process_interactions()
        except Exception as e: print(f"Interaction processing failed: {e}")

    def job_run_ai_agent():
        print(f"[{datetime.now()}] AI Agent is generating the next post...")
        from src.agent import run_agent
        try: run_agent()
        except Exception as e: print(f"AI Agent failed: {e}")

    # Schedule jobs
    schedule.every(5).minutes.do(job_check_posts)
    schedule.every(5).minutes.do(job_process_interactions)
    
    # Refresh tokens every Sunday at 3 AM
    schedule.every().sunday.at("03:00").do(job_refresh_tokens)
    
    # Other standard jobs
    schedule.every().day.at("08:00").do(job_run_ai_agent)
    schedule.every().day.at("14:00").do(job_run_ai_agent)
    schedule.every().day.at("20:00").do(job_run_ai_agent)
    
    print("Scheduler started. Automatic token refresh active (Sundays 03:00).")
    
    # Initial run
    job_check_posts()
    job_process_interactions()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
