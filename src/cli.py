import argparse
import os
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv
from src.database import init_db, add_scheduled_post, get_stats, get_all_pending, get_pending_approval, mark_post_status
from src.scheduler import run_scheduler
from src.threads_client import ThreadsClient

def main():
    # Force reload of environment variables within the main function
    load_dotenv(override=True)
    
    # Map variables to locals to avoid scope issues
    APP_ID = os.getenv('THREADS_APP_ID')
    APP_SECRET = os.getenv('THREADS_APP_SECRET')
    REDIRECT_URI = os.getenv('THREADS_REDIRECT_URI')
    TOKEN_TARGET = os.getenv('THREADS_ACCESS_TOKEN_TARGET')

    parser = argparse.ArgumentParser(description="Threads Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add post
    add_parser = subparsers.add_parser("add", help="Schedule a new post")
    add_parser.add_argument("content", help="Text content of the post")
    add_parser.add_argument("--time", help="Scheduled time (YYYY-MM-DD HH:MM)", required=True)
    add_parser.add_argument("--platform", choices=['threads', 'x'], default='threads', help="Platform (default: threads)")

    # List posts
    subparsers.add_parser("list", help="List pending posts")
    
    # Approve post
    approve_parser = subparsers.add_parser("approve", help="Approve a post for publishing")
    approve_parser.add_argument("id", type=int, help="The ID of the post to approve")

    # Delete post
    delete_parser = subparsers.add_parser("delete", help="Delete a scheduled post by ID")
    delete_parser.add_argument("id", type=int, help="The ID of the post to delete")

    # Auto Agent
    auto_parser = subparsers.add_parser("auto", help="Run the autonomous agent once")
    auto_parser.add_argument("--dry-run", action="store_true", help="Generate posts but don't save them to the database")

    # View stats
    stats_parser = subparsers.add_parser("stats", help="View collected stats")
    stats_parser.add_argument("--refresh", action="store_true", help="Fetch fresh stats from API before displaying")

    # Run scheduler
    subparsers.add_parser("run", help="Run the scheduler daemon")

    # Auth
    auth_parser = subparsers.add_parser("auth", help="Authenticate with Threads")
    auth_parser.add_argument("--account", choices=['source', 'target'], default='target', help="Which account to authenticate (default: target/bot)")

    args = parser.parse_args()

    init_db()

    if args.command == "add":
        try:
            scheduled_time = datetime.strptime(args.time, "%Y-%m-%d %H:%M")
            post_id = add_scheduled_post(args.content, scheduled_time, platform=args.platform)
            print(f"Post scheduled with ID: {post_id} for {scheduled_time} on {args.platform}")
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD HH:MM")

    elif args.command == "list":
        pending = get_all_pending()
        approval = get_pending_approval()
        
        if not pending and not approval:
            print("📭 No posts in queue.")
        else:
            if approval:
                print("\n📝 WAITING FOR APPROVAL")
                print("=" * 90)
                for post in approval:
                    post_id, content, platform, time_str = post
                    print(f"🆔 ID: {post_id} | 🕒 {time_str} | 📱 {platform.upper()}")
                    print(f"📝 CONTENT:")
                    print(f"{content}")
                    print("-" * 90)
            
            if pending:
                print("\n📅 SCHEDULED POSTS QUEUE (APPROVED)")
                print("=" * 90)
                for post in pending:
                    post_id, content, platform, time_str = post
                    print(f"🆔 ID: {post_id} | 🕒 {time_str} | 📱 {platform.upper()}")
                    print(f"📝 CONTENT:")
                    print(f"{content}")
                    print("-" * 90)
            
            print(f"Total: {len(approval)} waiting approval, {len(pending)} approved pending.\n")

    elif args.command == "approve":
        mark_post_status(args.id, 'pending')
        print(f"✅ Post {args.id} approved and moved to active queue.")

    elif args.command == "delete":
        import sqlite3
        from src.config import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scheduled_posts WHERE id = ?", (args.id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ Post {args.id} has been killed.")
        else:
            print(f"❌ Post {args.id} not found.")
        conn.close()

    elif args.command == "auto":
        from src.agent import run_agent
        run_agent(dry_run=args.dry_run)

    elif args.command == "stats":
        if args.refresh:
            print("🔄 Fetching fresh statistics from Threads API...")
            from src.database import log_stat
            client = ThreadsClient(APP_ID, APP_SECRET, REDIRECT_URI, TOKEN_TARGET)
            try:
                insights = client.get_insights()
                if 'data' in insights:
                    for metric in insights['data']:
                        name = metric['name']
                        values = metric.get('values', [])
                        if values:
                            latest_value = values[-1]['value']
                            log_stat(name, latest_value, platform='threads')
                            print(f"✅ Updated: {name} = {latest_value}")
                else:
                    print("⚠️ No fresh data available from API.")
            except Exception as e:
                print(f"❌ Failed to refresh stats: {e}")

        stats = get_stats()
        if not stats:
            print("No stats collected yet.")
        else:
            print(f"{'Date':<12} {'Platform':<10} {'Metric':<20} {'Value':<10}")
            print("-" * 55)
            for stat in stats:
                print(f"{stat[0]:<12} {stat[3]:<10} {stat[1]:<20} {stat[2]:<10}")

    elif args.command == "run":
        run_scheduler()

    elif args.command == "auth":
        if not APP_ID or not APP_SECRET or not REDIRECT_URI:
            print(f"Please check your .env. Required: THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI.")
            return

        client = ThreadsClient(APP_ID, APP_SECRET, REDIRECT_URI)
        auth_url = client.get_auth_url()
        print(f"\n=== Threads Authentication ({args.account.upper()} ACCOUNT) ===")
        print(f"DEBUG: Redirect URI being sent: {REDIRECT_URI}")
        print(f"1. Open this URL in your browser:\n\n{auth_url}\n")
        print("2. Authorize the app.")
        print("3. You will be redirected to your Redirect URI with a `code` parameter.")
        
        code = input("\nEnter the code: ").strip()
        if "#_" in code:
            code = code.split("#_")[0]
        if "?" in code:
             parsed = urllib.parse.urlparse(code)
             code = urllib.parse.parse_qs(parsed.query).get('code', [code])[0]

        if code:
            try:
                token_data = client.exchange_code_for_token(code)
                print("\nAuthentication successful!")
                env_var = "THREADS_ACCESS_TOKEN_TARGET" if args.account == 'target' else "THREADS_ACCESS_TOKEN_SOURCE"
                print(f"Update your .env with:\n{env_var}={token_data['access_token']}")
            except Exception as e:
                print(f"Authentication failed: {e}")
        else:
            print("Operation cancelled.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
