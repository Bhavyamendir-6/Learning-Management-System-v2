"""Ask Question Tool for Learning Content Agent — single-call FileSearch pattern."""

from ....config import GEMINI_MODEL_NAME
import traceback
from google.genai import types
from dotenv import load_dotenv

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    get_full_store_name,
)

load_dotenv()


async def ask_question(
    question: str,
    document_name: str,
    tool_context=None,
) -> str:
    """
    Answer a question about a specific uploaded PDF document using File Search.

    Args:
        question: The user's question about the document
        document_name: The display name of the PDF document to search

    Returns:
        str: The answer to the question, or an error message
    """
    try:
        client = get_client()

        # ── Resolve store ──────────────────────────────────────────────────────
        store_name = get_user_store(tool_context=tool_context)
        full_store_name = get_full_store_name(store_name)

        if not full_store_name:
            return (
                f"Could not find your document store ('{store_name}'). "
                "Please upload a PDF first, then try again."
            )

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

        response = client.models.generate_content(
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

        return response.text or "Failed to generate an answer. Please try again."

    except Exception as e:
        print(f"[ask_question] Error:\n{traceback.format_exc()}")
        return f"Error answering question: {str(e)}"
