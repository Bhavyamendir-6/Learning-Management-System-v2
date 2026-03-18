"""Generate Flashcards Tool for Learning Content Agent — two-pass FileSearch + structured output."""

from ....config import GEMINI_MODEL_NAME
import json
import traceback
from typing import Optional
from google.genai import types
from dotenv import load_dotenv

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    get_full_store_name,
)
from Models.models import FlashcardList

load_dotenv()


async def generate_flashcards(
    document_name: str,
    num_flashcards: int = 10,
    topic: Optional[str] = None,
    tool_context=None,
) -> str:
    """
    Generate study flashcards from a specific uploaded PDF document using File Search.

    Args:
        document_name: The display name of the PDF document to generate flashcards from
        num_flashcards: Number of flashcards to generate (default: 10, max: 50)
        topic: Optional specific topic or chapter to focus on

    Returns:
        str: JSON string containing the flashcards, or an error message
    """
    try:
        client = get_client()

        # ── Step 1: Resolve store ──────────────────────────────────────────────
        store_name = get_user_store(tool_context=tool_context)
        full_store_name = get_full_store_name(store_name)

        if not full_store_name:
            return (
                f"Could not find your document store ('{store_name}'). "
                "Please upload a PDF first, then try again."
            )

        num_flashcards = max(1, min(num_flashcards, 50))
        topic_clause = f" Focus specifically on the topic: '{topic}'." if topic else ""

        # ── Step 2 (Pass 1): Retrieve document content via FileSearch ──────────
        # response_schema and FileSearch cannot be combined in one Gemini call.
        # Retrieve plain-text content first, then generate structured JSON separately.
        retrieval_prompt = (
            f"Read the document '{document_name}' thoroughly and return a detailed "
            "summary of ALL its key topics, facts, concepts, terms, and important details. "
            f"Be comprehensive — this content will be used to generate {num_flashcards} flashcards."
            f"{topic_clause}"
        )

        try:
            retrieval_response = client.models.generate_content(
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
            print(
                f"[generate_flashcards] Pass-1 retrieval error:\n{traceback.format_exc()}"
            )
            return (
                f"Error reading content from '{document_name}': {str(e)}. "
                "Please try again."
            )

        if not document_content.strip():
            return (
                f"Could not retrieve any content from '{document_name}'. "
                "The document may still be processing — please wait a moment and try again."
            )

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
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=flashcard_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=FlashcardList,
                ),
            )
        except Exception as e:
            print(
                f"[generate_flashcards] Pass-2 generation error:\n{traceback.format_exc()}"
            )
            return f"Error generating flashcards: {str(e)}. Please try again."

        # Try response.parsed first, then fall back to raw JSON text
        flashcard_data = response.parsed
        if not flashcard_data or not flashcard_data.flashcards:
            try:
                raw_text = response.text or ""
                if raw_text.strip():
                    raw_json = json.loads(raw_text)
                    flashcard_data = FlashcardList(**raw_json)
            except Exception as parse_err:
                print(f"[generate_flashcards] JSON fallback parse error: {parse_err}")
                flashcard_data = None

        if not flashcard_data or not flashcard_data.flashcards:
            return (
                "The flashcard generator returned an empty response. Please try again."
            )

        flashcards_json = flashcard_data.model_dump()

        # ── Step 4: Persist state for publishing ──────────────────────────────
        if tool_context:
            tool_context.state["last_generated_content"] = flashcards_json
            tool_context.state["last_generated_type"] = "flashcard_set"

        return json.dumps(flashcards_json)

    except Exception as e:
        print(f"[generate_flashcards] Unexpected error:\n{traceback.format_exc()}")
        return f"Unexpected error while generating flashcards: {str(e)}"
