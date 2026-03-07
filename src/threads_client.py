import requests
import urllib.parse
from datetime import datetime
import time

class ThreadsClient:
    BASE_URL = "https://graph.threads.net/v1.0"
    
    def __init__(self, app_id, app_secret, redirect_uri, access_token=None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.user_id = None

    def get_auth_url(self, scopes=['threads_basic', 'threads_content_publish', 'threads_manage_replies', 'threads_manage_insights', 'threads_delete', 'threads_keyword_search', 'threads_profile_discovery']):
        params = {
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'scope': ','.join(scopes),
            'response_type': 'code'
        }
        return f"https://threads.net/oauth/authorize?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code):
        url = "https://graph.threads.net/oauth/access_token"
        data = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data['access_token']
        
        # Upgrade to long-lived
        try:
            long_lived_data = self.get_long_lived_token(self.access_token)
            self.access_token = long_lived_data['access_token']
            token_data['access_token'] = self.access_token
        except: pass
        
        return token_data

    def get_long_lived_token(self, short_lived_token):
        url = "https://graph.threads.net/access_token"
        params = {
            'grant_type': 'th_exchange_token',
            'client_secret': self.app_secret,
            'access_token': short_lived_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_profile(self):
        url = f"{self.BASE_URL}/me"
        params = {
            'fields': 'id,username,name,threads_profile_picture_url,threads_biography',
            'access_token': self.access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        profile = response.json()
        self.user_id = profile['id']
        return profile

    def search_posts(self, query, limit=10):
        """
        Searches for public posts by keyword. Requires threads_keyword_search.
        """
        url = f"{self.BASE_URL}/threads/search"
        params = {
            'q': query,
            'limit': limit,
            'access_token': self.access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def like_post(self, post_id):
        """
        Likes a post.
        Note: Per documentation, likes might require a POST to /{media-id}/likes
        """
        url = f"{self.BASE_URL}/{post_id}/likes"
        params = {'access_token': self.access_token}
        # Try both POST and empty body as some Graph API versions are picky
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()

    def delete_post(self, post_id):
        """
        Deletes a post. Requires threads_delete.
        """
        url = f"{self.BASE_URL}/{post_id}"
        params = {'access_token': self.access_token}
        response = requests.delete(url, params=params)
        response.raise_for_status()
        return response.json()

    def post_text(self, text):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads"
        data = {'media_type': 'TEXT', 'text': text, 'access_token': self.access_token}
        res = requests.post(url, data=data)
        res.raise_for_status()
        container_id = res.json()['id']
        
        # Wait and publish
        time.sleep(3)
        url_pub = f"{self.BASE_URL}/{self.user_id}/threads_publish"
        res_pub = requests.post(url_pub, data={'creation_id': container_id, 'access_token': self.access_token})
        res_pub.raise_for_status()
        return res_pub.json()['id']

    def get_user_threads(self, limit=20):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads"
        params = {
            'fields': 'id,text,timestamp,like_count,reply_count,repost_count',
            'limit': limit,
            'access_token': self.access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_replies(self, post_id):
        url = f"{self.BASE_URL}/{post_id}/replies"
        params = {'fields': 'id,text,username', 'access_token': self.access_token}
        return requests.get(url, params=params).json()

    def get_insights(self):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads_insights"
        params = {
            'metric': 'views,likes,replies,reposts,quotes',
            'period': 'day',
            'access_token': self.access_token
        }
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
            return res.json()
        except:
            # Fallback to manual
            threads = self.get_user_threads(limit=50)
            likes = sum((p.get('like_count') or 0) for p in threads.get('data', []))
            replies = sum((p.get('reply_count') or 0) for p in threads.get('data', []))
            return {'data': [{'name': 'likes', 'values': [{'value': likes}]}, {'name': 'replies', 'values': [{'value': replies}]}]}
