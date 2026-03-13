import json
from google import genai
import ollama
import os
import random
from datetime import datetime
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = None
        self.log_file = "data/ai_prompts.log"
        
        # VISUAL STYLE BLUEPRINT
        self.visual_style = {
            "style": "Minimalist futuristic technical art",
            "palette": "Deep slate, electric blue, neon orange accents",
            "atmosphere": "Cinematic, high contrast, clean lines",
            "technical_detail": "Schematic diagrams, internal components, digital glow"
        }
        
        os.makedirs("data", exist_ok=True)
        
        if self.provider == 'gemini' and GEMINI_API_KEY:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                models = self.gemini_client.models.list()
                flash_models = [m.name for m in models if 'flash' in m.name.lower()]
                if flash_models:
                    self.gemini_model_id = flash_models[0].split('/')[-1]
                else:
                    self.gemini_model_id = 'gemini-1.5-flash'
            except:
                self.provider = 'ollama'
        
        if self.provider == 'ollama':
            self.ollama_client = ollama.Client(host=OLLAMA_HOST)

    def is_active(self): return True

    def _log_prompt(self, prompt, response):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n🕒 {timestamp} | {self.provider}\n📥 PROMPT:\n{prompt}\n📤 RESPONSE:\n{response}\n")
        except: pass

    def _generate(self, prompt, expect_json=False):
        try:
            if self.provider == 'gemini':
                config = {'response_mime_type': 'application/json'} if expect_json else None
                res = self.gemini_client.models.generate_content(model=self.gemini_model_id, contents=prompt, config=config)
                content = res.text.strip()
            else:
                format_type = 'json' if expect_json else None
                res = self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
                content = res['response'].strip()
            self._log_prompt(prompt, content)
            return content
        except Exception as e:
            self._log_prompt(prompt, f"ERROR: {e}")
            raise e

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"""
        Act like a Creative Branding Consultant. 
        Context: {posts_text}
        Successes: {top_posts}
        
        TASK: Describe this person's 'Social Avatar'. 
        What are their core obsessions? What's their unique voice? 
        Provide in 3 sentences. ENGLISH ONLY.
        """
        return self._generate(prompt)

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        Act like an Intuitive Content Strategist.
        Persona: {persona}
        Performance: {performance_report}
        
        TASK: Imagine what this person would write about in the next 24h. 
        Don't just repeat what's in the profile. Synthesize new ideas at the intersection of their interests (e.g. AI + Off-roading, Python + DIY hardware, Productivity + Minimalism).
        Think about: 1. Technical rants, 2. Unexpected discoveries, 3. Future predictions, 4. Workflow hacks.
        
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "creative technical topic description"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "The hidden complexity of simple automation"}]}

    def generate_post(self, persona, context=None, examples=None):
        structures = [
            "Myth-busting: Identify a common technical misconception and destroy it.",
            "Horror Story: A specific technical failure and the lesson learned.",
            "Contrarian Take: Why a popular tech trend is actually bad for engineers.",
            "Deep Insight: A subtle technical detail about hardware or code that matters.",
            "Curiosity Gap: A mystery about how things work under the hood."
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        Persona: {persona}
        Topic: {context}
        Structure to follow: {selected_structure}
        
        TASK: Write a SCROLL-STOPPING Threads post. Max 500 chars.
        RULES:
        1. BE AUTHENTIC. Speak like a person who builds things with their hands and code.
        2. NO generic AI talk. Use specific technical terms.
        3. Use a strong HOOK.
        4. End with a specific question to drive engagement.
        5. Write in ENGLISH ONLY.
        
        Return JSON ONLY: {{"text": "post content"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"text": None}

    def generate_image_prompt(self, post_text):
        prompt = f"""
        Post: "{post_text}"
        Style: {json.dumps(self.visual_style)}
        TASK: Generate an artistic image prompt for Pollinations.ai. Max 150 chars.
        """
        return self._generate(prompt)

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        Act like an Engagement Specialist.
        Persona: {persona}
        Reply: "{reply_text}" to: "{post_text}"
        TASK: Write a smart, short reply in English.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point! Let's talk more about the technical side."}
