"""Generate Flashcards Tool for Learning Content Agent — two-pass FileSearch + structured output."""

from ....config import GEMINI_MODEL_NAME
import json
import logging
from typing import Annotated, Optional
from google.genai import types
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
)
from Models.models import FlashcardList


async def generate_flashcards(
    document_name: Annotated[str, "The display name of the PDF document to generate flashcards from"],
    num_flashcards: Annotated[int, "Number of flashcards to generate (1-50, recommended: 10)"],
    topic: Annotated[Optional[str], "Optional specific topic or chapter to focus on"],
    tool_context: ToolContext,
) -> dict:
    """
    Generate study flashcards from a specific uploaded PDF document using File Search.

    Args:
        document_name: The display name of the PDF document to generate flashcards from
        num_flashcards: Number of flashcards to generate (1-50)
        topic: Optional specific topic or chapter to focus on

    Returns:
        dict: Flashcard data, or an error message
    """
    try:
        client = get_client()

        # ── Step 1: Resolve store ──────────────────────────────────────────────
        full_store_name = get_user_store(tool_context=tool_context)

        if not full_store_name:
            return {
                "status": "error",
                "message": "Could not find your document store. Please upload a PDF first, then try again.",
            }

        num_flashcards = max(1, min(num_flashcards, 50))
        topic_clause = f" Focus specifically on the topic: '{topic}'." if topic else ""

        # ── Step 2 (Pass 1): Retrieve document content via FileSearch ──────────
        retrieval_prompt = (
            f"Read the document '{document_name}' thoroughly and return a detailed "
            "summary of ALL its key topics, facts, concepts, terms, and important details. "
            f"Be comprehensive — this content will be used to generate {num_flashcards} flashcards."
            f"{topic_clause}"
        )

        try:
            retrieval_response = await client.aio.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=retrieval_prompt,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[full_store_name]
                            )
                        )
                    ],
                ),
            )
            document_content = retrieval_response.text or ""
        except Exception as e:
            logger.error("[generate_flashcards] pass-1 retrieval error for doc=%r: %s", document_name, e, exc_info=True)
            return {
                "status": "error",
                "message": f"Error reading content from '{document_name}': {str(e)}. Please try again.",
            }

        if not document_content.strip():
            return {
                "status": "error",
                "message": (
                    f"Could not retrieve any content from '{document_name}'. "
                    "The document may still be processing — please wait a moment and try again."
                ),
            }

        # ── Step 3 (Pass 2): Generate structured flashcards from retrieved content
        flashcard_prompt = (
            f"Based on the following document content, generate exactly {num_flashcards} "
            f"study flashcards from the document '{document_name}'.{topic_clause}\n\n"
            "Requirements:\n"
            "- Each flashcard must have a clear question or term on the front.\n"
            "- Each flashcard must have a complete answer or definition on the back.\n"
            "- Assign a category (topic/subject area) to each flashcard.\n"
            "- Assign a difficulty level (Easy, Medium, or Hard) to each flashcard.\n"
            "- Balance difficulty levels across the set.\n"
            "- Cover diverse topics from the document.\n"
            "- Questions should test understanding, not just recall.\n\n"
            f"Document content:\n{document_content}"
        )

        try:
            response = await client.aio.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=flashcard_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FlashcardList,
                ),
            )
        except Exception as e:
            logger.error("[generate_flashcards] pass-2 generation error: %s", e, exc_info=True)
            return {"status": "error", "message": f"Error generating flashcards: {str(e)}. Please try again."}

        # Try response.parsed first, then fall back to raw JSON text
        flashcard_data = response.parsed
        if not flashcard_data or not flashcard_data.flashcards:
            try:
                raw_text = response.text or ""
                if raw_text.strip():
                    raw_json = json.loads(raw_text)
                    flashcard_data = FlashcardList(**raw_json)
            except Exception as parse_err:
                logger.warning("[generate_flashcards] JSON fallback parse error: %s", parse_err)
                flashcard_data = None

        if not flashcard_data or not flashcard_data.flashcards:
            return {
                "status": "error",
                "message": "The flashcard generator returned an empty response. Please try again.",
            }

        flashcards_json = flashcard_data.model_dump()

        # ── Step 4: Persist state for publishing ──────────────────────────────
        tool_context.state["last_generated_content"] = flashcards_json
        tool_context.state["last_generated_type"] = "flashcard_set"

        return flashcards_json

    except Exception as e:
        logger.exception("[generate_flashcards] unexpected error: %s", e)
        return {"status": "error", "message": f"Unexpected error while generating flashcards: {str(e)}"}
