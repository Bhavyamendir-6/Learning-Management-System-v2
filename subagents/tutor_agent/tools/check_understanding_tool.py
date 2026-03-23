"""Check Understanding Tool - poses a mini comprehension check after explaining a concept."""

from ....config import GEMINI_MODEL_NAME
import json
import logging
from typing import Annotated, Optional
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import get_client

logger = logging.getLogger(__name__)


async def check_understanding(
    concept: Annotated[Optional[str], "The specific concept to check comprehension on; defaults to the active tutoring topic"],
    tool_context: ToolContext,
) -> dict:
    """
    Pose 1-2 quick comprehension questions to verify the student understands a concept.

    Uses the active tutoring session's topic and document context. Designed to be called
    after the tutor has explained something, to confirm retention before moving on.

    Args:
        concept: The specific concept to check; defaults to the active tutoring topic

    Returns:
        dict: Comprehension check questions and scoring instructions
    """
    try:
        client = get_client()

        # Pull from active session state
        topic = concept or tool_context.state.get("tutor_topic", "the current topic")
        document_name = tool_context.state.get("tutor_document", "")
        difficulty_level = tool_context.state.get("tutor_difficulty", "intermediate")
        topic_content = tool_context.state.get("tutor_content", "")
        history = tool_context.state.get("tutor_history", [])

        # Guard: require an active tutoring session with loaded content
        if not topic_content:
            return {
                "status": "error",
                "error": (
                    "No active tutoring session found. "
                    "Please start a tutoring session first by calling start_tutoring_session."
                ),
            }

        # Summarise recent conversation for context
        recent_history = history[-6:] if len(history) > 6 else history
        conversation_context = " | ".join(
            f"{'Tutor' if msg['role'] == 'tutor' else 'Student'}: {msg['content']}"
            for msg in recent_history
        )

        difficulty_instructions = {
            "beginner": (
                "Use simple, direct questions. Avoid trick questions. "
                "Accept paraphrased correct answers."
            ),
            "intermediate": (
                "Ask questions that require applying the concept, not just recalling it."
            ),
            "advanced": (
                "Ask questions that probe edge cases, exceptions, or deeper implications."
            ),
        }

        check_prompt = (
            f"You are a tutor who just finished explaining '{topic}' "
            + (f"from '{document_name}'" if document_name else "")
            + f". Difficulty: {difficulty_level}. "
            f"{difficulty_instructions.get(difficulty_level, '')}. "
            + (f"Document content: {topic_content}. " if topic_content else "")
            + (
                f"Recent conversation: {conversation_context}. "
                if conversation_context
                else ""
            )
            + "Create a mini comprehension check with EXACTLY 2 questions: "
            "1. A recall question — tests if the student remembers a key fact. "
            "2. An application question — tests if the student can use or apply the concept. "
            "For each question also provide: "
            "- The ideal answer (what a correct response should include). "
            "- A hint the tutor can give if the student is stuck. "
            "Format as a clear, friendly check-in, not a formal exam."
        )

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=check_prompt,
        )

        check_message = response.text or (
            f"Let's do a quick check on '{topic}'. Can you explain the main idea in your own words?"
        )

        # Mark the check in history
        history = tool_context.state.get("tutor_history", [])
        history.append(
            {
                "role": "tutor",
                "content": f"[Understanding Check]\n{check_message}",
            }
        )
        tool_context.state["tutor_history"] = history

        # Persist to database
        try:
            from Tools.db_handler import update_tutor_session_history

            tutor_session_id = tool_context.state.get("tutor_session_id")
            if tutor_session_id:
                await update_tutor_session_history(tutor_session_id, history)
        except Exception as e:
            logger.warning("[check_understanding] DB update warning: %s", e)

        return {
            "status": "understanding_check",
            "concept": topic,
            "check_message": check_message,
        }

    except Exception as e:
        return {"status": "error", "message": f"Error generating understanding check: {str(e)}"}
