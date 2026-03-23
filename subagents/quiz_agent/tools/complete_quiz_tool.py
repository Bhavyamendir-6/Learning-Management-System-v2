"""Complete Quiz Tool - marks a quiz session as completed and returns the final score."""

from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def complete_quiz(tool_context: ToolContext) -> dict:
    """
    Mark the current quiz session as completed and return the final score.

    Returns:
        dict: Final score summary and completion message
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        quiz_session_id = tool_context.state.get("current_quiz_session_id")

        if not quiz_session_id:
            return {"status": "error", "message": "No active quiz session to complete."}

        from Tools.db_handler import complete_quiz_session, validate_session
        session = await validate_session(quiz_session_id)
        if not session:
            return {"status": "error", "message": "Quiz session not found or already completed."}

        success = await complete_quiz_session(quiz_session_id)
        if not success:
            return {"status": "error", "message": "Error completing quiz session."}

        total = session.get("total_questions", 5)
        score = session.get("current_score", 0)
        pct = round((score / total) * 100) if total > 0 else 0

        # Clear session state
        tool_context.state["current_quiz_session_id"] = None

        if pct >= 80:
            msg = f"Excellent! You scored {score}/{total} ({pct}%). Great work!"
        elif pct >= 60:
            msg = f"Good job! You scored {score}/{total} ({pct}%). Keep practicing!"
        else:
            msg = f"You scored {score}/{total} ({pct}%). Consider retrying to improve!"

        return {
            "status": "completed",
            "score": score,
            "total": total,
            "percentage": pct,
            "message": msg,
        }

    except Exception as e:
        return {"status": "error", "message": f"Error completing quiz: {str(e)}"}
