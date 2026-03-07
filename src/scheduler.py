import time
import schedule
from datetime import datetime
from src.database import init_db, get_pending_posts, mark_post_status, log_stat
from src.threads_client import ThreadsClient
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, logger
from src.agent import run_agent
from src.interactions import process_interactions
from src.notifications import send_telegram_notification
from src.analytics import get_weekly_summary

def run_scheduler():
    init_db()
    
    if not THREADS_ACCESS_TOKEN_TARGET:
        logger.error("THREADS_ACCESS_TOKEN_TARGET is missing in .env.")
        return

    threads_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET)

    def job_check_posts():
        logger.info("Checking for pending posts...")
        posts = get_pending_posts()
        
        if not posts:
            logger.info("No pending posts found.")
            return

        for post in posts:
            post_id, content, platform = post
            if platform != 'threads':
                continue # Ignore non-threads posts

            logger.info(f"Publishing post {post_id} to Threads...")
            
            try:
                published_id = threads_client.post_text(content)
                logger.info(f"SUCCESS! Published to Threads. ID: {published_id}")
                send_telegram_notification(f"🚀 *Post Published!*\n\n*Content:* {content[:100]}...")
                mark_post_status(post_id, 'posted')
            except Exception as e:
                logger.error(f"FAILED to publish post {post_id}: {e}")
                mark_post_status(post_id, 'failed')

    def job_fetch_stats():
        logger.info("Fetching daily statistics...")
        try:
            insights = threads_client.get_insights()
            if 'data' in insights:
                for metric in insights['data']:
                    name = metric['name']
                    values = metric.get('values', [])
                    if values:
                        latest_value = values[-1]['value']
                        log_stat(name, latest_value, platform='threads')
                        logger.info(f"Logged: {name} = {latest_value}")
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")

    def job_run_ai_agent():
        logger.info("AI Agent starting strategy session...")
        try:
            run_agent()
        except Exception as e:
            logger.error(f"AI Agent failed: {e}")

    def job_process_interactions():
        logger.info("Checking for new replies/interactions...")
        try:
            process_interactions()
        except Exception as e:
            logger.error(f"Interaction processing failed: {e}")

    def job_weekly_review():
        logger.info("Starting Weekly Strategy Review...")
        try:
            summary = get_weekly_summary()
            send_telegram_notification(f"📊 *Weekly Strategy Review*\n\n{summary}")
            run_agent() 
        except Exception as e:
            logger.error(f"Weekly review failed: {e}")

    # Schedule
    schedule.every(5).minutes.do(job_check_posts)
    schedule.every().day.at("23:59").do(job_fetch_stats)
    schedule.every().day.at("08:00").do(job_run_ai_agent)
    schedule.every().day.at("14:00").do(job_run_ai_agent)
    schedule.every().day.at("20:00").do(job_run_ai_agent)
    schedule.every().sunday.at("21:00").do(job_weekly_review)
    schedule.every(30).minutes.do(job_process_interactions)
    
    logger.info("--- THREADS SHADOW BOT STARTED ---")
    
    # Run once on start
    job_fetch_stats() # Initial stats collection
    job_check_posts()
    job_process_interactions()
    job_run_ai_agent()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
