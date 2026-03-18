"""Learning Content Agent - Handles document Q&A, summaries, and flashcard generation"""

from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .prompt import LEARNING_CONTENT_AGENT_PROMPT
from .tools import ask_question, generate_summary, generate_flashcards

learning_content_agent = Agent(
    name="LearningContent_Agent",
    model=GEMINI_MODEL_NAME,
    description="Helps users learn from documents through Q&A, summaries, and flashcard generation. Transfer to this agent when users want to ask questions, create summaries, or generate flashcards from uploaded documents.",
    instruction=LEARNING_CONTENT_AGENT_PROMPT,
    tools=[ask_question, generate_summary, generate_flashcards],
)
