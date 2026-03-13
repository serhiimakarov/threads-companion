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
    """
    Uploads an image to ImgBB. 
    image_source can be a URL or a local file path.
    """
    if not IMGBB_API_KEY: return None
    
    try:
        if not is_local:
            print(f"DEBUG: Downloading from URL: {image_source[:50]}...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(image_source, headers=headers, timeout=30)
            if res.status_code != 200: return None
            img_data = res.content
        else:
            print(f"DEBUG: Reading local file: {image_source}")
            with open(image_source, 'rb') as f:
                img_data = f.read()

        # Convert to JPEG for 100% compatibility
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

    print(f"🧠 AI Agent: Influencer 2.0 Mode...")
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
            ai_response = brain.generate_post(persona, context=slot['topic'])
            content = ai_response.get('text')
            if not content: continue
            
            image_url = None
            if ai_response.get('wants_image'):
                img_prompt = brain.generate_image_prompt(content)
                
                # 1. Try Pollinations PRO
                encoded = urllib.parse.quote(img_prompt)
                image_url = upload_to_imgbb(f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true")
                
                # 2. Try Dynamic Unsplash
                if not image_url:
                    print("🔄 AI Gen failed. Trying Unsplash...")
                    keywords = ai_response.get('image_keywords', 'tech')
                    image_url = upload_to_imgbb(f"https://source.unsplash.com/featured/1024x1024?{urllib.parse.quote(keywords)}")
                
                # 3. LOCAL FALLBACK (The Rescue)
                if not image_url:
                    print("🔄 External APIs failed. Using LOCAL fallback image...")
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    assets_dir = os.path.join(base_dir, "assets", "default_images")
                    if os.path.exists(assets_dir):
                        local_assets = [os.path.join(assets_dir, f) for f in os.listdir(assets_dir) if f.endswith(".jpg")]
                        if local_assets:
                            image_url = upload_to_imgbb(random.choice(local_assets), is_local=True)
                    else:
                        print(f"⚠️ Assets directory not found at {assets_dir}")

            target_time = datetime.datetime.strptime(slot['time'], "%H:%M").time()
            scheduled_dt = datetime.datetime.combine(datetime.datetime.now().date(), target_time)
            if scheduled_dt <= datetime.datetime.now(): scheduled_dt += timedelta(days=1)

            if not dry_run:
                post_id = add_scheduled_post(content, scheduled_dt, platform='threads', status='pending_approval')
                print(f"✅ Scheduled for Approval: ID {post_id} at {scheduled_dt}")

                # Send to Telegram with Buttons
                from src.notifications import send_telegram_notification, get_approval_buttons
                msg = f"📝 *New Post Draft (ID {post_id}):*\n\n{content}"
                send_telegram_notification(msg, reply_markup=get_approval_buttons(post_id))
            else:

        except Exception as e:
            print(f"❌ Slot failed: {e}")

if __name__ == "__main__":
    run_agent()
