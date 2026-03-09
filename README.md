# Threads Shadow AI Agent 🤖🧵🦾

A fully autonomous social media agent designed to "shadow" a reference account, optimize engagement using AI, and manage a secondary account with zero human intervention. Optimized for the 2025 Threads algorithm and local execution.

## 🌟 Features

- **Dual-Account "Shadowing":** Analyzes a source account to learn vibe, topics, and timing.
- **Autonomous Strategy:** Decides how many posts to schedule and at what times (with human-like jitter).
- **AI Brain (Cloud/Local):** Supports Google Gemini 2.5 Flash and local LLMs via Ollama.
- **Shadow Browser Engine:** Bypasses API restrictions by using Playwright to like posts via a headless browser.
- **Smart Engagement:** Automatically replies to followers and likes comments using AI evaluation.
- **Outbound Growth:** Searches for niche-specific tags and leaves smart comments on strangers' posts to grow the audience.
- **Telegram Notifications:** Get real-time updates on your phone for every post, like, and reply.
- **Raspberry Pi Ready:** Fully containerized with Docker for 24/7 low-power operation.

## 🛠️ Tech Stack

- **Python 3.11+**
- **Playwright** (Browser Automation)
- **Google GenAI / Ollama** (LLM Brain)
- **SQLite** (Persistent Queue & Stats)
- **Docker & Docker Compose**

## 🚀 Quick Start

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and fill in:
- `THREADS_ACCESS_TOKEN_SOURCE`: Your manual reference account.
- `THREADS_ACCESS_TOKEN_TARGET`: The bot-controlled account.
- `GEMINI_API_KEY` (or set `AI_PROVIDER=ollama`).
- `TELEGRAM_BOT_TOKEN` & `CHAT_ID`.

### 3. Initialize Browser Session
Run this once to log into your Shadow account manually and save cookies:
```bash
mkdir -p data && ./venv/bin/python3 src/session_manager.py
```

### 4. Run the Bot
```bash
# Direct run
./venv/bin/python3 manage.py run

# Background run
nohup ./venv/bin/python3 manage.py run > bot.log 2>&1 &
```

## 🐳 Docker Deployment (Raspberry Pi)

```bash
docker-compose up -d --build
```
*Note: Database and session data are stored in the `./data` volume for persistence.*

## 📊 Commands

- `./manage.py auth --account [source/target]`: Authenticate accounts.
- `./manage.py auto`: Manually trigger an AI strategy & posting session.
- `./manage.py list`: View all upcoming scheduled posts.
- `./manage.py stats`: View engagement metrics.
- `./manage.py delete [ID]`: Remove a pending post from the queue.

## 📈 The Shadow Strategy
The bot follows a "Micro-Gap" strategy for 2025:
- **Frequency:** 2-3 posts per day.
- **Timing:** Optimized morning windows (9:45 AM - 11:15 AM).
- **Engagement:** Every post ends with a call-to-action question.
- **Mimicry:** Learns from your top-performing manual posts.

---
Built with ❤️ by Serhii Makarov & his AI Assistant.
