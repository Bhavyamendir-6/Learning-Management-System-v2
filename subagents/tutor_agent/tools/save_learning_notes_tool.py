"""Save Learning Notes Tool - saves a key insight from the tutoring session."""

import json
from typing import Annotated, Optional
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def save_learning_notes(
    insight: Annotated[str, "The key insight or learning point to save"],
    topic: Annotated[Optional[str], "The topic this insight relates to (from current session)"],
    document_name: Annotated[Optional[str], "The document this insight relates to (from current session)"],
    tool_context: ToolContext,
) -> dict:
    """
    Save a key learning insight from the current tutoring session to the database.

    Args:
        insight: The key insight to save
        topic: The topic (auto-read from session state if not provided)
        document_name: The document (auto-read from session state if not provided)

    Returns:
        dict: Confirmation with the saved note ID
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        # Fall back to session state for topic/document
        if not topic:
            topic = tool_context.state.get("tutor_topic", "General")
        if not document_name:
            document_name = tool_context.state.get("tutor_document", "Unknown")

        session_id = tool_context.state.get("session_id", "") or ""

        from Tools.db_handler import save_tutor_note
        note_id = await save_tutor_note(
            user_id=user_id,
            session_id=session_id,
            document_name=document_name or "Unknown",
            topic=topic or "General",
            insight=insight,
        )

        return {
            "status": "saved",
            "note_id": note_id,
            "topic": topic,
            "insight": insight[:100] + ("..." if len(insight) > 100 else ""),
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
