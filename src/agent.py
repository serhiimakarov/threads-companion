import datetime
import random
import sqlite3
import base64
import requests
import io
import os
import urllib.parse
from datetime import timedelta
from PIL import Image
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH, IMGBB_API_KEY

def run_agent(dry_run=False):
    from src.threads_client import ThreadsClient
    from src.database import add_scheduled_post, init_db
    from src.analytics import analyze_user_profile, get_weekly_summary
    from src.ai_brain import AIBrain
    from src.notifications import send_telegram_notification, get_approval_buttons

    print(f"🧠 AI Agent: Multi-Agent Production Line...")
    init_db()
    
    brain = AIBrain()
    source_token = THREADS_ACCESS_TOKEN_SOURCE or THREADS_ACCESS_TOKEN_TARGET
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = source_client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
        decisions = brain.decide_strategy(persona, 12)
    except Exception as e:
        print(f"❌ Init failed: {e}")
        return

    for slot in decisions.get('slots', []):
        try:
            # --- STAGE 1: WRITER DRAFT ---
            print(f"✍️ Writer is drafting: {slot['topic']}...")
            ai_response = brain.generate_post(persona, context=slot['topic'])
            draft_content = ai_response.get('text')
            if not draft_content: continue
            
            # --- STAGE 2: EDITOR ANALYSIS ---
            print(f"🧐 Editor is analyzing the draft...")
            analysis = brain.analyze_post(draft_content)
            print(f"📝 Editorial Feedback: {analysis[:100]}...")
            
            # --- STAGE 3: WRITER REFINEMENT ---
            print(f"✨ Writer is refining the post based on feedback...")
            final_content = brain.refine_post(draft_content, analysis)
            
            # --- SCHEDULING ---
            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            scheduled_dt = datetime.datetime.combine(datetime.datetime.now().date(), target_time)
            if scheduled_dt <= datetime.datetime.now(): scheduled_dt += timedelta(days=1)

            if not dry_run:
                post_id = add_scheduled_post(final_content, scheduled_dt, platform='threads', status='pending_approval')
                print(f"✅ Scheduled for Approval: ID {post_id}")
                
                # Send to Telegram with Buttons
                msg = f"🚀 *Final Banger (ID {post_id}):*\n\n{final_content}\n\n--- 🧐 *Editor's Note:*\n{analysis}"
                send_telegram_notification(msg, reply_markup=get_approval_buttons(post_id))
            else:
                print(f"\n🧪 DRY RUN FINAL: {final_content}")
                print(f"🧐 EDITOR FEEDBACK: {analysis}")
            
        except Exception as e:
            print(f"❌ Slot failed: {e}")

if __name__ == "__main__":
    run_agent()
