# backend/config.py

import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    #DATABASE_URL = os.getenv('DATABASE_URL', 'your_default_db_url')
    ASSISTANT_NAME = "Course Selection Assistant"
    ASSISTANT_MODEL = "gpt-4o"  # Ensure this is the correct model identifier
    # Add other configuration variables as needed
