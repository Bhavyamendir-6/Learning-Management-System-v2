"""Start Tutoring Session Tool - initiates an interactive tutoring session on a topic."""

from ....config import GEMINI_MODEL_NAME
import json
import logging
from typing import Annotated
from google.genai import types
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    extract_user_id_from_context,
)
from Models.models import TutoringOpening
from utils.document_utils import find_document


async def start_tutoring_session(
    topic: Annotated[str, "The concept or topic to be tutored on (e.g. 'photosynthesis', 'Newton's laws')"],
    document_name: Annotated[str, "The display name of the PDF document to use as source material"],
    difficulty_level: Annotated[str, "Difficulty: 'beginner', 'intermediate', or 'advanced'"],
    tool_context: ToolContext,
) -> dict:
    """
    Begin an interactive tutoring session on a specific topic from a document.

    Retrieves relevant content from the document using File Search, then opens
    with a brief introduction and a Socratic guiding question to engage the student.

    Args:
        topic: The concept or topic to be tutored on
        document_name: The display name of the PDF document to use as source material
        difficulty_level: 'beginner', 'intermediate', or 'advanced'

    Returns:
        dict: Session info and the tutor's opening message
    """
    try:
        client = get_client()

        difficulty_level = difficulty_level.lower()
        if difficulty_level not in ("beginner", "intermediate", "advanced"):
            difficulty_level = "intermediate"

        full_store_name = get_user_store(tool_context=tool_context)

        try:
            documents = list(
                client.file_search_stores.documents.list(parent=full_store_name)
            )
        except Exception as e:
            return {"status": "error", "message": f"Error accessing document store: {str(e)}"}

        if not documents:
            return {"status": "error", "message": "No documents found in your store. Please upload a PDF first."}

        target_doc, document_name = find_document(documents, document_name)
        if not target_doc:
            available = "\n".join(
                [f"  - {getattr(d, 'display_name', 'Unknown')}" for d in documents]
            )
            return {
                "status": "error",
                "message": (
                    f"Document '{document_name}' not found.\n\n"
                    f"Available documents:\n{available}\n\n"
                    "Please use the exact name from the list above."
                ),
            }

        # Retrieve topic-specific content via File Search
        retrieval_prompt = (
            f"From the document '{document_name}', retrieve all content related to "
            f"the topic: '{topic}'. Include definitions, key concepts, important facts, "
            f"examples, and any related subtopics. Be thorough."
        )

        retrieval_response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=retrieval_prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[full_store_name]
                        )
                    )
                ],
            ),
        )
        topic_content = retrieval_response.text or ""
        if not topic_content.strip():
            return {
                "status": "error",
                "message": (
                    f"Could not find content about '{topic}' in '{document_name}'. "
                    "Try a different topic or check the document name."
                ),
            }

        # Build difficulty-appropriate opening prompt
        difficulty_instructions = {
            "beginner": (
                "Use simple language, avoid jargon, and use everyday analogies. "
                "Start from first principles."
            ),
            "intermediate": (
                "Assume basic familiarity with the subject. Use domain terminology "
                "where appropriate but explain it when introduced."
            ),
            "advanced": (
                "Assume strong background knowledge. Use precise technical language, "
                "explore nuances, and challenge the student to think deeply."
            ),
        }

        opening_prompt = (
            f"You are a Socratic tutor helping a student learn about '{topic}' "
            f"from the document '{document_name}'. "
            f"Difficulty: {difficulty_level}. {difficulty_instructions[difficulty_level]}. "
            f"Document content on this topic: {topic_content}. "
            "Generate a tutoring opening with: "
            "1. A brief introduction to the topic (2-3 sentences max). "
            "2. ONE open-ended Socratic question to gauge what the student already knows. "
            "Do NOT give away the full explanation yet — the goal is to start a dialogue."
        )

        opening_response = await client.aio.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=opening_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TutoringOpening,
            ),
        )
        opening_data: TutoringOpening = opening_response.parsed
        if opening_data:
            opening_message = (
                f"{opening_data.introduction}\n\n{opening_data.opening_question}"
            )
        else:
            opening_message = f"Let's explore '{topic}' together. What do you already know about this topic?"

        # Persist session state
        tool_context.state["tutor_topic"] = topic
        tool_context.state["tutor_document"] = document_name
        tool_context.state["tutor_difficulty"] = difficulty_level
        tool_context.state["tutor_content"] = topic_content
        tool_context.state["tutor_opening_question"] = (
            opening_data.opening_question if opening_data else ""
        )
        tool_context.state["tutor_history"] = [
            {"role": "tutor", "content": opening_message}
        ]
        tool_context.state["tutor_active"] = True

        # Persist to database
        try:
            from Tools.db_handler import start_tutor_session

            uid = extract_user_id_from_context(tool_context) or "anonymous-user"
            session_id = tool_context.state.get("session_id") or uid

            tutor_session_id = await start_tutor_session(
                user_id=uid,
                session_id=session_id,
                document_name=document_name,
                topic=topic,
                difficulty_level=difficulty_level,
            )
            tool_context.state["tutor_session_id"] = tutor_session_id
        except Exception as e:
            logger.warning("[start_tutoring_session] DB persistence warning: %s", e)

        return {
            "status": "session_started",
            "topic": topic,
            "document": document_name,
            "difficulty_level": difficulty_level,
            "tutor_message": opening_message,
        }

    except Exception as e:
        return {"status": "error", "message": f"Error starting tutoring session: {str(e)}"}
