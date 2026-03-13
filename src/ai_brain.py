import json
from google import genai
import ollama
import os
import random
from datetime import datetime
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST
from src.persona_config import PERSONA_DATA

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = None
        self.log_file = "data/ai_prompts.log"
        self.persona = PERSONA_DATA
        
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
            try:
                self.ollama_client = ollama.Client(host=OLLAMA_HOST)
            except: pass

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

    def get_system_prompt(self):
        return f"""
        YOU ARE: {self.persona['identity']}
        CORE TOPICS: {', '.join(self.persona['topics'])}
        STYLE: {self.persona['style']['tone']}
        PRINCIPLES: {'; '.join(self.persona['principles'])}
        LINGUISTIC MARKERS: {', '.join(self.persona['style']['linguistic_markers'])}
        FORBIDDEN PHRASES: {', '.join(self.persona['style']['forbidden'])}
        CRITICAL: Write in ENGLISH only.
        """

    def generate_persona(self, posts_text, top_posts=None):
        # We now use the static constitution but can still 'tune' it with recent vibe
        return self.persona['identity']

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        
        TASK: Project 3-5 specific technical or solopreneur topics for the next 24h.
        Be authentic to your PHP/JS and DIY background.
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "specific topic description"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "The reality of independent product engineering"}]}

    def generate_post(self, persona, context=None, examples=None):
        system = self.get_system_prompt()
        structures = [
            "Technical Myth-busting: Destroy a common dev/hardware misconception.",
            "Engineering Horror Story: A real fail and the lesson.",
            "Contrarian Take: Why a popular tool or method is strategic debt.",
            "Deep Technical Insight: A detail about code or hardware performance.",
            "The Beauty of Efficiency: A rant about clean design or minimalism."
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        {system}
        Topic: {context}
        Structure: {selected_structure}
        
        TASK: Write a SCROLL-STOPPING Threads post. Max 500 chars.
        1. Use a punchy HOOK.
        2. Speak like a senior PHP/JS engineer.
        3. End with a question for builders.
        
        Return JSON ONLY: {{"text": "post content"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"text": None}

    def evaluate_interaction(self, persona, post_text, reply_text):
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        Reply: "{reply_text}" to: "{post_text}"
        
        TASK: Write a smart, short reply in English. Avoid generic 'AI' phrases.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point. Let's look at the technical trade-offs."}
