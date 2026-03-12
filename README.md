# Threads Shadow AI Agent 🤖🧵🦾

A fully autonomous social media agent designed to "shadow" a reference account, optimize engagement using AI, and manage a secondary account with zero human intervention. Optimized for the 2025 Threads algorithm and Raspberry Pi execution.

## 🌟 Key Features

- **Dual-Account "Shadowing":** Analyzes a source account to learn vibe, topics, and timing.
- **Autonomous Strategy:** Decides posting slots and topics based on historical performance and niche trends.
- **AI Brain (Cloud/Local):** Supports Google Gemini (with dynamic model selection) and local LLMs via Ollama.
- **Visual Evolution:** Automatically generates themed AI images (Pollinations.ai) and hosts them (ImgBB) for rich media posts.
- **Smart Engagement:** 
    - **Auto-Replies:** Detects and responds to comments in real-time (API-based).
    - **Smart Mentions:** Mentions niche leaders to drive external reach.
    - **Deep Cookie Engine:** Uses system-level `curl` with cookie jars to simulate browser actions (likes) safely on ARM/RPi.
- **Human-in-the-loop (Approval Mode):** AI generates drafts in `pending_approval` status. You review and approve via CLI before they go live.
- **Session Health Monitor:** Proactively checks if cookies are valid and sends "SOS" to Telegram if a refresh is needed.
- **Strict Language Policy:** Always communicates in English to maintain a professional international profile.

## 🛠️ Tech Stack

- **Python 3.11+**
- **System Curl & Requests** (Lightweight Web Simulation)
- **Google GenAI / Ollama** (LLM Brain)
- **SQLite** (Persistent Queue & Stats)
- **Telegram Bot API** (Notifications & Monitoring)

## 🚀 Quick Start

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials
Copy `.env.example` to `.env` and fill in:
- `THREADS_ACCESS_TOKEN_SOURCE`: Reference account.
- `THREADS_ACCESS_TOKEN_TARGET`: Bot-controlled account.
- `GEMINI_API_KEY`: For the brain.
- `TELEGRAM_BOT_TOKEN` & `CHAT_ID`: For alerts.
- `IMGBB_API_KEY`: For image hosting.

### 3. Initialize Session (The "IP-Match" Hack)
To bypass Meta's IP-binding, log in via an SSH tunnel:
1. `ssh -D 8080 -N pi@your_rpi_ip`
2. Set browser proxy to SOCKS5 `127.0.0.1:8080`.
3. Log in to `threads.com` and run:
```bash
./venv/bin/python3 src/session_manager.py
```

### 4. Run the Bot
```bash
./bin/python3 manage.py run
```

## 📊 CLI Commands

- `./manage.py list`: View approval queue and approved scheduled posts.
- `./manage.py approve [ID]`: Move a draft to the active publishing queue.
- `./manage.py auto --dry-run`: Test AI generation without saving.
- `./manage.py stats --refresh`: Fetch and view latest engagement metrics.
- `./manage.py delete [ID]`: Remove any post from the database.

## 🐳 Deployment (RPi)
The bot is designed to run 24/7 as a background process or via Docker. Use `nohup` for simple persistence:
```bash
nohup ./bin/python3 manage.py run > bot.log 2>&1 &
```

---
Built with ❤️ by Serhii Makarov & his AI Assistant.
