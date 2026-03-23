"""Batch Upload PDF Tool - uploads multiple PDFs to the user's Gemini File Search store."""

import logging
import os
from typing import Annotated, List

from google.genai import types
from google.adk.tools import ToolContext
from Tools.file_search_store_manager import (
    extract_user_id_from_context,
    get_client,
    get_full_store_name,
)

logger = logging.getLogger(__name__)


async def _upload_single_file_from_path(
    client,
    file_path: str,
    full_store_name: str,
    current_index: int,
    total_files: int,
) -> tuple:
    """Upload a single file. Returns (filename, success, error_message)."""
    fname = os.path.basename(file_path)
    try:
        if not os.path.exists(file_path):
            return fname, False, f"File not found: {file_path}"
        upload_cfg = types.UploadToFileSearchStoreConfig(
            mime_type="application/pdf", display_name=fname,
        )
        with open(file_path, "rb") as f:
            client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=full_store_name,
                file=f,
                config=upload_cfg,
            )
        return fname, True, None
    except Exception as e:
        return fname, False, str(e)


async def batch_upload_pdf(
    file_paths: Annotated[List[str], "List of local file paths to PDFs to upload. E.g. ['C:/docs/a.pdf', 'C:/docs/b.pdf']"],
    tool_context: ToolContext,
) -> dict:
    """
    Upload multiple PDF documents to the user's personal File Search store.

    Args:
        file_paths: List of local paths to PDF files

    Returns:
        dict: Summary of successful and failed uploads
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"

    if not file_paths:
        return {"status": "error", "message": "No file paths provided."}

    try:
        client = get_client()
        full_store_name = get_full_store_name(user_id, tool_context=tool_context)

        successful_uploads = []
        failed_uploads = []
        total = len(file_paths)

        for i, file_path in enumerate(file_paths, start=1):
            fname, success, error = await _upload_single_file_from_path(
                client, file_path, full_store_name, i, total
            )
            if success:
                successful_uploads.append(fname)
                # Record in DB
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
                    logger.warning("[batch_upload_pdf] DB record warning for %s: %s", fname, e)
            else:
                failed_uploads.append({"filename": fname, "error": error})

        return {
            "status": "completed",
            "total": total,
            "successful": successful_uploads,
            "failed": failed_uploads,
            "message": f"Batch upload complete: {len(successful_uploads)}/{total} files uploaded.",
        }

    except Exception as e:
        return {"status": "error", "message": f"Batch upload failed: {str(e)}"}
