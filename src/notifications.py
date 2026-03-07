import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_notification(message):
    """
    Sends a message to the configured Telegram chat.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return # Silently skip if not configured

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
