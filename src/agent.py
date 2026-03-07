import datetime
import random
import sqlite3
from datetime import timedelta
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH, logger
from src.threads_client import ThreadsClient
from src.database import add_scheduled_post, init_db
from src.analytics import analyze_user_profile
from src.ai_brain import AIBrain
from src.notifications import send_telegram_notification
from src.spy_knowledge import SPY_TARGETS

def run_agent(dry_run=False):
    logger.info(f"🧠 AI Agent is taking executive decisions {'(DRY RUN)' if dry_run else ''}...")
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
            logger.info(f"🛡️ Strategy locked for next 24h. No new slots needed.")
            return

    if not THREADS_ACCESS_TOKEN_TARGET:
        logger.error("Target token missing.")
        return
    
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    brain = AIBrain()
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = source_client.get_user_threads(limit=20)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        insights = analyze_user_profile(source_client)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return

    # --- NEW: SMART CROSS-POLLINATION (Warmup) ---
    if threads_data.get('data') and not dry_run:
        try:
            last_source = threads_data['data'][0]
            # Decision: Should we 'quote' this post?
            quote_context = f"The human just posted: '{last_source.get('text')}'"
            persona = brain.generate_persona(posts_text)
            
            # Use Dan Koe style for insightful quotes
            quote_comment = brain.generate_post(persona, context=f"Add a profound or tactical comment to this: {quote_context}", mentor_style=SPY_TARGETS['dankoe'])
            
            if quote_comment:
                logger.info(f"🔗 Strategy: Cross-pollinating with Source post. Comment: {quote_comment[:30]}...")
                # We schedule this for VERY SOON (within 1 hour)
                warmup_time = datetime.datetime.now() + timedelta(minutes=random.randint(15, 45))
                add_scheduled_post(quote_comment, warmup_time, platform='threads')
        except Exception as e:
            logger.error(f"Warmup strategy failed: {e}")

    # --- MAIN STRATEGY ---
    top_posts_str = "\n---\n".join(insights['top_performing_posts'])
    persona = brain.generate_persona(posts_text, top_posts=top_posts_str)
    
    decisions = brain.decide_strategy(persona, insights['peak_hour'])
    logger.info(f"🎯 Strategy Confirmed: {len(decisions.get('slots', []))} high-impact slots decided.")

    scheduled_count = 0
    mentor_list = list(SPY_TARGETS.keys())
    
    for i, slot in enumerate(decisions.get('slots', [])):
        try:
            mentor_name = random.choice(mentor_list) if i % 2 == 0 else "Original Human"
            mentor_style = SPY_TARGETS.get(mentor_name) if mentor_name != "Original Human" else None
            
            content = brain.generate_post(persona, context=slot['topic'], examples=top_posts_str, mentor_style=mentor_style)
            if not content: continue
            
            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            now = datetime.datetime.now()
            scheduled_dt = datetime.datetime.combine(now.date(), target_time)
            
            if scheduled_dt <= now:
                scheduled_dt += timedelta(days=1)
            
            scheduled_dt += timedelta(minutes=random.randint(-15, 15))

            if dry_run:
                print(f"\n--- [STRATEGY PREVIEW: {mentor_name}] ---\nTime: {scheduled_dt}\nContent: {content}\n")
            else:
                add_scheduled_post(content, scheduled_dt, platform='threads')
                logger.info(f"✅ Slot Secured: {scheduled_dt} (Inspiration: {mentor_name})")
            
            scheduled_count += 1
        except Exception as e:
            logger.error(f"Slot failed: {e}")

    if scheduled_count > 0 and not dry_run:
        send_telegram_notification(f"⚔️ *Challenge Update*\n\nSeized *{scheduled_count}* slots. Integrated Smart Cross-Pollination. Mentor rotation active. 🦾")

if __name__ == "__main__":
    run_agent()
