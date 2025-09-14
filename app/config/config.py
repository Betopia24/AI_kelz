
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# OpenAI API Key (required for transcription and analysis)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# You can add other configuration variables here as needed
# For example:
# GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
# SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac']

if not OPENAI_API_KEY:
    print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
    print("   Please set your OpenAI API key in a .env file or as an environment variable")
    print("   Example: export OPENAI_API_KEY='your-api-key-here'")

class Settings:
    OPENAI_API_KEY = OPENAI_API_KEY

settings = Settings()