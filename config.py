import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Logging configuration (consumed by utils/logging_config.py)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")       # DEBUG | INFO | WARNING | ERROR
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true")   # true | false
