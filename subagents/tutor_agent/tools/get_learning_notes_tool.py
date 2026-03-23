"""Get Learning Notes Tool - retrieves saved learning notes for the user."""

from typing import Annotated, Optional
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def get_learning_notes(
    topic: Annotated[Optional[str], "Filter notes by topic. Leave blank to retrieve all notes."],
    document_name: Annotated[Optional[str], "Filter notes by document name. Leave blank for all documents."],
    limit: Annotated[int, "Maximum number of notes to return (recommended: 20)"],
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve saved learning notes for the user, optionally filtered by topic or document.

    Args:
        topic: Optional topic filter
        document_name: Optional document filter
        limit: Maximum number of notes to return

    Returns:
        dict: List of saved notes
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    # Apply sensible defaults inside the function body
    limit = limit or 20

    try:
        from Tools.db_handler import get_tutor_notes
        notes = await get_tutor_notes(
            user_id=user_id,
            topic=topic,
            document_name=document_name,
            limit=limit,
        )

        if not notes:
            return {
                "status": "no_notes",
                "message": "No learning notes found. Save insights during tutoring sessions to build your notes!",
                "notes": [],
            }

        return {
            "status": "success",
            "count": len(notes),
            "notes": [
                {
                    "id": n.get("id", ""),
                    "topic": n.get("topic", ""),
                    "document": n.get("document_name", ""),
                    "insight": n.get("insight", ""),
                    "saved_at": (n.get("created_at") or "")[:10],
                }
                for n in notes
            ],
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
