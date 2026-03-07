# Threads Shadow AI: The Autonomous Social Agent 🤖⚔️🦾

An experimental AI agent for Threads operating in "Shadow Mode." It analyzes your main account (Source), studies top indie hacker strategies, and manages a parallel profile (Target) to compete for maximum engagement.

## ✨ Key Features

*   **Shadow Mode:** Analyzes your main account (Source) for inspiration, tone, and vibe.
*   **Dual-Brain AI:** Supports both cloud-based **Google Gemini** and local **Ollama (Llama 3.2)**.
*   **Mentor Integration:** Incorporates principles from Alex Hormozi, Pieter Levels, Marc Lou, and Dan Koe for content generation.
*   **Smart Cross-Pollination:** Automatically creates high-engagement quote-posts based on your manual activity.
*   **Total Autonomy:** The bot independently decides posting frequency (1-4 posts/day) and optimal timing with human-like jitter.
*   **Telegram Control:** Real-time notifications for every post, like, or strategy shift.
*   **Weekly Strategy Review:** Automatic deep-dive analysis every Sunday to pivot the strategy for the following week.
*   **Docker Ready:** Optimized for 24/7 operation on Raspberry Pi.

## 🚀 Quick Start

### 1. Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy `.env.example` to `.env` and fill in your keys:
*   `THREADS_APP_ID / SECRET`: From the Meta for Developers dashboard.
*   `GEMINI_API_KEY`: For cloud-based AI.
*   `TELEGRAM_BOT_TOKEN / CHAT_ID`: For mobile notifications.
*   `AI_PROVIDER`: Choose `gemini` or `ollama`.

### 3. Meta App Setup
To get your `THREADS_APP_ID` and `THREADS_APP_SECRET`:
1.  Go to [Meta for Developers](https://developers.facebook.com/).
2.  **Create App:** Choose "Other" -> "Next" -> "Threads".
3.  **Permissions:** Ensure `threads_content_publish`, `threads_basic`, and `threads_manage_replies` are enabled.
4.  **Redirect URI:** In Threads -> Settings, add `https://threads.local/auth/callback`.
5.  **Local Fix:** Add `127.0.0.1 threads.local` to your `/etc/hosts` file.

### 4. Authentication (Critical!)
The bot automatically handles **Long-lived tokens (60 days)**. You must authorize both accounts:
```bash
./venv/bin/python3 manage.py auth --account source # Your manual profile
./venv/bin/python3 manage.py auth --account target # The bot profile
```

## 🛠️ Usage (CLI)

*   **Run the Bot (Daemon):**
    `nohup ./venv/bin/python3 manage.py run > bot.log 2>&1 &`
*   **Strategy Preview (Dry Run):**
    `./venv/bin/python3 manage.py auto --dry-run` — Preview AI generated content.
*   **View Queue:**
    `./venv/bin/python3 manage.py list` — See upcoming scheduled posts.
*   **Check Performance:**
    `./venv/bin/python3 manage.py stats --refresh` — View engagement metrics.

## 🐳 Docker (Raspberry Pi)

```bash
docker-compose up -d --build
```
Data (SQLite and logs) are stored in the `./data` folder for persistence.

## 📈 "Challenge 2026" Strategy
The Shadow account is locked to **Plain English** and focuses on three pillars:
1.  **Myth-busting:** Debunking common misconceptions in Tech and DIY.
2.  **Behind-the-scenes:** The logic of building autonomous systems.
3.  **Engagement Hooks:** Every post ends with a targeted question.

---
*Created with 🦾 by Gemini CLI for @serhiimakarov*
