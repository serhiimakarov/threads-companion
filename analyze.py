import os
import sys
import collections
import statistics
from datetime import datetime
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE
from src.threads_client import ThreadsClient

# Add local path for imports if needed
sys.path.append(os.getcwd())

def analyze_threads():
    if not THREADS_ACCESS_TOKEN_SOURCE:
        print("Error: Please run './manage.py auth' first.")
        return

    print("🔍 Initializing Threads Analyzer...")
    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE)
    
    try:
        profile = client.get_user_profile()
        print(f"👤 Analyzing user: @{profile.get('username')} ({profile.get('name')})")
        
        print("📥 Fetching recent threads...")
        # Fetch up to 50 recent posts
        threads_data = client.get_user_threads(limit=50)
        posts = threads_data.get('data', [])
        
        if not posts:
            print("❌ No threads found to analyze! Go post something first! 😉")
            return

        print(f"📊 Analyzing {len(posts)} recent posts...\n")
        
        # --- Metrics ---
        timestamps = []
        lengths = []
        words = []
        media_types = collections.Counter()
        
        for post in posts:
            text = post.get('text', '')
            media_type = post.get('media_type', 'UNKNOWN')
            timestamp_str = post.get('timestamp') # ISO format
            
            # Text Analysis
            if text:
                lengths.append(len(text))
                # Simple word tokenization (lowercase, strip punctuation)
                for word in text.split():
                    clean_word = "".join(c for c in word if c.isalnum()).lower()
                    if len(clean_word) > 3: # Skip small words
                        words.append(clean_word)
            
            # Timing Analysis
            if timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamps.append(dt)
            
            media_types[media_type] += 1

        # --- Report Generation ---
        
        # 1. Posting Habits (Time of Day)
        hours = [t.hour for t in timestamps]
        most_common_hour = statistics.mode(hours) if hours else 0
        time_period = "Morning 🌅" if 5 <= most_common_hour < 12 else \
                      "Afternoon ☀️" if 12 <= most_common_hour < 17 else \
                      "Evening 🌆" if 17 <= most_common_hour < 22 else "Night 🌙"

        # 2. Verbosity
        avg_len = statistics.mean(lengths) if lengths else 0
        verbosity = "Silent Type 🤫" if avg_len < 20 else \
                    "Tweeter 🐦" if avg_len < 100 else \
                    "Storyteller 📖" if avg_len < 280 else "Novelist 📚"

        # 3. Top Words
        common_words = collections.Counter(words).most_common(5)
        top_topics = ", ".join([w[0] for w in common_words])

        print(f"--- 📝 {profile.get('username')}'s Threads Persona ---")
        print(f"🕒 **Peak Posting Time:** {most_common_hour}:00 ({time_period})")
        print(f"🗣️ **Verbosity:** {verbosity} (Avg {int(avg_len)} chars/post)")
        print(f"📸 **Media Mix:** {dict(media_types)}")
        if top_topics:
            print(f"🔑 **Obsessions (Top Keywords):** {top_topics}")
        
        print("\n--- 💡 Fun Prediction ---")
        if "TEXT" in media_types and media_types["TEXT"] > media_types.get("IMAGE", 0):
            print("🔮 You prefer words over pictures. A true intellectual!")
        elif "IMAGE" in media_types:
            print("🔮 A visual thinker! Your gallery is probably aesthetic.")
        else:
            print("🔮 You are a mysterious poster.")

        print("\nAnalyze complete! Have fun threading! 🧵")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    analyze_threads()
