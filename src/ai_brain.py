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
        
        # VISUAL STYLE BLUEPRINT (Based on createbangers advice)
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
        Act like a Personal Brand Consultant for Threads. 
        Analyze these posts: {posts_text}. 
        Successes: {top_posts}.
        
        TASK: Craft a razor-sharp POSITIONING statement for this Social Avatar.
        Define: 
        1. Unique Angle (e.g., The DIY Automation Strategist).
        2. Target Audience (e.g., IndieHackers, IoT enthusiasts).
        3. The core 'Pain' you destroy (e.g., complexity of tech automation).
        Provide in 3 powerful sentences. ENGLISH ONLY.
        """
        return self._generate(prompt)

    def generate_post(self, persona, context=None, examples=None):
        # VIRAL STRUCTURES PICKER
        structures = [
            "Myth-busting: Identify a common tech lie and destroy it.",
            "Horror Story: A technical failure and the lesson learned.",
            "Contrarian Hot Take: An unpopular opinion about AI or Software.",
            "Step-by-step Framework: How to optimize a specific workflow.",
            "The Curiosity Gap: A 'Did you know' style opening that reveals a secret."
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        Persona: {persona}
        Context: {context}
        Structure to follow: {selected_structure}
        
        TASK: Create a SCROLL-STOPPING Threads post.
        RULES:
        1. Write in ENGLISH ONLY.
        2. Use a 'Hook' first line (Pattern Interrupt).
        3. No hashtags, no placeholders.
        4. End with a compelling question.
        5. Structure: [HOOK] -> [VALUE/STORY] -> [CTA/QUESTION].
        
        Return JSON ONLY: {{"text": "post content", "wants_image": bool, "image_theme": "visual prompt description"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"text": None, "wants_image": False, "image_theme": None}

    def generate_image_prompt(self, post_text):
        prompt = f"""
        Post: "{post_text}"
        Visual Style Guide: {json.dumps(self.visual_style)}
        
        TASK: Generate a high-quality, artistic image prompt for Pollinations.ai.
        Include elements from our Visual Style Guide to maintain brand consistency.
        Return ONLY the prompt string. Max 150 chars.
        """
        return self._generate(prompt)

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        Act like an Engagement Specialist.
        Persona: {persona}
        Someone replied: "{reply_text}" to your post: "{post_text}"
        
        TASK: Write a value-packed, smart reply in English. 
        Aim to turn this into a conversation. 
        If it's a hater, be firm but professional. If it's a fan, be helpful.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting take! Let's dive deeper into this."}
