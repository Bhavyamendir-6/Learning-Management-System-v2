"""
Tools/file_search_store_manager.py — Gemini File Search store management.

Each user gets their own store: lms-agent-store-{sanitized_user_id}.
An in-process cache maps display names to real fileSearchStores/<id> paths
to avoid repeated API calls.
"""

import hashlib
import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_client: Optional[genai.Client] = None
_store_name_cache: dict = {}


def get_client() -> genai.Client:
    """Return the shared Gemini client, creating it on first call."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def sanitize_user_id(user_id: str) -> str:
    """
    Strip characters that are invalid in a File Search store display name.
    Keeps alphanumeric, hyphens, and underscores.
    Falls back to MD5 hash if the result is empty.
    """
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", user_id)
    if not sanitized:
        sanitized = hashlib.md5(user_id.encode()).hexdigest()
    return sanitized


def get_store_name(user_id: str) -> str:
    """Return the display name for a user's File Search store."""
    return f"lms-agent-store-{sanitize_user_id(user_id)}"


def ensure_user_store_exists(user_id: str, client: genai.Client) -> str:
    """
    Return the full resource name (fileSearchStores/<id>) for the user's store,
    creating it if it doesn't exist yet.
    """
    display_name = get_store_name(user_id)

    if display_name in _store_name_cache:
        return _store_name_cache[display_name]

    # List existing stores and look for a match
    list_error = None
    try:
        stores = client.file_search_stores.list()
        for store in stores:
            if store.display_name == display_name:
                _store_name_cache[display_name] = store.name
                return store.name
    except Exception as e:
        list_error = e

    # Create a new store
    try:
        store = client.file_search_stores.create(
            config=types.CreateFileSearchStoreConfig(display_name=display_name)
        )
        _store_name_cache[display_name] = store.name
        return store.name
    except Exception as e:
        detail = f"create failed: {e}"
        if list_error:
            detail = f"list failed: {list_error}; {detail}"
        raise ValueError(f"Failed to create File Search store for user {user_id}: {detail}")


def get_full_store_name(user_id: str, tool_context=None) -> str:
    """
    Return the full resource name (fileSearchStores/<id>) for the user's store.
    Creates the store if it doesn't exist.
    """
    client = get_client()
    return ensure_user_store_exists(user_id, client)


def get_user_store(tool_context=None) -> str:
    """
    Convenience function that resolves user_id from tool_context and returns
    the full store resource name (fileSearchStores/<id>).
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"
    return get_full_store_name(user_id, tool_context=tool_context)


def extract_user_id_from_context(tool_context) -> Optional[str]:
    """
    Extract the current_user_id from ADK tool context session state.
    Returns None if tool_context is unavailable or user_id is not set.
    """
    if not tool_context:
        return None
    if hasattr(tool_context, "state") and isinstance(tool_context.state, dict):
        return tool_context.state.get("current_user_id") or None
    try:
        return tool_context.state.get("current_user_id") or None
    except Exception:
        return None
