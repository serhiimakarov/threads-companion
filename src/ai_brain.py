import json
from google import genai
import ollama
import os
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = 'gemini-2.0-flash'
        
        if self.provider == 'gemini' and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            except:
                print("⚠️ Failed to init Gemini. Switching to Ollama.")
                self.provider = 'ollama'
        else:
            self.provider = 'ollama'

        if self.provider == 'ollama':
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)
            print(f"🤖 Local Brain Ready (Ollama: {OLLAMA_MODEL})")

    def is_active(self): return True

    def _generate(self, prompt, expect_json=False):
        if self.provider == 'gemini':
            try:
                config = {'response_mime_type': 'application/json'} if expect_json else None
                res = self.gemini_client.models.generate_content(model=self.gemini_model_id, contents=prompt, config=config)
                return res.text.strip()
            except Exception as e:
                print(f"⚠️ Gemini error ({e}). Falling back to Ollama for this request...")
                format_type = 'json' if expect_json else None
                res = ollama.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
                return res['response'].strip()
        else:
            format_type = 'json' if expect_json else None
            res = self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
            return res['response'].strip()

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"Describe the 'Social Avatar' based on these posts: {posts_text}. Recent success: {top_posts}. 2-3 sentences."
        return self._generate(prompt)

    def generate_post(self, persona, context=None, examples=None):
        prompt = f"""
        Persona: {persona}
        Context: {context}
        Examples: {examples}
        TASK: Create a Threads post that drives replies. 
        No hashtags. End with a question. Plain English. Max 400 chars.
        """
        return self._generate(prompt).replace('"', '')

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        Persona: {persona}
        Peak: {peak_hour}:00
        Data: {performance_report}
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "viral topic"}}]}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "Tech opinion"}]}

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"Persona: {persona}. Post: {post_text}. Reply to: {reply_text}. Return JSON: {{\"like\": true, \"reply\": \"text\"}}"
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point!"}
