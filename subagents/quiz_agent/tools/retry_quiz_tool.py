"""
ADK tool for retrying quiz questions the user got wrong.

Generates new questions focused on topics from incorrectly answered questions
in a previous quiz session, using File Search for document-grounded content.
"""

from ....config import GEMINI_MODEL_NAME
import json
import logging
from typing import Annotated, Optional
from google.genai import types
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    get_full_store_name,
    extract_user_id_from_context,
)
from Tools.db_handler import (
    get_session_answers,
    get_last_completed_quiz,
    start_quiz_session,
    get_quiz_history,
)


async def retry_quiz(
    quiz_session_id: Annotated[Optional[str], "Optional UUID string of the quiz to retry. If not provided, uses the most recent completed quiz."],
    tool_context: ToolContext,
) -> dict:
    """
    Generate a new quiz focused on topics the user previously got wrong.

    Retrieves wrong answers from a past quiz session and generates new questions
    on those specific topics using File Search over the same document.

    Args:
        quiz_session_id: Optional UUID string of the quiz to retry

    Returns:
        dict: New quiz questions focused on weak topics, or an error
    """
    try:
        # 1. Resolve user ID
        user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

        # 2. Find the source quiz session
        original_session = None

        if quiz_session_id:
            try:
                history = await get_quiz_history(user_id=user_id, limit=50)
                for s in history:
                    if str(s.get("_id", "")) == quiz_session_id:
                        original_session = s
                        break
                if not original_session:
                    return {
                        "status": "error",
                        "message": f"Quiz session '{quiz_session_id}' not found for your account.",
                    }
            except Exception as e:
                return {"status": "error", "message": f"Error looking up quiz session '{quiz_session_id}': {str(e)}"}
        else:
            original_session = await get_last_completed_quiz(user_id)

        if not original_session:
            return {
                "status": "error",
                "message": "No completed quiz found to retry. Please complete a quiz first, then ask to retry your wrong answers.",
            }

        original_session_id = str(original_session.get("_id", ""))
        document_name = original_session.get("document_name", "")

        if not document_name:
            return {"status": "error", "message": "The original quiz session has no document name. Cannot generate retry questions."}

        # 3. Get wrong answers
        answers = await get_session_answers(original_session_id)
        wrong_answers = [a for a in answers if not a.get("is_correct", True)]

        if not wrong_answers:
            return {
                "status": "all_correct",
                "message": f"You got all questions correct in your last quiz on '{document_name}'. No retry needed!",
            }

        # 4. Build topic descriptions from wrong questions
        wrong_topics = []
        for wa in wrong_answers:
            question_text = wa.get("question_text", "")
            if question_text:
                wrong_topics.append(question_text)

        num_questions = min(len(wrong_topics), 5)

        topics_block = ", ".join(
            f"{i + 1}. {topic}" for i, topic in enumerate(wrong_topics)
        )

        # 5. Generate new questions via File Search
        client = get_client()
        store_name = get_user_store(tool_context=tool_context)
        full_store_name = get_full_store_name(store_name)

        retry_prompt = (
            f"Based on the content of the document '{document_name}', generate exactly {num_questions} new multiple-choice quiz questions. "
            f"IMPORTANT: These questions must focus on the SAME TOPICS as the following questions that the user previously answered incorrectly: {topics_block}. "
            "Generate NEW questions (not the same questions) that test the same concepts and topics. "
            "Requirements: "
            "- Medium difficulty level. "
            "- Each question must have exactly 4 options labeled A, B, C, D. "
            "- Exactly one correct answer per question. "
            "- Include a helpful hint that guides thinking without revealing the answer. "
            "- Include a brief explanation for why the correct answer is correct. "
            "- Questions must be different from the original questions listed above. "
            "Return ONLY a valid JSON array with this exact structure, no other text: "
            "[{'question_number': 1, 'question': '...', 'options': {'A': '...', 'B': '...', 'C': '...', 'D': '...'}, 'correct_answer': 'B', 'hint': '...', 'explanation': '...'}]"
        )

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=retry_prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[full_store_name]
                        )
                    )
                ]
            ),
        )

        # 6. Parse JSON from response
        response_text = response.text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        questions = json.loads(response_text)

        if not isinstance(questions, list) or len(questions) == 0:
            return {"status": "error", "message": "Failed to generate retry quiz questions. Please try again."}

        # 7. Store quiz state in session
        tool_context.state["quiz_questions"] = questions
        tool_context.state["quiz_current_index"] = 0
        tool_context.state["quiz_score"] = 0
        tool_context.state["quiz_document"] = document_name
        tool_context.state["quiz_active"] = True

        # Persist to PostgreSQL as a retry session
        try:
            session_id = tool_context.state.get("session_id") or user_id

            quiz_session_id_new = await start_quiz_session(
                user_id=user_id,
                session_id=session_id,
                document_name=document_name,
                questions_list=questions,
            )

            tool_context.state["current_quiz_session_id"] = quiz_session_id_new

            # Mark as retry in PostgreSQL
            try:
                await _mark_retry(quiz_session_id_new, original_session_id)
            except Exception as e:
                logger.warning("[retry_quiz] failed to set retry metadata: %s", e)

        except Exception as e:
            logger.warning("[retry_quiz] failed to persist retry quiz to database: %s", e)

        return {
            "status": "retry_quiz_generated",
            "document": document_name,
            "retry_of_session": original_session_id,
            "wrong_topics_count": len(wrong_topics),
            "total_questions": len(questions),
            "questions": questions,
        }

    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to parse retry quiz questions from the AI response. Please try again."}
    except Exception as e:
        return {"status": "error", "message": f"Error generating retry quiz: {str(e)}"}


async def _mark_retry(new_session_id: str, original_session_id: str) -> None:
    """Mark a quiz session as a retry of another session in PostgreSQL."""
    import uuid as _uuid

    from database.connection import get_session
    from database.models import QuizSession
    from sqlalchemy import update

    async with get_session() as db:
        await db.execute(
            update(QuizSession)
            .where(QuizSession.id == _uuid.UUID(new_session_id))
            .values(
                is_retry=True,
                retry_of_session_id=_uuid.UUID(original_session_id),
            )
        )
