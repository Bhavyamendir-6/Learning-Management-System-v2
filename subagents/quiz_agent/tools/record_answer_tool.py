"""Record Answer Tool - records a user's answer to a quiz question."""

from typing import Annotated
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import extract_user_id_from_context


async def record_answer(
    question_number: Annotated[int, "The question number (1-5)"],
    user_answer: Annotated[str, "The user's chosen answer: 'A', 'B', 'C', or 'D'"],
    correct_answer: Annotated[str, "The correct answer: 'A', 'B', 'C', or 'D'"],
    is_correct: Annotated[bool, "Whether the user's answer is correct"],
    tool_context: ToolContext,
) -> dict:
    """
    Record a user's answer to a quiz question in the database.

    Args:
        question_number: The question number (1-5)
        user_answer: The user's chosen answer letter
        correct_answer: The correct answer letter
        is_correct: Whether the answer was correct

    Returns:
        dict: Confirmation with correctness feedback
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        quiz_session_id = tool_context.state.get("current_quiz_session_id")

        if not quiz_session_id:
            return {"status": "error", "message": "No active quiz session found. Please start a quiz first."}

        from Tools.db_handler import record_answer as db_record_answer
        success = await db_record_answer(
            quiz_session_id=quiz_session_id,
            question_number=question_number,
            question_text="",
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
        )

        if success:
            result_msg = "Correct!" if is_correct else f"Incorrect. The correct answer was {correct_answer}."
            return {"status": "recorded", "is_correct": is_correct, "message": result_msg}
        return {"status": "error", "message": "Error recording answer. Please try again."}

    except Exception as e:
        return {"status": "error", "message": f"Error recording answer: {str(e)}"}
