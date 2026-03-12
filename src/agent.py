import datetime
import random
import sqlite3
import base64
import requests
import io
import urllib.parse
from datetime import timedelta
from PIL import Image
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_TARGET, THREADS_ACCESS_TOKEN_SOURCE, DATABASE_PATH, IMGBB_API_KEY

def upload_to_imgbb(image_url):
    if not IMGBB_API_KEY:
        print("⚠️ IMGBB_API_KEY missing.")
        return None
    
    try:
        print(f"DEBUG: Downloading image from: {image_url[:60]}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        img_res = requests.get(image_url, headers=headers, timeout=30)
        
        if img_res.status_code != 200:
            print(f"⚠️ Download failed (Status {img_res.status_code})")
            return None
            
        img = Image.open(io.BytesIO(img_res.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=95)
        img_data = output.getvalue()

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
        return None
    except Exception as e:
        print(f"❌ ImgBB Error: {e}")
        return None

def run_agent(dry_run=False):
    from src.threads_client import ThreadsClient
    from src.database import add_scheduled_post, init_db
    from src.analytics import analyze_user_profile, get_weekly_summary
    from src.ai_brain import AIBrain
    from src.notifications import send_telegram_notification

    print(f"🧠 AI Agent is seizing control... {'(DRY RUN)' if dry_run else ''}")
    init_db()
    
    brain = AIBrain()
    source_token = THREADS_ACCESS_TOKEN_SOURCE if THREADS_ACCESS_TOKEN_SOURCE else THREADS_ACCESS_TOKEN_TARGET
    source_client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, source_token)
    
    try:
        threads_data = source_client.get_user_threads(limit=10)
        posts_text = "\n---\n".join([p.get('text', '') for p in threads_data.get('data', []) if p.get('text')])
        persona = brain.generate_persona(posts_text)
        performance_report = get_weekly_summary()
        decisions = brain.decide_strategy(persona, 12, performance_report=performance_report)
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return

    for slot in decisions.get('slots', []):
        try:
            ai_response = brain.generate_post(persona, context=slot['topic'])
            content = ai_response.get('text')
            if not content: continue
            
            # --- INTELLIGENT IMAGE PIPELINE ---
            image_url = None
            if ai_response.get('wants_image'):
                img_prompt = brain.generate_image_prompt(content)
                encoded_prompt = urllib.parse.quote(img_prompt)
                
                # Try Level 1: Pollinations PRO
                primary_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random.randint(1, 99999)}"
                image_url = upload_to_imgbb(primary_url)
                
                # Try Level 2: Unsplash Fallback
                if not image_url:
                    print("🔄 AI Generation failed. Switching to Unsplash Fallback...")
                    keywords = ai_response.get('image_keywords', 'technology,server,ai')
                    fallback_url = f"https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1024&q=80" 
                    # Note: in real world we'd use Unsplash Search API or a reliable proxy
                    image_url = upload_to_imgbb(fallback_url)

            # --- SCHEDULING ---
            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            scheduled_dt = datetime.datetime.combine(datetime.datetime.now().date(), target_time)
            if scheduled_dt <= datetime.datetime.now(): scheduled_dt += timedelta(days=1)

            if not dry_run:
                post_id = add_scheduled_post(content, scheduled_dt, platform='threads', status='pending_approval')
                if image_url:
                    conn = sqlite3.connect(DATABASE_PATH)
                    conn.cursor().execute('UPDATE scheduled_posts SET image_url = ? WHERE id = ?', (image_url, post_id))
                    conn.commit()
                    conn.close()
                print(f"✅ Scheduled: ID {post_id}")
            else:
                print(f"🧪 DRY RUN: {content[:50]}... Image: {image_url}")
            
        except Exception as e:
            print(f"❌ Slot failed: {e}")

if __name__ == "__main__":
    run_agent()
