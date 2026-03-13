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
        Act like a Personal Brand Consultant. 
        Current Context: DIY Electronics, Raspberry Pi, Software Engineering, Python, Automation, Jeeps, and AI experiments.
        
        TASK: Craft a razor-sharp POSITIONING statement for this Social Avatar.
        Focus on being a technical expert who builds real things.
        3 sentences max. ENGLISH ONLY.
        """
        return self._generate(prompt)

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        Act like a Content Strategist.
        Persona: {persona}
        Performance: {performance_report}
        
        TASK: Decide posting slots for the next 24h. 
        Focus on varied technical topics: Hardware, Code, Automation, Off-roading.
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "specific technical topic"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "Technical DIY Insight"}]}

    def generate_post(self, persona, context=None, examples=None):
        structures = [
            "Myth-busting: A common technical misconception.",
            "Horror Story: A hardware/software failure.",
            "Contrarian Take: Why a popular tool/method is actually bad.",
            "Deep Insight: A subtle technical detail that changes everything.",
            "Curiosity Gap: A mystery about a specific hardware/code."
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        Persona: {persona}
        Topic: {context}
        Structure: {selected_structure}
        
        TASK: Create a SCROLL-STOPPING Threads post. Max 500 chars.
        RULES:
        1. NO generic 'AI talking about AI' posts. Be a TECH EXPERT first.
        2. Talk about real things: soldering, latency, backends, engines, sensors.
        3. Use a strong HOOK.
        4. NO hashtags, NO placeholders.
        5. End with a specific question about the TOPIC.
        6. NO mention of being an 'AI agent' unless the topic is specifically about building one.
        
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
        Style: Minimalist technical art, neon orange accents, cinematic.
        TASK: Generate a high-quality image prompt for Pollinations.ai. Max 150 chars.
        """
        return self._generate(prompt)

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        Act like an Engagement Specialist.
        Persona: {persona}
        Reply: "{reply_text}" to: "{post_text}"
        TASK: Write a smart, short reply in English. Avoid being generic.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point! Let's talk more about the technical side."}
