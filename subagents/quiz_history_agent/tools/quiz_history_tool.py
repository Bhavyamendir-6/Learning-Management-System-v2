"""Quiz History Tool - retrieves the user's past quiz sessions."""

from typing import Annotated, Optional
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def quiz_history(
    document_name: Annotated[Optional[str], "Filter results to quizzes on a specific document. Leave blank for all quizzes."],
    limit: Annotated[int, "Maximum number of sessions to return (recommended: 10)"],
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve the user's past quiz sessions with scores.

    Args:
        document_name: Optional filter by document name
        limit: Maximum number of sessions to return

    Returns:
        dict: List of quiz sessions with scores and dates
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"
    limit = limit or 10

    try:
        from Tools.db_handler import get_quiz_history
        sessions = await get_quiz_history(
            user_id=user_id,
            limit=limit,
            document_name=document_name,
        )

        if not sessions:
            return {"status": "no_history", "sessions": [], "message": "No quiz history found. Take a quiz to get started!"}

        return {
            "status": "success",
            "count": len(sessions),
            "sessions": [
                {
                    "session_id": str(s.get("_id", ""))[:8],
                    "full_id": str(s.get("_id", "")),
                    "document": s.get("document_name", "Unknown"),
                    "score": s.get("final_score", 0) if s.get("status") == "completed" else s.get("current_score", 0),
                    "total": s.get("total_questions", 5),
                    "status": s.get("status", "unknown"),
                    "date": (s.get("started_at") or "")[:10],
                }
                for s in sessions
            ],
        }

    except Exception as e:
        return {"status": "error", "message": f"Error retrieving quiz history: {str(e)}"}
