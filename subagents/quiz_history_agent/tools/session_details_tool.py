"""Session Details Tool - retrieves detailed results for a specific quiz session."""

from typing import Annotated
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def session_details(
    quiz_session_id: Annotated[str, "The UUID of the quiz session to retrieve details for"],
    tool_context: ToolContext,
) -> dict:
    """
    Retrieve detailed results for a specific quiz session including all answers.

    Args:
        quiz_session_id: UUID string of the quiz session

    Returns:
        dict: Detailed view of the session with per-question results
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        from Tools.db_handler import get_session_answers

        # Get session
        from database.connection import get_session as db_get_session
        from database.repositories import QuizRepository
        import uuid
        async with db_get_session() as db_session:
            repo = QuizRepository(db_session)
            qs = await repo.get_by_id(uuid.UUID(quiz_session_id))

        if not qs:
            return {"status": "error", "message": f"Quiz session '{quiz_session_id}' not found."}

        answers = await get_session_answers(quiz_session_id)

        score = qs.final_score if qs.final_score is not None else qs.current_score
        total = qs.total_questions
        date = qs.started_at.strftime("%Y-%m-%d %H:%M") if qs.started_at else "Unknown"

        return {
            "status": "success",
            "session": {
                "id": str(qs.id),
                "document": qs.document_name,
                "date": date,
                "status": qs.status,
                "score": score,
                "total": total,
            },
            "answers": [
                {
                    "question_number": a.get("question_number"),
                    "question_text": a.get("question_text", ""),
                    "user_answer": a.get("user_answer"),
                    "correct_answer": a.get("correct_answer"),
                    "is_correct": a.get("is_correct"),
                }
                for a in answers
            ],
        }

    except Exception as e:
        return {"status": "error", "message": f"Error retrieving session details: {str(e)}"}
