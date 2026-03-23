"""
utils/adk_logging_plugin.py — ADK Plugin for structured, correlated LMS logging.

Registered globally on the App so it covers ALL agents (root + 6 sub-agents)
without adding callbacks to each individual Agent() definition.

Logging strategy:
  INFO  — high-value operational events:
            session start/end (with total duration),
            every tool call (name, agent, args preview, result preview, duration_ms)
  DEBUG — LLM internals (model name, tools list, token counts, agent transitions)
  ERROR — any tool error or model error (with full traceback via exc_info=True)

Log lines are tagged with session_id, user_id, and invocation_id so you can
grep/filter a complete trace for a single user conversation.

Usage (fastapi_backend/adk_runner.py):
    from utils.adk_logging_plugin import LMSLoggingPlugin
    app = App(name=APP_NAME, root_agent=root_agent, plugins=[LMSLoggingPlugin()])
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional, TYPE_CHECKING

from google.genai import types
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

if TYPE_CHECKING:
    from google.adk.agents.invocation_context import InvocationContext

logger = logging.getLogger("lms.adk")


class LMSLoggingPlugin(BasePlugin):
    """
    Production-grade ADK logging plugin for the LMS multi-agent system.

    Differences from the built-in LoggingPlugin:
    - Uses Python logging module (not print) — writes to file + console via setup_logging().
    - Adds duration_ms timing to every agent, model, and tool log entry.
    - Extracts session_id / user_id / invocation_id for full log correlation.
    - Sanitizes large binary args (e.g. file_content bytes) before logging.
    - INFO for operational events; DEBUG for LLM internals; ERROR for failures.
    """

    def __init__(self) -> None:
        super().__init__("lms_logging_plugin")
        # Timing dicts keyed by string tokens so concurrent invocations don't collide
        self._invocation_start: dict[str, float] = {}
        self._agent_start: dict[str, float] = {}
        self._model_start: dict[str, float] = {}
        self._tool_start: dict[str, float] = {}

    # ── Session / Run level ──────────────────────────────────────────────────

    async def on_user_message_callback(
        self,
        *,
        invocation_context: "InvocationContext",
        user_message: types.Content,
    ) -> Optional[types.Content]:
        """Log every incoming user message with its session context."""
        inv_id = invocation_context.invocation_id
        session_id = invocation_context.session.id
        user_id = invocation_context.user_id
        preview = _preview_content(user_message)
        logger.info(
            "[user_message] session=%s user=%s inv=%s | %r",
            session_id,
            user_id,
            inv_id,
            preview,
        )
        return None

    async def before_run_callback(
        self,
        *,
        invocation_context: "InvocationContext",
    ) -> Optional[types.Content]:
        """Record invocation start time; log session + user context."""
        inv_id = invocation_context.invocation_id
        self._invocation_start[inv_id] = time.monotonic()
        session_id = invocation_context.session.id
        user_id = invocation_context.user_id
        root_agent = getattr(invocation_context.agent, "name", "unknown")
        logger.info(
            "[run_start] session=%s user=%s inv=%s root_agent=%s",
            session_id,
            user_id,
            inv_id,
            root_agent,
        )
        return None

    async def after_run_callback(
        self,
        *,
        invocation_context: "InvocationContext",
    ) -> Optional[None]:
        """Log invocation completion with total wall-clock duration."""
        inv_id = invocation_context.invocation_id
        start = self._invocation_start.pop(inv_id, None)
        duration_ms = int((time.monotonic() - start) * 1000) if start else -1
        session_id = invocation_context.session.id
        user_id = invocation_context.user_id
        final_agent = getattr(invocation_context.agent, "name", "unknown")
        logger.info(
            "[run_end] session=%s user=%s inv=%s final_agent=%s duration_ms=%d",
            session_id,
            user_id,
            inv_id,
            final_agent,
            duration_ms,
        )
        return None

    # ── Agent level ──────────────────────────────────────────────────────────

    async def before_agent_callback(
        self,
        *,
        agent: BaseAgent,
        callback_context: CallbackContext,
    ) -> Optional[types.Content]:
        """Debug-log each agent activation (useful for tracing agent transfers)."""
        inv_id = callback_context.invocation_id
        agent_name = callback_context.agent_name
        key = f"{inv_id}:{agent_name}"
        self._agent_start[key] = time.monotonic()
        logger.debug("[agent_start] inv=%s agent=%s", inv_id, agent_name)
        return None

    async def after_agent_callback(
        self,
        *,
        agent: BaseAgent,
        callback_context: CallbackContext,
    ) -> Optional[types.Content]:
        """Debug-log each agent completion with its duration."""
        inv_id = callback_context.invocation_id
        agent_name = callback_context.agent_name
        key = f"{inv_id}:{agent_name}"
        start = self._agent_start.pop(key, None)
        duration_ms = int((time.monotonic() - start) * 1000) if start else -1
        logger.debug(
            "[agent_end] inv=%s agent=%s duration_ms=%d",
            inv_id,
            agent_name,
            duration_ms,
        )
        return None

    # ── Model (LLM) level ────────────────────────────────────────────────────

    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> Optional[LlmResponse]:
        """Debug-log each LLM call: which agent, which model, which tools are available."""
        inv_id = callback_context.invocation_id
        agent_name = callback_context.agent_name
        model = getattr(llm_request, "model", None) or "default"
        key = f"{inv_id}:{agent_name}:model"
        self._model_start[key] = time.monotonic()
        tools = list(llm_request.tools_dict.keys()) if llm_request.tools_dict else []
        logger.debug(
            "[llm_request] inv=%s agent=%s model=%s tools=%s",
            inv_id,
            agent_name,
            model,
            tools,
        )
        return None

    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> Optional[LlmResponse]:
        """Debug-log LLM response: token counts and duration. Errors at ERROR level."""
        inv_id = callback_context.invocation_id
        agent_name = callback_context.agent_name
        key = f"{inv_id}:{agent_name}:model"
        start = self._model_start.pop(key, None)
        duration_ms = int((time.monotonic() - start) * 1000) if start else -1

        if llm_response.error_code:
            logger.error(
                "[llm_response] inv=%s agent=%s ERROR code=%s msg=%s duration_ms=%d",
                inv_id,
                agent_name,
                llm_response.error_code,
                llm_response.error_message,
                duration_ms,
            )
        else:
            tokens_in = tokens_out = None
            if llm_response.usage_metadata:
                tokens_in = llm_response.usage_metadata.prompt_token_count
                tokens_out = llm_response.usage_metadata.candidates_token_count
            logger.debug(
                "[llm_response] inv=%s agent=%s tokens_in=%s tokens_out=%s duration_ms=%d",
                inv_id,
                agent_name,
                tokens_in,
                tokens_out,
                duration_ms,
            )
        return None

    async def on_model_error_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
        error: Exception,
    ) -> Optional[LlmResponse]:
        """Log LLM errors with full traceback for diagnosis."""
        inv_id = callback_context.invocation_id
        agent_name = callback_context.agent_name
        logger.error(
            "[llm_error] inv=%s agent=%s error=%s",
            inv_id,
            agent_name,
            error,
            exc_info=True,
        )
        return None

    # ── Tool level ───────────────────────────────────────────────────────────

    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """INFO-log every tool invocation: name, calling agent, sanitized args."""
        call_id = tool_context.function_call_id
        self._tool_start[call_id] = time.monotonic()
        agent_name = tool_context.agent_name
        safe_args = _sanitize_args(tool_args)
        logger.info(
            "[tool_start] agent=%s tool=%s call_id=%s args=%s",
            agent_name,
            tool.name,
            call_id,
            safe_args,
        )
        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict,
    ) -> Optional[dict]:
        """INFO-log tool completion: duration and a short result preview."""
        call_id = tool_context.function_call_id
        start = self._tool_start.pop(call_id, None)
        duration_ms = int((time.monotonic() - start) * 1000) if start else -1
        agent_name = tool_context.agent_name
        result_preview = str(result)[:150] if result else "None"
        logger.info(
            "[tool_end] agent=%s tool=%s call_id=%s duration_ms=%d result=%r",
            agent_name,
            tool.name,
            call_id,
            duration_ms,
            result_preview,
        )
        return None

    async def on_tool_error_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception,
    ) -> Optional[dict]:
        """ERROR-log tool failures with full traceback."""
        call_id = tool_context.function_call_id
        self._tool_start.pop(call_id, None)  # clean up timing entry
        agent_name = tool_context.agent_name
        logger.error(
            "[tool_error] agent=%s tool=%s call_id=%s error=%s",
            agent_name,
            tool.name,
            call_id,
            error,
            exc_info=True,
        )
        return None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _preview_content(content: Optional[types.Content], max_len: int = 120) -> str:
    """Return the first text part of a Content object, truncated."""
    if not content or not content.parts:
        return "(empty)"
    for part in content.parts:
        if part.text:
            text = part.text.strip()
            return text[:max_len] + "..." if len(text) > max_len else text
    return "(non-text content)"


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of tool_args safe for logging:
    - Replace binary file_content with a byte-count summary.
    - Truncate any string value longer than 200 characters.
    """
    safe: dict[str, Any] = {}
    for key, value in args.items():
        if key == "file_content" and isinstance(value, bytes):
            safe[key] = f"<bytes len={len(value)}>"
        elif isinstance(value, str) and len(value) > 200:
            safe[key] = value[:200] + "..."
        else:
            safe[key] = value
    return safe
