import json
from google import genai
import ollama
import os
from datetime import datetime
from src.config import GEMINI_API_KEY, AI_PROVIDER, OLLAMA_MODEL, OLLAMA_HOST

class AIBrain:
    def __init__(self):
        self.provider = AI_PROVIDER
        self.gemini_client = None
        self.gemini_model_id = None
        self.log_file = "data/ai_prompts.log"
        
        # Ensure data dir exists for logging
        os.makedirs("data", exist_ok=True)
        
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

    def _log_prompt(self, prompt, response):
        """Logs the AI interaction to a file."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"🕒 TIMESTAMP: {timestamp} | PROVIDER: {self.provider}\n")
                f.write(f"📥 PROMPT:\n{prompt}\n")
                f.write(f"📤 RESPONSE:\n{response}\n")
                f.write(f"{'='*80}\n")
        except Exception as e:
            print(f"❌ Failed to log AI interaction: {e}")

    def _generate(self, prompt, expect_json=False):
        response_text = ""
        try:
            if self.provider == 'gemini':
                config = {'response_mime_type': 'application/json'} if expect_json else None
                res = self.gemini_client.models.generate_content(
                    model=self.gemini_model_id, 
                    contents=prompt, 
                    config=config
                )
                response_text = res.text.strip()
            else:
                format_type = 'json' if expect_json else None
                res = self.ollama_client.generate(model=OLLAMA_MODEL, prompt=prompt, format=format_type)
                response_text = res['response'].strip()
            
            # Log the successful interaction
            self._log_prompt(prompt, response_text)
            return response_text
            
        except Exception as e:
            print(f"⚠️ AI generate error: {e}")
            self._log_prompt(prompt, f"ERROR: {str(e)}")
            raise e

    def generate_persona(self, posts_text, top_posts=None):
        prompt = f"""
        Describe the 'Social Avatar' based on these posts: {posts_text}. Recent success: {top_posts}.
        CRITICAL: Describe the persona in ENGLISH only.
        """
        try:
            return self._generate(prompt)
        except:
            return "A technical DIY enthusiast and software engineer focusing on automation."

    def generate_quote_comment(self, persona, post_text):
        prompt = f"""
        Persona: {persona}
        Someone else's post: "{post_text}"
        TASK: Write a short (max 250 chars) comment to add to this post when quoting it.
        CRITICAL RULES:
        1. Write in ENGLISH only.
        2. Be smart, additive, or slightly provocative.
        3. End with a question if it fits.
        """
        try:
            return self._generate(prompt).replace('"', '')
        except:
            return "This is a great point. What's your take on this?"

    def generate_external_comment(self, persona, post_text):
        prompt = f"""
        Persona: {persona}
        Strangers post: "{post_text}"
        TASK: Write a short (max 200 chars), smart, witty comment to attract attention.
        CRITICAL RULES:
        1. Write in ENGLISH only.
        2. NO PLACEHOLDERS.
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
        Return ONLY the prompt string in ENGLISH, no meta-text. Max 100 characters.
        """
        try:
            return self._generate(prompt)
        except:
            return "Minimalist futuristic technology and DIY electronics."

    def generate_mention_post(self, persona, target_username, post_context):
        prompt = f"""
        Persona: {persona}
        Target User: @{target_username}
        Their Content: "{post_context}"
        
        TASK: Write a very short Threads post (max 200 chars) mentioning @{target_username}.
        CRITICAL RULES:
        1. Write in ENGLISH only.
        2. Be smart, ask for their opinion, or give a tech-compliment.
        3. Goal: Start a conversation. No hashtags.
        """
        try:
            return self._generate(prompt).replace('"', '')
        except:
            return f"Hey @{target_username}, really interesting insights! What's your take on the current state of automation?"

    def generate_post(self, persona, context=None, examples=None):
        prompt = f"""
        Persona: {persona}
        Context: {context}
        Examples: {examples}
        TASK: Create a Threads post that drives replies. 
        CRITICAL RULES:
        1. Write in ENGLISH only.
        2. Return JSON ONLY: {{"text": "your post text", "wants_image": bool, "image_theme": "short theme"}}
        3. No hashtags. End with a question. Plain English. Max 400 chars.
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
        TASK: Decide posting strategy.
        CRITICAL: All topics and descriptions must be in ENGLISH.
        Return JSON ONLY: {{"slots": [{{"time": "HH:MM", "topic": "viral topic"}}]}}
        """
        try:
            raw = self._generate(prompt, expect_json=True)
            return json.loads(raw)
        except:
            return {"slots": [{"time": f"{peak_hour:02d}:00", "topic": "General Tech update"}]}

    def evaluate_interaction(self, persona, post_text, reply_text):
        prompt = f"""
        You are: {persona}
        Someone replied: "{reply_text}" to your post: "{post_text}"
        
        TASK: Decide if you should like and how to reply.
        CRITICAL RULES:
        1. ALWAYS answer in ENGLISH, even if the user speaks another language (like Russian or Ukrainian).
        2. If the user speaks Russian, carefully but firmly switch the conversation to English.
        3. NEVER use Russian language in your response.
        4. Be friendly, smart, and stay in character.
        
        Return JSON ONLY: {{\"like\": true, \"reply\": \"your reply text in English\"}}
        """
        try:
            return json.loads(self._generate(prompt, expect_json=True))
        except:
            return {"like": True, "reply": "Interesting point! I prefer to keep my technical discussions in English to reach a broader audience. What do you think?"}
