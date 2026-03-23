"""Ask Question Tool for Learning Content Agent — single-call FileSearch pattern."""

from ....config import GEMINI_MODEL_NAME
import logging
from typing import Annotated
from google.genai import types
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
)


async def ask_question(
    question: Annotated[str, "The user's question about the document"],
    document_name: Annotated[str, "The display name of the PDF document to search"],
    tool_context: ToolContext,
) -> dict:
    """
    Answer a question about a specific uploaded PDF document using File Search.

    Args:
        question: The user's question about the document
        document_name: The display name of the PDF document to search

    Returns:
        dict: The answer to the question, or an error message
    """
    try:
        client = get_client()

        # ── Resolve store ──────────────────────────────────────────────────────
        full_store_name = get_user_store(tool_context=tool_context)

        if not full_store_name:
            return {
                "status": "error",
                "message": "Could not find your document store. Please upload a PDF first, then try again.",
            }

        # ── Call Gemini with FileSearch ────────────────────────────────────────
        prompt = (
            f'Answer the following question using ONLY the document "{document_name}".\n\n'
            f"Question:\n{question}\n\n"
            "Requirements:\n"
            "- Base your answer ONLY on content found in the document.\n"
            "- Be thorough but concise.\n"
            "- If the document does not contain enough information to answer, say so clearly.\n"
            "- Cite relevant sections or details from the document where possible."
        )

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt,
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

        answer = response.text or "Failed to generate an answer. Please try again."
        return {"status": "success", "answer": answer}

    except Exception as e:
        logger.error("[ask_question] error: %s", e, exc_info=True)
        return {"status": "error", "message": f"Error answering question: {str(e)}"}
