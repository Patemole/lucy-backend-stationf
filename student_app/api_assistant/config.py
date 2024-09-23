# backend/config.py
# backend/config.py

import os

# Securely load your OpenAI API key from an environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
