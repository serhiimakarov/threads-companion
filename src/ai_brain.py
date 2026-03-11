import json
from google import genai
import ollama
import os
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = None
        
        if self.provider == 'gemini' and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                models = self.gemini_client.models.list()
                flash_models = [m.name for m in models if 'flash' in m.name.lower()]
                if flash_models:
                    self.gemini_model_id = flash_models[0].split('/')[-1]
                    print(f"✨ Dynamic AI Selection: Using {self.gemini_model_id}")
                else:
                    self.gemini_model_id = 'gemini-1.5-flash'
            except Exception as e:
                print(f"⚠️ Failed to dynamic init Gemini: {e}. Switching to Ollama.")
                self.provider = 'ollama'
        else:
            self.provider = 'ollama'

        if self.provider == 'ollama':
            try:
                self.ollama_client = ollama.Client(host=OLLAMA_HOST)
                print(f"🤖 Local Brain Ready (Ollama: {OLLAMA_MODEL})")
            except:
                print("⚠️ Ollama not reachable.")

    def is_active(self): return True

    def _generate(self, prompt, expect_json=False):
        if self.provider == 'gemini':
            try:
                config = {'response_mime_type': 'application/json'} if expect_json else None
                res = self.gemini_client.models.generate_content(
                    model=self.gemini_model_id, 
                    contents=prompt, 
                    config=config
                )
                return res.text.strip()
            except Exception as e:
                print(f"⚠️ Gemini generate error: {e}")
                raise e
        else:
            format_type = 'json' if expect_json else None
            res = self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
            return res['response'].strip()

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"Describe the 'Social Avatar' based on these posts: {posts_text}. Recent success: {top_posts}. 2-3 sentences."
        try:
            return self._generate(prompt)
        except:
            return "A technical DIY enthusiast and software engineer focusing on automation."

    def generate_quote_comment(self, persona, post_text):
        prompt = f"""
        Persona: {persona}
        Someone else's post: "{post_text}"
        TASK: Write a short (max 250 chars) comment to add to this post when quoting it.
        Be smart, additive, or slightly provocative. Plain English. End with a question if it fits.
        """
        try:
            return self._generate(prompt).replace('"', '')
        except:
            return "This is a great point. What's your take on this?"

    def generate_external_comment(self, persona, post_text):
        prompt = f"""
        Persona: {persona}
        Strangers post: "{post_text}"
        Write a short (max 200 chars), smart, witty comment to attract attention.
        CRITICAL: Plain English. NO PLACEHOLDERS.
        """
        try:
            return self._generate(prompt).replace('"', '')
        except:
            return "Great post! Always interesting to see these kind of insights."

    def generate_image_prompt(self, post_text):
        prompt = f"""
        Post Text: "{post_text}"
        TASK: Generate a simple, artistic image prompt for an AI image generator (like DALL-E or Midjourney).
        The image should represent the theme of the post.
        Return ONLY the prompt string, no meta-text. Max 100 characters.
        """
        try:
            return self._generate(prompt)
        except:
            return "Minimalist futuristic technology and DIY electronics."

    def generate_post(self, persona, context=None, examples=None):
        prompt = f"""
        Persona: {persona}
        Context: {context}
        Examples: {examples}
        TASK: Create a Threads post that drives replies. 
        Return JSON ONLY: {{"text": "your post text", "wants_image": bool, "image_theme": "short theme"}}
        No hashtags. End with a question. Plain English. Max 400 chars.
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"text": None, "wants_image": False, "image_theme": None}

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        Persona: {persona}
        Peak: {peak_hour}:00
        Data: {performance_report}
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "viral topic"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "General Tech update"}]}

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"Persona: {persona}. Post: {post_text}. Reply to: {reply_text}. Return JSON: {{\"like\": true, \"reply\": \"text\"}}"
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point!"}
