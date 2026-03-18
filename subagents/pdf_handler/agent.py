"""PDF Handler Agent - Manages PDF uploads, file listing, and document management"""

from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .tools import (
    upload_pdf,
    list_files,
    batch_upload_pdf,
)
from .prompt import PDF_HANDLER_PROMPT

pdf_handler_agent = Agent(
    name="PDF_Handler",
    model=GEMINI_MODEL_NAME,
    description="Manages PDF document uploads and file listing operations.",
    instruction=PDF_HANDLER_PROMPT,
    tools=[upload_pdf, list_files, batch_upload_pdf],
)
