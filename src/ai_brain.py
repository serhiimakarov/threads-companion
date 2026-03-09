import json
from google import genai
import ollama
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        
        if self.provider == 'gemini':
            if not GEMINI_API_KEY:
                print("⚠️ GEMINI_API_KEY missing. Falling back to local Ollama.")
                self.provider = 'ollama'
            else:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                try:
                    models = self.gemini_client.models.list()
                    available = [m.name for m in models]
                    self.gemini_model_id = 'gemini-1.5-flash' if 'gemini-1.5-flash' in available else available[0]
                except:
                    self.gemini_model_id = 'gemini-1.5-flash'

        if self.provider == 'ollama':
            self.ollama_model = OLLAMA_MODEL
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)
            print(f"🤖 Local Brain Initialized (Ollama: {self.ollama_model} at {OLLAMA_HOST})")

    def is_active(self):
        return True

    def _generate(self, prompt, expect_json=False):
        if self.provider == 'gemini':
            config = {'response_mime_type': 'application/json'} if expect_json else None
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_id,
                contents=prompt,
                config=config
            )
            return response.text.strip()
        else:
            format_type = 'json' if expect_json else None
            response = self.ollama_client.generate(model=self.ollama_model, prompt=prompt, format=format_type)
            return response['response'].strip()

    def _safety_filter(self, text):
        forbidden_keywords = ["russia", "russian", "putin", "kremlin", "moscow", "rossiya"]
        text_lower = text.lower()
        for word in forbidden_keywords:
            if word in text_lower:
                print(f"🚨 SAFETY TRIGGER: Blocked post containing forbidden word '{word}'")
                return False
        return True

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"""
        Based on these recent Threads posts and top-performing posts, describe their "Social Avatar".
        Recent Posts: {posts_text}
        Top Performing Posts: {top_posts if top_posts else "None available."}
        Provide a concise 2-3 sentence description.
        """
        try:
            return self._generate(prompt)
        except Exception as e:
            print(f"AI Persona Error: {e}")
            return "A technical DIY enthusiast and software engineer."

    def generate_post(self, persona, context=None, examples=None):
        prompt = f"""
        You are the following Social Avatar: {persona}
        
        Using the examples of top performing posts:
        {examples}
        
        Generate a new Threads post for the following context or topic: "{context}"
        
        CRITICAL RULES:
        1. Write in PLAIN ENGLISH only. No metadata or notes.
        2. BE AUTHENTIC. Use the same tone, slang, and formatting as in the examples.
        3. NO PLACEHOLDERS. Never use brackets like [topic], [name], or [cause]. If you don't have a specific detail, don't mention it.
        4. NO HASHTAGS. Threads prefers natural text.
        5. NO PRO-RUSSIAN content. The user is Ukrainian.
        6. END WITH A QUESTION or a thought-provoking statement to drive replies.
        7. LIMIT TO 400 characters max.
        
        Post content:
        """
        try:
            content = self._generate(prompt).replace('"', '')
            if "\n\n" in content:
                content = content.split("\n\n")[0].strip()
            
            for noise in ["Here is a post:", "Post content:", "Post:"]:
                content = content.replace(noise, "").strip()
            
            if not self._safety_filter(content):
                return None
            return content
        except Exception as e:
            print(f"AI Post Error: {e}")
            return None

    def generate_external_comment(self, persona, post_text):
        prompt = f"""
        You are: {persona}
        Strangers post: "{post_text}"
        Write a short (max 200 chars), smart, witty comment to attract attention.
        CRITICAL: Plain English. NO PLACEHOLDERS.
        """
        try:
            return self._generate(prompt).replace('"', '')
        except Exception as e:
            print(f"AI External Comment Error: {e}")
            return None

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        You are: {persona}
        Someone replied: "{reply_text}" to your post: "{post_text}"
        Return JSON ONLY: {{"like": bool, "reply": "string or null"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {'like': True, 'reply': None}

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        You are the following Social Avatar: {persona}
        
        CURRENT PERFORMANCE DATA:
        {performance_report if performance_report else "No historical data yet."}
        
        STRATEGIC GOAL:
        - Peak Posting Hour: {peak_hour}:00
        - Optimize for GROWTH and ENGAGEMENT.
        
        TASK:
        Decide your posting strategy for the next 24 hours.
        Adjust your posting frequency (1-4 posts) and topics based on what has worked recently according to the performance data.
        If a certain topic failed, try a different approach.
        
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "short description"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "General DIY/Tech update"}]}
