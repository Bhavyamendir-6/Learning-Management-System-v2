"""List Files Tool - lists PDFs in the user's Gemini File Search store."""

from google.adk.tools import ToolContext
from Tools.file_search_store_manager import (
    extract_user_id_from_context,
    get_client,
    get_full_store_name,
)


async def list_files(tool_context: ToolContext) -> dict:
    """
    List all PDF documents in the user's personal File Search store.

    Returns:
        dict: List of document names and count
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

        documents = list(
            client.file_search_stores.documents.list(parent=full_store_name)
        )

        if not documents:
            return {
                "status": "empty",
                "documents": [],
                "count": 0,
                "message": "Your document library is empty. Upload a PDF to get started!",
            }

        doc_names = [
            getattr(doc, "display_name", None) or getattr(doc, "name", "Unknown")
            for doc in documents
        ]

        return {
            "status": "success",
            "documents": doc_names,
            "count": len(doc_names),
        }

    except Exception as e:
        return {"status": "error", "message": f"Error listing documents: {str(e)}"}
