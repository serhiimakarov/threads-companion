# Threads Scheduler & Analytics Bot

This project allows you to schedule posts to Threads and track basic statistics using the official Threads API.

## Prerequisites

- Python 3.8+
- A Meta for Developers App with Threads API access.

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Create a virtual environment and install dependencies:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**

    Copy `.env.example` to `.env`:

    ```bash
    cp .env.example .env
    ```

    Open `.env` and fill in your App ID, App Secret, and Redirect URI.

## Meta App Setup

1.  Go to [Meta for Developers](https://developers.facebook.com/).
2.  Create a new App (Type: "Use Case" -> "Threads" or "Other" -> "Threads").
3.  In the App Dashboard, go to **Threads** settings.
4.  Add your **Redirect URI** (e.g., `https://localhost/` or any URL you control).
5.  Get your **App ID** and **App Secret** from the App settings.
6.  Add the **Threads API** product to your app.

## Authentication

Run the auth command to generate an access token:

```bash
./venv/bin/python3 manage.py auth
```

Follow the on-screen instructions:
1.  Open the provided URL in your browser.
2.  Authorize the app.
3.  You will be redirected to your Redirect URI.
4.  Copy the `code` parameter from the URL (e.g., `...&code=YOUR_CODE_HERE#_`).
5.  Paste the code into the terminal.
6.  Copy the generated `THREADS_ACCESS_TOKEN` and add it to your `.env` file.

## Usage

### Schedule a Post

```bash
./venv/bin/python3 manage.py add "Hello World from CLI!" --time "2023-10-27 10:00"
```

### List Pending Posts

```bash
./venv/bin/python3 manage.py list
```

### Run the Scheduler

Start the scheduler process. This will check for pending posts every 5 minutes and publish them. It also fetches stats daily.

```bash
./venv/bin/python3 manage.py run
```

*Note: Keep this process running in the background (e.g., using `screen`, `tmux`, or `nohup`).*

### View Stats

```bash
./venv/bin/python3 manage.py stats
```

## Project Structure

- `src/`: Source code.
- `manage.py`: CLI entry point.
- `threads_scheduler.db`: SQLite database (created automatically).
