import datetime
import random
import sqlite3
from datetime import timedelta
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH
from src.threads_client import ThreadsClient
from src.database import add_scheduled_post, init_db
from src.analytics import analyze_user_profile
from src.ai_brain import AIBrain
from src.notifications import send_telegram_notification

def run_agent(dry_run=False):
    print(f"🧠 AI Agent is seizing control... {'(DRY RUN)' if dry_run else ''}")
    init_db()
    
    # --- SPAM PROTECTION ---
    if not dry_run:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        one_day_from_now = datetime.datetime.now() + timedelta(days=1)
        cursor.execute('SELECT COUNT(*) FROM scheduled_posts WHERE status = "pending" AND scheduled_time < ?', (one_day_from_now,))
        pending_count = cursor.fetchone()[0]
        conn.close()

        if pending_count > 0:
            print(f"🛡️ Spam Protection: {pending_count} posts already scheduled for the next 24h. Skipping strategy session.")
            return

    if not THREADS_ACCESS_TOKEN_TARGET:
        print("❌ Error: Target token missing.")
        return
    
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    brain = AIBrain()
    if not brain.is_active():
        print("⚠️ AI brain inactive.")
        return

    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = source_client.get_user_threads(limit=20)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        insights = analyze_user_profile(source_client)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return

    top_posts_str = "\n---\n".join(insights['top_performing_posts'])
    persona = brain.generate_persona(posts_text, top_posts=top_posts_str)
    
    # --- PROACTIVE DECISION MAKING ---
    decisions = brain.decide_strategy(persona, insights['peak_hour'])
    print(f"🎯 AI Strategy: {len(decisions.get('slots', []))} posts decided.")

    scheduled_count = 0
    for slot in decisions.get('slots', []):
        try:
            content = brain.generate_post(persona, context=slot['topic'], examples=top_posts_str)
            if not content: continue
            
            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            now = datetime.datetime.now()
            scheduled_dt = datetime.datetime.combine(now.date(), target_time)
            
            if scheduled_dt <= now:
                scheduled_dt += timedelta(days=1)
                
            jitter = random.randint(-15, 15)
            scheduled_dt += timedelta(minutes=jitter)

            # ONLY THREADS
            if not dry_run:
                add_scheduled_post(content, scheduled_dt, platform='threads')
                print(f"✅ Scheduled: \"{content[:30]}...\" at {scheduled_dt}")
            else:
                print(f"\n🧪 [DRY RUN] Generated for {scheduled_dt}:")
                print("-" * 60)
                print(content)
                print("-" * 60)
            scheduled_count += 1
            
        except Exception as e:
            print(f"❌ Failed to schedule slot: {e}")

    if scheduled_count > 0 and not dry_run:
        send_telegram_notification(f"🧠 *AI Strategy Session Complete*\n\nCleaned the slate and decided on *{scheduled_count}* new posts for the next 24 hours.")

if __name__ == "__main__":
    run_agent()
