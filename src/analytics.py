import collections
import statistics
from datetime import datetime

def get_weekly_summary():
    """
    Reads the last 7 days of stats from the database and returns a trend summary.
    """
    import sqlite3
    from src.config import DATABASE_PATH
    from datetime import datetime, timedelta

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    seven_days_ago = (datetime.now() - timedelta(days=7)).date()

    cursor.execute('''
        SELECT metric_name, SUM(metric_value) 
        FROM stats 
        WHERE metric_date >= ? 
        GROUP BY metric_name
    ''', (seven_days_ago,))

    weekly_stats = cursor.fetchall()
    conn.close()

    if not weekly_stats:
        return "No data collected yet for this week."

    summary = "Weekly Performance:\n"
    for name, value in weekly_stats:
        summary += f"- {name}: {value}\n"

    return summary

def analyze_user_profile(client):
    """
    Analyzes user profile and posts to return structured insights.
    """
    profile = client.get_user_profile()
    threads_data = client.get_user_threads(limit=50)
    posts = threads_data.get('data', [])
    
    if not posts:
        return None

    # --- Metrics ---
    timestamps = []
    lengths = []
    words = []
    media_types = collections.Counter()
    engagement_data = []
    
    for post in posts:
        text = post.get('text', '')
        media_type = post.get('media_type', 'UNKNOWN')
        timestamp_str = post.get('timestamp')
        
        # Engagement
        likes = post.get('like_count') or 0
        replies = post.get('reply_count') or 0
        reposts = post.get('repost_count') or 0
        engagement_score = (likes * 1.0) + (replies * 2.0) + (reposts * 3.0)
        
        if text:
            lengths.append(len(text))
            engagement_data.append({'text': text, 'score': engagement_score})
            for word in text.split():
                clean_word = "".join(c for c in word if c.isalnum()).lower()
                if len(clean_word) > 3:
                    words.append(clean_word)
        
        if timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            timestamps.append(dt)
        
        media_types[media_type] += 1

    # Sorting by performance
    top_performing = sorted(engagement_data, key=lambda x: x['score'], reverse=True)[:5]

    # Analysis
    hours = [t.hour for t in timestamps]
    peak_hour = statistics.mode(hours) if hours else 9
    
    avg_len = statistics.mean(lengths) if lengths else 0
    common_words = [w[0] for w in collections.Counter(words).most_common(10)]

    return {
        'username': profile.get('username'),
        'peak_hour': peak_hour,
        'avg_length': int(avg_len),
        'media_mix': dict(media_types),
        'top_words': common_words,
        'top_performing_posts': [p['text'] for p in top_performing],
        'post_count': len(posts)
    }
