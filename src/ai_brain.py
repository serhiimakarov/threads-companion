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
        dna = self.persona['linguistic_dna']
        return f"""
        YOU ARE: {self.persona['identity']}
        PHILOSOPHY: {self.persona['philosophy']}
        PROJECTS: {', '.join(self.persona['projects'])}
        TONE: {dna['tone']}
        REACTIONS: Use '{dna['reactions']['inefficiency']}' for bad tech, 
        and '{dna['reactions']['inevitable failure']}' for unavoidable issues.
        PRINCIPLES: {'; '.join(self.persona['principles'])}
        """

    def generate_persona(self, posts_text, top_posts=None):
        return self.persona['identity']

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
        """
        ROLE: WRITER. Creates the first draft.
        """
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        Topic: {context}
        TASK: Write a first draft for a Threads post. Max 500 chars.
        Focus on technical authenticity and a strong hook.
        Return JSON ONLY: {{"text": "draft content"}}
        """
        try:
            raw = self._generate(prompt, expect_json=True, role="WRITER_DRAFT")
            return json.loads(raw)
        except:
            return {"text": None}

    def analyze_post(self, draft_text):
        """
        ROLE: EDITOR. Analyzes the draft and provides detailed critique.
        """
        prompt = f"""
        ACT AS A SENIOR EDITOR & TECH-LEAD.
        USER PERSONA: {self.persona['identity']}
        PHILOSOPHY: {self.persona['philosophy']}
        
        CRITIQUE THIS DRAFT:
        "{draft_text}"
        
        TASK: Provide a detailed analysis. Look for:
        1. CLICHES: Is it too chatbot-y?
        2. SLANG: Is 'cringe' or 'shit happens' used unnaturally?
        3. BRANDING: Are project names used too much?
        4. FLOW: Is the hook strong? Is the question at the end generic?
        
        Return your analysis as a list of specific improvements.
        """
        return self._generate(prompt, role="EDITOR_CRITIQUE")

    def refine_post(self, draft_text, analysis):
        """
        ROLE: WRITER. Rewrites the post based on Editor's feedback.
        """
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        
        ORIGINAL DRAFT:
        "{draft_text}"
        
        EDITOR'S FEEDBACK:
        {analysis}
        
        TASK: Rewrite the post to be 100% authentic. 
        Incorporate the feedback. Keep it under 500 chars. 
        Speak like a human engineer, not an AI trying to sound like one.
        Return ONLY the final text.
        """
        return self._generate(prompt, role="WRITER_FINAL").replace('"', '')

    def evaluate_interaction(self, persona, post_text, reply_text):
        system = self.get_system_prompt()
        prompt = f"""
        {system}
        Reply: "{reply_text}" to: "{post_text}"
        TASK: Write a smart, short reply in English.
        Return JSON: {{"like": true, "reply": "text"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True, role="ENGAGEMENT"))
        except:
            return {"like": True, "reply": "Interesting point."}
