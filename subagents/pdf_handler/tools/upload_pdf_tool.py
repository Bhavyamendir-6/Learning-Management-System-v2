"""Upload PDF Tool - uploads a single PDF to the user's Gemini File Search store."""

import logging
import os
from typing import Annotated, Optional

from google.genai import types
from google.adk.tools import ToolContext
from Tools.file_search_store_manager import (
    extract_user_id_from_context,
    get_client,
    get_full_store_name,
)

logger = logging.getLogger(__name__)


async def upload_pdf(
    file_path: Annotated[Optional[str], "Local file path to the PDF to upload. E.g. 'C:/docs/lecture.pdf'"],
    display_name: Annotated[Optional[str], "Display name for the uploaded document. E.g. 'quantum_computing_overview.pdf'"],
    file_content: Annotated[Optional[bytes], "Raw PDF bytes (used by ADK Web drag-and-drop uploads)"],
    filename: Annotated[Optional[str], "Filename to use when uploading from bytes"],
    tool_context: ToolContext,
) -> dict:
    """
    Upload a PDF document to the user's personal File Search store.

    Supports two modes:
    - file_path: path to a local file on disk (use display_name to set a friendly name)
    - file_content + filename: raw bytes (injected by before_tool_callback for ADK Web uploads)

    Args:
        file_path: Local path to the PDF file
        display_name: Friendly display name for the document
        file_content: Raw PDF bytes (used by ADK Web drag-and-drop)
        filename: Filename to use when uploading from bytes

    Returns:
        dict: Upload result with status and filename
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

        if file_content and isinstance(file_content, bytes):
            fname = display_name or filename or "uploaded_document.pdf"
            import io
            file_obj = io.BytesIO(file_content)
            file_obj.name = fname
            upload_cfg = types.UploadToFileSearchStoreConfig(
                mime_type="application/pdf", display_name=fname,
            )
            result = client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=full_store_name,
                file=file_obj,
                config=upload_cfg,
            )
            # Record upload in DB
            try:
                from database.connection import get_session
                from database.models import UploadedDocument
                import uuid as uuid_mod
                async with get_session() as session:
                    doc = UploadedDocument(
                        user_id=uuid_mod.UUID(user_id),
                        filename=fname,
                    )
                    session.add(doc)
                    await session.commit()
            except Exception as e:
                logger.warning("[upload_pdf] DB record warning: %s", e)
            return {"status": "success", "filename": fname, "message": f"Successfully uploaded '{fname}' to your document library."}

        if file_path:
            if not os.path.exists(file_path):
                return {"status": "error", "message": f"File not found at path: {file_path}"}
            fname = display_name or os.path.basename(file_path)
            upload_cfg = types.UploadToFileSearchStoreConfig(
                mime_type="application/pdf", display_name=fname,
            )
            with open(file_path, "rb") as f:
                result = client.file_search_stores.upload_to_file_search_store(
                    file_search_store_name=full_store_name,
                    file=f,
                    config=upload_cfg,
                )
            # Record upload in DB
            try:
                from database.connection import get_session
                from database.models import UploadedDocument
                import uuid as uuid_mod
                async with get_session() as session:
                    doc = UploadedDocument(
                        user_id=uuid_mod.UUID(user_id),
                        filename=fname,
                    )
                    session.add(doc)
                    await session.commit()
            except Exception as e:
                logger.warning("[upload_pdf] DB record warning: %s", e)
            return {"status": "success", "filename": fname, "message": f"Successfully uploaded '{fname}' to your document library."}

        return {"status": "error", "message": "No file path or file content provided. Please specify a file to upload."}

    except Exception as e:
        return {"status": "error", "message": f"Upload failed: {str(e)}"}
