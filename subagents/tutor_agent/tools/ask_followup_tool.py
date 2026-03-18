"""Ask Followup Tool - continues a Socratic tutoring dialogue based on student's response."""

from ....config import GEMINI_MODEL_NAME
import json

from Tools.file_search_store_manager import get_client


async def ask_followup(
    user_response: str,
    tool_context=None,
) -> str:
    """
    Continue the tutoring dialogue by responding to the student's last message.

    Reads conversation history and document context from session state, generates
    a Socratic response that acknowledges/corrects/expands on the student's input,
    then poses the next guiding question.

    Args:
        user_response: The student's latest message or answer

    Returns:
        str: JSON with the tutor's next message
    """
    try:
        client = get_client()

        # Load session state
        topic = "the topic"
        document_name = "the document"
        difficulty_level = "intermediate"
        topic_content = ""
        history = []

        if tool_context:
            topic = tool_context.state.get("tutor_topic", topic)
            document_name = tool_context.state.get("tutor_document", document_name)
            difficulty_level = tool_context.state.get(
                "tutor_difficulty", difficulty_level
            )
            topic_content = tool_context.state.get("tutor_content", "")
            history = tool_context.state.get("tutor_history", [])

        # Guard: session must be active before continuing the dialogue
        if not topic_content:
            return json.dumps(
                {
                    "status": "error",
                    "error": (
                        "No active tutoring session found. "
                        "Please start a tutoring session first by calling start_tutoring_session."
                    ),
                }
            )

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

        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=followup_prompt,
        )

        tutor_message = (
            response.text or "Interesting! Can you tell me more about what you think?"
        )

        # Append tutor reply to history and persist
        history.append({"role": "tutor", "content": tutor_message})

        if tool_context:
            tool_context.state["tutor_history"] = history

            # Persist updated history to database
            try:
                from Tools.db_handler import update_tutor_session_history

                tutor_session_id = tool_context.state.get("tutor_session_id")
                if tutor_session_id:
                    await update_tutor_session_history(tutor_session_id, history)
            except Exception as e:
                print(f"[ask_followup] DB update warning: {str(e)}")

        return json.dumps(
            {
                "status": "followup_sent",
                "tutor_message": tutor_message,
                "turns_so_far": len([m for m in history if m["role"] == "student"]),
            }
        )

    except Exception as e:
        return f"Error generating follow-up: {str(e)}"
