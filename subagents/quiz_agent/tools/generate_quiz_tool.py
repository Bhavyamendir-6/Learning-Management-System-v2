from ....config import GEMINI_MODEL_NAME
import json
import traceback
from google.genai import types
from dotenv import load_dotenv

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    get_full_store_name,
    extract_user_id_from_context,
)
from Models.models import Quiz

load_dotenv()


def _normalize_doc_name(name: str) -> str:
    """Normalize a document name for fuzzy matching (lowercase, no extension)."""
    name = name.strip().lower()
    if name.endswith(".pdf"):
        name = name[:-4]
    return name


async def generate_quiz(document_name: str, tool_context=None) -> str:
    """
    Generate a 5-question MCQ quiz from a specific uploaded PDF document.
    Call this tool when the user wants to take a quiz on a document.

    Args:
        document_name: The display name of the PDF document to generate quiz from
        tool_context: ADK tool context (automatically provided)

    Returns:
        str: JSON string containing quiz questions, or an error message
    """
    try:
        client = get_client()

        # ── Step 1: Resolve store ──────────────────────────────────────────────
        store_name = get_user_store(tool_context=tool_context)
        full_store_name = get_full_store_name(store_name)

        if not full_store_name:
            return (
                f"Could not find your document store ('{store_name}'). "
                "Please upload a PDF first, then try again."
            )

        # ── Step 2: List documents ─────────────────────────────────────────────
        try:
            documents = list(
                client.file_search_stores.documents.list(parent=full_store_name)
            )
        except Exception as e:
            return (
                f"Error accessing document store '{store_name}': {str(e)}. "
                "Please try again or re-upload your document."
            )

        if not documents:
            return (
                "No documents found in your store. "
                "Please upload a PDF first, then ask for a quiz."
            )

        # ── Step 3: Find the requested document (fuzzy match) ─────────────────
        target_doc = None
        normalized_input = _normalize_doc_name(document_name)
        for doc in documents:
            display = getattr(doc, "display_name", "") or ""
            if (
                display == document_name
                or _normalize_doc_name(display) == normalized_input
            ):
                target_doc = doc
                document_name = display  # use the exact stored name going forward
                break

        if not target_doc:
            available = ", ".join(
                [getattr(d, "display_name", "Unknown") for d in documents]
            )
            return (
                f"Document '{document_name}' was not found in your store. "
                f"Documents available: {available}. "
                "Please use one of the exact names above."
            )

        # ── Step 4 (Pass 1): Retrieve document content via FileSearch ──────────
        # response_schema and FileSearch cannot be combined in one Gemini call.
        # Retrieve plain-text content first, then generate structured JSON separately.
        retrieval_prompt = (
            f"Read the document '{document_name}' thoroughly and return a detailed "
            "summary of ALL its key topics, facts, concepts, and important details. "
            "Be comprehensive — this summary will be used to create quiz questions."
        )

        try:
            retrieval_response = client.models.generate_content(
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
            document_content = retrieval_response.text or ""
        except Exception as e:
            print(f"[generate_quiz] Pass-1 retrieval error:\n{traceback.format_exc()}")
            return (
                f"Error reading content from '{document_name}': {str(e)}. "
                "Please try again."
            )

        if not document_content.strip():
            return (
                f"Could not retrieve any content from '{document_name}'. "
                "The document may still be processing — please wait a moment and try again."
            )

        # ── Step 5 (Pass 2): Generate structured quiz from retrieved content ───
        quiz_prompt = (
            f"Based on the following document content, generate exactly 5 multiple-choice quiz questions. "
            f"Document: '{document_name}'. "
            f"Content: {document_content}. "
            "Requirements: "
            "- Medium difficulty level. "
            "- Each question must have exactly 4 options labeled A, B, C, D. "
            "- Exactly one correct answer per question. "
            "- Include a helpful hint that guides thinking without revealing the answer. "
            "- Include a brief explanation for why the correct answer is correct. "
            "- Questions should cover different sections/topics from the document."
        )

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=quiz_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Quiz,
                ),
            )
        except Exception as e:
            print(f"[generate_quiz] Pass-2 generation error:\n{traceback.format_exc()}")
            return f"Error generating quiz questions: {str(e)}. Please try again."

        # Try response.parsed first, then fall back to raw JSON text
        quiz_data = response.parsed
        if not quiz_data or not quiz_data.questions:
            try:
                raw_text = response.text or ""
                if raw_text.strip():
                    raw_json = json.loads(raw_text)
                    quiz_data = Quiz(**raw_json)
            except Exception as parse_err:
                print(f"[generate_quiz] JSON fallback parse error: {parse_err}")
                quiz_data = None

        if not quiz_data or not quiz_data.questions:
            raw_preview = (response.text or "")[:400]
            print(f"[generate_quiz] Empty quiz_data. Raw response: {raw_preview}")
            return (
                "The quiz generator returned an empty response. "
                "Please try again in a moment."
            )

        questions = [q.model_dump() for q in quiz_data.questions]

        # ── Step 6: Persist state ──────────────────────────────────────────────
        if tool_context:
            tool_context.state["quiz_questions"] = questions
            tool_context.state["quiz_current_index"] = 0
            tool_context.state["quiz_score"] = 0
            tool_context.state["quiz_document"] = document_name
            tool_context.state["quiz_active"] = True

            try:
                from Tools.db_handler import start_quiz_session

                uid = extract_user_id_from_context(tool_context) or "anonymous-user"
                session_id = tool_context.state.get("session_id") or uid

                quiz_session_id = await start_quiz_session(
                    user_id=uid,
                    session_id=session_id,
                    document_name=document_name,
                    questions_list=questions,
                )
                tool_context.state["quiz_session_id"] = quiz_session_id

            except Exception as e:
                # Non-fatal: quiz works in-memory even if DB persistence fails
                print(f"[generate_quiz] DB persistence warning: {str(e)}")

        quiz_session_id = (
            tool_context.state.get("quiz_session_id") if tool_context else None
        )
        return json.dumps(
            {
                "status": "quiz_generated",
                "document": document_name,
                "total_questions": len(questions),
                "questions": questions,
                "quiz_session_id": quiz_session_id,
                "first_question": questions[0],
            }
        )

    except Exception as e:
        print(f"[generate_quiz] Unexpected error:\n{traceback.format_exc()}")
        return f"Unexpected error while generating quiz: {str(e)}"
