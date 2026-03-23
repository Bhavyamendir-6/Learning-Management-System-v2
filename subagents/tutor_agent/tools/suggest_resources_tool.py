"""Suggest Resources Tool - suggests related documents or topics for further learning."""

from typing import Annotated
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context, get_client, get_full_store_name


async def suggest_resources(
    current_topic: Annotated[str, "The topic the user is currently studying"],
    tool_context: ToolContext,
) -> dict:
    """
    Suggest related documents or topics for further learning based on the current topic.

    Args:
        current_topic: The topic being studied in the current session

    Returns:
        dict: Suggested resources and related topics
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

        documents = list(
            client.file_search_stores.documents.list(parent=full_store_name)
        )

        doc_names = [
            getattr(d, "display_name", None) or getattr(d, "name", "Unknown")
            for d in documents
        ]

        if not doc_names:
            return {
                "status": "no_documents",
                "message": "No documents found in your library. Upload more PDFs to get suggestions.",
                "suggestions": [],
            }

        return {
            "status": "success",
            "current_topic": current_topic,
            "available_documents": doc_names,
            "message": f"You have {len(doc_names)} document(s) in your library that may contain related content.",
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
