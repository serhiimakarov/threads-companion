import sqlite3
from src.config import DATABASE_PATH

def get_target_performance():
    """
    Analyzes the bot's own performance from the database.
    Returns top performing topics and average engagement.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get last 20 posted items with their stats
    cursor.execute('SELECT metric_name, metric_value FROM stats WHERE platform = "threads" ORDER BY metric_date DESC LIMIT 10')
    stats = cursor.fetchall()
    
    # Get last 10 posted contents to analyze their "vibe"
    cursor.execute('SELECT content FROM scheduled_posts WHERE status = "posted" ORDER BY scheduled_time DESC LIMIT 10')
    recent_posts = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return {
        "recent_stats": stats,
        "recent_posts": recent_posts
    }

def analyze_user_profile(client):
    """
    Analyzes the SOURCE user profile to get initial vibe and peak hours.
    """
    try:
        threads = client.get_user_threads(limit=30)
        data = threads.get('data', [])
        
        if not data:
            return {"peak_hour": 10, "top_performing_posts": []}

        # Calculate peak hour
        hours = []
        for post in data:
            ts = post.get('timestamp')
            if ts:
                dt = ts.split('T')[1].split(':')[0]
                hours.append(int(dt))
        
        peak_hour = max(set(hours), key=hours.count) if hours else 10
        
        # Get top 3 posts by engagement
        sorted_posts = sorted(data, key=lambda x: (x.get('like_count', 0) + x.get('reply_count', 0)), reverse=True)
        top_posts = [p.get('text', '') for p in sorted_posts[:3] if p.get('text')]
        
        return {
            "peak_hour": peak_hour,
            "top_performing_posts": top_posts
        }
    except Exception as e:
        print(f"Profile analysis failed: {e}")
        return {"peak_hour": 10, "top_performing_posts": []}

def get_weekly_summary():
    """
    Generates a strategic summary for the user and the AI itself.
    """
    from src.ai_brain import AIBrain
    
    performance = get_target_performance()
    brain = AIBrain()
    
    stats_str = "\n".join([f"{s[0]}: {s[1]}" for s in performance['recent_stats']])
    posts_str = "\n---\n".join(performance['recent_posts'])
    
    prompt = f"""
    Analyze the following performance data for our Threads Bot:
    
    Current Stats:
    {stats_str}
    
    Recent Posts:
    {posts_str}
    
    Provide a brief strategic summary:
    1. What topics seem to work?
    2. What should we change in our tone or timing?
    3. How is our growth progressing?
    """
    
    try:
        return brain._generate(prompt)
    except:
        return "Growth is steady. Continue following the current persona."
