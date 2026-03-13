import json
import os
from src.threads_client import ThreadsClient
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE

def fetch_all_source_data(limit=100):
    """
    Fetches as many posts and replies as possible from the source account.
    """
    print(f"📡 Step 1: Connecting to Source account...")
    if not THREADS_ACCESS_TOKEN_SOURCE:
        print("❌ Error: THREADS_ACCESS_TOKEN_SOURCE is missing.")
        return

    client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE)
    
    all_data = {
        "profile": {},
        "threads": [],
        "replies": []
    }

    try:
        # 1. Get Profile
        print("👤 Fetching profile info...")
        all_data["profile"] = client.get_user_profile()
        
        # 2. Get Threads (Posts)
        print(f"📝 Fetching up to {limit} threads...")
        threads_response = client.get_user_threads(limit=limit)
        all_data["threads"] = threads_response.get('data', [])
        
        # 3. Get Replies (This is tricky via API, usually we get replies TO our posts)
        # But we can also look at what we've been replying to if the API allows.
        # Currently our client gets replies to a specific post.
        print(f"💬 Analyzing replies within {len(all_data['threads'])} threads...")
        for thread in all_data["threads"]:
            try:
                thread_id = thread['id']
                replies_response = client.get_replies(thread_id)
                thread_replies = replies_response.get('data', [])
                # Filter replies made by the source user themselves
                my_replies = [r for r in thread_replies if r.get('username') == all_data["profile"].get('username')]
                all_data["replies"].extend(my_replies)
            except Exception as e:
                print(f"⚠️ Could not fetch replies for thread {thread['id']}: {e}")

        # Save to file
        os.makedirs("data", exist_ok=True)
        file_path = "data/source_raw_data.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Data collection complete! Total threads: {len(all_data['threads'])}, Total own replies found: {len(all_data['replies'])}")
        print(f"📁 Saved to {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Big Fetch failed: {e}")
        return None

if __name__ == "__main__":
    fetch_all_source_data()
