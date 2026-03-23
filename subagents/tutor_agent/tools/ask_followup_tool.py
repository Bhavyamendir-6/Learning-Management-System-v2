"""Ask Followup Tool - continues a Socratic tutoring dialogue based on student's response."""

from ....config import GEMINI_MODEL_NAME
import json
import logging
from typing import Annotated
from google.adk.tools import ToolContext

from Tools.file_search_store_manager import get_client

logger = logging.getLogger(__name__)


async def ask_followup(
    user_response: Annotated[str, "The student's latest message or answer to the tutor's question"],
    tool_context: ToolContext,
) -> dict:
    """
    Continue the tutoring dialogue by responding to the student's last message.

    Reads conversation history and document context from session state, generates
    a Socratic response that acknowledges/corrects/expands on the student's input,
    then poses the next guiding question.

    Args:
        user_response: The student's latest message or answer

    Returns:
        dict: The tutor's next message
    """
    try:
        client = get_client()

        # Load session state
        topic = tool_context.state.get("tutor_topic", "the topic")
        document_name = tool_context.state.get("tutor_document", "the document")
        difficulty_level = tool_context.state.get("tutor_difficulty", "intermediate")
        topic_content = tool_context.state.get("tutor_content", "")
        history = tool_context.state.get("tutor_history", [])

        # Guard: session must be active before continuing the dialogue
        if not topic_content:
            return {
                "status": "error",
                "error": (
                    "No active tutoring session found. "
                    "Please start a tutoring session first by calling start_tutoring_session."
                ),
            }

        # Append student message to history
        history.append({"role": "student", "content": user_response})

        # Build conversation context string
        conversation_so_far = " | ".join(
            f"{'Tutor' if msg['role'] == 'tutor' else 'Student'}: {msg['content']}"
            for msg in history
        )

        difficulty_instructions = {
            "beginner": "Use simple language, everyday analogies, and be encouraging.",
            "intermediate": "Use domain terminology, explain when needed, challenge gently.",
            "advanced": "Use precise technical language, probe deeper understanding, challenge assumptions.",
        }

        followup_prompt = (
            f"You are a Socratic tutor teaching '{topic}' from '{document_name}'. "
            f"Difficulty: {difficulty_level}. {difficulty_instructions.get(difficulty_level, '')}. "
            f"Document content on this topic: {topic_content}. "
            f"Conversation so far: {conversation_so_far}. "
            "Write your next tutor response. You must: "
            "1. Acknowledge what the student said (correct what's wrong, reinforce what's right). "
            "2. Build on their response with a key insight from the document. "
            "3. End with ONE follow-up question that deepens understanding. "
            "Keep the response focused and concise. Do NOT dump all information at once."
        )

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=followup_prompt,
        )

        tutor_message = (
            response.text or "Interesting! Can you tell me more about what you think?"
        )

        # Append tutor reply to history and persist
        history.append({"role": "tutor", "content": tutor_message})

        tool_context.state["tutor_history"] = history

        # Persist updated history to database
        try:
            from Tools.db_handler import update_tutor_session_history

            tutor_session_id = tool_context.state.get("tutor_session_id")
            if tutor_session_id:
                await update_tutor_session_history(tutor_session_id, history)
        except Exception as e:
            logger.warning("[ask_followup] DB update warning: %s", e)

        return {
            "status": "followup_sent",
            "tutor_message": tutor_message,
            "turns_so_far": len([m for m in history if m["role"] == "student"]),
        }

    except Exception as e:
        return {"status": "error", "message": f"Error generating follow-up: {str(e)}"}
