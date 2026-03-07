import sqlite3
from src.config import DATABASE_PATH
from datetime import datetime

def get_connection():
    return sqlite3.connect(DATABASE_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            scheduled_time TIMESTAMP NOT NULL,
            platform TEXT DEFAULT 'threads',
            status TEXT DEFAULT 'pending', -- pending, posted, failed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration for existing table if platform column doesn't exist
    try:
        cursor.execute("ALTER TABLE scheduled_posts ADD COLUMN platform TEXT DEFAULT 'threads'")
    except sqlite3.OperationalError:
        pass # Already exists

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_date DATE NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            platform TEXT DEFAULT 'threads',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(metric_date, metric_name, platform)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_interactions (
            reply_id TEXT PRIMARY KEY,
            action TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

def is_interaction_processed(reply_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_interactions WHERE reply_id = ?', (reply_id,))
    res = cursor.fetchone()
    conn.close()
    return res is not None

def mark_interaction_processed(reply_id, action):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO processed_interactions (reply_id, action) VALUES (?, ?)', (reply_id, action))
    conn.commit()
    conn.close()

def add_scheduled_post(content, scheduled_time, platform='threads'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO scheduled_posts (content, scheduled_time, platform) VALUES (?, ?, ?)', (content, scheduled_time, platform))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def get_pending_posts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, platform FROM scheduled_posts WHERE status = 'pending' AND scheduled_time <= ?", (datetime.now(),))
    posts = cursor.fetchall()
    conn.close()
    return posts

def get_all_pending():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, content, platform, scheduled_time FROM scheduled_posts WHERE status = 'pending' ORDER BY scheduled_time ASC")
    posts = cursor.fetchall()
    conn.close()
    return posts

def mark_post_status(post_id, status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE scheduled_posts SET status = ? WHERE id = ?', (status, post_id))
    conn.commit()
    conn.close()

def log_stat(metric_name, value, platform='threads', date=None):
    if date is None:
        date = datetime.now().date()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO stats (metric_date, metric_name, metric_value, platform) 
        VALUES (?, ?, ?, ?)
        ON CONFLICT(metric_date, metric_name, platform) DO UPDATE SET
        metric_value = excluded.metric_value,
        updated_at = CURRENT_TIMESTAMP
    ''', (date, metric_name, value, platform))
    conn.commit()
    conn.close()

def get_stats(platform=None):
    conn = get_connection()
    cursor = conn.cursor()
    if platform:
        cursor.execute('SELECT metric_date, metric_name, metric_value, platform FROM stats WHERE platform = ? ORDER BY metric_date DESC, metric_name ASC', (platform,))
    else:
        cursor.execute('SELECT metric_date, metric_name, metric_value, platform FROM stats ORDER BY metric_date DESC, metric_name ASC')
    stats = cursor.fetchall()
    conn.close()
    return stats
