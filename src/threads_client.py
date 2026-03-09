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

    def get_auth_url(self, scopes=['threads_basic', 'threads_content_publish', 'threads_manage_replies', 'threads_manage_insights', 'threads_delete']):
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
        return token_data

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

    def like_post(self, post_id):
        """
        Likes a thread post (or reply).
        """
        url = f"{self.BASE_URL}/{post_id}/likes"
        params = {
            'access_token': self.access_token
        }
        response = requests.post(url, params=params)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"DEBUG: Like failed for {post_id}. Status: {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
            raise e
        return response.json()

    def get_replies(self, post_id):
        url = f"{self.BASE_URL}/{post_id}/replies"
        params = {
            'fields': 'id,text,timestamp,username',
            'access_token': self.access_token
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def create_reply_container(self, reply_to_id, text):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads"
        data = {
            'media_type': 'TEXT',
            'text': text,
            'reply_to_id': reply_to_id,
            'access_token': self.access_token
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()['id']

    def post_text(self, text):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads"
        data = {
            'media_type': 'TEXT',
            'text': text,
            'access_token': self.access_token
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        container_id = response.json()['id']
        
        # Wait for container and publish
        time.sleep(3)
        return self.publish_container(container_id)

    def publish_container(self, container_id):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads_publish"
        data = {
            'creation_id': container_id,
            'access_token': self.access_token
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()['id']

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

    def get_insights(self):
        if not self.user_id: self.get_user_profile()
        url = f"{self.BASE_URL}/{self.user_id}/threads_insights"
        params = {
            'metric': 'views,likes,replies,reposts,quotes',
            'period': 'day',
            'access_token': self.access_token
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except:
            return {}
