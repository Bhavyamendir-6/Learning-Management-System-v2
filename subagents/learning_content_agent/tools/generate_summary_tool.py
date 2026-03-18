"""Generate Summary Tool for Learning Content Agent — two-pass FileSearch + structured output."""

from ....config import GEMINI_MODEL_NAME
import json
import traceback
from google.genai import types
from dotenv import load_dotenv

from Tools.file_search_store_manager import (
    get_client,
    get_user_store,
    get_full_store_name,
)
from Models.models import Summary

load_dotenv()


async def generate_summary(
    document_name: str,
    summary_type: str = "brief",
    tool_context=None,
) -> str:
    """
    Generate a summary of a specific uploaded PDF document using File Search.

    Args:
        document_name: The display name of the PDF document to summarize
        summary_type: Type of summary - "brief", "detailed", or "key_points" (default: "brief")

    Returns:
        str: JSON string containing the summary, or an error message
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

        # ── Step 2 (Pass 1): Retrieve document content via FileSearch ──────────
        # response_schema and FileSearch cannot be combined in one Gemini call.
        # Retrieve plain-text content first, then generate structured JSON separately.
        retrieval_prompt = (
            f"Read the document '{document_name}' thoroughly and return a detailed "
            "summary of ALL its key topics, facts, concepts, and important details. "
            "Be comprehensive — this content will be used to generate a structured summary."
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
            print(
                f"[generate_summary] Pass-1 retrieval error:\n{traceback.format_exc()}"
            )
            return (
                f"Error reading content from '{document_name}': {str(e)}. "
                "Please try again."
            )

        if not document_content.strip():
            return (
                f"Could not retrieve any content from '{document_name}'. "
                "The document may still be processing — please wait a moment and try again."
            )

        # ── Step 3 (Pass 2): Generate structured summary from retrieved content ─
        type_instructions = {
            "brief": "Create a concise summary (2-3 paragraphs) covering the main points.",
            "detailed": "Create a comprehensive, detailed summary covering all major sections and key details.",
            "key_points": "Extract and list the key points and main takeaways as bullet points.",
        }
        instruction = type_instructions.get(summary_type, type_instructions["brief"])

        summary_prompt = (
            f"Based on the following document content, generate a {summary_type} summary "
            f"of the document '{document_name}'.\n\n"
            f"{instruction}\n\n"
            f"Document content:\n{document_content}\n\n"
            "Include:\n"
            "- title\n"
            "- content (the summary text)\n"
            "- summary_type\n"
            "- key_takeaways (list of key points)"
        )

        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=summary_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Summary,
                ),
            )
        except Exception as e:
            print(
                f"[generate_summary] Pass-2 generation error:\n{traceback.format_exc()}"
            )
            return f"Error generating summary: {str(e)}. Please try again."

        # Try response.parsed first, then fall back to raw JSON text
        summary_data = response.parsed
        if not summary_data:
            try:
                raw_text = response.text or ""
                if raw_text.strip():
                    raw_json = json.loads(raw_text)
                    summary_data = Summary(**raw_json)
            except Exception as parse_err:
                print(f"[generate_summary] JSON fallback parse error: {parse_err}")
                summary_data = None

        if not summary_data:
            return "The summary generator returned an empty response. Please try again."

        return json.dumps(summary_data.model_dump())

    except Exception as e:
        print(f"[generate_summary] Unexpected error:\n{traceback.format_exc()}")
        return f"Unexpected error while generating summary: {str(e)}"
