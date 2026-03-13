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

def upload_to_imgbb(image_source, is_local=False):
    if not IMGBB_API_KEY: return None
    try:
        if not is_local:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(image_source, headers=headers, timeout=30)
            if res.status_code != 200: return None
            img_data = res.content
        else:
            with open(image_source, 'rb') as f: img_data = f.read()

        img = Image.open(io.BytesIO(img_data))
        if img.mode != 'RGB': img = img.convert('RGB')
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        final_data = output.getvalue()

        url = "https://api.imgbb.com/1/upload"
        payload = {"key": IMGBB_API_KEY, "image": base64.b64encode(final_data).decode('utf-8')}
        res = requests.post(url, data=payload)
        json_res = res.json()
        if res.status_code == 200 and 'data' in json_res:
            return json_res['data']['url']
        return None
    except Exception: return None

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
        performance_report = get_weekly_summary()
        decisions = brain.decide_strategy(persona, 12, performance_report=performance_report)
    except Exception as e:
        print(f"❌ Init failed: {e}")
        return

    for slot in decisions.get('slots', []):
        try:
            # --- STAGE 1: DRAFTING ---
            print(f"✍️ Drafting: {slot['topic'][:50]}...")
            ai_response = brain.generate_post(persona, context=slot['topic'])
            draft_content = ai_response.get('text')
            if not draft_content: continue
            
            # --- STAGE 2: EDITING ---
            print(f"🧐 Editorial Review...")
            analysis = brain.analyze_post(draft_content)
            
            # --- STAGE 3: REFINING ---
            final_content = brain.refine_post(draft_content, analysis)
            
            # Scheduling
            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            scheduled_dt = datetime.datetime.combine(datetime.datetime.now().date(), target_time)
            if scheduled_dt <= datetime.datetime.now(): scheduled_dt += timedelta(days=1)

            if not dry_run:
                post_id = add_scheduled_post(final_content, scheduled_dt, platform='threads', status='pending_approval')
                print(f"✅ Scheduled: ID {post_id}")
                
                # Truncate editorial note for Telegram (avoid 400 errors)
                safe_analysis = analysis[:500] + "..." if len(analysis) > 500 else analysis
                msg = f"🚀 *Final Banger (ID {post_id}):*\n\n{final_content}\n\n--- 🧐 *Editor Feedback:*\n_{safe_analysis}_"
                send_telegram_notification(msg, reply_markup=get_approval_buttons(post_id))
            else:
                print(f"🧪 DRY RUN FINAL: {final_content}")
            
        except Exception as e:
            print(f"❌ Slot failed: {e}")

if __name__ == "__main__":
    run_agent()
