import os
import logging
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("threads-bot")

# Threads Credentials
THREADS_APP_ID = os.getenv('THREADS_APP_ID')
THREADS_APP_SECRET = os.getenv('THREADS_APP_SECRET')
THREADS_REDIRECT_URI = os.getenv('THREADS_REDIRECT_URI')
THREADS_ACCESS_TOKEN_TARGET = os.getenv('THREADS_ACCESS_TOKEN_TARGET')
THREADS_ACCESS_TOKEN_SOURCE = os.getenv('THREADS_ACCESS_TOKEN_SOURCE')

# AI Credentials
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini').lower() # 'gemini' or 'ollama'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
DATABASE_PATH = os.getenv('DATABASE_PATH', 'threads_scheduler.db')

# Telegram Notifications
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Image Hosting
IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')

if not THREADS_APP_ID or not THREADS_APP_SECRET:
    logger.warning("THREADS_APP_ID or THREADS_APP_SECRET environment variables are not set.")
