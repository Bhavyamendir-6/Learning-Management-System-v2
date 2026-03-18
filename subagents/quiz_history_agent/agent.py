"""Quiz History Agent - Handles quiz history and performance analytics"""

from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .tools import quiz_history, session_details, document_stats
from .prompt import QUIZ_HISTORY_AGENT_PROMPT

quiz_history_agent = Agent(
    name="Quiz_Historian",
    model=GEMINI_MODEL_NAME,
    description="Handles quiz history, session details, and per-document performance stats. Transfer to this agent when the user asks about past quizzes, scores, performance, or wants to review a specific quiz.",
    instruction=QUIZ_HISTORY_AGENT_PROMPT,
    tools=[quiz_history, session_details, document_stats],
)
