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
        
        # VISUAL STYLE BLUEPRINT (Stays consistent for branding)
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
        Act like a Deep Identity Analyst. 
        Context (Past Posts): {posts_text}
        Successes: {top_posts}
        
        TASK: Synthesize the deep identity of this person. 
        Identify the underlying philosophy (e.g., radical self-reliance, optimization, technical curiosity).
        What drives them to build things? What is their unique stance on the world?
        Provide in 3 punchy sentences. ENGLISH ONLY.
        """
        return self._generate(prompt)

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        prompt = f"""
        Act like an Intuitive Creative Strategist.
        Persona Worldview: {persona}
        Performance Stats: {performance_report}
        
        TASK: Imagine 5 unique technical or lifestyle topics this person would be passionate to talk about today. 
        RULES:
        1. DO NOT use generic keywords like 'Python', 'Raspberry Pi' or 'AI' unless they are central to a VERY specific story.
        2. Synthesize new ideas based on the persona's worldview.
        3. Think about: physical building, maintenance of complex systems, obscure technical failures, the beauty of efficient design, or rants against modern low-quality tech.
        4. Be bold, unpredictable, and highly specific. 
        
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "highly specific and unique technical/lifestyle topic"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "The friction of modern automated systems"}]}

    def generate_post(self, persona, context=None, examples=None):
        structures = [
            "Myth-busting: Identify a common technical misconception and destroy it.",
            "Horror Story: A specific technical/mechanical failure and the lesson learned.",
            "Contrarian Take: Why a popular method/tool is actually a strategic debt.",
            "Deep Insight: A subtle detail about hardware, code, or mechanics that changes everything.",
            "The Curiosity Gap: A mystery about how complex systems work under the hood."
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        Persona Worldview: {persona}
        Topic: {context}
        Structure: {selected_structure}
        
        TASK: Write a SCROLL-STOPPING Threads post. Max 500 chars.
        RULES:
        1. NO generic filler. Speak with the authority of someone who has actual dirt or code on their hands.
        2. Start with a punchy HOOK.
        3. Use specific technical, mechanical, or operational details to build credibility.
        4. End with a question that demands an expert-level or passionate answer.
        5. Write in ENGLISH ONLY. 
        6. DO NOT use the word 'Shadow AI' or 'Autonomous Agent' here.
        
        Return JSON ONLY: {{"text": "post content"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"text": None}

    def generate_image_prompt(self, post_text):
        prompt = f"Post: {post_text}. Style: {json.dumps(self.visual_style)}. Generate an artistic image prompt for AI. Max 100 chars."
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
