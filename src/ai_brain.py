import json
from google import genai
import ollama
import os
import random
from datetime import datetime
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST
from src.persona_config import load_persona

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = None
        self.log_file = "data/ai_prompts.log"
        self.persona = load_persona()
        
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

    def _log_prompt(self, prompt, response, role="BRAIN"):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n🕒 {timestamp} | ROLE: {role} | PROVIDER: {self.provider}\n📥 PROMPT:\n{prompt}\n📤 RESPONSE:\n{response}\n")
        except: pass

    def _generate(self, prompt, expect_json=False, role="BRAIN"):
        try:
            if self.provider == 'gemini':
                config = {'response_mime_type': 'application/json'} if expect_json else None
                res = self.gemini_client.models.generate_content(model=self.gemini_model_id, contents=prompt, config=config)
                content = res.text.strip()
            else:
                format_type = 'json' if expect_json else None
                res = self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
                content = res['response'].strip()
            self._log_prompt(prompt, content, role=role)
            return content
        except Exception as e:
            self._log_prompt(prompt, f"ERROR: {e}", role=role)
            raise e

    def get_system_prompt(self):
        self.persona = load_persona()
        dna = self.persona.get('linguistic_dna', {})
        reactions = dna.get('reactions', {})
        return f"""
        YOU ARE: {self.persona.get('identity')}
        PHILOSOPHY: {self.persona.get('philosophy')}
        PROJECTS: {', '.join(self.persona.get('projects', []))}
        TONE: {dna.get('tone')}
        REACTIONS: Use '{reactions.get('inefficiency')}' for bad tech, 
        and '{reactions.get('inevitable failure')}' for unavoidable issues.
        PRINCIPLES: {'; '.join(self.persona.get('principles', []))}
        """

    def generate_persona(self, posts_text, top_posts=None):
        return self.persona.get('identity', 'Pragmatic Engineer')

    def decide_strategy(self, persona, peak_hour, performance_report=None):
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        TASK: Project 3 specific technical topics for today.
        Avoid obvious 'AI news'. Focus on real engineering.
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "specific engineering topic"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True, role="STRATEGIST")
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "Pragmatic software engineering hacks"}]}

    def generate_post(self, persona, context=None, examples=None):
        system = self.get_system_prompt()
        structures = [
            "Technical Myth-busting", "Engineering Horror Story", "Contrarian Take", "Deep Technical Insight", "The Beauty of Efficiency"
        ]
        selected_structure = random.choice(structures)
        
        prompt = f"""
        {system}
        Topic: {context}
        Structure: {selected_structure}
        
        TASK: Write a SCROLL-STOPPING Threads post. Max 500 chars.
        1. Use a punchy HOOK.
        2. Speak like a senior PHP/JS engineer.
        3. Use LINGUISTIC MARKERS ONLY IF they feel 100% natural.
        
        Return JSON ONLY: {{"text": "raw post content"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True, role="WRITER_DRAFT")
            return json.loads(raw)
        except:
            return {"text": None}

    def analyze_post(self, draft_text):
        """
        ROLE: EDITOR. Provides detailed critique.
        """
        prompt = f"""
        ACT AS A SENIOR EDITOR & TECH-LEAD.
        USER PERSONA: {self.persona.get('identity')}
        PHILOSOPHY: {self.persona.get('philosophy')}
        
        CRITIQUE THIS DRAFT:
        "{draft_text}"
        
        TASK: Provide a detailed analysis. Look for cliches, unnatural slang, or weak hooks.
        Return your analysis as a list of specific improvements.
        """
        return self._generate(prompt, role="EDITOR_CRITIQUE")

    def refine_post(self, draft_text, analysis):
        """
        ROLE: WRITER. Rewrites based on feedback.
        """
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        
        ORIGINAL DRAFT: "{draft_text}"
        EDITOR'S FEEDBACK: {analysis}
        
        TASK: Rewrite the post to be 100% authentic. Keep it under 500 chars.
        Return ONLY the final text.
        """
        return self._generate(prompt, role="WRITER_FINAL").replace('"', '')

    def edit_post(self, raw_post_text):
        # Legacy method for compatibility or quick edits
        analysis = self.analyze_post(raw_post_text)
        return self.refine_post(raw_post_text, analysis)

    def evaluate_interaction(self, persona, post_text, reply_text):
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        Reply: "{reply_text}" to: "{post_text}"
        TASK: Write a smart, short reply in English. Avoid generic AI fluff.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True, role="ENGAGEMENT"))
        except:
            return {"like": True, "reply": "Interesting point. Worth investigating."}
