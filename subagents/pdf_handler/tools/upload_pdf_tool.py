"""Upload PDF Tool - uploads a single PDF to the user's Gemini File Search store."""

import logging
import os
from typing import Annotated, Optional
from google.genai import types
from Tools.file_search_store_manager import (
    extract_user_id_from_context,
    get_client,
    get_full_store_name,
)

logger = logging.getLogger(__name__)


async def upload_pdf(
    file_path: Annotated[Optional[str], "Local file path to the PDF to upload. E.g. '/tmp/lecture.pdf'"],
    display_name: Annotated[Optional[str], "Display name for the uploaded document. E.g. 'quantum_computing_overview.pdf'"],
    tool_context=None,
) -> dict:
    """
    Upload a PDF document to the user's personal File Search store.

    Args:
        file_path: Local path to the PDF file on disk
        display_name: Friendly display name for the document

    Returns:
        dict: Upload result with status and filename
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    try:
        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

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
