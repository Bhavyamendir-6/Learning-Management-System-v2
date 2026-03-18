"""Quiz Agent - Handles interactive quizzes"""

from ...config import GEMINI_MODEL_NAME
from google.adk.agents import Agent
from .tools import generate_quiz, record_answer, complete_quiz, retry_quiz
from .prompt import QUIZ_AGENT_PROMPT

quiz_agent = Agent(
    name="Quiz_Master",
    model=GEMINI_MODEL_NAME,
    description="Handles interactive MCQ quizzes based on uploaded PDF documents. Transfer to this agent when the user wants to take a quiz, test their knowledge, or be quizzed on a document.",
    instruction=QUIZ_AGENT_PROMPT,
    tools=[generate_quiz, record_answer, complete_quiz, retry_quiz],
)
