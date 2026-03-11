import json
from google import genai
import ollama
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        if self.provider == 'gemini' and GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            self.gemini_model_id = 'gemini-1.5-flash'
        else:
            self.provider = 'ollama'
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)

    def is_active(self): return True

    def _generate(self, prompt, expect_json=False):
        if self.provider == 'gemini':
            config = {'response_mime_type': 'application/json'} if expect_json else None
            return self.gemini_client.models.generate_content(model=self.gemini_model_id, contents=prompt, config=config).text.strip()
        else:
            format_type = 'json' if expect_json else None
            return self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)['response'].strip()

    def generate_post(self, persona, context=None, examples=None):
        prompt = f"""
        You are: {persona}
        Context: {context}
        Examples: {examples}
        
        TASK: Create a VIRAL Threads post.
        RULES:
        1. NO hashtags, NO placeholders.
        2. Must end with a compelling QUESTION to start a discussion.
        3. Mention a niche authority if relevant (e.g. @raspberrypi, @python.learning).
        4. Use human-like casual tech slang.
        5. Max 400 chars.
        """
        try:
            content = self._generate(prompt).replace('"', '')
            return content
        except: return None

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        You are: {persona}
        Perf: {performance_report}
        Strategy for next 24h. Focus on DISCUSSIONS.
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "viral topic"}}]}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "Controversial tech opinion"}]}

    def evaluate_interaction(self, persona, post_text, reply_text):
        # AI now ALWAYS wants to reply to boost engagement
        prompt = f"""
        You are: {persona}
        Reply to this comment: "{reply_text}" on your post: "{post_text}"
        Be friendly, smart, and keep the conversation going.
        Return JSON ONLY: {{"like": true, "reply": "your reply text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point! What do you think about the future of this technology?"}
