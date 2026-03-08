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
                # Discover Gemini model
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
        return True # Ollama is assumed active if installed

    def _generate(self, prompt, expect_json=False):
        """Internal helper to route generation to correct provider"""
        if self.provider == 'gemini':
            config = {'response_mime_type': 'application/json'} if expect_json else None
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_id,
                contents=prompt,
                config=config
            )
            return response.text.strip()
        else:
            # Ollama generation
            format_type = 'json' if expect_json else None
            response = self.ollama_client.generate(model=self.ollama_model, prompt=prompt, format=format_type)
            return response['response'].strip()

    def _safety_filter(self, text):
        """
        Final safety check to ensure no pro-Russian or forbidden content slips through.
        Returns True if safe, False if unsafe.
        """
        forbidden_keywords = [
            "russia", "russian", "putin", "kremlin", "moscow", 
            "rossiya", "rossiya", "z-army", "v-army", "special operation"
        ]
        text_lower = text.lower()
        for word in forbidden_keywords:
            if word in text_lower:
                print(f"🚨 SAFETY TRIGGER: Blocked post containing forbidden word '{word}'")
                return False
        return True

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"""
        Based on these recent Threads posts and top-performing posts, describe their "Social Avatar" or online persona.
        
        Recent Posts:
        {posts_text}
        
        Top Performing Posts:
        {top_posts if top_posts else "None available."}
        
        Provide a concise 2-3 sentence description of this persona.
        """
        try:
            return self._generate(prompt)
        except Exception as e:
            print(f"AI Persona Error: {e}")
            return "A versatile storyteller."

    def generate_post(self, persona, context=None, examples=None, mentor_style=None):
        prompt = f"""
        INSTRUCTION: You are a social media bot generating content for a PLAIN ENGLISH audience.
        
        REFERENCE PERSONA: {persona}
        {f"MENTOR STYLE: {mentor_style}" if mentor_style else ""}
        
        CRITICAL CONSTRAINTS:
        - LANGUAGE: Use ONLY Standard English. 
        - ALPHABET: Use ONLY Latin characters (A-Z).
        - GEOPOLITICS: The user is UKRAINIAN. 
        - SAFETY: NEVER generate content that is pro-Russian, mentions Russia in a positive light, or supports the aggressor state. 
        - SAFETY: Avoid any Russian terminology or cultural references.
        - Tone: Professional but tech-focused and relatable.
        
        CONTENT GOAL:
        - Topic: {context if context else "General tech/DIY update"}
        - Length: Max 280 characters.
        - Hook: Start with a strong statement.
        - Engagement: ALWAYS end with a direct question to the reader.
        
        Reference examples (translate the VIBE, not the language):
        {examples if examples else "None."}
        
        GENERATE ENGLISH POST CONTENT:
        (CRITICAL: Output ONLY the final post text. No explanations, no notes, no metadata, no 'Here is your post' markers. ONLY the content itself.)
        """
        try:
            content = self._generate(prompt).replace('"', '')
            # Strip common AI 'preambles' or 'explanations' if they exist
            if "\n\n" in content:
                parts = [p.strip() for p in content.split("\n\n") if p.strip()]
                if parts:
                    content = parts[0]
            
            # Remove things like "Here is a post:" or "Post:"
            for noise in ["Here is a post:", "Post content:", "Post:"]:
                content = content.replace(noise, "").strip()
            
            # Final Safety Check
            if not self._safety_filter(content):
                return None
                
            return content
        except Exception as e:
            print(f"AI Post Error: {e}")
            return None

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        You are: {persona}
        Someone replied to your post: "{post_text}"
        Reply: "{reply_text}"
        
        Return JSON ONLY: {{"like": bool, "reply": "string or null"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except Exception as e:
            print(f"AI Interaction Error: {e}")
            return {'like': True, 'reply': None}

    def decide_strategy(self, persona, peak_hour):
        prompt = f"""
        You are: {persona}
        Peak Posting Hour: {peak_hour}:00
        Decide your strategy for the next 24 hours.
        
        Return JSON ONLY: {{"count": 1-4, "slots": [{{"time": "HH:MM", "topic": "short description"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except Exception as e:
            print(f"AI Strategy Error: {e}")
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "General update"}]}
