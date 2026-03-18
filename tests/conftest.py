"""Load environment variables before any test runs."""

import os
from dotenv import load_dotenv

# Load .env from project root so tools have access to GEMINI_API_KEY etc.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
