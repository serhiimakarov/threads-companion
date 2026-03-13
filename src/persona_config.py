import json
import os

# Dynamic loader for Persona Constitution
DEFAULT_PERSONA_PATH = "data/persona.json"

def load_persona():
    if os.path.exists(DEFAULT_PERSONA_PATH):
        with open(DEFAULT_PERSONA_PATH, 'r') as f:
            return json.load(f)
    return {}

PERSONA_DATA = load_persona()
