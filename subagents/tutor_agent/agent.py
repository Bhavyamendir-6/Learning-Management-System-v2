"""AI Tutor Agent - Personalized one-on-one Socratic tutoring from uploaded documents"""

from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .prompt import TUTOR_AGENT_PROMPT
from .tools import (
    start_tutoring_session,
    ask_followup,
    check_understanding,
    save_learning_notes,
    get_learning_notes,
)

tutor_agent = Agent(
    name="AI_Tutor",
    model=GEMINI_MODEL_NAME,
    description=(
        "Provides personalized, interactive Socratic tutoring on topics from uploaded PDF documents. "
        "Transfer to this agent when the user wants to be tutored, learn a topic interactively, "
        "get one-on-one explanation of a concept, or have a guided learning conversation."
    ),
    instruction=TUTOR_AGENT_PROMPT,
    tools=[
        start_tutoring_session,
        ask_followup,
        check_understanding,
        save_learning_notes,
        get_learning_notes,
    ],
)
