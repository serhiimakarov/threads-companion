import json
import os
from src.threads_client import ThreadsClient
from src.ai_brain import AIBrain
from src.config import THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE
from src.notifications import send_telegram_notification
from src.persona_config import DEFAULT_PERSONA_PATH, load_persona

class PersonaManager:
    def __init__(self):
        self.brain = AIBrain()
        self.current_persona = load_persona()

    def sync_and_evolve(self, limit=30):
        """
        Fetches new data and asks AI to propose an evolution of the persona.
        """
        print(f"🔄 Persona Evolution: Syncing with Source...")
        if not THREADS_ACCESS_TOKEN_SOURCE:
            return

        client = ThreadsClient(THREADS_APP_ID, THREADS_APP_SECRET, THREADS_REDIRECT_URI, THREADS_ACCESS_TOKEN_SOURCE)
        
        try:
            # 1. Fetch recent activity
            threads_response = client.get_user_threads(limit=limit)
            new_posts = [t.get('text', '') for t in threads_response.get('data', []) if t.get('text')]
            
            posts_blob = "\n---\n".join(new_posts)
            
            # 2. Ask AI to evaluate if persona should evolve
            prompt = f"""
            ACT AS A DIGITAL TWIN ARCHITECT.
            
            CURRENT PERSONA CONSTITUTION:
            {json.dumps(self.current_persona, indent=2)}
            
            NEW ACTIVITY FROM SOURCE USER:
            {posts_blob}
            
            TASK: 
            Analyze if the user's focus, tone, or projects have shifted. 
            Identify NEW technical obsessions or changes in linguistic style.
            
            Return a JSON object with two keys:
            1. "has_changes": boolean
            2. "proposed_persona": the FULL updated persona JSON (v3.x) if changes exist, else null.
            3. "changelog": a short string describing what's new.
            """
            
            raw_response = self.brain._generate(prompt, expect_json=True, role="PERSONA_EVOLVER")
            evolution = json.loads(raw_response)
            
            if evolution.get('has_changes') and evolution.get('proposed_persona'):
                # Store proposed persona temporarily
                temp_path = "data/proposed_persona.json"
                with open(temp_path, 'w') as f:
                    json.dump(evolution['proposed_persona'], f, indent=4)
                
                # Notify User via Telegram
                changelog = evolution.get('changelog', 'Minor stylistic updates.')
                msg = f"🧠 *Persona Evolution Proposed!*\n\nI noticed shifts in your style/topics:\n_{changelog}_\n\nShould I upgrade my Persona Constitution?"
                
                # Custom buttons for persona approval
                reply_markup = {
                    "inline_keyboard": [[
                        {"text": "✅ Upgrade Persona", "callback_data": "persona_upgrade"},
                        {"text": "🗑️ Keep Current", "callback_data": "persona_discard"}
                    ]]
                }
                send_telegram_notification(msg, reply_markup=reply_markup)
                print("📝 Evolution proposed and sent to Telegram.")
            else:
                print("✅ Persona is up to date. No evolution needed.")

        except Exception as e:
            print(f"❌ Persona Evolution failed: {e}")

    def apply_upgrade(self):
        """Finalizes the upgrade by moving proposed to current."""
        temp_path = "data/proposed_persona.json"
        if os.path.exists(temp_path):
            os.rename(temp_path, DEFAULT_PERSONA_PATH)
            print("🏆 Persona upgraded successfully!")
            return True
        return False

if __name__ == "__main__":
    manager = PersonaManager()
    manager.sync_and_evolve()
