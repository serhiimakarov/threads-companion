import time
import schedule
from datetime import datetime
from src.database import init_db, get_pending_posts, mark_post_status, log_stat
from src.threads_client import ThreadsClient
from src.x_client import XClient
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET
from src.agent import run_agent
from src.interactions import process_interactions
from src.outbound import run_outbound_engagement
from src.notifications import send_telegram_notification
from src.analytics import get_weekly_summary

def run_scheduler():
    init_db()
    
    if not THREADS_ACCESS_TOKEN_TARGET:
        print("Error: THREADS_ACCESS_TOKEN_TARGET is missing in .env. Please run './manage.py auth --account target' first.")
        return

    threads_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)
    x_client = XClient()

    def job_check_posts():
        print(f"[{datetime.now()}] Checking for pending posts...")
        posts = get_pending_posts()
        
        if not posts:
            print("No pending posts found.")
            return

        for post in posts:
            post_id, content, platform = post
            print(f"Publishing post {post_id} to {platform}: {content[:30]}...")
            
            try:
                if platform == 'threads':
                    published_id = threads_client.post_text(content)
                elif platform == 'x':
                    if not x_client.is_active():
                        raise Exception("X Client not configured.")
                    published_id = x_client.post_text(content)
                else:
                    raise Exception(f"Unknown platform: {platform}")
                    
                print(f"Successfully published post {post_id} to {platform}. ID: {published_id}")
                send_telegram_notification(f"🚀 *Post Published!*\n\n*Platform:* {platform.upper()}\n*Content:* {content[:100]}...")
                mark_post_status(post_id, 'posted')
            except Exception as e:
                print(f"Failed to publish post {post_id} to {platform}: {e}")
                mark_post_status(post_id, 'failed')

    def job_fetch_stats():
        print(f"[{datetime.now()}] Fetching stats...")
        try:
            insights = threads_client.get_insights()
            if 'data' in insights:
                for metric in insights['data']:
                    name = metric['name']
                    values = metric.get('values', [])
                    if values:
                        latest_value = values[-1]['value']
                        log_stat(name, latest_value, platform='threads')
                        print(f"Logged Threads stat: {name} = {latest_value}")
        except Exception as e:
            print(f"Error fetching Threads stats: {e}")

    def job_run_ai_agent():
        print(f"[{datetime.now()}] AI Agent is generating the next post...")
        try:
            run_agent()
        except Exception as e:
            print(f"AI Agent failed: {e}")

    def job_process_interactions():
        print(f"[{datetime.now()}] AI Agent is checking for new replies to engage with...")
        try:
            process_interactions()
        except Exception as e:
            print(f"Interaction processing failed: {e}")

    def job_outbound_growth():
        print(f"[{datetime.now()}] AI Agent is going outbound to find new friends...")
        try:
            run_outbound_engagement()
        except Exception as e:
            print(f"Outbound growth failed: {e}")

    def job_weekly_review():
        print(f"[{datetime.now()}] Running Weekly Strategy Review...")
        try:
            summary = get_weekly_summary()
            message = f"📊 *Weekly Strategy Review*\n\n{summary}\nOptimizing next week's vibe based on this data."
            send_telegram_notification(message)
            run_agent() 
        except Exception as e:
            print(f"Weekly review failed: {e}")

    # Schedule jobs
    schedule.every(5).minutes.do(job_check_posts)
    schedule.every().day.at("23:59").do(job_fetch_stats)
    
    # Generate new AI posts 3 times per day
    schedule.every().day.at("08:00").do(job_run_ai_agent)
    schedule.every().day.at("14:00").do(job_run_ai_agent)
    schedule.every().day.at("20:00").do(job_run_ai_agent)
    
    # Weekly Review every Sunday at 9 PM
    schedule.every().sunday.at("21:00").do(job_weekly_review)
    
    # Check for interactions every 30 minutes
    schedule.every(30).minutes.do(job_process_interactions)
    
    # Outbound Growth 2 times per day
    schedule.every().day.at("11:00").do(job_outbound_growth)
    schedule.every().day.at("17:00").do(job_outbound_growth)
    
    print("Scheduler started. Press Ctrl+C to exit.")
    
    # Initial run on startup
    job_check_posts()
    job_process_interactions()
    job_outbound_growth()
    job_run_ai_agent()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
