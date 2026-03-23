"""
ADK Runner wrapper for FastAPI — native async implementation.

FastAPI is natively asynchronous, so we don't need a background thread event loop
like we did in Flask. We can just use the running asyncio event loop directly.
"""

import os
import sys
import uuid
import importlib
import logging
from pathlib import Path

from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types as genai_types
from utils.adk_logging_plugin import LMSLoggingPlugin


# Path setup to resolve LMS_Agent_UI packages
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent

for p in (str(WORKSPACE_ROOT), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


load_dotenv(PROJECT_ROOT / ".env")


# Import root_agent from LMS_Agent_UI package
_pkg_name = PROJECT_ROOT.name
_lms_pkg = importlib.import_module(_pkg_name)
root_agent = _lms_pkg.root_agent

APP_NAME = "lms_agent"
logger = logging.getLogger(__name__)

_POSTGRES_URL = os.getenv("POSTGRES_URL")
if not _POSTGRES_URL:
    raise RuntimeError("POSTGRES_URL environment variable is not set.")

# Initialize ADK Service and Runner. In FastAPI lifecycle we don't start it in
# a secondary thread because FastAPI's Uvicorn runs an asyncio event loop natively.
_session_service = DatabaseSessionService(db_url=_POSTGRES_URL)

# ── Context Caching ────────────────────────────────────────────────────────────
# Caches large system prompts (instructions) with the model so they are not
# re-sent on every request. Requires ADK >= v1.15.0 and Gemini 2.0+ models.
# min_tokens=2048  → only cache when context is large enough to be worth it
# ttl_seconds=600  → keep the cache alive for 10 minutes of inactivity
# cache_intervals=5 → refresh the cache after every 5 uses
try:
    from google.adk.apps.app import App, EventsCompactionConfig
    from google.adk.agents.context_cache_config import ContextCacheConfig

    _app = App(
        name=APP_NAME,
        root_agent=root_agent,
        # ── Logging: global plugin covering all agents, tools, and LLM calls ──────
        plugins=[LMSLoggingPlugin()],
        # ── Context Caching: caches system prompts so they aren't re-sent each request ──
        context_cache_config=ContextCacheConfig(
            min_tokens=2048,
            ttl_seconds=600,
            cache_intervals=5,
        ),
        # ── Context Compression: summarizes old conversation history every 5 turns ──
        # Requires v1 session DB schema (migrated via drop_adk_sessions.py)
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=5,
            overlap_size=1,
        ),
    )
    _runner = Runner(
        app=_app,
        session_service=_session_service,
    )
except (ImportError, Exception) as _cache_err:
    # Graceful fallback: if ADK version doesn't support context caching yet,
    # fall back to a standard Runner so the app still works.

    logger.warning(
        "Context caching not available (%s). Running without it.", _cache_err
    )
    _runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=_session_service,
    )


async def _get_or_create_session(user_id: str, session_id: str):
    """Return an existing ADK session or create a new one (Postgres-backed)."""
    session = await _session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = await _session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
            # Seed user identity so tools can read it via tool_context
            state={"current_user_id": user_id},
        )
    return session


async def run_agent_stream(
    user_id: str,
    session_id: str,
    message: str,
    file_bytes: bytes | None = None,
    filename: str | None = None,
):
    """
    Stream a response from the LMS agent using Server-Sent Events pattern.
    Yields JSON-encoded chunks: status events for tool calls / agent transfers,
    and text events for the final response content.
    """
    import json as _json

    parts: list[genai_types.Part] = [genai_types.Part(text=message)]

    if file_bytes and filename:
        parts.append(
            genai_types.Part(
                inline_data=genai_types.Blob(
                    mime_type="application/pdf", data=file_bytes
                )
            )
        )

    content = genai_types.Content(role="user", parts=parts)

    # Ensure session row exists in Postgres
    await _get_or_create_session(user_id, session_id)

    # Track emitted status events so we don't duplicate
    _emitted: set[str] = set()

    async for event in _runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        # ── Emit agent transfer events ─────────────────────────────────────
        if (
            hasattr(event, "actions")
            and event.actions
            and hasattr(event.actions, "transfer_to_agent")
            and event.actions.transfer_to_agent
        ):
            key = f"transfer:{event.actions.transfer_to_agent}"
            if key not in _emitted:
                _emitted.add(key)
                yield _json.dumps(
                    {
                        "type": "status",
                        "event": "agent_transfer",
                        "agent": event.actions.transfer_to_agent,
                    }
                )

        # ── Emit tool-call events ──────────────────────────────────────────
        try:
            fn_calls = event.get_function_calls()
        except Exception:
            fn_calls = []

        if fn_calls:
            for fc in fn_calls:
                tool_name = getattr(fc, "name", None) or str(fc)
                agent_name = getattr(event, "author", "") or ""
                key = f"tool:{agent_name}:{tool_name}"
                if key not in _emitted:
                    _emitted.add(key)
                    yield _json.dumps(
                        {
                            "type": "status",
                            "event": "tool_call",
                            "tool": tool_name,
                            "agent": agent_name,
                        }
                    )

        # ── Emit final text response ───────────────────────────────────────
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        yield _json.dumps({"type": "text", "content": part.text})


async def create_new_session(user_id: str) -> str:
    """Create a brand-new ADK session for a user and return its session_id."""
    session_id = str(uuid.uuid4())
    await _get_or_create_session(user_id, session_id)
    return session_id


async def list_user_sessions(user_id: str) -> list[dict]:
    """List all ADK sessions for a given user_id, most-recent first."""
    sessions = await _session_service.list_sessions(app_name=APP_NAME, user_id=user_id)
    result = []
    for s in sessions.sessions if sessions else []:
        result.append(
            {
                "session_id": s.id,
                "user_id": s.user_id,
                "created_at": s.last_update_time,
            }
        )
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return result


async def delete_session(user_id: str, session_id: str) -> bool:
    """Delete an ADK session (removes its events/state from Postgres)."""
    try:
        await _session_service.delete_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id,
        )
        return True
    except Exception:
        return False


async def get_session_history(user_id: str, session_id: str) -> list[dict]:
    """Reconstruct the display-ready chat message list from ADK event history."""
    from datetime import datetime, timezone

    session = await _session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    if session is None:
        return []

    messages = []
    for event in session.events:
        if not event.content or not event.content.parts:
            continue

        text_parts = [p.text for p in event.content.parts if p.text]
        if not text_parts:
            continue
        text = "\n".join(text_parts)

        ts = ""
        if event.timestamp:
            ts = datetime.fromtimestamp(event.timestamp, tz=timezone.utc).strftime(
                "%H:%M"
            )

        if event.author == "user":
            messages.append({"role": "user", "text": text, "ts": ts})
        elif event.is_final_response():
            messages.append({"role": "agent", "text": text, "ts": ts})

    return messages
