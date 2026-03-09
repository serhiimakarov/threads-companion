import tweepy
from src.config import X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, X_BEARER_TOKEN

class XClient:
    def __init__(self):
        self.api_key = X_API_KEY
        self.api_secret = X_API_SECRET
        self.access_token = X_ACCESS_TOKEN
        self.access_token_secret = X_ACCESS_TOKEN_SECRET
        self.bearer_token = X_BEARER_TOKEN
        
        # V2 Client (Recommended for modern apps)
        self.client_v2 = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            try:
                self.client_v2 = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
            except Exception as e:
                print(f"X Client V2 Init Error: {e}")
            
        # V1.1 API (Fallback)
        self.api_v1 = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            try:
                auth = tweepy.OAuth1UserHandler(self.api_key, self.api_secret, self.access_token, self.access_token_secret)
                self.api_v1 = tweepy.API(auth)
            except Exception as e:
                print(f"X API V1 Init Error: {e}")

    def is_active(self):
        return self.client_v2 is not None or self.api_v1 is not None

    def post_text(self, text):
        if not self.is_active():
            raise ValueError("X API credentials missing.")
        
        # Try V2 first
        try:
            print("Attempting X V2 post...")
            response = self.client_v2.create_tweet(text=text)
            return response.data['id']
        except Exception as v2_err:
            print(f"X V2 post failed ({v2_err}). Trying V1.1 fallback...")
            # Fallback to V1.1
            try:
                status = self.api_v1.update_status(status=text)
                return status.id
            except Exception as v1_err:
                print(f"X V1.1 fallback also failed: {v1_err}")
                raise v2_err # Raise original V2 error if both fail

    def get_user_tweets(self, user_id=None, limit=10):
        if not self.client_v2: return []
        try:
            if user_id is None:
                user_id = self.client_v2.get_me().data.id
            response = self.client_v2.get_users_tweets(id=user_id, max_results=limit)
            return response.data
        except Exception as e:
            print(f"X fetch tweets error: {e}")
            return []
