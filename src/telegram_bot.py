import requests
import time
import json
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.database import mark_post_status

def handle_callback(callback_query):
    """Processes button clicks from Telegram."""
    data = callback_query.get('data', '')
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    
    # We only respond to our own chat
    if str(chat_id) != str(TELEGRAM_CHAT_ID):
        return

    post_id = None
    action = None
    
    if data.startswith("approve_"):
        post_id = data.replace("approve_", "")
        action = "approved"
        mark_post_status(post_id, 'pending')
        status_text = "✅ *Post Approved and Scheduled!*"
    elif data.startswith("delete_"):
        post_id = data.replace("delete_", "")
        action = "deleted"
        # We use a trick to 'kill' it in DB
        mark_post_status(post_id, 'failed')
        status_text = "🗑️ *Post Deleted.*"
    
    if action:
        # Edit the original message to show status
        orig_text = callback_query['message'].get('text', '')
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"{orig_text}\n\n{status_text}",
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
        
        # Answer callback to remove loading state
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", 
                      json={"callback_query_id": callback_query['id']})

def run_telegram_listener():
    """Simple polling listener for Telegram callbacks."""
    print("📡 Telegram Approval Listener started...")
    last_update_id = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 30}
            res = requests.get(url, params=params, timeout=35)
            updates = res.json().get('result', [])
            
            for update in updates:
                last_update_id = update['update_id']
                if 'callback_query' in update:
                    handle_callback(update['callback_query'])
                    
        except Exception as e:
            print(f"⚠️ Telegram Listener Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_telegram_listener()
