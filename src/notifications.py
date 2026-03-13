import requests
import json
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notification(text, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram notification: {e}")
        return False

def get_approval_buttons(post_id):
    """Generates inline buttons for post approval."""
    return {
        "inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve_{post_id}"},
            {"text": "🗑️ Delete", "callback_data": f"delete_{post_id}"}
        ]]
    }
