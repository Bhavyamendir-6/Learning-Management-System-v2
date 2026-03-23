"""Request Example Tool - generates a concrete example for a concept from the document."""

from ....config import GEMINI_MODEL_NAME
import json
from typing import Annotated, Optional
from google.genai import types
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context, get_client, get_full_store_name
from utils.document_utils import normalize_doc_name, find_document


async def request_example(
    concept: Annotated[str, "The concept or topic to illustrate with an example"],
    document_name: Annotated[Optional[str], "The document to draw the example from"],
    tool_context: ToolContext,
) -> dict:
    """
    Generate a concrete example for a concept, grounded in the user's document.

    Args:
        concept: The concept to illustrate
        document_name: The source document (uses active session document if not provided)

    Returns:
        dict: The generated example
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        if not document_name:
            document_name = tool_context.state.get("tutor_document", "")

        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=f"Using the document '{document_name}', provide a concrete, clear example that illustrates the concept: '{concept}'. Keep it concise and directly tied to the document content.",
            config=types.GenerateContentConfig(
                tools=[types.Tool(file_search=types.FileSearch(file_search_stores=[full_store_name]))],
            ),
        )

        example_text = response.text or "Could not generate an example at this time."
        return {"status": "success", "concept": concept, "example": example_text}

    except Exception as e:
        return {"status": "error", "message": str(e)}
