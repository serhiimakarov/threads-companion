import datetime
import random
import sqlite3
import base64
import requests
from datetime import timedelta
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH, IMGBB_API_KEY

def upload_to_imgbb(image_url):
    from PIL import Image
    import io
    if not IMGBB_API_KEY:
        print("⚠️ IMGBB_API_KEY missing. Skipping image upload.")
        return None
    
    try:
        print(f"DEBUG: Downloading image from: {image_url[:100]}...")
        # 1. Download from source
        headers = {'User-Agent': 'Mozilla/5.0'}
        img_res = requests.get(image_url, headers=headers, timeout=30)
        if img_res.status_code != 200:
            print(f"⚠️ Failed to download image (Status {img_res.status_code})")
            return None
        
        print(f"DEBUG: Image size downloaded: {len(img_res.content)} bytes. Content-type: {img_res.headers.get('Content-Type')}")
            
        # 2. CONVERT TO JPEG using Pillow (Ensures compatibility)
        try:
            img = Image.open(io.BytesIO(img_res.content))
        except Exception as e:
            print(f"❌ Pillow Error (Could not identify image): {e}")
            # If it's not a valid image file, maybe it's an error page or redirect
            return None

        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        img_data = output.getvalue()

        # 3. Upload to ImgBB
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBB_API_KEY,
            "image": base64.b64encode(img_data).decode('utf-8'),
        }
        res = requests.post(url, data=payload)
        json_res = res.json()
        
        if res.status_code == 200 and 'data' in json_res:
            print(f"✅ Hosted on ImgBB: {json_res['data']['url']}")
            return json_res['data']['url']
        else:
            print(f"❌ ImgBB Upload Failed: {json_res.get('error', {}).get('message', 'Unknown Error')}")
            return None
    except Exception as e:
        print(f"❌ ImgBB Exception: {e}")
        return None

def run_agent(dry_run=False):
    from src.threads_client import ThreadsClient
    from src.database import add_scheduled_post, init_db
    from src.analytics import analyze_user_profile, get_weekly_summary
    from src.ai_brain import AIBrain
    from src.notifications import send_telegram_notification

    print(f"🧠 AI Agent is seizing control... {'(DRY RUN)' if dry_run else ''}")
    init_db()
    
    # --- SPAM PROTECTION ---
    if not dry_run:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        one_day_from_now = datetime.datetime.now() + timedelta(days=1)
        cursor.execute('SELECT COUNT(*) FROM scheduled_posts WHERE status IN ("pending", "pending_approval") AND scheduled_time < ?', (one_day_from_now,))
        pending_count = cursor.fetchone()[0]
        conn.close()

        if pending_count >= 3:
            print(f"🛡️ Spam Protection: {pending_count} posts already scheduled. Skipping strategy session.")
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
    
    # --- PROACTIVE SELF-OPTIMIZATION ---
    performance_report = get_weekly_summary()
    print(f"📊 Analyzing self-performance: {performance_report[:50]}...")
    
    decisions = brain.decide_strategy(persona, insights['peak_hour'], performance_report=performance_report)
    print(f"🎯 AI Optimized Strategy: {len(decisions.get('slots', []))} posts decided.")

    scheduled_count = 0
    for slot in decisions.get('slots', []):
        try:
            ai_response = brain.generate_post(persona, context=slot['topic'], examples=top_posts_str)
            content = ai_response.get('text')
            if not content: continue
            
            # --- IMAGE GENERATION ---
            image_url = None
            if ai_response.get('wants_image'):
                theme = ai_response.get('image_theme', slot['topic'])
                image_prompt = brain.generate_image_prompt(f"{content} Theme: {theme}")
                import urllib.parse
                encoded_prompt = urllib.parse.quote(image_prompt)
                
                # Link from Pollinations
                raw_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={random.randint(1, 99999)}"
                
                if not dry_run:
                    print(f"🖼️ Uploading generated image to ImgBB...")
                    image_url = upload_to_imgbb(raw_url)
                else:
                    image_url = raw_url
                
                print(f"🖼️ Image Ready: {image_url}")

            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            now = datetime.datetime.now()
            scheduled_dt = datetime.datetime.combine(now.date(), target_time)
            
            if scheduled_dt <= now:
                scheduled_dt += timedelta(days=1)
                
            jitter = random.randint(-15, 15)
            scheduled_dt += timedelta(minutes=jitter)

            if not dry_run:
                add_scheduled_post(content, scheduled_dt, platform='threads', status='pending_approval')
                if image_url:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute('UPDATE scheduled_posts SET image_url = ? WHERE content = ? AND scheduled_time = ?', (image_url, content, scheduled_dt))
                    conn.commit()
                    conn.close()
                print(f"✅ Scheduled for Approval: \"{content[:30]}...\" at {scheduled_dt}")
            else:
                print(f"\n🧪 [DRY RUN] Generated for {scheduled_dt}:")
                print("-" * 60)
                print(content)
                if image_url: print(f"🖼️ IMAGE: {image_url}")
                print("-" * 60)
            scheduled_count += 1
            
        except Exception as e:
            print(f"❌ Failed to schedule slot: {e}")

    if scheduled_count > 0 and not dry_run:
        send_telegram_notification(f"🧠 *AI Strategy Session Complete*\n\nDecided on *{scheduled_count}* new posts for the next 24 hours. Waiting for your approval.")

if __name__ == "__main__":
    run_agent()
